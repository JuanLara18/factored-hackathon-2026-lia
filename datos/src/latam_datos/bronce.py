"""DAT-1.2: constructor de bronce. CSV del espejo a Parquet, todo como texto, un lote por objeto y etag.

Bronce es de solo agregar (R-DAT-05): una reentrega agrega un lote nuevo y no toca los anteriores; nada se
corrige. Metadatos por fila: `_lote_id`, `_linea`, `_huella_fila`. El resto vive en `bronce._lotes`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from latam_datos.config import (
    GENERACION_ACTUAL,
    GENERACION_RESPALDO,
    PREFIJO_AUTORIZADO,
    PREFIJO_RESPALDO,
    Rutas,
)
from latam_datos.espejo import leer_indice
from latam_datos.reglas import (
    UMBRAL_MALFORMADAS,
    UMBRAL_SOLAPAMIENTO,
    Hallazgo,
    Resultado,
    bom_residual,
    comparar_encabezado,
    decodificar_utf8,
    quitar_bom,
    solapamiento,
)

_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
_SEP = "\x1f"
_NULO = "@@sin_nulos@@"

_DDL_LOTES = """
CREATE TABLE IF NOT EXISTS bronce._lotes (
    lote_id VARCHAR PRIMARY KEY, source_key VARCHAR, etag VARCHAR, tamano BIGINT,
    last_modified TIMESTAMP, huella_encabezado VARCHAR, generacion VARCHAR, tenia_bom BOOLEAN,
    filas BIGINT, ingerido_en TIMESTAMP, clase VARCHAR,
    estado VARCHAR, tabla VARCHAR, process_date VARCHAR, columnas VARCHAR, huella_lote VARCHAR,
    filas_cuarentena BIGINT, ruta_parquet VARCHAR
)
"""

ESTADO_APLICADO = "aplicado"


@dataclass
class ResultadoBronce:
    hallazgos: list[Hallazgo] = field(default_factory=lambda: [])
    aplicados: list[str] = field(default_factory=lambda: [])
    bloqueados: list[str] = field(default_factory=lambda: [])
    ignorados: list[str] = field(default_factory=lambda: [])


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def lote_id_de(source_key: str, etag: str) -> str:
    """Primeros 16 caracteres hexadecimales de SHA-256 de `source_key` y `etag`."""
    return sha(f"{source_key}{_SEP}{etag}")[:16]


def generacion_de(source_key: str) -> str:
    return GENERACION_RESPALDO if source_key.startswith(PREFIJO_RESPALDO) else GENERACION_ACTUAL


def _tabla_y_fecha(source_key: str) -> tuple[str, str]:
    partes = source_key.split("/")
    resto = "/".join(partes[2:])
    m = _FECHA.search(resto)
    return partes[1], (m.group(0) if m else "sin_fecha")


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


class _Lineas:
    """Iterador de líneas que recuerda cuáles consumió cada registro, para guardar la línea cruda."""

    def __init__(self, texto: str) -> None:
        self._it = io.StringIO(texto, newline="")
        self.consumidas: list[str] = []

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        linea = next(self._it)
        self.consumidas.append(linea)
        return linea


def _escribir_parquet(
    con: duckdb.DuckDBPyConnection,
    destino: Path,
    columnas: list[str],
    filas: list[list[str]],
) -> None:
    """Todo VARCHAR; los vacíos se conservan como cadena vacía (copia fiel)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "lote.csv"
        with ruta.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
            w.writerow(columnas)
            w.writerows(filas)
        tipos = ", ".join(f"{_literal(c)}: 'VARCHAR'" for c in columnas)
        con.execute(
            f"COPY (SELECT * FROM read_csv({_literal(ruta.as_posix())}, header=true, "
            f"columns={{{tipos}}}, nullstr={_literal(_NULO)})) "
            f"TO {_literal(destino.as_posix())} (FORMAT parquet, COMPRESSION zstd)"
        )


def _encabezado_de_referencia(con: duckdb.DuckDBPyConnection, tabla: str) -> list[str] | None:
    """Sin contrato de fuente todavía, la referencia es el primer lote aplicado de la tabla."""
    fila = con.execute(
        "SELECT columnas FROM bronce._lotes WHERE tabla = ? AND estado = ? "
        "ORDER BY ingerido_en, source_key LIMIT 1",
        [tabla, ESTADO_APLICADO],
    ).fetchone()
    return None if fila is None else json.loads(fila[0])


def _llaves_vigentes(con: duckdb.DuckDBPyConnection, rutas: Rutas, source_key: str) -> set[str] | None:
    fila = con.execute(
        "SELECT ruta_parquet, columnas FROM bronce._lotes WHERE source_key = ? AND estado = ? "
        "ORDER BY ingerido_en DESC, rowid DESC LIMIT 1",
        [source_key, ESTADO_APLICADO],
    ).fetchone()
    if fila is None:
        return None
    primera = json.loads(fila[1])[0]
    filas = con.execute(
        f'SELECT DISTINCT "{primera}" FROM read_parquet(?)',
        [(rutas.bronce / fila[0]).as_posix()],
    ).fetchall()
    return {str(r[0]) for r in filas}


def _registrar(con: duckdb.DuckDBPyConnection, valores: tuple[object, ...]) -> None:
    con.execute("INSERT INTO bronce._lotes VALUES (" + ", ".join("?" * 18) + ")", list(valores))


def construir_bronce(
    rutas: Rutas,
    con: duckdb.DuckDBPyConnection,
    ahora: datetime,
    contratos: dict[str, list[str]] | None = None,
) -> ResultadoBronce:
    """Procesa cada CSV del espejo bajo `data/` que no tenga ya un lote con su etag (Q-BRZ-10)."""
    con.execute(_DDL_LOTES)
    resultado = ResultadoBronce()
    indice = leer_indice(rutas.espejo)
    marca = ahora.astimezone(UTC).replace(tzinfo=None)
    for source_key in sorted(indice):
        if not source_key.startswith(PREFIJO_AUTORIZADO) or not source_key.endswith(".csv"):
            continue
        meta = indice[source_key]
        etag = str(meta["etag"])
        lote_id = lote_id_de(source_key, etag)
        tabla, process_date = _tabla_y_fecha(source_key)

        def hallar(
            regla: str,
            res: Resultado,
            detalle: str,
            filas: int = 0,
            *,
            _t: str = tabla,
            _l: str = lote_id,
            _k: str = source_key,
        ) -> None:
            resultado.hallazgos.append(Hallazgo(regla, res, detalle, _t, _l, _k, filas))

        if con.execute(
            "SELECT 1 FROM bronce._lotes WHERE source_key = ? AND etag = ?", [source_key, etag]
        ).fetchone():
            resultado.ignorados.append(lote_id)
            hallar("Q-BRZ-10", "control", "mismo etag ya registrado; no crea lote")
            continue

        previo = con.execute(
            "SELECT 1 FROM bronce._lotes WHERE source_key = ? AND estado = ?", [source_key, ESTADO_APLICADO]
        ).fetchone()
        clase = "REENTREGA" if previo else "NUEVO"
        crudo = (rutas.espejo / source_key).read_bytes()
        sin_bom, tenia_bom = quitar_bom(crudo)
        if tenia_bom:
            hallar("Q-BRZ-02", "aviso", "BOM UTF-8 quitado")

        def cerrar(
            estado: str,
            filas: int,
            columnas: list[str],
            huella_enc: str,
            huella_lote: str,
            cuarentena: int,
            ruta: str,
            *,
            _c: str = clase,
            _b: bool = tenia_bom,
            _m: dict[str, object] = meta,
            _t: str = tabla,
            _p: str = process_date,
            _l: str = lote_id,
            _k: str = source_key,
            _e: str = etag,
        ) -> None:
            _registrar(
                con,
                (
                    _l, _k, _e, int(str(_m["tamano"])),
                    datetime.fromisoformat(str(_m["last_modified"])).astimezone(UTC).replace(tzinfo=None),
                    huella_enc, generacion_de(_k), _b, filas, marca, _c, estado, _t, _p,
                    json.dumps(columnas), huella_lote, cuarentena, ruta,
                ),
            )  # fmt: skip
            (resultado.aplicados if estado == ESTADO_APLICADO else resultado.bloqueados).append(_l)

        texto = decodificar_utf8(sin_bom)
        if texto is None:
            hallar("Q-BRZ-04", "bloqueado", "el archivo no es UTF-8 válido")
            cerrar("bloqueado_esquema", 0, [], "", "", 0, "")
            continue

        lineas = _Lineas(texto)
        lector = csv.reader(lineas)
        try:
            columnas = next(lector)
        except StopIteration:
            hallar("Q-BRZ-03", "bloqueado", "archivo sin encabezado")
            cerrar("bloqueado_esquema", 0, [], "", "", 0, "")
            continue
        huella_enc = sha(_SEP.join(columnas))
        if bom_residual(columnas):
            hallar("Q-BRZ-02", "bloqueado", "un nombre de columna empieza con U+FEFF")
            cerrar("bloqueado_esquema", 0, columnas, huella_enc, "", 0, "")
            continue
        esperado = (contratos or {}).get(tabla) or _encabezado_de_referencia(con, tabla)
        cmp = comparar_encabezado(esperado, columnas)
        if cmp == "bloqueado":
            hallar("Q-BRZ-03", "bloqueado", "columna faltante, renombrada o encabezado inválido")
            cerrar("bloqueado_esquema", 0, columnas, huella_enc, "", 0, "")
            continue
        if cmp == "aditivo":
            hallar("Q-BRZ-03", "aviso", "columnas nuevas frente a la referencia")

        lineas.consumidas.clear()
        buenas: list[list[str]] = []
        malas: list[list[str]] = []
        huellas: list[str] = []
        linea_ini = 2
        for campos in lector:
            n_lineas = len(lineas.consumidas)
            cruda = "".join(lineas.consumidas)
            lineas.consumidas.clear()
            if len(campos) != len(columnas):
                malas.append([lote_id, str(linea_ini), cruda])
            else:
                h = sha(_SEP.join(campos))
                huellas.append(h)
                buenas.append([*campos, lote_id, str(linea_ini), h])
            linea_ini += n_lineas
        total = len(buenas) + len(malas)
        if total == 0:
            hallar("Q-BRZ-11", "aviso", "archivo vacío: solo encabezado")
        if malas:
            if len(malas) / total > UMBRAL_MALFORMADAS:
                hallar("Q-BRZ-05", "bloqueado", f"{len(malas)} de {total} filas malformadas", len(malas))
                cerrar("bloqueado_sistematico", 0, columnas, huella_enc, "", len(malas), "")
                continue
            hallar("Q-BRZ-05", "cuarentena", f"{len(malas)} filas malformadas a cuarentena", len(malas))

        if clase == "REENTREGA":
            vigentes = _llaves_vigentes(con, rutas, source_key)
            if vigentes:
                comun = solapamiento({f[0] for f in buenas}, vigentes)
                if comun < UMBRAL_SOLAPAMIENTO:
                    hallar(
                        "Q-BRZ-08",
                        "bloqueado",
                        f"solapamiento de llaves {comun:.0%}: regeneración",
                        len(buenas),
                    )
                    cerrar("bloqueado_regeneracion", 0, columnas, huella_enc, "", len(malas), "")
                    continue

        relativa = f"{tabla}/process_date={process_date}/{lote_id}.parquet"
        _escribir_parquet(
            con, rutas.bronce / relativa, [*columnas, "_lote_id", "_linea", "_huella_fila"], buenas
        )
        if malas:
            _escribir_parquet(
                con,
                rutas.bronce / "_cuarentena" / tabla / f"{lote_id}.parquet",
                ["_lote_id", "_linea", "linea_cruda"],
                malas,
            )
        huella_lote = sha(huella_enc + _SEP + _SEP.join(huellas))
        cerrar(ESTADO_APLICADO, len(buenas), columnas, huella_enc, huella_lote, len(malas), relativa)
    return resultado
