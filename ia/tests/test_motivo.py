"""Pruebas sin red del clasificador de motivo: métricas, abstención y tubería sobre un fixture mínimo."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from latam_ia.comprension.motivo import (
    MOTIVOS,
    ModeloCalibrado,
    SenalesContacto,
    a_fila,
    columnas,
    pista_de_enrutamiento,
    sugerir_motivo,
)
from latam_ia.experimentos import metricas as m
from latam_ia.experimentos.motivo import construir, reglas_b1


def _datos(n: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    y = rng.integers(0, len(MOTIVOS), n)
    base = np.array([540, 263, 431, 478, 205, 360], dtype=float)
    return pd.DataFrame(
        {
            "y": y,
            "hora": rng.integers(0, 24, n).astype(float),
            "dia_semana": rng.integers(0, 7, n).astype(float),
            "n_productos": rng.integers(0, 3, n).astype(float),
            "antiguedad_dias": rng.integers(0, 900, n).astype(float),
            "espera_segundos": rng.normal(120, 50, n),
            "duracion_segundos": base[y] + rng.normal(0, 40, n),
            "sentimiento": rng.normal(0, 0.3, n).clip(-1, 1),
            "resuelto": rng.integers(0, 2, n).astype(float),
            "requiere_seguimiento": rng.integers(0, 2, n).astype(float),
            "escalado": rng.integers(0, 2, n).astype(float),
            "tipo_interaccion": rng.choice(["Inbound Call", "Chat"], n),
            "canal": rng.choice(["Phone", "App"], n),
            "segmento": rng.choice(["Basic", "Plus"], n),
            "pais": rng.choice(["CO", "MX"], n),
        }
    )


def test_metricas_basicas() -> None:
    y = np.array([0, 1, 1, 2])
    assert m.macro_f1(y, y, 3) == pytest.approx(1.0)
    prob = np.eye(3)[y]
    assert m.ece(prob, y) == pytest.approx(0.0)
    assert m.brier(prob, y) == pytest.approx(0.0)
    c = m.costo_abstencion(np.array([[0.9, 0.1], [0.55, 0.45]]), np.array([0, 1]), 0.8, 5.0, 1.0)
    assert c["cobertura"] == 0.5 and c["costo"] == pytest.approx(0.5)


def test_temperatura_corrige_sobreconfianza() -> None:
    rng = np.random.default_rng(1)
    y = rng.integers(0, 3, 3000)
    logits = np.eye(3)[y] * 1.0 + rng.normal(0, 1.0, (3000, 3))
    t = m.escalar_temperatura(logits * 5.0, y)  # logits inflados x5
    assert t > 3.0


def test_bootstrap_por_cliente_es_determinista() -> None:
    cl = np.repeat(np.arange(50), 4)
    f = lambda w: {"media": float(w.mean())}  # noqa: E731
    a = m.bootstrap_clusters(cl, f, 50, 3)
    assert a == m.bootstrap_clusters(cl, f, 50, 3)
    assert a["media"][0] < 1.0 < a["media"][1]


def test_reglas_sin_duracion_caen_en_la_mayoritaria() -> None:
    d = _datos(20)
    d["duracion_segundos"] = np.nan
    assert set(reglas_b1(d).tolist()) == {MOTIVOS.index("Transaccional")}


def test_tuberia_y_abstencion() -> None:
    d = _datos()
    pipe = construir("logistica", "llamada").fit(d[columnas("llamada")], d["y"])
    modelo = ModeloCalibrado(pipe, MOTIVOS, 1.0, 0.99, "prueba", "llamada")
    larga = SenalesContacto(
        tipo_interaccion="Inbound Call", duracion_segundos=900, sentimiento=-0.4, resuelto=False
    )
    s = sugerir_motivo(larga, modelo, umbral=0.0)
    assert s.motivo in MOTIVOS and not s.abstiene and s.accion_permitida is False
    vacio = sugerir_motivo(SenalesContacto(), modelo)  # sin señales y umbral alto: se abstiene
    assert vacio.abstiene and vacio.motivo is None
    assert "sin pista fiable" in pista_de_enrutamiento(vacio)
    assert "solo orientativo" in pista_de_enrutamiento(s)
    assert a_fila(SenalesContacto()).shape == (1, 14)
