"""Pista de riesgo de plazo (IA-10): abstención, banda y que nunca autorice una acción. Sin red ni datos."""

from __future__ import annotations

import numpy as np
import pandas as pd
from latam_ia.comprension.riesgo_plazo import (
    PistaRiesgo,
    SenalesDisputa,
    a_fila,
    columnas,
    pista_de_plazo,
    riesgo_plazo,
)
from latam_ia.experimentos.riesgo_plazo import aplicar_platt, captura_topk, umbral_precision


class Falso:
    def __init__(self, p: float, con_senal: bool = True) -> None:
        self.p = p
        self.con_senal = con_senal
        self.version = "falso"
        self.umbral_alto = 0.30
        self.umbral_medio = 0.22
        self.region = (0.10, 0.50)

    def probabilidades(self, filas: pd.DataFrame) -> np.ndarray:
        assert list(filas.columns) == columnas()
        return np.array([self.p])


CASO = SenalesDisputa(categoria="Transactions", subcategoria="Cargo no reconocido", hora=3, quejas_previas=0)


def test_sin_modelo_o_sin_senal_se_abstiene() -> None:
    a = riesgo_plazo(CASO, None)
    b = riesgo_plazo(CASO, Falso(0.4, con_senal=False))
    assert a.abstiene and b.abstiene and a.probabilidad is None and b.banda is None
    assert not a.en_riesgo and not b.en_riesgo


def test_bandas_y_region_calibrada() -> None:
    assert riesgo_plazo(CASO, Falso(0.40)).banda == "alta"
    assert riesgo_plazo(CASO, Falso(0.25)).banda == "media"
    assert riesgo_plazo(CASO, Falso(0.15)).banda == "baja"
    fuera = riesgo_plazo(CASO, Falso(0.90))
    assert fuera.abstiene and fuera.motivo_abstencion == "región sin calibración verificada"
    assert riesgo_plazo(CASO, Falso(0.40)).en_riesgo and not riesgo_plazo(CASO, Falso(0.15)).en_riesgo


def test_la_pista_nunca_permite_una_accion_y_el_texto_es_orientativo() -> None:
    p = riesgo_plazo(CASO, Falso(0.40))
    assert p.accion_permitida is False
    assert "solo orientativo" in pista_de_plazo(p)
    assert "sin pista fiable" in pista_de_plazo(
        PistaRiesgo(probabilidad=None, banda=None, abstiene=True, version_modelo="x")
    )


def test_fila_solo_con_rasgos_de_radicacion() -> None:
    fila = a_fila(CASO)
    assert list(fila.columns) == columnas()
    for posterior in ("status", "resolution_date", "first_response_date", "sla_breached", "estado"):
        assert posterior not in fila.columns


def test_metricas_del_experimento() -> None:
    y = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    p = np.linspace(1, 0, 10)
    assert captura_topk(p, y, 0.3, np.ones(10)) == 1.0
    assert umbral_precision(np.full(100, 0.2), np.zeros(100), 0.5) is None
    assert np.allclose(aplicar_platt(np.array([0.3]), (1.0, 0.0)), 0.3)
