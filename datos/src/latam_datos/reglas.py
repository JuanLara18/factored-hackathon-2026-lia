"""Reglas Q-BRZ sobre las tablas crudas `latam_bank.bronce_<tabla>` (definición 2.4, ajustadas por D-30).

Todo es SQL generado con el dialecto del motor (BigQuery en producción). Las reglas que hablaban de objetos,
etag, BOM, codificación o lotes quedaron fuera porque la carga es de un proceso externo (ver README).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from latam_datos.contrato import (
    CONTRATO,
    DATASET,
    FIN_PARTICIONES,
    INICIO_PARTICIONES,
    PREFIJO_BRONCE,
    REPORTE,
    TablaCruda,
)
from latam_datos.motor import Logico, Motor

UMBRAL_VACIOS = 0.005
MUESTRA_MINIMA_PERCENTILES = 20

Resultado = Literal["ok", "aviso", "bloqueado"]

# regla -> (dimension, severidad declarada)
REGLAS: dict[str, tuple[str, str]] = {
    "Q-BRZ-01": ("completitud", "aviso"),
    "Q-BRZ-03": ("conformidad", "bloqueante si falta tabla o columna requerida; aviso si sobran columnas"),
    "Q-BRZ-05": ("validez", "aviso"),
    "Q-BRZ-06": ("completitud", "aviso"),
    "Q-BRZ-11": ("completitud", "aviso"),
    "Q-BRZ-12": ("unicidad", "aviso"),
    "Q-BRZ-13": ("completitud", "aviso"),
}


@dataclass(frozen=True)
class Hallazgo:
    regla_id: str
    resultado: Resultado
    detalle: str
    tabla: str | None = None
    filas_afectadas: int = 0


def _t(motor: Motor, tabla: str) -> str:
    return motor.t(f"{DATASET}.{PREFIJO_BRONCE}{tabla}")


def _vacio(motor: Motor, columna: str) -> str:
    c = motor.ident(columna)
    return f"({c} IS NULL OR TRIM({c}) = '')"


# ---------------------------------------------------------------- SQL de cada regla


def sql_dias_faltantes(motor: Motor, t: TablaCruda) -> str:
    """Q-BRZ-01: días de la ventana sin ninguna fila en la tabla."""
    assert t.fecha
    f = motor.fecha_segura(motor.ident(t.fecha))
    return (
        f"WITH presentes AS (SELECT DISTINCT {f} AS dia FROM {_t(motor, t.nombre)} WHERE {f} IS NOT NULL), "
        f"rango AS ({motor.serie_de_dias(INICIO_PARTICIONES, FIN_PARTICIONES)}) "
        "SELECT r.dia FROM rango AS r LEFT JOIN presentes AS p ON p.dia = r.dia "
        "WHERE p.dia IS NULL ORDER BY r.dia"
    )


def sql_conteos_atipicos(motor: Motor, t: TablaCruda) -> str:
    """Q-BRZ-06: días cuyo conteo cae fuera de los percentiles 1 y 99 de su día de la semana."""
    assert t.fecha
    f = motor.fecha_segura(motor.ident(t.fecha))
    return (
        f"SELECT dia, n, p1, p99 FROM ("
        f"SELECT dia, n, {motor.percentil('n', 0.01, 'dow')} AS p1, "
        f"{motor.percentil('n', 0.99, 'dow')} AS p99, "
        f"COUNT(*) OVER (PARTITION BY dow) AS m FROM ("
        f"SELECT {f} AS dia, {motor.dia_semana(f)} AS dow, COUNT(*) AS n FROM {_t(motor, t.nombre)} "
        f"WHERE {f} IS NOT NULL GROUP BY dia, dow)) "
        f"WHERE m >= {MUESTRA_MINIMA_PERCENTILES} AND (n < p1 OR n > p99) ORDER BY dia"
    )


def sql_fechas_ilegibles(motor: Motor, t: TablaCruda) -> str:
    assert t.fecha
    c = motor.ident(t.fecha)
    return (
        f"SELECT COUNT(*) FROM {_t(motor, t.nombre)} "
        f"WHERE NOT {_vacio(motor, t.fecha)} AND {motor.fecha_segura(c)} IS NULL"
    )


def sql_filas(motor: Motor, t: TablaCruda) -> str:
    return f"SELECT COUNT(*) FROM {_t(motor, t.nombre)}"


def sql_llave_vacia(motor: Motor, t: TablaCruda) -> str:
    assert t.llave
    return f"SELECT COUNT(*) FROM {_t(motor, t.nombre)} WHERE {_vacio(motor, t.llave)}"


def sql_llave_duplicada(motor: Motor, t: TablaCruda) -> str:
    """Q-BRZ-12: (llaves repetidas, filas sobrantes). Plata decide el ganador; aquí solo se mide."""
    assert t.llave
    k = motor.ident(t.llave)
    return (
        f"SELECT COUNT(*), COALESCE(SUM(n - 1), 0) FROM "
        f"(SELECT {k}, COUNT(*) AS n FROM {_t(motor, t.nombre)} "
        f"WHERE NOT {_vacio(motor, t.llave)} GROUP BY {k} HAVING COUNT(*) > 1)"
    )


def sql_vacios_requeridas(motor: Motor, t: TablaCruda) -> str:
    """Q-BRZ-13: una columna con la cantidad de filas vacías por cada columna requerida, en una pasada."""
    sumas = ", ".join(f"SUM(CASE WHEN {_vacio(motor, c)} THEN 1 ELSE 0 END)" for c in t.requeridas)
    return f"SELECT COUNT(*), {sumas} FROM {_t(motor, t.nombre)}"


# ---------------------------------------------------------------- evaluación


def evaluar(motor: Motor, contrato: tuple[TablaCruda, ...] = CONTRATO) -> list[Hallazgo]:
    """Corre las reglas sobre cada tabla del contrato y devuelve los hallazgos."""
    hallazgos: list[Hallazgo] = []
    columnas: dict[str, dict[str, str]] = {}
    for tabla, col, tipo in motor.consultar(motor.columnas_de(DATASET)):
        if str(tabla).startswith(PREFIJO_BRONCE):
            columnas.setdefault(str(tabla).removeprefix(PREFIJO_BRONCE), {})[str(col)] = str(tipo)

    for t in contrato:
        if t.nombre not in columnas:
            hallazgos.append(
                Hallazgo("Q-BRZ-03", "bloqueado", "tabla esperada ausente en latam_bank (bronce_*)", t.nombre)
            )
            continue
        presentes = columnas[t.nombre]
        # Q-BRZ-03: columnas requeridas presentes y de tipo texto
        faltan = [c for c in (*t.requeridas, *([t.llave] if t.llave else [])) if c not in presentes]
        if faltan:
            hallazgos.append(
                Hallazgo(
                    "Q-BRZ-03",
                    "bloqueado",
                    f"faltan columnas requeridas: {', '.join(sorted(set(faltan)))}",
                    t.nombre,
                )
            )
            continue
        no_texto = sorted(c for c, tp in presentes.items() if tp.upper() not in ("STRING", "VARCHAR"))
        if no_texto:
            hallazgos.append(
                Hallazgo(
                    "Q-BRZ-03",
                    "aviso",
                    f"columnas que no son texto: {', '.join(no_texto)}",
                    t.nombre,
                    len(no_texto),
                )
            )

        # Q-BRZ-11: tabla vacía
        total = int(motor.consultar(sql_filas(motor, t))[0][0])
        if total == 0:
            hallazgos.append(Hallazgo("Q-BRZ-11", "aviso", "tabla vacía", t.nombre))
            continue

        if t.llave:
            vacias = int(motor.consultar(sql_llave_vacia(motor, t))[0][0])
            if vacias:
                hallazgos.append(
                    Hallazgo("Q-BRZ-05", "aviso", f"{vacias} filas con llave vacía", t.nombre, vacias)
                )
            repetidas, sobrantes = motor.consultar(sql_llave_duplicada(motor, t))[0]
            if int(repetidas):
                detalle = f"{int(repetidas)} llaves repetidas, {int(sobrantes)} filas sobrantes"
                hallazgos.append(Hallazgo("Q-BRZ-12", "aviso", detalle, t.nombre, int(sobrantes)))

        if t.requeridas:
            fila = motor.consultar(sql_vacios_requeridas(motor, t))[0]
            for col, n in zip(t.requeridas, fila[1:], strict=True):
                if n and int(n) / total > UMBRAL_VACIOS:
                    detalle = f"{col}: {int(n)} de {total} vacías"
                    hallazgos.append(Hallazgo("Q-BRZ-13", "aviso", detalle, t.nombre, int(n)))

        if t.fecha and t.de_hechos:
            ilegibles = int(motor.consultar(sql_fechas_ilegibles(motor, t))[0][0])
            if ilegibles:
                detalle = f"{ilegibles} filas con {t.fecha} no interpretable como fecha"
                hallazgos.append(Hallazgo("Q-BRZ-05", "aviso", detalle, t.nombre, ilegibles))
            dias: list[date] = [d for (d,) in motor.consultar(sql_dias_faltantes(motor, t))]
            if dias:
                muestra = ", ".join(d.isoformat() for d in dias[:10])
                resto = f" y {len(dias) - 10} más" if len(dias) > 10 else ""
                detalle = f"faltan {len(dias)} días: {muestra}{resto}"
                hallazgos.append(Hallazgo("Q-BRZ-01", "aviso", detalle, t.nombre, len(dias)))
            for dia, n, p1, p99 in motor.consultar(sql_conteos_atipicos(motor, t)):
                detalle = f"{dia}: {int(n)} filas fuera de [{float(p1):.1f}, {float(p99):.1f}]"
                hallazgos.append(Hallazgo("Q-BRZ-06", "aviso", detalle, t.nombre, int(n)))
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
    ("filas_afectadas", "entero"),
    ("detalle", "texto"),
    ("evaluado_en", "fecha_hora"),
)


def reportar(motor: Motor, corrida_id: str, hallazgos: list[Hallazgo], ahora: datetime) -> int:
    """Una fila por hallazgo y, para toda regla sin hallazgos, una fila `ok`."""
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
