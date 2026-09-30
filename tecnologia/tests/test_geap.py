import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from google import genai
from google.genai import errors as errores_genai
from latam_tecnologia.canales import geap
from latam_tecnologia.canales.geap import LlamadaMalformada, ModeloGeap, es_malformada, es_transitorio
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.settings import ModelSettings


def _malformada() -> ModelResponse:
    return ModelResponse(
        parts=[], finish_reason="error", provider_details={"finish_reason": "MALFORMED_FUNCTION_CALL"}
    )


def _ok() -> ModelResponse:
    return ModelResponse(parts=[TextPart("hola")], finish_reason="stop")


@pytest.fixture(autouse=True)
def _sin_espera(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(geap, "ESPERA_REINTENTO", 0)
    geap.MEDIDOR.reiniciar()


def _modelo() -> ModeloGeap:
    cliente = genai.Client(api_key="x")
    return ModeloGeap("gemini-2.5-flash-lite", provider=GoogleProvider(client=cliente))


def _guion(
    monkeypatch: pytest.MonkeyPatch, pasos: list[Callable[[], ModelResponse]]
) -> list[ModelSettings | None]:
    ajustes: list[ModelSettings | None] = []

    async def falso(
        self: Any, messages: Any, model_settings: ModelSettings | None, params: Any
    ) -> ModelResponse:
        ajustes.append(model_settings)
        return pasos[min(len(ajustes), len(pasos)) - 1]()

    monkeypatch.setattr(GoogleModel, "request", falso)
    return ajustes


def _pide(modelo: ModeloGeap, ajustes: ModelSettings | None = None) -> ModelResponse:
    return asyncio.run(modelo.request([], ajustes, geap.ModelRequestParameters()))


def _falla(error: Exception) -> Callable[[], ModelResponse]:
    def f() -> ModelResponse:
        raise error

    return f


def test_reintenta_una_vez_la_llamada_malformada(monkeypatch: pytest.MonkeyPatch) -> None:
    ajustes = _guion(monkeypatch, [_malformada, _ok])
    r = _pide(_modelo(), {"temperature": 0.0})
    assert r.parts[0] == TextPart("hola")
    assert len(ajustes) == 2
    assert ajustes[0] == {"temperature": 0.0}
    assert ajustes[1] == {"temperature": geap.TEMPERATURA_REINTENTO}
    assert geap.MEDIDOR.llamadas == 2 and geap.MEDIDOR.reintentos == 1


def test_reintenta_una_vez_un_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    ajustes = _guion(monkeypatch, [_falla(ModelHTTPError(503, "m", None)), _ok])
    _pide(_modelo())
    assert len(ajustes) == 2


def test_no_reintenta_mas_de_una_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    ajustes = _guion(monkeypatch, [_malformada])
    with pytest.raises(LlamadaMalformada):
        _pide(_modelo())
    assert len(ajustes) == 2


def test_no_reintenta_un_error_del_cliente(monkeypatch: pytest.MonkeyPatch) -> None:
    ajustes = _guion(monkeypatch, [_falla(ModelHTTPError(400, "m", None))])
    with pytest.raises(ModelHTTPError):
        _pide(_modelo())
    assert len(ajustes) == 1


def test_clasifica_errores_de_google_y_malformadas() -> None:
    assert es_transitorio(errores_genai.ServerError(500, {"error": {"message": "x"}}))
    assert es_transitorio(errores_genai.ClientError(429, {"error": {"message": "x"}}))
    assert not es_transitorio(errores_genai.ClientError(400, {"error": {"message": "x"}}))
    assert es_malformada(_malformada())
    con_llamada = ModelResponse(
        parts=[ToolCallPart("t", {})], provider_details={"finish_reason": "MALFORMED_FUNCTION_CALL"}
    )
    assert not es_malformada(con_llamada)
    assert not es_malformada(_ok())


def test_fabrica_usa_vertex_global() -> None:
    modelo, nombre = geap.crear_modelo_geap({"LATAM_GCP_PROJECT": "p"})
    assert nombre == f"geap:{geap.MODELO_DEFECTO}"
    assert modelo.client.vertexai is True
