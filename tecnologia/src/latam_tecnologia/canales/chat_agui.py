"""Superficie de chat AG-UI (spike S3): modelo simulado, frases filtradas, componente y aprobación."""

from __future__ import annotations

import json
import secrets
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from pathlib import Path

from ag_ui.core import BaseEvent, TextMessageContentEvent, TextMessageEndEvent, TextMessageStartEvent
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic_ai import Agent, DeferredToolRequests, ModelMessage, ModelRequest, RunContext, ToolReturnPart
from pydantic_ai.messages import TextPart, TextPartDelta
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel
from pydantic_ai.ui.ag_ui import AGUIAdapter, AGUIEventStream

from latam_tecnologia.canales.frases import FiltroFrase, SegmentadorFrases, filtrar_frase

VIGENCIA_NONCE_S = 300.0
PLANTILLA_RESPALDO = "Voy a revisar esto con un asesor para darte una respuesta correcta."
WEB_DIR = Path(__file__).resolve().parents[3] / "web" / "spike_s3"


@dataclass
class Confirmaciones:
    """Nonces de confirmación: vigentes 5 minutos, de una sola sesión y de un solo uso (R-TEC-77)."""

    reloj: Callable[[], float] = time.monotonic
    _vivos: dict[str, tuple[str, float]] = field(default_factory=dict[str, tuple[str, float]])

    def emitir(self, sesion: str) -> str:
        nonce = secrets.token_hex(8)
        self._vivos[nonce] = (sesion, self.reloj() + VIGENCIA_NONCE_S)
        return nonce

    def consumir(self, nonce: str, sesion: str) -> bool:
        vivo = self._vivos.pop(nonce, None)
        return vivo is not None and vivo[0] == sesion and self.reloj() < vivo[1]


@dataclass
class FiltradoEventStream(AGUIEventStream[Confirmaciones, str | DeferredToolRequests]):
    """Traduce texto del modelo a un `TEXT_MESSAGE_CONTENT` por frase que pasó el filtro."""

    filtro: FiltroFrase = filtrar_frase
    traza: list[str] = field(default_factory=list[str])
    _seg: SegmentadorFrases = field(default_factory=SegmentadorFrases, init=False)
    _bloqueado: bool = field(default=False, init=False)

    def _emitir(self, frases: list[str]) -> list[BaseEvent]:
        eventos: list[BaseEvent] = []
        for frase in frases:
            if self._bloqueado:
                break
            r = self.filtro(frase)
            if r.bloqueada:
                self._bloqueado = True
                self.traza.append(f"filtro_salida.bloqueo {r.motivo}")
                texto = PLANTILLA_RESPALDO
            else:
                texto = r.texto
            eventos.append(TextMessageContentEvent(message_id=self.message_id, delta=texto + " "))
        return eventos

    async def handle_text_start(self, part: TextPart, follows_text: bool = False) -> AsyncIterator[BaseEvent]:
        if not follows_text:
            self._started_message_id = self.new_message_id()
            self._seg = SegmentadorFrases()
            self._bloqueado = False
            yield TextMessageStartEvent(message_id=self.message_id)
        for e in self._emitir(self._seg.alimentar(part.content)):
            yield e

    async def handle_text_delta(self, delta: TextPartDelta) -> AsyncIterator[BaseEvent]:
        for e in self._emitir(self._seg.alimentar(delta.content_delta)):
            yield e

    async def handle_text_end(
        self, part: TextPart, followed_by_text: bool = False
    ) -> AsyncIterator[BaseEvent]:
        for e in self._emitir(self._seg.vaciar()):
            yield e
        if not followed_by_text:
            yield TextMessageEndEvent(message_id=self.message_id)


@dataclass
class ChatAdapter(AGUIAdapter[Confirmaciones, str | DeferredToolRequests]):
    traza: list[str] = field(default_factory=list[str])

    def build_event_stream(self) -> FiltradoEventStream:
        return FiltradoEventStream(
            self.run_input, accept=self.accept, ag_ui_version=self.ag_ui_version, traza=self.traza
        )


def _retorno(messages: list[ModelMessage], herramienta: str) -> str | None:
    for m in reversed(messages):
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, ToolReturnPart) and p.tool_name == herramienta:
                    return str(p.content)
    return None


def _trozos(texto: str, n: int = 6) -> list[str]:
    return [texto[i : i + n] for i in range(0, len(texto), n)]


def crear_agente(*, texto_inseguro: bool = False) -> Agent[Confirmaciones, str]:
    """Agente con un modelo simulado (sin llamadas de pago). `texto_inseguro` inyecta un dato sensible."""

    async def flujo(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | DeltaToolCalls]:
        if (r := _retorno(messages, "solicitar_confirmacion")) is not None:
            for t in _trozos("Listo. " + r + " Gracias por avisarnos."):
                yield t
            return
        if (nonce := _retorno(messages, "preparar_confirmacion")) is None:
            yield {0: DeltaToolCall(name="preparar_confirmacion", json_args="{}", tool_call_id="c-prep")}
            return
        intro = "Encontré el cargo de $ 1.234,56 en Tienda Uno. "
        if texto_inseguro:
            intro += "Tu tarjeta 4111 1111 1111 1111 quedó registrada. "
        intro += "Necesito tu confirmación para continuar."
        for t in _trozos(intro):
            yield t
        ficha = {"comercio": "Tienda Uno", "monto": "1.234,56", "moneda": "COP", "estado": "aprobada"}
        yield {1: DeltaToolCall(name="FichaTransaccion", tool_call_id="c-ficha")}
        for t in _trozos(json.dumps(ficha), 20):
            yield {1: DeltaToolCall(json_args=t)}
        args = {"nonce": nonce, "accion": "disputar_cargo", "monto": "1.234,56"}
        yield {2: DeltaToolCall(name="solicitar_confirmacion", tool_call_id="c-conf")}
        for t in _trozos(json.dumps(args), 20):
            yield {2: DeltaToolCall(json_args=t)}

    agente: Agent[Confirmaciones, str] = Agent(
        FunctionModel(stream_function=flujo), deps_type=Confirmaciones, output_type=str
    )

    @agente.tool
    def preparar_confirmacion(ctx: RunContext[Confirmaciones]) -> str:  # pyright: ignore[reportUnusedFunction]
        return ctx.deps.emitir(ctx.conversation_id or "")

    @agente.tool(requires_approval=True)
    def solicitar_confirmacion(  # pyright: ignore[reportUnusedFunction]
        ctx: RunContext[Confirmaciones], nonce: str, accion: str, monto: str
    ) -> str:
        if not ctx.deps.consumir(nonce, ctx.conversation_id or ""):
            return "La confirmación no es válida o venció."
        return f"Quedó confirmada la acción {accion} por {monto}."

    return agente


def crear_app(*, texto_inseguro: bool = False, confirmaciones: Confirmaciones | None = None) -> FastAPI:
    app = FastAPI()
    agente = crear_agente(texto_inseguro=texto_inseguro)
    conf = confirmaciones or Confirmaciones()
    traza: list[str] = []
    app.state.traza = traza

    @app.post("/agui")
    async def agui(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        return await ChatAdapter.dispatch_request(request, agent=agente, deps=conf, traza=traza)

    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
