"""Estadística fija de 2.8.8 (R-IA-73, R-IA-74): pass^k combinatorio, Wilson y regla del tres."""

from __future__ import annotations

from math import comb, sqrt

Z95 = 1.959963984540054


def wilson(exitos: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Intervalo de Wilson al 95%; con n = 0 no dice nada (0, 1)."""
    if n == 0:
        return (0.0, 1.0)
    p = exitos / n
    denom = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / denom
    medio = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centro - medio), min(1.0, centro + medio))


def regla_del_tres(n: int) -> float:
    """Cota superior al 95% de una tasa con cero eventos en n intentos."""
    return 1.0 if n == 0 else min(1.0, 3 / n)


def pass_k(exitos: int, n: int, k: int) -> float:
    """Estimador de τ-bench: C(c, k) / C(n, k). Con k mayor que n no hay estimación: 0."""
    if k > n or n == 0:
        return 0.0
    return comb(exitos, k) / comb(n, k)


def tasa(exitos: int, n: int) -> dict[str, float | int]:
    bajo, alto = wilson(exitos, n)
    return {"x": exitos, "n": n, "tasa": (exitos / n) if n else 0.0, "ic95_bajo": bajo, "ic95_alto": alto}
