"""Gemini en Gemini Enterprise Agent Platform (GEAP, antes Vertex AI) con ADC, D-32.

Proveedor nativo de PydanticAI (`GoogleModel` con `GoogleCloudProvider`, Vertex, ubicación `global`): devuelve
las firmas de pensamiento de Gemini 3 y evita las llamadas malformadas del punto compatible con OpenAI.
dbt-bigquery corre aparte (`uvx`), por eso ya no choca con `google-genai` en el lock.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from google.genai import errors as errores_genai
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_ai.settings import ModelSettings

VARIABLE_PROYECTO = "LATAM_GCP_PROJECT"
VARIABLE_UBICACION = "LATAM_GEAP_LOCATION"
VARIABLE_PROVEEDOR = "LATAM_MODELO_PROVEEDOR"
VARIABLE_MODELO = "LATAM_MODELO"
UBICACION_DEFECTO = "global"
MODELO_DEFECTO = "gemini-3.1-flash-lite"
REINTENTOS = 1
ESPERA_REINTENTO = 1.5  # segundos antes de reintentar
TEMPERATURA_REINTENTO = 0.8  # a temperatura 0 la misma llamada malformada saldría igual
FINISH_MALFORMADO = "MALFORMED_FUNCTION_CALL"


def usa_geap(env: Mapping[str, str]) -> bool:
    """GEAP si se pide (`LATAM_MODELO_PROVEEDOR=geap`) o si hay proyecto y no hay llave de AI Studio."""
    if env.get(VARIABLE_PROVEEDOR, "").lower() == "geap":
        return True
    return bool(env.get(VARIABLE_PROYECTO)) and not env.get("GEMINI_API_KEY")


def id_modelo(env: Mapping[str, str], defecto: str = MODELO_DEFECTO) -> str:
    """Id del modelo sin prefijo."""
    m = env.get(VARIABLE_MODELO, "")
    return defecto if m in ("", "guionado") else m


@dataclass
class Medidor:
    """Consumo acumulado del proceso: llamadas al modelo (con reintentos), tokens y tiempo de espera."""

    llamadas: int = 0
    reintentos: int = 0
    entrada: int = 0
    salida: int = 0
    segundos: float = 0.0
    errores: int = 0

    def reiniciar(self) -> None:
        self.llamadas = self.reintentos = self.entrada = self.salida = self.errores = 0
        self.segundos = 0.0


MEDIDOR = Medidor()


class LlamadaMalformada(UnexpectedModelBehavior):
    """Gemini cerró con `MALFORMED_FUNCTION_CALL`: la llamada a herramienta no es válida."""


def es_malformada(respuesta: ModelResponse) -> bool:
    """Cierre `MALFORMED_FUNCTION_CALL` sin ninguna llamada a herramienta utilizable."""
    detalles = respuesta.provider_details or {}
    crudo = str(detalles.get("finish_reason", ""))
    return crudo.upper() == FINISH_MALFORMADO.upper() and not any(
        isinstance(p, ToolCallPart) for p in respuesta.parts
    )


def es_transitorio(error: BaseException) -> bool:
    """Reintentable: llamada malformada, 5xx, 429 o corte de conexión. Un 4xx propio no lo es."""
    if isinstance(error, LlamadaMalformada):
        return True
    if isinstance(error, ModelHTTPError):
        return error.status_code >= 500 or error.status_code == 429
    if isinstance(error, errores_genai.APIError):
        codigo = error.code or 0
        return codigo >= 500 or codigo == 429
    return False


class ModeloGeap(GoogleModel):
    """`GoogleModel` que reintenta una vez ante llamadas malformadas o errores 5xx transitorios."""

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        intento = 0
        while True:
            MEDIDOR.llamadas += 1
            t0 = time.monotonic()
            try:
                respuesta = await super().request(messages, model_settings, model_request_parameters)
                if es_malformada(respuesta):
                    raise LlamadaMalformada(f"finish_reason={FINISH_MALFORMADO}")
            except Exception as error:
                MEDIDOR.segundos += time.monotonic() - t0
                MEDIDOR.errores += 1
                if intento >= REINTENTOS or not es_transitorio(error):
                    raise
                intento += 1
                MEDIDOR.reintentos += 1
                model_settings = cast(
                    ModelSettings, {**(model_settings or {}), "temperature": TEMPERATURA_REINTENTO}
                )
                await asyncio.sleep(ESPERA_REINTENTO)
                continue
            MEDIDOR.segundos += time.monotonic() - t0
            MEDIDOR.entrada += respuesta.usage.input_tokens
            MEDIDOR.salida += respuesta.usage.output_tokens
            return respuesta


def crear_modelo_geap(env: Mapping[str, str], defecto: str = MODELO_DEFECTO) -> tuple[ModeloGeap, str]:
    """Modelo de PydanticAI sobre GEAP (Vertex, ADC). No toca la red hasta la primera llamada."""
    proyecto = env[VARIABLE_PROYECTO]
    ubicacion = env.get(VARIABLE_UBICACION) or UBICACION_DEFECTO
    modelo = id_modelo(env, defecto)
    proveedor = GoogleCloudProvider(project=proyecto, location=ubicacion)
    return ModeloGeap(modelo, provider=proveedor), f"geap:{modelo}"
