"""Pista de riesgo de plazo de una disputa al radicarla (IA-10).

Es una pista, no una decisión: devuelve una probabilidad calibrada y una banda solo dentro de la región donde
la calibración se verificó en validación; fuera de ella, o si el experimento no encontró señal sobre las
líneas base, se abstiene. Solo sirve para subir la prioridad de un traspaso a una persona; nunca niega, decide
ni ejecuta. Las columnas y la construcción de la fila viven aquí para que el experimento y la inferencia usen
lo mismo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np
import pandas as pd  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, ConfigDict, Field

NUM = (
    "antiguedad_dias",
    "quejas_previas",
    "hora",
    "dia_semana",
    "n_tx_30d",
    "monto_tx_30d_usd",
    "monto_reclamado",
)
CAT = ("categoria", "subcategoria", "tipo_caso", "canal", "pais", "segmento", "tipo_producto", "moneda")
Banda = Literal["alta", "media", "baja"]


class SenalesDisputa(BaseModel):
    """Lo que se sabe al radicar. Ningún campo posterior (estado, fechas de respuesta o de cierre)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    categoria: str | None = None
    subcategoria: str | None = None
    tipo_caso: str | None = None
    canal: str | None = None
    pais: str | None = None
    segmento: str | None = None
    tipo_producto: str | None = None
    moneda: str | None = None
    antiguedad_dias: int | None = Field(default=None, ge=0)
    quejas_previas: int | None = Field(default=None, ge=0)
    hora: int | None = Field(default=None, ge=0, le=23)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    n_tx_30d: int | None = Field(default=None, ge=0)
    monto_tx_30d_usd: float | None = Field(default=None, ge=0)
    monto_reclamado: float | None = Field(default=None, ge=0)


class PistaRiesgo(BaseModel):
    """Pista de riesgo. `probabilidad` y `banda` son None cuando el modelo se abstiene."""

    model_config = ConfigDict(frozen=True)

    probabilidad: float | None
    banda: Banda | None
    abstiene: bool
    motivo_abstencion: str | None = None
    version_modelo: str
    accion_permitida: bool = False

    @property
    def en_riesgo(self) -> bool:
        return not self.abstiene and self.banda == "alta"


class ModeloRiesgo(Protocol):
    """Lo mínimo que se pide al modelo."""

    version: str
    con_senal: bool
    umbral_alto: float
    umbral_medio: float
    region: tuple[float, float]

    def probabilidades(self, filas: pd.DataFrame) -> np.ndarray: ...


def columnas() -> list[str]:
    return [*NUM, *CAT]


def a_fila(s: SenalesDisputa) -> pd.DataFrame:
    datos = s.model_dump()
    fila: dict[str, Any] = {}
    for c in NUM:
        fila[c] = np.nan if datos[c] is None else float(datos[c])
    for c in CAT:
        fila[c] = datos[c]
    return pd.DataFrame([fila])


def riesgo_plazo(caso: SenalesDisputa, modelo: ModeloRiesgo | None) -> PistaRiesgo:
    """Probabilidad de incumplir el plazo, banda y abstención. Solo orientativa."""
    if modelo is None:
        return PistaRiesgo(
            probabilidad=None,
            banda=None,
            abstiene=True,
            motivo_abstencion="sin modelo",
            version_modelo="ninguno",
        )
    if not modelo.con_senal:
        return PistaRiesgo(
            probabilidad=None,
            banda=None,
            abstiene=True,
            motivo_abstencion="el experimento no mostró señal sobre las líneas base",
            version_modelo=modelo.version,
        )
    p = float(np.asarray(modelo.probabilidades(a_fila(caso)))[0])
    lo, hi = modelo.region
    if not lo <= p <= hi:
        return PistaRiesgo(
            probabilidad=None,
            banda=None,
            abstiene=True,
            motivo_abstencion="región sin calibración verificada",
            version_modelo=modelo.version,
        )
    banda: Banda = "alta" if p >= modelo.umbral_alto else ("media" if p >= modelo.umbral_medio else "baja")
    return PistaRiesgo(probabilidad=p, banda=banda, abstiene=False, version_modelo=modelo.version)


def pista_de_plazo(p: PistaRiesgo) -> str:
    """Texto breve para el agente humano: contexto, no instrucción."""
    if p.abstiene or p.probabilidad is None:
        return "riesgo de plazo: sin pista fiable"
    return f"en riesgo de plazo: banda {p.banda} (p={p.probabilidad:.2f}, solo orientativo)"


class ModeloCalibradoRiesgo:
    """Árboles de gradiente con escalado de Platt ajustado en validación; implementa `ModeloRiesgo`."""

    def __init__(
        self,
        pipeline: Any,
        platt: tuple[float, float],
        umbral_alto: float,
        umbral_medio: float,
        region: tuple[float, float],
        con_senal: bool,
        version: str,
    ) -> None:
        self.pipeline = pipeline
        self.platt = platt
        self.umbral_alto = umbral_alto
        self.umbral_medio = umbral_medio
        self.region = region
        self.con_senal = con_senal
        self.version = version

    def probabilidades(self, filas: pd.DataFrame) -> np.ndarray:
        crudo = np.asarray(self.pipeline.predict_proba(filas[columnas()]))[:, 1]
        z = np.log(np.clip(crudo, 1e-9, 1 - 1e-9) / np.clip(1 - crudo, 1e-9, 1.0))
        a, b = self.platt
        return np.asarray(1.0 / (1.0 + np.exp(-(a * z + b))))


def cargar_modelo(ruta: Path) -> ModeloRiesgo:
    import joblib  # pyright: ignore[reportMissingTypeStubs]

    modelo: ModeloRiesgo = joblib.load(ruta)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return modelo
