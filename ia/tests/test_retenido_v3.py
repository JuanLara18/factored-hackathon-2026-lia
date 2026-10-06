"""Retenido v3 (IA-5.5): congelado por huella antes de construir las capacidades que evalúa."""

from __future__ import annotations

from collections import Counter

from latam_ia.evaluacion.esquema import DIR_RETENIDO_V3, cargar_escenarios, cargar_retenidos
from latam_ia.evaluacion.retenido import huella_retenido, validar_etiquetas

# Congelado el 5 de octubre de 2026 con el prompt 1.6.0 y el trabajador 0.7.0 en producción. Si esta huella
# cambia, el conjunto dejó de ser retenido: no se edita un caso después de ver resultados, se versiona otro.
HUELLA_V3 = "2e2318519474950d8f52a8601eb86c7ae3721a1b3f32973f3a539a0aeacae9f4"

V3 = cargar_retenidos(DIR_RETENIDO_V3)
PAIS = {"CUST-0101": "MX", "CUST-0102": "AR", "CUST-0103": "CO"}


def test_la_huella_es_la_del_congelamiento() -> None:
    assert huella_retenido(DIR_RETENIDO_V3) == HUELLA_V3


def test_mezcla_de_categorias_idiomas_y_paises() -> None:
    assert len(V3) == 43
    assert {e.categoria for e in V3} == {"N", "A", "E", "F", "X", "P", "S", "M"}
    assert Counter(e.idioma for e in V3) == {"es": 28, "pt": 15}
    assert {e.registro for e in V3} == {"usted", "vos", "voce"}
    # el retenido anterior tenía 31 casos de Colombia, 1 de Argentina y ninguno de México
    assert Counter(PAIS[e.cliente] for e in V3) == {"CO": 18, "MX": 16, "AR": 9}
    assert {e.fallo for e in V3 if e.fallo} == {
        "sesion_vencida_al_inicio",
        "sesion_vence_a_mitad",
        "bigquery_caido",
        "firestore_caido",
        "runtime_caido",
    }


def test_no_se_cruza_con_desarrollo_ni_con_el_retenido_anterior() -> None:
    vistos = cargar_escenarios() + cargar_retenidos()
    assert not {e.id for e in vistos} & {e.id for e in V3}
    assert not {e.guion.turnos[0].decir for e in vistos} & {e.guion.turnos[0].decir for e in V3}
    assert len({e.guion.turnos[0].decir for e in V3}) == len(V3)


def test_etiquetas_coherentes_con_la_politica() -> None:
    assert validar_etiquetas(V3) == []
    for e in V3:
        assert not (e.esperado.debe_citar and e.esperado.sin_citas), e.id
