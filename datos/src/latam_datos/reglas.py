"""DAT-1.3: reglas de bronce Q-BRZ-01 a Q-BRZ-11 (definición, sección 2.4) y su reporte en platino.

Las comprobaciones puras (BOM, codificación, encabezado, solapamiento) son funciones sin efectos; el
constructor de bronce las aplica por lote y `evaluar_globales` cubre las que miran todo el conjunto.
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

import duckdb

from latam_datos.config import GENERACION_ACTUAL
from latam_datos.espejo import ObjetoS3

BOM = codecs.BOM_UTF8
BOM_CARACTER = "﻿"
INICIO_PARTICIONES = date(2023, 6, 17)
FIN_PARTICIONES = date(2026, 6, 17)
UMBRAL_MALFORMADAS = 0.01
UMBRAL_SOLAPAMIENTO = 0.5
MUESTRA_MINIMA_PERCENTILES = 20

Resultado = Literal["ok", "aviso", "bloqueado", "cuarentena", "control"]

# regla -> (dimension, severidad declarada en la definicion)
REGLAS: dict[str, tuple[str, str]] = {
    "Q-BRZ-01": ("completitud", "aviso"),
    "Q-BRZ-02": ("conformidad", "bloqueante"),
    "Q-BRZ-03": ("conformidad", "segun caso"),
    "Q-BRZ-04": ("conformidad", "bloqueante"),
    "Q-BRZ-05": ("validez", "cuarentena o bloqueante"),
    "Q-BRZ-06": ("completitud", "aviso"),
    "Q-BRZ-07": ("consistencia", "bloqueante"),
    "Q-BRZ-08": ("consistencia", "bloqueante"),
    "Q-BRZ-09": ("conformidad", "aviso"),
    "Q-BRZ-10": ("unicidad", "control de idempotencia"),
    "Q-BRZ-11": ("completitud", "aviso"),
}


@dataclass(frozen=True)
class Hallazgo:
    regla_id: str
    resultado: Resultado
    detalle: str
    tabla: str | None = None
    lote_id: str | None = None
    source_key: str | None = None
    filas_afectadas: int = 0


# ---------------------------------------------------------------- comprobaciones puras


def quitar_bom(datos: bytes) -> tuple[bytes, bool]:
    """Q-BRZ-02: si los tres primeros bytes son EF BB BF se quitan y se registra."""
    if datos.startswith(BOM):
        return datos[len(BOM) :], True
    return datos, False


def decodificar_utf8(datos: bytes) -> str | None:
    """Q-BRZ-04: None si el archivo no es UTF-8 válido."""
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return None


def bom_residual(columnas: list[str]) -> bool:
    """Q-BRZ-02: algún nombre de columna decodificado empieza con U+FEFF."""
    return any(c.startswith(BOM_CARACTER) for c in columnas)


def comparar_encabezado(
    esperado: list[str] | None, real: list[str]
) -> Literal["identico", "aditivo", "bloqueado"]:
    """Q-BRZ-03. Sin referencia (primera vez) el encabezado se acepta como idéntico."""
    if len(set(real)) != len(real) or any(c == "" for c in real):
        return "bloqueado"
    if esperado is None or esperado == real:
        return "identico"
    if set(esperado) <= set(real):
        return "aditivo"
    return "bloqueado"


def solapamiento(nuevas: set[str], vigentes: set[str]) -> float:
    """Q-BRZ-08: fracción de las llaves de la reentrega que ya estaban en la versión vigente."""
    if not nuevas:
        return 1.0
    return len(nuevas & vigentes) / len(nuevas)


def dias_faltantes(presentes: set[date], inicio: date, fin: date) -> list[date]:
    """Q-BRZ-01: días del rango sin archivo."""
    dias = (inicio + timedelta(days=i) for i in range((fin - inicio).days + 1))
    return [d for d in dias if d not in presentes]


def percentil(valores: list[int], p: float) -> float:
    """Percentil por interpolación lineal (p entre 0 y 100)."""
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return float(ordenados[0])
    pos = (len(ordenados) - 1) * p / 100
    bajo = int(pos)
    alto = min(bajo + 1, len(ordenados) - 1)
    return ordenados[bajo] + (ordenados[alto] - ordenados[bajo]) * (pos - bajo)


# ---------------------------------------------------------------- reglas sobre el conjunto


def _fecha(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def evaluar_globales(bronce: duckdb.DuckDBPyConnection, objetos: list[ObjetoS3]) -> list[Hallazgo]:
    """Q-BRZ-01, 06, 07 y 09 sobre el estado acumulado de `bronce._lotes` y el inventario del bucket."""
    hallazgos: list[Hallazgo] = []
    filas = bronce.execute(
        "SELECT tabla, process_date, filas, lote_id, source_key FROM bronce._lotes "
        "WHERE estado = 'aplicado' ORDER BY source_key, ingerido_en"
    ).fetchall()

    # Q-BRZ-01: solo tablas con particiones diarias fechadas
    fechas: dict[str, set[date]] = {}
    for tabla, pd, _f, _l, _k in filas:
        d = _fecha(pd)
        if d is not None:
            fechas.setdefault(tabla, set()).add(d)
    for tabla in sorted(fechas):
        faltan = dias_faltantes(fechas[tabla], INICIO_PARTICIONES, FIN_PARTICIONES)
        if faltan:
            muestra = ", ".join(d.isoformat() for d in faltan[:10])
            resto = f" y {len(faltan) - 10} más" if len(faltan) > 10 else ""
            detalle = f"faltan {len(faltan)} días: {muestra}{resto}"
            hallazgos.append(Hallazgo("Q-BRZ-01", "aviso", detalle, tabla, None, None, len(faltan)))

    # Q-BRZ-06: percentiles 1 y 99 por tabla y día de la semana, calculados sobre el histórico de lotes
    grupos: dict[tuple[str, int], list[tuple[int, str, str]]] = {}
    for tabla, pd, nfilas, lote, key in filas:
        d = _fecha(pd)
        if d is not None:
            grupos.setdefault((tabla, d.weekday()), []).append((int(nfilas), lote, key))
    for (tabla, dia), miembros in sorted(grupos.items()):
        if len(miembros) < MUESTRA_MINIMA_PERCENTILES:
            continue
        p1 = percentil([m[0] for m in miembros], 1)
        p99 = percentil([m[0] for m in miembros], 99)
        for nfilas, lote, key in miembros:
            if nfilas < p1 or nfilas > p99:
                detalle = f"{nfilas} filas fuera de [{p1:.1f}, {p99:.1f}] (día de la semana {dia})"
                hallazgos.append(Hallazgo("Q-BRZ-06", "aviso", detalle, tabla, lote, key, nfilas))

    # Q-BRZ-07: toda fila que llega a bronce viene de la generación `data/`
    ajenos = bronce.execute(
        "SELECT tabla, lote_id, source_key, filas FROM bronce._lotes "
        "WHERE estado = 'aplicado' AND generacion <> ?",
        [GENERACION_ACTUAL],
    ).fetchall()
    for tabla, lote, key, nfilas in ajenos:
        hallazgos.append(
            Hallazgo("Q-BRZ-07", "bloqueado", "lote de otra generación", tabla, lote, key, int(nfilas))
        )

    # Q-BRZ-09: objetos fuera de la fuente autorizada
    for o in objetos:
        if not o.autorizado:
            detalle = "objeto fuera de la fuente autorizada; no se ingiere"
            hallazgos.append(Hallazgo("Q-BRZ-09", "aviso", detalle, None, None, o.key))
    return hallazgos


# ---------------------------------------------------------------- reporte en platino

_DDL_REPORTE = """
CREATE TABLE IF NOT EXISTS platino.reporte_calidad_corrida (
    corrida_id VARCHAR, zona VARCHAR, regla_id VARCHAR, dimension VARCHAR, severidad VARCHAR,
    resultado VARCHAR, tabla VARCHAR, lote_id VARCHAR, source_key VARCHAR,
    filas_afectadas BIGINT, detalle VARCHAR, evaluado_en TIMESTAMP
)
"""


def reportar(
    platino: duckdb.DuckDBPyConnection, corrida_id: str, hallazgos: list[Hallazgo], ahora: datetime
) -> int:
    """Una fila por hallazgo y, para toda regla sin hallazgos, una fila `ok`: el reporte cubre las 11."""
    platino.execute(_DDL_REPORTE)
    con_hallazgo = {h.regla_id for h in hallazgos}
    todos = list(hallazgos) + [
        Hallazgo(r, "ok", "sin hallazgos") for r in sorted(REGLAS) if r not in con_hallazgo
    ]
    marca = ahora.replace(tzinfo=None)
    platino.executemany(
        "INSERT INTO platino.reporte_calidad_corrida VALUES (?, 'bronce', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                corrida_id,
                h.regla_id,
                REGLAS[h.regla_id][0],
                REGLAS[h.regla_id][1],
                h.resultado,
                h.tabla,
                h.lote_id,
                h.source_key,
                h.filas_afectadas,
                h.detalle,
                marca,
            )
            for h in todos
        ],
    )
    return len(todos)
