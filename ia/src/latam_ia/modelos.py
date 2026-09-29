"""Fábrica delgada de modelos de PydanticAI.

Con `GEMINI_API_KEY` en el entorno usa Gemini (nivel gratuito de AI Studio, D-30); sin ella devuelve
`TestModel`, de modo que las pruebas y el CI nunca llaman a un proveedor real. Cuando se reabra la
facturación basta con otra rama en `crear_modelo` para `Proveedor.VERTEX_AI` (D-29).

Gemini se consulta por su punto de compatibilidad con OpenAI: el paquete `google-genai` que exige el
proveedor `google-gla:` de PydanticAI choca hoy con `google-cloud-aiplatform` de dbt-bigquery.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

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
    if spec.proveedor is Proveedor.GEMINI_API and env.get(VARIABLE_LLAVE):
        proveedor = OpenAIProvider(base_url=URL_GEMINI, api_key=env[VARIABLE_LLAVE])
        return OpenAIChatModel(spec.id, provider=proveedor)
    return TestModel()
