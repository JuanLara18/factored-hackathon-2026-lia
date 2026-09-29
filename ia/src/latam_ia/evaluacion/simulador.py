"""Simulador de cliente de texto (2.8.3).

Guionado por defecto: dice lo que el guion manda, sin modelo. Con `GEMINI_API_KEY` puede conducirlo un modelo
que solo ve marcadores `{{hecho}}`: el arnés pone los valores localmente después (D-15). En ambos casos
`verificar_fidelidad` decide si el simulador respetó el guion; una violación es `falla_simulador`.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model

from latam_ia.evaluacion.agente_referencia import norm
from latam_ia.evaluacion.esquema import Guion, HechoOculto, Intencion
from latam_ia.modelos import VARIABLE_LLAVE, crear_modelo
from latam_ia.registro.esquema import Modelo, Proveedor

MARCADOR = re.compile(r"\{\{([a-z_][a-z0-9_]*)\}\}")
SPEC_SIMULADOR = Modelo(
    proveedor=Proveedor.GEMINI_API,
    familia="google",
    id="gemini-2.5-flash-lite",
    temperatura=0.7,
    max_salida=200,
)


@dataclass(frozen=True)
class TurnoCliente:
    texto: str
    intencion: Intencion


@dataclass(frozen=True)
class ContextoSimulador:
    ultimo_agente: str | None
    confirmacion_pendiente: bool
    turnos_cliente: int


class Simulador(Protocol):
    modo: str

    def siguiente(self, ctx: ContextoSimulador) -> TurnoCliente | None: ...


def sustituir(texto: str, hechos: Mapping[str, HechoOculto]) -> str:
    """Pone los valores del caso en los marcadores; uno desconocido queda a la vista del verificador."""
    return MARCADOR.sub(lambda m: hechos[m.group(1)].valor if m.group(1) in hechos else m.group(0), texto)


class SimuladorGuionado:
    modo = "guionado"

    def __init__(self, guion: Guion) -> None:
        self._guion = guion
        self._i = 0

    def siguiente(self, ctx: ContextoSimulador) -> TurnoCliente | None:
        if self._i >= len(self._guion.turnos) or ctx.turnos_cliente >= self._guion.max_turnos:
            return None
        t = self._guion.turnos[self._i]
        self._i += 1
        return TurnoCliente(sustituir(t.decir, self._guion.hechos), t.intencion)


class SalidaSimulador(BaseModel):
    texto: str
    intencion: Intencion = "hablar"
    termina: bool = False


class SimuladorLLM:
    modo = "llm"

    def __init__(self, guion: Guion, idioma: str, registro: str, modelo: Model) -> None:
        self._guion = guion
        hechos = "\n".join(
            f"- {{{{{k}}}}}: escríbelo tal cual, con las llaves; "
            + (f"solo si te preguntan por: {', '.join(h.si_pregunta)}" if h.si_pregunta else "puedes decirlo")
            for k, h in guion.hechos.items()
        )
        ejemplo = "\n".join(f"- ({t.intencion}) {re.sub(r'\d', '#', t.decir)}" for t in guion.turnos)
        instrucciones = (
            f"Eres un cliente de un banco que escribe por chat en {idioma} con trato de {registro}. "
            f"Objetivo: {guion.objetivo}\nHechos que conoces, siempre como marcador:\n{hechos}\n"
            f"Forma general de tus turnos:\n{ejemplo}\n"
            "Nunca inventes montos, fechas, comercios ni datos que no estén como marcador. Usa la intención "
            "'confirmar' solo si el asistente te pide confirmar una acción y quieres, 'rechazar' si no. "
            "Marca termina=true cuando tu objetivo esté cumplido."
        )
        self._agente: Agent[None, SalidaSimulador] = Agent(
            modelo, output_type=SalidaSimulador, instructions=instrucciones
        )
        self._historial: list[ModelMessage] = []

    def siguiente(self, ctx: ContextoSimulador) -> TurnoCliente | None:
        if ctx.turnos_cliente >= self._guion.max_turnos:
            return None
        entrada = ctx.ultimo_agente or "(la conversación empieza: escribe tu primer mensaje)"
        if ctx.confirmacion_pendiente:
            entrada += "\n[El asistente espera que confirmes o rechaces la acción.]"
        r = self._agente.run_sync(entrada, message_history=self._historial)
        self._historial = r.all_messages()
        if r.output.termina and not r.output.texto.strip():
            return None
        return TurnoCliente(sustituir(r.output.texto, self._guion.hechos), r.output.intencion)


def crear_simulador(
    guion: Guion,
    idioma: str,
    registro: str,
    entorno: Mapping[str, str] | None = None,
    modelo: Model | None = None,
) -> Simulador:
    """LLM solo con `GEMINI_API_KEY` (o un modelo inyectado); guionado si no. Nunca hay red sin llave."""
    env = os.environ if entorno is None else entorno
    if modelo is None:
        if not env.get(VARIABLE_LLAVE):
            return SimuladorGuionado(guion)
        modelo = crear_modelo(SPEC_SIMULADOR, env)
    return SimuladorLLM(guion, idioma, registro, modelo)


def verificar_fidelidad(guion: Guion, turnos: list[tuple[str | None, str]]) -> list[str]:
    """Fallas del simulador sobre pares (último mensaje del agente, turno del cliente).

    Revela un hecho que solo debía decir si se lo preguntaban; deja un marcador sin resolver; pasa del
    máximo de turnos del guion.
    """
    fallas: list[str] = []
    if len(turnos) > guion.max_turnos:
        fallas.append(f"más turnos ({len(turnos)}) que el máximo del guion ({guion.max_turnos})")
    for i, (agente, texto) in enumerate(turnos, start=1):
        if MARCADOR.search(texto):
            fallas.append(f"turno {i}: marcador sin resolver")
        previo = norm(agente or "")
        for nombre, h in guion.hechos.items():
            if h.si_pregunta and h.valor in texto and not any(norm(k) in previo for k in h.si_pregunta):
                fallas.append(f"turno {i}: revela {nombre} sin que se lo pregunten")
    return fallas
