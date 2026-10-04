"""Pruebas sin red de la tabla de disparidad con un fixture sintético con disparidades sembradas."""

from __future__ import annotations

import math
from pathlib import Path

from latam_gobierno.equidad import (
    FilaDisparidad,
    a_markdown,
    cargar_casos,
    comparar,
    newcombe,
    tabla_disparidad,
    wilson,
)

FIXTURE = Path(__file__).resolve().parents[1] / "equidad" / "fixtures" / "casos_ejemplo.json"


def _fila(filas: list[FilaDisparidad], dim: str, grupo: str, metrica: str) -> FilaDisparidad:
    return next(f for f in filas if (f.dimension, f.grupo, f.metrica) == (dim, grupo, metrica))


def test_wilson_y_newcombe() -> None:
    lo, hi = wilson(50, 100)
    assert lo < 0.5 < hi
    assert math.isnan(wilson(0, 0)[0])
    d, d_lo, d_hi = newcombe(80, 100, 50, 100)
    assert d_lo < d < d_hi
    assert abs(d - 0.3) < 1e-9
    assert d_lo > 0


def test_comparar_exige_brecha_y_intervalo() -> None:
    peor = comparar(60, 100, 90, 100, "mayor_mejor")
    assert peor.investigar
    pequena = comparar(88, 100, 90, 100, "mayor_mejor")
    assert not pequena.investigar
    ruido = comparar(6, 10, 9, 10, "mayor_mejor")
    assert not ruido.investigar  # brecha grande pero intervalo con el cero
    mala = comparar(30, 100, 5, 100, "menor_mejor")
    assert mala.investigar


def test_portugues_se_marca_y_ar_es_muestra_insuficiente() -> None:
    filas = tabla_disparidad(cargar_casos(FIXTURE))
    assert _fila(filas, "idioma", "pt", "resolucion_segura").estado == "investigar"
    assert _fila(filas, "idioma", "es", "resolucion_segura").estado == "referencia"
    assert _fila(filas, "pais", "AR", "resolucion_segura").estado == "muestra_insuficiente"
    assert _fila(filas, "idioma", "pt", "latencia_p95").estado == "investigar"
    assert _fila(filas, "pais", "CO", "resolucion_segura").estado in {"ok", "referencia"}


def test_un_inseguro_obliga_a_investigar_ese_grupo() -> None:
    filas = tabla_disparidad(cargar_casos(FIXTURE))
    assert _fila(filas, "pais", "MX", "inseguro").estado == "investigar"
    assert _fila(filas, "pais", "CO", "inseguro").estado == "ok"


def test_sin_dato_y_markdown() -> None:
    casos = [{"caso": "x", "idioma": "", "resultado": "exito", "escalo": False, "debia_escalar": False}]
    filas = tabla_disparidad(casos, dimensiones=("idioma",))
    assert all(f.grupo == "sin_dato" and f.estado == "muestra_insuficiente" for f in filas)
    assert a_markdown(filas).startswith("| Dimensión")
    assert filas[0].como_dict()["dif"] is None
