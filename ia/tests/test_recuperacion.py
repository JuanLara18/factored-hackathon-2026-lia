"""Evaluación de la recuperación de política (IA-12): juicios, partición y métricas, sin red."""

from __future__ import annotations

from latam_ia.evaluacion.esquema import DIR_RETENIDO_V3, cargar_escenarios, cargar_retenidos
from latam_ia.recuperacion.__main__ import (
    cargar_consultas,
    decidir,
    decisiones,
    evaluar_sistema,
    partir,
    puntajes_azar,
    puntajes_lexicos,
    resultado,
)
from latam_tecnologia.herramientas.conocimiento import cargar_articulos

ARTICULOS = cargar_articulos()
IDS = [a.id for a in ARTICULOS]
CONSULTAS = cargar_consultas()


def test_los_juicios_cubren_todos_los_articulos_y_los_dos_idiomas() -> None:
    assert len({c["q"] for c in CONSULTAS}) == len(CONSULTAS) == 131
    por_articulo = {i: sum(c["articulo"] == i for c in CONSULTAS) for i in IDS}
    assert min(por_articulo.values()) >= 6
    assert {c["articulo"] for c in CONSULTAS} - {None} == set(IDS)
    assert sum(c["articulo"] is None for c in CONSULTAS) == 30
    assert {c["idioma"] for c in CONSULTAS} == {"es", "pt"}


def test_ninguna_pregunta_repite_un_escenario_del_agente() -> None:
    escenarios = cargar_escenarios() + cargar_retenidos() + cargar_retenidos(DIR_RETENIDO_V3)
    dichos = {t.decir for e in escenarios for t in e.guion.turnos}
    assert not dichos & {c["q"] for c in CONSULTAS}


def test_la_particion_es_estable_y_estratificada() -> None:
    validacion, prueba = partir(CONSULTAS)
    assert (len(validacion), len(prueba)) == (63, 68)
    assert partir(CONSULTAS) == (validacion, prueba)
    assert not {c["q"] for c in validacion} & {c["q"] for c in prueba}
    for conjunto in (validacion, prueba):
        assert {c["articulo"] for c in conjunto} - {None} == set(IDS)  # cada artículo está en las dos mitades


def test_resultados_y_costo() -> None:
    con, sin = {"q": "a", "articulo": "K-01"}, {"q": "b", "articulo": None}
    assert resultado(con, ["K-01"]) == "correcta" and resultado(con, ["K-02"]) == "cita_equivocada"
    assert resultado(con, []) == "sin_respuesta"
    assert resultado(sin, []) == "abstencion_correcta" and resultado(sin, ["K-01"]) == "cita_falsa"
    assert decidir([0.2, 0.9, 0.89], ["a", "b", "c"], umbral=0.5, margen=0.02) == ["b", "c"]
    assert decidir([0.2, 0.4, 0.3], ["a", "b", "c"], umbral=0.5, margen=0.02) == []
    p = {"a": [1.0] + [0.0] * 15, "b": [1.0] + [0.0] * 15}
    d = decisiones([con, sin], p, IDS, umbral=0.5, margen=0.0)
    assert d["correcta"] == 1 and d["cita_falsa"] == 1 and d["costo_medio"] == 2.5


def test_bm25_supera_al_azar_en_prueba_sin_red() -> None:
    validacion, prueba = partir(CONSULTAS)
    todas = validacion + prueba
    azar = evaluar_sistema("azar", puntajes_azar(todas, len(IDS)), validacion, prueba, IDS)
    bm25 = evaluar_sistema("bm25", puntajes_lexicos(todas, ARTICULOS), validacion, prueba, IDS)
    assert bm25["prueba"]["costo_medio"] < azar["prueba"]["costo_medio"]
    assert bm25["orden_prueba"]["recall_1"] > 0.5 > azar["orden_prueba"]["recall_1"]
    assert bm25["prueba"]["cita_falsa"] == 0
