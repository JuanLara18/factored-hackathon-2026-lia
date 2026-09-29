"""DAT-1.3: reglas de bronce Q-BRZ-01 a Q-BRZ-11 (definición, sección 2.4) y su reporte en `latam_platino`.

Las comprobaciones sobre un archivo (BOM, codificación, encabezado) son funciones puras que corren antes de
la carga; las que miran el conjunto (01, 06, 07, 08, 09, 10) son SQL de BigQuery generado con el dialecto
del motor.
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from latam_datos.config import GENERACION_ACTUAL, INVENTARIO, LOTES, REPORTE
from latam_datos.motor import Logico, Motor

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


# ---------------------------------------------------------------- reglas SQL sobre el conjunto


def sql_solapamiento(motor: Motor, staging: str, destino: str, llave: str, lote_vigente: str) -> str:
    """Q-BRZ-08: (llaves distintas de la reentrega, cuántas ya estaban en la versión vigente)."""
    k = motor.ident(llave)
    return (
        f"SELECT COUNT(DISTINCT n.{k}), COUNT(DISTINCT CASE WHEN v.k IS NOT NULL THEN n.{k} END) "
        f"FROM {motor.t(staging)} AS n LEFT JOIN "
        f"(SELECT DISTINCT {k} AS k FROM {motor.t(destino)} WHERE _lote_id = {motor.lit(lote_vigente)}) AS v "
        f"ON n.{k} = v.k"
    )


def sql_dias_faltantes(motor: Motor) -> str:
    """Q-BRZ-01: (tabla, día) del rango sin archivo, solo para tablas con particiones diarias."""
    fecha = motor.fecha_segura("process_date")
    return (
        f"WITH presentes AS (SELECT DISTINCT tabla, {fecha} AS dia FROM {motor.t(LOTES)} "
        f"WHERE estado = 'aplicado' AND {fecha} IS NOT NULL), "
        f"tablas AS (SELECT DISTINCT tabla FROM presentes), "
        f"rango AS ({motor.serie_de_dias(INICIO_PARTICIONES, FIN_PARTICIONES)}) "
        f"SELECT t.tabla, r.dia FROM tablas AS t CROSS JOIN rango AS r "
        f"LEFT JOIN presentes AS p ON p.tabla = t.tabla AND p.dia = r.dia "
        f"WHERE p.dia IS NULL ORDER BY t.tabla, r.dia"
    )


def sql_conteos_atipicos(motor: Motor) -> str:
    """Q-BRZ-06: lotes con filas fuera de los percentiles 1 y 99 de su tabla y día de la semana."""
    fecha = motor.fecha_segura("process_date")
    part = "tabla, dow"
    return (
        f"SELECT tabla, lote_id, source_key, filas, p1, p99 FROM ("
        f"SELECT tabla, lote_id, source_key, filas, "
        f"{motor.percentil('filas', 0.01, part)} AS p1, {motor.percentil('filas', 0.99, part)} AS p99, "
        f"COUNT(*) OVER (PARTITION BY {part}) AS n FROM ("
        f"SELECT tabla, lote_id, source_key, filas, {motor.dia_semana(fecha)} AS dow "
        f"FROM {motor.t(LOTES)} WHERE estado = 'aplicado' AND {fecha} IS NOT NULL)) "
        f"WHERE n >= {MUESTRA_MINIMA_PERCENTILES} AND (filas < p1 OR filas > p99) ORDER BY source_key"
    )


def sql_generacion_ajena(motor: Motor) -> str:
    """Q-BRZ-07: lotes aplicados que no son de la generación `data/`."""
    return (
        f"SELECT tabla, lote_id, source_key, filas FROM {motor.t(LOTES)} "
        f"WHERE estado = 'aplicado' AND generacion <> {motor.lit(GENERACION_ACTUAL)} ORDER BY source_key"
    )


def sql_no_autorizados(motor: Motor) -> str:
    """Q-BRZ-09: objetos fuera de la fuente autorizada en la última instantánea del inventario."""
    inv = motor.t(INVENTARIO)
    return (
        f"SELECT source_key FROM {inv} WHERE NOT autorizado "
        f"AND corrida_id = (SELECT MAX(corrida_id) FROM {inv}) ORDER BY source_key"
    )


def evaluar_globales(motor: Motor) -> list[Hallazgo]:
    """Q-BRZ-01, 06, 07 y 09 sobre el estado acumulado de `latam_bronce._lotes` y el inventario."""
    hallazgos: list[Hallazgo] = []
    faltan: dict[str, list[date]] = {}
    for tabla, dia in motor.consultar(sql_dias_faltantes(motor)):
        faltan.setdefault(str(tabla), []).append(dia)
    for tabla, dias in sorted(faltan.items()):
        muestra = ", ".join(d.isoformat() for d in dias[:10])
        resto = f" y {len(dias) - 10} más" if len(dias) > 10 else ""
        detalle = f"faltan {len(dias)} días: {muestra}{resto}"
        hallazgos.append(Hallazgo("Q-BRZ-01", "aviso", detalle, tabla, None, None, len(dias)))
    for tabla, lote, key, filas, p1, p99 in motor.consultar(sql_conteos_atipicos(motor)):
        detalle = f"{filas} filas fuera de [{float(p1):.1f}, {float(p99):.1f}]"
        hallazgos.append(Hallazgo("Q-BRZ-06", "aviso", detalle, str(tabla), str(lote), str(key), int(filas)))
    for tabla, lote, key, filas in motor.consultar(sql_generacion_ajena(motor)):
        hallazgos.append(
            Hallazgo(
                "Q-BRZ-07",
                "bloqueado",
                "lote de otra generación",
                str(tabla),
                str(lote),
                str(key),
                int(filas),
            )
        )
    for (key,) in motor.consultar(sql_no_autorizados(motor)):
        detalle = "objeto fuera de la fuente autorizada; no se ingiere"
        hallazgos.append(Hallazgo("Q-BRZ-09", "aviso", detalle, None, None, str(key)))
    return hallazgos


# ---------------------------------------------------------------- reporte en platino

_COLUMNAS_REPORTE: tuple[tuple[str, Logico], ...] = (
    ("corrida_id", "texto"),
    ("zona", "texto"),
    ("regla_id", "texto"),
    ("dimension", "texto"),
    ("severidad", "texto"),
    ("resultado", "texto"),
    ("tabla", "texto"),
    ("lote_id", "texto"),
    ("source_key", "texto"),
    ("filas_afectadas", "entero"),
    ("detalle", "texto"),
    ("evaluado_en", "fecha_hora"),
)


def reportar(motor: Motor, corrida_id: str, hallazgos: list[Hallazgo], ahora: datetime) -> int:
    """Una fila por hallazgo y, para toda regla sin hallazgos, una fila `ok`: el reporte cubre las 11."""
    cols = ", ".join(f"{c} {motor.tipo(t)}" for c, t in _COLUMNAS_REPORTE)
    motor.ejecutar(f"CREATE TABLE IF NOT EXISTS {motor.t(REPORTE)} ({cols})")
    con_hallazgo = {h.regla_id for h in hallazgos}
    todos = [
        *hallazgos,
        *(Hallazgo(r, "ok", "sin hallazgos") for r in sorted(REGLAS) if r not in con_hallazgo),
    ]
    filas = [
        "("
        + ", ".join(
            motor.lit(v)
            for v in (
                corrida_id,
                "bronce",
                h.regla_id,
                REGLAS[h.regla_id][0],
                REGLAS[h.regla_id][1],
                h.resultado,
                h.tabla,
                h.lote_id,
                h.source_key,
                h.filas_afectadas,
                h.detalle,
                ahora,
            )
        )
        + ")"
        for h in todos
    ]
    for i in range(0, len(filas), 500):
        motor.ejecutar(f"INSERT INTO {motor.t(REPORTE)} VALUES " + ", ".join(filas[i : i + 500]))
    return len(todos)
