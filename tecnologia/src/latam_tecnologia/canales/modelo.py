"""Modelo del chat: Gemini en GEAP (D-32) o con `GEMINI_API_KEY`; sin nada, un guion con las herramientas."""

from __future__ import annotations

import json
import os
import re
from collections.abc import AsyncIterator, Mapping
from typing import Any, cast

from pydantic_ai import ModelMessage, ModelRequest, ToolReturnPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from latam_tecnologia.canales.geap import VARIABLE_MODELO, VARIABLE_PROYECTO, crear_modelo_geap, usa_geap
from latam_tecnologia.canales.textos import describir_comercio, estado_transaccion, plantilla

VARIABLE_LLAVE = "GEMINI_API_KEY"
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODELO_GEMINI = "gemini-2.5-flash-lite"
_NO_RECONOCE = re.compile(r"no\s+(la\s+)?reconozc?o|no\s+es\s+m[ií]a", re.IGNORECASE)
_RECONOCE = re.compile(r"\bla\s+reconozco\b|\bes\s+m[ií]a\b", re.IGNORECASE)


def _registro(info: AgentInfo) -> str:
    return "vos" if info.instructions and "Registro: vos" in info.instructions else "usted"


def _partes(messages: list[ModelMessage]) -> tuple[str, list[ToolReturnPart], list[ToolReturnPart]]:
    """Último texto del cliente, retornos de herramienta posteriores a él y todos los retornos."""
    ultimo = ""
    tras: list[ToolReturnPart] = []
    todos: list[ToolReturnPart] = []
    for m in messages:
        if not isinstance(m, ModelRequest):
            continue
        for p in m.parts:
            if isinstance(p, UserPromptPart):
                ultimo, tras = str(p.content), []
            elif isinstance(p, ToolReturnPart):
                tras.append(p)
                todos.append(p)
    return ultimo, tras, todos


def _dinero(monto: str) -> str:
    entero, _, dec = f"{float(monto):,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{dec}"


def _trozos(texto: str, n: int = 24) -> list[str]:
    return [texto[i : i + n] for i in range(0, len(texto), n)]


def _filas(contenido: Any) -> list[dict[str, Any]]:
    """El adaptador puede devolver el resultado ya decodificado (lista) o como texto JSON."""
    if isinstance(contenido, str):
        contenido = json.loads(contenido)
    return cast(list[dict[str, Any]], contenido)


def _tx_de(retornos: list[ToolReturnPart]) -> dict[str, Any] | None:
    for r in reversed(retornos):
        if r.tool_name == "listar_transacciones":
            filas = _filas(r.content)
            return filas[0] if filas else None
    return None


def crear_modelo_guionado() -> FunctionModel:
    """Conduce una disputa: lista, ficha, aprobación y cierre. Todo el texto sale de plantillas."""

    async def flujo(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | DeltaToolCalls]:
        reg = _registro(info)
        usuario, tras, todos = _partes(messages)
        if (r := next((p for p in tras if p.tool_name == "abrir_disputa"), None)) is not None:
            if r.outcome == "denied":
                texto = plantilla("cierre.sin_cambios", reg)
            else:
                texto = plantilla(
                    "cierre.chat",
                    reg,
                    hecho=f"quedó registrado el reclamo {r.content}",
                    no_hecho="no se bloqueó la tarjeta ni se movió dinero",
                    que_sigue="el banco revisará el cargo y se lo hará saber por este canal",
                )
            for t in _trozos(texto):
                yield t
            return
        if (tx := _tx_de(tras)) is not None:
            monto = tx["monto"]["monto"]
            texto = plantilla(
                "identificando.chat",
                reg,
                cargo="cargo",
                comercio=describir_comercio(tx["comercio"], tx.get("tipo")),
                fecha=str(tx["event_ts"])[:10],
                monto=_dinero(monto),
                moneda=str(tx["monto"]["moneda"]),
            )
            for t in _trozos(texto):
                yield t
            digitos = re.sub(r"\D", "", str(tx["product_id"])).rjust(4, "0")[-4:]
            ficha = {
                "comercio": describir_comercio(tx["comercio"], tx.get("tipo")),
                "monto": _dinero(monto),
                "moneda": tx["monto"]["moneda"],
                "fecha": str(tx["event_ts"])[:10],
                "estado": estado_transaccion(tx["estado"]),
                "tarjeta_final": digitos,
            }
            yield {
                1: DeltaToolCall(name="FichaTransaccion", json_args=json.dumps(ficha), tool_call_id="ficha")
            }
            return
        previa = _tx_de(todos)
        if previa is not None and _NO_RECONOCE.search(usuario):
            args = {"transaction_id": previa["transaction_id"], "motivo": "es_mia_no_la_reconozco"}
            yield {0: DeltaToolCall(name="abrir_disputa", json_args=json.dumps(args), tool_call_id="disputa")}
            return
        if previa is not None and _RECONOCE.search(usuario):
            for t in _trozos(plantilla("cierre.sin_cambios", reg)):
                yield t
            return
        yield {0: DeltaToolCall(name="listar_transacciones", json_args='{"limite": 1}', tool_call_id="lista")}

    return FunctionModel(stream_function=flujo)


def crear_modelo(entorno: Mapping[str, str] | None = None) -> tuple[Model, str]:
    """`LATAM_MODELO=guionado` fuerza el guion; luego GEAP (D-32), luego AI Studio, luego el guion."""
    env = os.environ if entorno is None else entorno
    if env.get(VARIABLE_MODELO) == "guionado":
        return crear_modelo_guionado(), "guionado"
    if env.get(VARIABLE_PROYECTO) and usa_geap(env):
        return crear_modelo_geap(env)
    if env.get(VARIABLE_LLAVE):
        proveedor = OpenAIProvider(base_url=URL_GEMINI, api_key=env[VARIABLE_LLAVE])
        return OpenAIChatModel(MODELO_GEMINI, provider=proveedor), f"gemini:{MODELO_GEMINI}"
    return crear_modelo_guionado(), "guionado"
