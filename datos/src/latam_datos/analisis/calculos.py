"""Funciones puras del análisis del problema: formato, agregación y puntuación."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

Fila = Mapping[str, Any]


def miles(n: float) -> str:
    """Entero con punto de miles: 686296 -> '686.296'."""
    return f"{round(n):,}".replace(",", ".")


def pct(parte: float, total: float, decimales: int = 1) -> str:
    """Porcentaje con coma decimal: pct(1, 4) -> '25,0%'. Total cero da 'n/d'."""
    if total == 0:
        return "n/d"
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + "%"


def dec(x: float, decimales: int = 1) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def razon(parte: float, total: float) -> float:
    return parte / total if total else math.nan


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson de una proporción."""
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centro - medio, centro + medio)


def suma(filas: Iterable[Fila], campo: str = "n", **filtro: Any) -> float:
    """Suma `campo` en las filas que cumplen todos los pares clave=valor de `filtro`."""
    return sum(f[campo] or 0 for f in filas if all(f[k] == v for k, v in filtro.items()))


def agrupar(filas: Iterable[Fila], clave: str, campo: str = "n") -> dict[Any, float]:
    salida: dict[Any, float] = defaultdict(float)
    for f in filas:
        salida[f[clave]] += f[campo] or 0
    return dict(salida)


def agrupar2(
    filas: Iterable[Fila], clave_a: str, clave_b: str, campo: str = "n"
) -> dict[Any, dict[Any, float]]:
    salida: dict[Any, dict[Any, float]] = defaultdict(lambda: defaultdict(float))
    for f in filas:
        salida[f[clave_a]][f[clave_b]] += f[campo] or 0
    return {a: dict(b) for a, b in salida.items()}


def meses_completos(serie: Mapping[str, float]) -> dict[str, float]:
    """Quita el primer y el último mes de una serie `{'YYYY-MM-DD': n}`, que son parciales en la ventana."""
    claves = sorted(serie)
    return {k: serie[k] for k in claves[1:-1]}


def cambio_doce_meses(serie: Mapping[str, float]) -> tuple[float, float, float]:
    """Promedio mensual de los primeros 12 y de los últimos 12 meses completos, y su variación relativa."""
    claves = sorted(serie)
    primero = sum(serie[k] for k in claves[:12]) / 12
    ultimo = sum(serie[k] for k in claves[-12:]) / 12
    return primero, ultimo, ultimo / primero - 1


def bloque_horario(hora: int) -> str:
    """Tercios del día: madrugada 00 a 07, mañana 08 a 15, tarde y noche 16 a 23."""
    if hora < 8:
        return "Night"
    return "Morning" if hora < 16 else "Afternoon"


def capacidad_por_bloque(activos: Mapping[str, float]) -> dict[str, float]:
    """Agentes activos por bloque; los rotativos se reparten en partes iguales (supuesto declarado)."""
    rot = activos.get("Rotating", 0) / 3
    return {b: activos.get(b, 0) + rot for b in ("Night", "Morning", "Afternoon")}


def indice_carga(demanda: Mapping[str, float], capacidad: Mapping[str, float]) -> dict[str, float]:
    """Participación en la demanda dividida por la participación en la capacidad (1 es equilibrio)."""
    td, tc = sum(demanda.values()), sum(capacidad.values())
    return {b: (demanda[b] / td) / (capacidad[b] / tc) for b in demanda}


def puntuar(candidatos: Mapping[str, Mapping[str, float]], pesos: Mapping[str, float]) -> dict[str, float]:
    """Suma ponderada (pesos normalizados) de puntajes de 1 a 5 por criterio."""
    total = sum(pesos.values())
    return {c: sum(p[k] * w for k, w in pesos.items()) / total for c, p in candidatos.items()}


def escala_1_5(valores: Mapping[str, float], mayor_es_mejor: bool = True) -> dict[str, float]:
    """Reescala lineal a 1..5 entre el mínimo y el máximo del conjunto."""
    lo, hi = min(valores.values()), max(valores.values())
    if hi == lo:
        return dict.fromkeys(valores, 3.0)
    return {
        k: 1 + 4 * ((v - lo) / (hi - lo) if mayor_es_mejor else (hi - v) / (hi - lo))
        for k, v in valores.items()
    }


def sensibilidad_volumen(
    candidatos: Mapping[str, Mapping[str, float]], pesos: Mapping[str, float], pasos: Sequence[float]
) -> list[tuple[float, str]]:
    """Líder al variar el peso del volumen; el resto de pesos se reparte en su proporción original."""
    resto = sum(w for k, w in pesos.items() if k != "volumen")
    salida: list[tuple[float, str]] = []
    for pv in pasos:
        nuevos = {k: (pv if k == "volumen" else w / resto * (1 - pv)) for k, w in pesos.items()}
        puntos = puntuar(candidatos, nuevos)
        salida.append((pv, max(puntos, key=lambda c: puntos[c])))
    return salida
