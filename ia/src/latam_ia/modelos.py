"""Fábrica delgada de modelos de PydanticAI.

Orden: `LATAM_MODELO=guionado` fuerza `TestModel`; con `LATAM_MODELO_PROVEEDOR=geap` (o `LATAM_GCP_PROJECT`
sin llave) Gemini en Gemini Enterprise Agent Platform con ADC (D-32); con `GEMINI_API_KEY` Gemini de AI Studio
(D-30); si no, `TestModel`, de modo que las pruebas y el CI nunca llaman a un proveedor real.

Ambos puntos usan la compatibilidad con OpenAI: el paquete `google-genai` que exige el proveedor `google` de
PydanticAI choca hoy con `google-cloud-aiplatform` de dbt-bigquery. La parte de GEAP vive en Tecnología
(`latam_tecnologia.canales.geap`) porque el chat la usa y IA depende de Tecnología.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from latam_tecnologia.canales.geap import VARIABLE_MODELO, crear_modelo_geap, usa_geap
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.openai import OpenAIProvider

from latam_ia.registro.esquema import Modelo, Proveedor

VARIABLE_LLAVE = "GEMINI_API_KEY"
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/openai/"


def crear_modelo(spec: Modelo, entorno: Mapping[str, str] | None = None) -> Model:
    """Modelo real si hay llave para el proveedor del registro; `TestModel` si no."""
    env = os.environ if entorno is None else entorno
    if env.get(VARIABLE_MODELO) == "guionado":
        return TestModel()
    if usa_geap(env):
        return crear_modelo_geap(env)[0]
    if spec.proveedor is Proveedor.GEMINI_API and env.get(VARIABLE_LLAVE):
        proveedor = OpenAIProvider(base_url=URL_GEMINI, api_key=env[VARIABLE_LLAVE])
        return OpenAIChatModel(spec.id, provider=proveedor)
    return TestModel()
