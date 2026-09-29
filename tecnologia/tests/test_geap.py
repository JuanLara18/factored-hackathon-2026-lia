import httpx
import pytest
from latam_tecnologia.canales import geap
from latam_tecnologia.canales.geap import ModeloGeap
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.providers.openai import OpenAIProvider


def _cuerpo(finish: str, texto: str = "hola") -> dict[str, object]:
    return {
        "id": "x",
        "object": "chat.completion",
        "created": 0,
        "model": "google/gemini-2.5-flash-lite",
        "choices": [
            {"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": texto}}
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


@pytest.fixture(autouse=True)
def _sin_espera(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(geap, "ESPERA_REINTENTO", 0)


def _agente(respuestas: list[httpx.Response]) -> tuple[Agent[None, str], list[int]]:
    llamadas: list[int] = []

    def manejar(request: httpx.Request) -> httpx.Response:
        llamadas.append(1)
        return respuestas[min(len(llamadas), len(respuestas)) - 1]

    cliente = httpx.AsyncClient(transport=httpx.MockTransport(manejar))
    sdk = AsyncOpenAI(base_url="https://ejemplo.test/v1", api_key="x", http_client=cliente, max_retries=0)
    proveedor = OpenAIProvider(openai_client=sdk)
    return Agent(ModeloGeap("google/gemini-2.5-flash-lite", provider=proveedor)), llamadas


def test_reintenta_una_vez_la_llamada_malformada() -> None:
    agente, llamadas = _agente(
        [
            httpx.Response(200, json=_cuerpo("malformed_function_call", "")),
            httpx.Response(200, json=_cuerpo("stop")),
        ]
    )
    assert agente.run_sync("hola").output == "hola"
    assert len(llamadas) == 2


def test_el_reintento_sube_la_temperatura() -> None:
    temperaturas: list[float | None] = []

    def manejar(request: httpx.Request) -> httpx.Response:
        import json

        temperaturas.append(json.loads(request.content).get("temperature"))
        if len(temperaturas) == 1:
            return httpx.Response(200, json=_cuerpo("malformed_function_call", ""))
        return httpx.Response(200, json=_cuerpo("stop"))

    cliente = httpx.AsyncClient(transport=httpx.MockTransport(manejar))
    sdk = AsyncOpenAI(base_url="https://ejemplo.test/v1", api_key="x", http_client=cliente, max_retries=0)
    agente = Agent(ModeloGeap("google/x", provider=OpenAIProvider(openai_client=sdk)))
    agente.run_sync("hola", model_settings={"temperature": 0.0})
    assert temperaturas == [0.0, geap.TEMPERATURA_REINTENTO]


def test_reintenta_una_vez_un_5xx() -> None:
    agente, llamadas = _agente(
        [httpx.Response(503, json={"error": {"message": "no"}}), httpx.Response(200, json=_cuerpo("stop"))]
    )
    assert agente.run_sync("hola").output == "hola"
    assert len(llamadas) == 2


def test_no_reintenta_mas_de_una_vez() -> None:
    agente, llamadas = _agente([httpx.Response(500, json={"error": {"message": "no"}})])
    with pytest.raises(ModelHTTPError):
        agente.run_sync("hola")
    assert len(llamadas) == 2


def test_no_reintenta_un_error_del_cliente() -> None:
    agente, llamadas = _agente([httpx.Response(400, json={"error": {"message": "mal"}})])
    with pytest.raises(ModelHTTPError):
        agente.run_sync("hola")
    assert len(llamadas) == 1
