"""DAT-1.2: constructor de bronce en BigQuery (`latam_bronce`). CSV de Cloud Storage a tablas todo STRING.

Bronce es de solo agregar (R-DAT-05): una reentrega agrega un lote nuevo y no reescribe los anteriores;
nada se corrige. Por cada objeto autorizado nuevo:

1. Se lee, se quita el BOM, se valida UTF-8 y encabezado, y se separan las filas malformadas (cuarentena).
   Las filas buenas se reescriben en un CSV normalizado con su número de línea física (`_linea`).
2. BigQuery lo carga como STRING a una tabla temporal; el solapamiento de llaves (Q-BRZ-08) y las huellas
   (`_huella_fila`, `huella_lote`) se calculan en SQL.
3. Si pasa, se agrega a `latam_bronce.<tabla>` con `_lote_id`, `_linea` y `_huella_fila` y se registra el lote
   en `latam_bronce._lotes`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from latam_datos.config import (
    CUARENTENA,
    GENERACION_ACTUAL,
    GENERACION_RESPALDO,
    LOTES,
    PREFIJO_RESPALDO,
    PREFIJO_STAGING,
)
from latam_datos.espejo import Almacen
from latam_datos.motor import SEPARADOR, Logico, Motor
from latam_datos.reglas import (
    UMBRAL_MALFORMADAS,
    UMBRAL_SOLAPAMIENTO,
    Hallazgo,
    Resultado,
    bom_residual,
    comparar_encabezado,
    decodificar_utf8,
    quitar_bom,
    sql_solapamiento,
)

_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
ESTADO_APLICADO = "aplicado"

_COLUMNAS_LOTES: tuple[tuple[str, Logico], ...] = (
    ("lote_id", "texto"),
    ("source_key", "texto"),
    ("etag", "texto"),
    ("generacion_objeto", "entero"),
    ("tamano", "entero"),
    ("last_modified", "fecha_hora"),
    ("huella_encabezado", "texto"),
    ("generacion", "texto"),
    ("tenia_bom", "booleano"),
    ("filas", "entero"),
    ("ingerido_en", "fecha_hora"),
    ("clase", "texto"),
    ("estado", "texto"),
    ("tabla", "texto"),
    ("process_date", "texto"),
    ("columnas", "texto"),
    ("huella_lote", "texto"),
    ("filas_cuarentena", "entero"),
    ("tabla_destino", "texto"),
)

_COLUMNAS_CUARENTENA: tuple[tuple[str, Logico], ...] = (
    ("lote_id", "texto"),
    ("tabla", "texto"),
    ("linea", "entero"),
    ("linea_cruda", "texto"),
)


@dataclass
class ResultadoBronce:
    hallazgos: list[Hallazgo] = field(default_factory=lambda: [])
    aplicados: list[str] = field(default_factory=lambda: [])
    bloqueados: list[str] = field(default_factory=lambda: [])
    ignorados: list[str] = field(default_factory=lambda: [])


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def lote_id_de(source_key: str, etag: str) -> str:
    """Primeros 16 hexadecimales de SHA-256 de `source_key` y `etag` (aquí, el md5 del contenido)."""
    return sha(f"{source_key}{SEPARADOR}{etag}")[:16]


def generacion_de(source_key: str) -> str:
    return GENERACION_RESPALDO if source_key.startswith(PREFIJO_RESPALDO) else GENERACION_ACTUAL


def tabla_y_fecha(source_key: str) -> tuple[str, str]:
    partes = source_key.split("/")
    m = _FECHA.search("/".join(partes[2:]))
    return re.sub(r"\W", "_", partes[1]), (m.group(0) if m else "sin_fecha")


def crear_tablas_bronce(motor: Motor) -> None:
    cols = ", ".join(f"{c} {motor.tipo(t)}" for c, t in _COLUMNAS_LOTES)
    motor.ejecutar(f"CREATE TABLE IF NOT EXISTS {motor.t(LOTES)} ({cols})")
    q = ", ".join(f"{c} {motor.tipo(t)}" for c, t in _COLUMNAS_CUARENTENA)
    motor.ejecutar(f"CREATE TABLE IF NOT EXISTS {motor.t(CUARENTENA)} ({q})")


class _Lineas:
    """Iterador de líneas que recuerda las que consumió cada registro, para conservar la línea cruda."""

    def __init__(self, texto: str) -> None:
        self._it = io.StringIO(texto, newline="")
        self.consumidas: list[str] = []

    def __iter__(self) -> _Lineas:
        return self

    def __next__(self) -> str:
        linea = next(self._it)
        self.consumidas.append(linea)
        return linea


def _hash_fila_sql(motor: Motor, columnas: list[str]) -> str:
    partes = [f"COALESCE({motor.ident(c)}, '')" for c in columnas]
    return motor.sha256("CONCAT(" + ", CHR(31), ".join(partes) + ")")


def _csv_normalizado(columnas: list[str], filas: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writerow([*columnas, "_linea"])
    w.writerows(filas)
    return buf.getvalue().encode("utf-8")


def construir_bronce(
    almacen: Almacen,
    motor: Motor,
    ahora: datetime,
    contratos: dict[str, list[str]] | None = None,
) -> ResultadoBronce:
    """Procesa cada CSV autorizado que no tenga ya un lote con su contenido (Q-BRZ-10)."""
    crear_tablas_bronce(motor)
    resultado = ResultadoBronce()
    marca = ahora.astimezone(UTC)
    lotes = motor.t(LOTES)
    for obj in almacen.listar():
        if not obj.autorizado or not obj.key.endswith(".csv"):
            continue
        source_key = obj.key
        lote_id = lote_id_de(source_key, obj.md5)
        tabla, process_date = tabla_y_fecha(source_key)
        destino = f"latam_bronce.{tabla}"

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

        ya = motor.consultar(
            f"SELECT 1 FROM {lotes} WHERE source_key = {motor.lit(source_key)} "
            f"AND etag = {motor.lit(obj.md5)}"
        )
        if ya:
            resultado.ignorados.append(lote_id)
            hallar("Q-BRZ-10", "control", "mismo contenido ya registrado; no crea lote")
            continue

        previo = motor.consultar(
            f"SELECT lote_id FROM {lotes} WHERE source_key = {motor.lit(source_key)} "
            f"AND estado = '{ESTADO_APLICADO}' ORDER BY ingerido_en DESC, lote_id DESC LIMIT 1"
        )
        clase = "REENTREGA" if previo else "NUEVO"
        sin_bom, tenia_bom = quitar_bom(almacen.leer(source_key))
        if tenia_bom:
            hallar("Q-BRZ-02", "aviso", "BOM UTF-8 quitado")

        def cerrar(
            estado: str,
            filas: int,
            columnas: list[str],
            huella_enc: str,
            huella_lote: str,
            cuarentena: int,
            tabla_destino: str,
            *,
            _c: str = clase,
            _b: bool = tenia_bom,
            _t: str = tabla,
            _p: str = process_date,
            _l: str = lote_id,
            _o: Any = obj,
        ) -> None:
            valores = (
                _l, _o.key, _o.md5, _o.generation, _o.tamano, _o.actualizado.astimezone(UTC), huella_enc,
                generacion_de(_o.key), _b, filas, marca, _c, estado, _t, _p, json.dumps(columnas),
                huella_lote, cuarentena, tabla_destino,
            )  # fmt: skip
            motor.ejecutar(f"INSERT INTO {lotes} VALUES (" + ", ".join(motor.lit(v) for v in valores) + ")")
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
        huella_enc = sha(SEPARADOR.join(columnas))
        if bom_residual(columnas):
            hallar("Q-BRZ-02", "bloqueado", "un nombre de columna empieza con U+FEFF")
            cerrar("bloqueado_esquema", 0, columnas, huella_enc, "", 0, "")
            continue
        referencia = (contratos or {}).get(tabla)
        if referencia is None:
            ref = motor.consultar(
                f"SELECT columnas FROM {lotes} WHERE tabla = {motor.lit(tabla)} "
                f"AND estado = '{ESTADO_APLICADO}' "
                f"ORDER BY ingerido_en, source_key LIMIT 1"
            )
            referencia = json.loads(ref[0][0]) if ref else None
        cmp = comparar_encabezado(referencia, columnas)
        if cmp == "bloqueado":
            hallar("Q-BRZ-03", "bloqueado", "columna faltante, renombrada o encabezado inválido")
            cerrar("bloqueado_esquema", 0, columnas, huella_enc, "", 0, "")
            continue
        if cmp == "aditivo":
            hallar("Q-BRZ-03", "aviso", "columnas nuevas frente a la referencia")

        lineas.consumidas.clear()
        buenas: list[list[str]] = []
        malas: list[tuple[int, str]] = []
        linea = 2
        for campos in lector:
            n = len(lineas.consumidas)
            cruda = "".join(lineas.consumidas)
            lineas.consumidas.clear()
            if len(campos) != len(columnas):
                malas.append((linea, cruda))
            else:
                buenas.append([*campos, str(linea)])
            linea += n
        total = len(buenas) + len(malas)
        if total == 0:
            hallar("Q-BRZ-11", "aviso", "archivo vacío: solo encabezado")
        if malas:
            if len(malas) / total > UMBRAL_MALFORMADAS:
                hallar("Q-BRZ-05", "bloqueado", f"{len(malas)} de {total} filas malformadas", len(malas))
                cerrar("bloqueado_sistematico", 0, columnas, huella_enc, "", len(malas), "")
                continue
            hallar("Q-BRZ-05", "cuarentena", f"{len(malas)} filas malformadas a cuarentena", len(malas))

        staging = f"latam_bronce._stg_{lote_id}"
        clave_staging = f"{PREFIJO_STAGING}{lote_id}.csv"
        uri = almacen.escribir(clave_staging, _csv_normalizado(columnas, buenas))
        try:
            motor.cargar_csv(uri, staging, [*columnas, "_linea"])
            if clase == "REENTREGA" and buenas:
                nuevas, comunes = motor.consultar(
                    sql_solapamiento(motor, staging, destino, columnas[0], str(previo[0][0]))
                )[0]
                if nuevas and int(comunes) / int(nuevas) < UMBRAL_SOLAPAMIENTO:
                    hallar(
                        "Q-BRZ-08",
                        "bloqueado",
                        f"solapamiento de llaves {int(comunes) / int(nuevas):.0%}: regeneración",
                        int(nuevas),
                    )
                    cerrar("bloqueado_regeneracion", 0, columnas, huella_enc, "", len(malas), "")
                    continue
            cols_sql = ", ".join(motor.ident(c) for c in columnas)
            defs = ", ".join(f"{motor.ident(c)} {motor.tipo('texto')}" for c in columnas)
            motor.ejecutar(
                f"CREATE TABLE IF NOT EXISTS {motor.t(destino)} ({defs}, _lote_id {motor.tipo('texto')}, "
                f"_linea {motor.tipo('entero')}, _huella_fila {motor.tipo('texto')})"
            )
            for c in columnas:  # evolución aditiva del esquema (Q-BRZ-03)
                motor.ejecutar(
                    f"ALTER TABLE {motor.t(destino)} ADD COLUMN IF NOT EXISTS "
                    f"{motor.ident(c)} {motor.tipo('texto')}"
                )
            motor.ejecutar(
                f"INSERT INTO {motor.t(destino)} ({cols_sql}, _lote_id, _linea, _huella_fila) "
                f"SELECT {cols_sql}, {motor.lit(lote_id)}, CAST(_linea AS {motor.tipo('entero')}), "
                f"{_hash_fila_sql(motor, columnas)} FROM {motor.t(staging)}"
            )
            fila = motor.consultar(
                f"SELECT COUNT(*), {motor.sha256(motor.agregar_texto('_huella_fila', 'CHR(31)', '_linea'))} "
                f"FROM {motor.t(destino)} WHERE _lote_id = {motor.lit(lote_id)}"
            )[0]
            huella_lote = sha(huella_enc + SEPARADOR + str(fila[1] or ""))
            for numero, cruda in malas:
                motor.ejecutar(
                    f"INSERT INTO {motor.t(CUARENTENA)} VALUES ({motor.lit(lote_id)}, "
                    f"{motor.lit(tabla)}, {numero}, {motor.lit(cruda)})"
                )
            cerrar(ESTADO_APLICADO, int(fila[0]), columnas, huella_enc, huella_lote, len(malas), destino)
        finally:
            motor.ejecutar(f"DROP TABLE IF EXISTS {motor.t(staging)}")
            almacen.borrar(clave_staging)
    return resultado
