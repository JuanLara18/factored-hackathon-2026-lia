"""Pruebas sin red de las funciones puras del análisis del problema."""

from __future__ import annotations

import math

from latam_datos.analisis import calculos as c
from latam_datos.analisis.consultas import SQL, parsear_consultas


def test_formato_es() -> None:
    assert c.miles(686296) == "686.296"
    assert c.pct(1, 4) == "25,0%"
    assert c.pct(1, 0) == "n/d"
    assert c.dec(2.5, 1) == "2,5"


def test_wilson_contiene_la_proporcion() -> None:
    lo, hi = c.wilson(204, 1000)
    assert lo < 0.204 < hi
    assert math.isnan(c.wilson(0, 0)[0])


def test_agrupar_y_suma() -> None:
    filas = [{"a": "x", "b": "p", "n": 2}, {"a": "x", "b": "q", "n": 3}, {"a": "y", "b": "p", "n": None}]
    assert c.suma(filas) == 5
    assert c.suma(filas, a="x", b="q") == 3
    assert c.agrupar(filas, "a") == {"x": 5, "y": 0}
    assert c.agrupar2(filas, "a", "b")["x"] == {"p": 2, "q": 3}


def test_meses_y_cambio() -> None:
    serie = {f"2024-{m:02d}-01": 100.0 for m in range(1, 13)} | {
        f"2025-{m:02d}-01": 110.0 for m in range(1, 13)
    }
    assert len(c.meses_completos(serie)) == 22
    ini, fin, var = c.cambio_doce_meses(serie)
    assert (ini, fin) == (100.0, 110.0) and abs(var - 0.1) < 1e-9


def test_capacidad_e_indice() -> None:
    assert (
        c.bloque_horario(7) == "Night"
        and c.bloque_horario(8) == "Morning"
        and c.bloque_horario(16) == "Afternoon"
    )
    cap = c.capacidad_por_bloque({"Night": 30, "Morning": 30, "Afternoon": 30, "Rotating": 30})
    assert cap == {"Night": 40, "Morning": 40, "Afternoon": 40}
    idx = c.indice_carga(
        {"Night": 50, "Morning": 25, "Afternoon": 25}, {"Night": 25, "Morning": 50, "Afternoon": 25}
    )
    assert idx["Night"] == 2 and idx["Morning"] == 0.5


def test_priorizacion_y_sensibilidad() -> None:
    esc = c.escala_1_5({"a": 0, "b": 5, "c": 10})
    assert esc == {"a": 1, "b": 3, "c": 5}
    cand = {"x": {"volumen": 1.0, "otro": 5.0}, "y": {"volumen": 5.0, "otro": 1.0}}
    assert c.puntuar(cand, {"volumen": 1, "otro": 1}) == {"x": 3, "y": 3}
    sens = c.sensibilidad_volumen(cand, {"volumen": 0.5, "otro": 0.5}, [0.1, 0.9])
    assert [ld for _, ld in sens] == ["x", "y"]


def test_consultas_se_parsean() -> None:
    q = parsear_consultas(SQL.read_text(encoding="utf-8"))
    assert {"cobertura", "motivo_canal", "quejas_linea_base", "calidad", "digital"} <= set(q)
    assert all("{ds}" in sql for sql in q.values())
