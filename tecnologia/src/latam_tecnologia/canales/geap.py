"""Gemini en Gemini Enterprise Agent Platform (GEAP, antes Vertex AI) con ADC, D-32.

Se usa el punto de compatibilidad con OpenAI de Vertex con un token que se refresca solo. El proveedor
`google` de PydanticAI exige `google-genai`, que choca con `google-cloud-aiplatform` de dbt-bigquery.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from threading import Lock
from typing import Any, cast

import google.auth
import httpx
from google.auth.transport.requests import Request as RequestGoogle
from openai import APIConnectionError, APIStatusError, AsyncOpenAI
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

VARIABLE_PROYECTO = "LATAM_GCP_PROJECT"
VARIABLE_UBICACION = "LATAM_GEAP_LOCATION"
VARIABLE_PROVEEDOR = "LATAM_MODELO_PROVEEDOR"
VARIABLE_MODELO = "LATAM_MODELO"
UBICACION_DEFECTO = "global"
# Gemini 3 por el punto OpenAI de Vertex falla con 400 (falta thought_signature tras cada herramienta):
# se usa 2.5 hasta pasar al proveedor nativo `google`, que sí devuelve las firmas.
MODELO_DEFECTO = "gemini-2.5-flash-lite"
REINTENTOS = 1
ESPERA_REINTENTO = 1.5  # segundos antes de reintentar
TEMPERATURA_REINTENTO = 0.8  # a temperatura 0 la misma llamada malformada saldría igual
FINISH_MALFORMADO = "malformed_function_call"
ALCANCE = "https://www.googleapis.com/auth/cloud-platform"


def usa_geap(env: Mapping[str, str]) -> bool:
    """GEAP si se pide (`LATAM_MODELO_PROVEEDOR=geap`) o si hay proyecto y no hay llave de AI Studio."""
    if env.get(VARIABLE_PROVEEDOR, "").lower() == "geap":
        return True
    return bool(env.get(VARIABLE_PROYECTO)) and not env.get("GEMINI_API_KEY")


def url_base(proyecto: str, ubicacion: str) -> str:
    host = "aiplatform.googleapis.com" if ubicacion == "global" else f"{ubicacion}-aiplatform.googleapis.com"
    return f"https://{host}/v1/projects/{proyecto}/locations/{ubicacion}/endpoints/openapi"


def id_modelo(env: Mapping[str, str], defecto: str = MODELO_DEFECTO) -> str:
    """Id sin prefijo; el endpoint de Vertex lo pide como `google/<id>`."""
    m = env.get(VARIABLE_MODELO, "")
    return defecto if m in ("", "guionado") else m


class TokenAdc(httpx.Auth):
    """Añade `Authorization: Bearer` con el token de ADC y lo renueva al vencer."""

    def __init__(self) -> None:
        self._cred: Any = None  # google.auth.credentials.Credentials
        self._lock = Lock()

    def _token(self) -> str:
        with self._lock:
            if self._cred is None:
                self._cred, _ = google.auth.default(scopes=[ALCANCE])  # pyright: ignore
            cred = cast(Any, self._cred)  # pyright: ignore[reportUnknownMemberType]
            if not cred.valid:
                cred.refresh(RequestGoogle())
            return str(cred.token)

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self._token()}"
        yield request


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
    """Gemini cerró con `finish_reason=malformed_function_call`: la llamada a herramienta no es válida."""


def es_transitorio(error: BaseException) -> bool:
    """Reintentable: llamada malformada, 5xx, 429 o corte de conexión. Un 4xx propio no lo es."""
    if isinstance(error, LlamadaMalformada | APIConnectionError):
        return True
    # El SDK rechaza el `finish_reason` de Gemini (no está en su lista) al validar la respuesta.
    if isinstance(error, UnexpectedModelBehavior) and FINISH_MALFORMADO in str(error):
        return True
    if isinstance(error, ModelHTTPError):
        return error.status_code >= 500 or error.status_code == 429
    if isinstance(error, APIStatusError):
        return error.status_code >= 500 or error.status_code == 429
    return False


class ModeloGeap(OpenAIChatModel):
    """`OpenAIChatModel` que reintenta una vez ante llamadas malformadas o errores 5xx transitorios."""

    def _map_finish_reason(self, key: Any) -> Any:
        if key == FINISH_MALFORMADO:
            raise LlamadaMalformada(f"finish_reason={FINISH_MALFORMADO}")
        return super()._map_finish_reason(key)

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
    """Modelo de PydanticAI sobre GEAP. No toca la red hasta la primera llamada."""
    proyecto = env[VARIABLE_PROYECTO]
    ubicacion = env.get(VARIABLE_UBICACION) or UBICACION_DEFECTO
    modelo = id_modelo(env, defecto)
    cliente = httpx.AsyncClient(auth=TokenAdc(), timeout=60)
    # Sin reintentos del SDK: la política de reintento es la de `ModeloGeap` (una vez).
    sdk = AsyncOpenAI(
        base_url=url_base(proyecto, ubicacion),
        api_key="adc",
        http_client=cliente,  # pyright: ignore[reportArgumentType]
        max_retries=0,
    )
    proveedor = OpenAIProvider(openai_client=sdk)
    return ModeloGeap(f"google/{modelo}", provider=proveedor), f"geap:{modelo}"
