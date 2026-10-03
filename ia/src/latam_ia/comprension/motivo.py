"""Clasificador del motivo de contacto como pista de enrutamiento (IA-2.2).

Es una pista, no una decisión: la función devuelve el motivo solo si la probabilidad calibrada alcanza el
umbral elegido en validación; si no, se abstiene y el caso sigue el camino humano. Nunca ejecuta efectos.
Las columnas y la construcción de rasgos viven aquí para que el experimento y la inferencia usen lo mismo.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, ConfigDict, Field

MOTIVOS: tuple[str, ...] = ("Comercial", "Producto", "Queja", "Retención", "Transaccional", "Técnico")

NUM_CONTACTO = ("hora", "dia_semana", "n_productos", "antiguedad_dias", "espera_segundos")
CAT_CONTACTO = ("tipo_interaccion", "canal", "segmento", "pais")
NUM_LLAMADA = ("duracion_segundos", "sentimiento", "resuelto", "requiere_seguimiento", "escalado")

CONJUNTOS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # Disponibles al abrir el contacto: sirven para enrutar antes de atender.
    "contacto": (NUM_CONTACTO, CAT_CONTACTO),
    # Se conocen al cerrar la llamada: sirven para sugerir el código de cierre, no para enrutar.
    "llamada": (NUM_CONTACTO + NUM_LLAMADA, CAT_CONTACTO),
}


class SenalesContacto(BaseModel):
    """Señales de un contacto, todas opcionales (faltan por construcción en chat y correo)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tipo_interaccion: str | None = None
    canal: str | None = None
    segmento: str | None = None
    pais: str | None = None
    hora: int | None = Field(default=None, ge=0, le=23)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    n_productos: int | None = Field(default=None, ge=0)
    antiguedad_dias: int | None = Field(default=None, ge=0)
    espera_segundos: int | None = Field(default=None, ge=0)
    duracion_segundos: int | None = Field(default=None, ge=0)
    sentimiento: float | None = Field(default=None, ge=-1.0, le=1.0)
    resuelto: bool | None = None
    requiere_seguimiento: bool | None = None
    escalado: bool | None = None


class SugerenciaMotivo(BaseModel):
    """Pista de enrutamiento. `motivo` es None cuando el modelo se abstiene."""

    model_config = ConfigDict(frozen=True)

    motivo: str | None
    probabilidad: float
    umbral: float
    abstiene: bool
    version_modelo: str
    accion_permitida: bool = False


class ModeloMotivo(Protocol):
    """Lo mínimo que se pide al modelo: probabilidades calibradas en el orden de `clases`."""

    version: str
    clases: Sequence[str]
    umbral: float

    def probabilidades(self, filas: pd.DataFrame) -> np.ndarray: ...


def columnas(conjunto: str) -> list[str]:
    num, cat = CONJUNTOS[conjunto]
    return [*num, *cat]


def a_fila(senales: SenalesContacto) -> pd.DataFrame:
    """Una fila con todas las columnas posibles (las ausentes quedan como NaN o None)."""
    datos = senales.model_dump()
    fila: dict[str, object] = {c: datos[c] for c in (*NUM_CONTACTO, *NUM_LLAMADA, *CAT_CONTACTO)}
    for c in (*NUM_CONTACTO, *NUM_LLAMADA):
        v = datos[c]
        fila[c] = np.nan if v is None else float(v)
    return pd.DataFrame([fila])


def sugerir_motivo(
    senales: SenalesContacto, modelo: ModeloMotivo, umbral: float | None = None
) -> SugerenciaMotivo:
    """Motivo sugerido o abstención. Es solo una pista: `accion_permitida` es siempre False."""
    u = modelo.umbral if umbral is None else umbral
    p = np.asarray(modelo.probabilidades(a_fila(senales)))[0]
    i = int(np.argmax(p))
    conf = float(p[i])
    abstiene = conf < u
    return SugerenciaMotivo(
        motivo=None if abstiene else str(modelo.clases[i]),
        probabilidad=conf,
        umbral=u,
        abstiene=abstiene,
        version_modelo=modelo.version,
    )


def pista_de_enrutamiento(s: SugerenciaMotivo) -> str:
    """Texto breve para el paso de comprensión del agente: contexto, no instrucción."""
    if s.abstiene or s.motivo is None:
        return "motivo de contacto: sin pista fiable (el caso sigue el camino humano)"
    return f"motivo de contacto probable: {s.motivo} (p={s.probabilidad:.2f}, solo orientativo)"


def cargar_modelo(ruta: Path) -> ModeloMotivo:
    """Carga el artefacto entrenado por `latam_ia.experimentos.motivo` (fuera de git)."""
    import joblib  # pyright: ignore[reportMissingTypeStubs]

    modelo: ModeloMotivo = joblib.load(ruta)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return modelo


class ModeloCalibrado:
    """Pipeline de sklearn con escalado de temperatura; implementa `ModeloMotivo`."""

    def __init__(
        self,
        pipeline: Any,
        clases: Sequence[str],
        temperatura: float,
        umbral: float,
        version: str,
        conjunto: str,
    ) -> None:
        self.pipeline = pipeline
        self.clases = tuple(clases)
        self.temperatura = temperatura
        self.umbral = umbral
        self.version = version
        self.conjunto = conjunto

    def logits(self, filas: pd.DataFrame) -> np.ndarray:
        proba = np.asarray(self.pipeline.predict_proba(filas[columnas(self.conjunto)]))
        return np.log(np.clip(proba, 1e-9, 1.0))

    def probabilidades(self, filas: pd.DataFrame) -> np.ndarray:
        z = self.logits(filas) / self.temperatura
        z = z - z.max(axis=1, keepdims=True)
        e = np.exp(z)
        return np.asarray(e / e.sum(axis=1, keepdims=True))
