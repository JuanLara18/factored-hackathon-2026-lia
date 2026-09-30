"""Chat web con el agente en Agent Runtime (D-32 fase 2): el canal reenvía cada turno y traduce a AG-UI.

Se activa con `LATAM_AGENT_RUNTIME_RECURSO=projects/<p>/locations/<l>/reasoningEngines/<id>`. El canal abre
la sesión de Agent Runtime con el cliente, el nivel y el vencimiento; el agente los lee de ahí. El canal
conserva lo suyo: vencimiento de la aprobación, texto de la plantilla y filtro de salida.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import secrets
from collections.abc import AsyncIterator, Callable
from typing import Any, Protocol

from ag_ui.core import (
    BaseEvent,
    Interrupt,
    RunErrorEvent,
    RunFinishedEvent,
    RunFinishedInterruptOutcome,
    RunFinishedSuccessOutcome,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from latam_comun.dominio import SesionAutenticada

from latam_tecnologia.canales.frases import SegmentadorFrases, filtrar_frase
from latam_tecnologia.runtime.agente import crear_cliente_sdk

VARIABLE_RECURSO = "LATAM_AGENT_RUNTIME_RECURSO"
TIEMPO_TURNO_S = 90.0  # tope de un turno completo; pasado, el cliente recibe el aviso y puede reintentar
MENSAJE_FALLA = (
    "No pude continuar en este momento. Intenta de nuevo en unos minutos o pide una persona del equipo."
)
log = logging.getLogger(__name__)
PLANTILLA_RESPALDO = "Voy a revisar esto con un asesor para darte una respuesta correcta."
_RECURSO = re.compile(r"^projects/([^/]+)/locations/([^/]+)/reasoningEngines/([^/]+)$")

Enriquecedor = Callable[[str, str, dict[str, Any]], tuple[str, str]]


class AgenteNoDisponible(Exception):
    """No se pudo abrir la sesión del agente (red, permisos o cuota)."""


class ClienteRuntime(Protocol):
    def crear_sesion(self, *, user_id: str, session_id: str, estado: dict[str, str]) -> None: ...

    def turno(
        self,
        *,
        user_id: str,
        session_id: str,
        mensaje: str | None,
        aprobaciones: dict[str, bool] | None,
        registro: str,
    ) -> AsyncIterator[dict[str, Any]]: ...


def id_usuario(cliente_id: str) -> str:
    """Seudónimo estable del cliente para Sessions; el id real solo viaja en el estado de la sesión."""
    return "u-" + hashlib.sha256(cliente_id.encode()).hexdigest()[:16]


def estado_de_confianza(s: SesionAutenticada, conversacion_id: str) -> dict[str, str]:
    return {
        "cliente_id": s.cliente_id,
        "nivel": s.nivel.value,
        "expira": s.expira.isoformat(),
        "conversacion_id": conversacion_id,
    }


class ClienteAgentRuntime:
    """Cliente real. El SDK (`agentplatform`, o `vertexai` en versiones previas) se importa al primer uso."""

    def __init__(self, recurso: str) -> None:
        m = _RECURSO.match(recurso)
        if m is None:
            raise ValueError(
                f"{VARIABLE_RECURSO} debe tener la forma projects/<p>/locations/<l>/reasoningEngines/<id>"
            )
        self.recurso = recurso
        self._proyecto, self._ubicacion = m.group(1), m.group(2)
        self._cliente: Any = None
        self._agente: Any = None

    def _c(self) -> Any:
        if self._cliente is None:
            self._cliente = crear_cliente_sdk(self._proyecto, self._ubicacion)
        return self._cliente

    def crear_sesion(self, *, user_id: str, session_id: str, estado: dict[str, str]) -> None:
        try:
            c = self._c()
            sesiones = getattr(c, "sessions", None) or c.agent_engines.sessions
            sesiones.create(
                name=self.recurso,
                user_id=user_id,
                config={"session_id": session_id, "session_state": estado, "ttl": "86400s"},
            )
        except Exception as error:
            log.warning("no se pudo crear la sesión del agente (%s)", type(error).__name__)
            raise AgenteNoDisponible from error

    async def turno(
        self,
        *,
        user_id: str,
        session_id: str,
        mensaje: str | None,
        aprobaciones: dict[str, bool] | None,
        registro: str,
    ) -> AsyncIterator[dict[str, Any]]:
        if self._agente is None:
            c = self._c()
            obtener = getattr(c, "runtimes", None) or c.agent_engines
            self._agente = obtener.get(name=self.recurso)
        async for evento in self._agente.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=mensaje,
            aprobaciones=aprobaciones,
            registro=registro,
        ):
            yield evento


def _evento(e: BaseEvent) -> str:
    return EventEncoder().encode(e)


def _cerrar_texto(abierto: bool, mensaje_id: str) -> list[str]:
    """Si ya se abrió un mensaje de texto, lo cierra para que el cliente no quede con uno a medias."""
    return [_evento(TextMessageEndEvent(message_id=mensaje_id))] if abierto else []


async def flujo_agui(
    cliente: ClienteRuntime,
    *,
    thread_id: str,
    user_id: str,
    mensaje: str | None,
    aprobaciones: dict[str, bool] | None,
    registro: str,
    enriquecer: Enriquecedor,
    traza: list[str],
    al_fallar: Callable[[], None] | None = None,
) -> AsyncIterator[str]:
    """Traduce los eventos del agente a AG-UI: texto por frase filtrada y aprobación como interrupción."""
    run_id = f"run-{secrets.token_hex(6)}"

    def fallo() -> None:
        if al_fallar is not None:  # el turno no se completó: quien lo pidió puede reintentar
            al_fallar()

    yield _evento(RunStartedEvent(thread_id=thread_id, run_id=run_id))
    mensaje_id = f"m-{secrets.token_hex(6)}"
    seg, bloqueado, abierto = SegmentadorFrases(), False, False

    def frases(lista: list[str]) -> list[str]:
        nonlocal bloqueado
        salida: list[str] = []
        for frase in lista:
            if bloqueado:
                break
            r = filtrar_frase(frase)
            if r.bloqueada:
                bloqueado = True
                traza.append(f"filtro_salida.bloqueo {r.motivo}")
                salida.append(PLANTILLA_RESPALDO + " ")
            else:
                salida.append(r.texto + " ")
        return salida

    interrupciones: list[Interrupt] = []
    herramientas: list[BaseEvent] = []  # se emiten tras el texto, como el modo en proceso

    def llamada(nombre: str, args: str) -> None:
        i = f"t-{secrets.token_hex(6)}"
        herramientas.extend(
            [
                ToolCallStartEvent(tool_call_id=i, tool_call_name=nombre, parent_message_id=mensaje_id),
                ToolCallArgsEvent(tool_call_id=i, delta=args),
                ToolCallEndEvent(tool_call_id=i),
            ]
        )

    try:
        async with asyncio.timeout(TIEMPO_TURNO_S):
            async for ev in cliente.turno(
                user_id=user_id,
                session_id=thread_id,
                mensaje=mensaje,
                aprobaciones=aprobaciones,
                registro=registro,
            ):
                tipo = ev.get("tipo")
                if tipo == "texto":
                    for delta in frases(seg.alimentar(str(ev["delta"]))):
                        if not abierto:
                            abierto = True
                            yield _evento(TextMessageStartEvent(message_id=mensaje_id))
                        yield _evento(TextMessageContentEvent(message_id=mensaje_id, delta=delta))
                elif tipo == "herramienta":
                    llamada(str(ev.get("nombre")), "{}")
                elif tipo == "ficha":
                    llamada("FichaTransaccion", json.dumps({k: str(v) for k, v in dict(ev["datos"]).items()}))
                elif tipo == "aprobacion":
                    for a in ev["aprobaciones"]:
                        texto, expira = enriquecer(f"int-{a['id']}", a["herramienta"], dict(a["args"]))
                        interrupciones.append(
                            Interrupt(
                                id=f"int-{a['id']}",
                                reason="tool_call",
                                message=texto,
                                tool_call_id=a["id"],
                                expires_at=expira,
                                metadata={"herramienta": a["herramienta"], "vigencia_s": 300},
                            )
                        )
                elif tipo == "error":
                    traza.append(f"runtime_error {ev.get('codigo')}")
                    fallo()
                    for cierre in _cerrar_texto(abierto, mensaje_id):
                        yield cierre
                    yield _evento(RunErrorEvent(message=MENSAJE_FALLA, code=str(ev.get("codigo"))))
                    return
    except TimeoutError:
        traza.append("runtime_tiempo_agotado")
        fallo()
        for cierre in _cerrar_texto(abierto, mensaje_id):
            yield cierre
        yield _evento(RunErrorEvent(message=MENSAJE_FALLA, code="tiempo"))
        return
    except Exception as error:  # red, permisos o cuota: el cliente no ve detalles
        traza.append(f"runtime_falla {type(error).__name__}")
        fallo()
        for cierre in _cerrar_texto(abierto, mensaje_id):
            yield cierre
        yield _evento(RunErrorEvent(message=MENSAJE_FALLA, code="runtime"))
        return
    for delta in frases(seg.vaciar()):
        if not abierto:
            abierto = True
            yield _evento(TextMessageStartEvent(message_id=mensaje_id))
        yield _evento(TextMessageContentEvent(message_id=mensaje_id, delta=delta))
    if not abierto and not interrupciones and not herramientas:
        # Sin texto, ficha ni aprobación: el cliente no puede quedar frente a un turno vacío.
        traza.append("runtime_turno_vacio")
        fallo()
        yield _evento(RunErrorEvent(message=MENSAJE_FALLA, code="vacio"))
        return
    if abierto:
        yield _evento(TextMessageEndEvent(message_id=mensaje_id))
    for e in herramientas:
        yield _evento(e)
    resultado = (
        RunFinishedInterruptOutcome(interrupts=interrupciones)
        if interrupciones
        else RunFinishedSuccessOutcome()
    )
    yield _evento(RunFinishedEvent(thread_id=thread_id, run_id=run_id, outcome=resultado))
