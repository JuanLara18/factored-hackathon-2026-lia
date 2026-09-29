"""Gemini en Gemini Enterprise Agent Platform (GEAP, antes Vertex AI) con ADC, D-32.

Se usa el punto de compatibilidad con OpenAI de Vertex con un token que se refresca solo. El proveedor
`google` de PydanticAI exige `google-genai`, que choca con `google-cloud-aiplatform` de dbt-bigquery.
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from threading import Lock
from typing import Any, cast

import google.auth
import httpx
from google.auth.transport.requests import Request as RequestGoogle
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

VARIABLE_PROYECTO = "LATAM_GCP_PROJECT"
VARIABLE_UBICACION = "LATAM_GEAP_LOCATION"
VARIABLE_PROVEEDOR = "LATAM_MODELO_PROVEEDOR"
VARIABLE_MODELO = "LATAM_MODELO"
UBICACION_DEFECTO = "global"
# Gemini 3 por el punto OpenAI de Vertex falla con 400 (falta thought_signature tras cada herramienta): se usa 2.5
# hasta pasar al proveedor nativo `google`, que sí devuelve las firmas.
MODELO_DEFECTO = "gemini-2.5-flash-lite"
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


def crear_modelo_geap(env: Mapping[str, str], defecto: str = MODELO_DEFECTO) -> tuple[OpenAIChatModel, str]:
    """Modelo de PydanticAI sobre GEAP. No toca la red hasta la primera llamada."""
    proyecto = env[VARIABLE_PROYECTO]
    ubicacion = env.get(VARIABLE_UBICACION) or UBICACION_DEFECTO
    modelo = id_modelo(env, defecto)
    cliente = httpx.AsyncClient(auth=TokenAdc(), timeout=60)
    proveedor = OpenAIProvider(base_url=url_base(proyecto, ubicacion), api_key="adc", http_client=cliente)
    return OpenAIChatModel(f"google/{modelo}", provider=proveedor), f"geap:{modelo}"
