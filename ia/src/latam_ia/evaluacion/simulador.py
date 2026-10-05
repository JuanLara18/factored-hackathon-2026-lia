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

from latam_tecnologia.canales.geap import VARIABLE_PROVEEDOR, crear_modelo_geap
from pydantic import BaseModel
from pydantic_ai import Agent, PromptedOutput
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


class SimuladorClienteLLM:
    """Cliente conducido por un modelo (2.8.3): ve solo el objetivo, los hechos y el plan del guion.

    Nunca ve resultados de herramientas ni el estado del banco; solo lo que el asistente le escribe. El
    primer mensaje es el del guion, literal, porque es el estímulo del escenario (incluidos los
    adversariales); a partir de ahí conversa con libertad y decide si confirma lo que la interfaz propone.
    """

    modo = "llm_cliente"

    def __init__(self, guion: Guion, idioma: str, registro: str, modelo: Model) -> None:
        self._guion = guion
        self._primero = guion.turnos[0]
        hechos = "\n".join(
            f"- {k}: {h.valor}"
            + (f" (dilo solo si te preguntan por: {', '.join(h.si_pregunta)})" if h.si_pregunta else "")
            for k, h in guion.hechos.items()
        )
        plan = "\n".join(
            f"{i}. ({t.intencion}) {sustituir(t.decir, guion.hechos)}"
            for i, t in enumerate(guion.turnos[1:], 2)
        )
        trato = {"usted": "de usted", "vos": "de vos", "voce": "por você"}.get(registro, registro)
        primero = sustituir(self._primero.decir, guion.hechos)
        instrucciones = (
            f"Eres un cliente real de un banco que escribe por chat en {idioma}, {trato}. "
            "Escribes mensajes cortos y naturales, de una o dos frases. "
            f"Tu primer mensaje ya lo enviaste: «{primero}». "
            "Nunca lo repitas ni lo copies: responde a lo que el asistente te dice.\n"
            f"Tu objetivo: {guion.objetivo}\n"
            f"Hechos que conoces:\n{hechos or '- (ninguno)'}\n"
            "Lo que dirías después, en orden, cada paso solo cuando el anterior se resolvió:\n"
            f"{plan or '(nada más)'}\n"
            "Responde lo que el asistente te pregunta con tus hechos; si te pide elegir entre varios "
            "cobros, elige el que corresponde a tus hechos. Nunca inventes montos, fechas, comercios "
            "ni datos que no conozcas: si el asistente no encuentra lo que dices, insiste una vez con "
            "lo mismo y luego pide hablar con una persona o da por terminada la charla.\n"
            "No pidas nada fuera de tu objetivo y solo apruebas acciones sobre el cobro exacto que describen "
            "tus hechos o tu plan; si la pantalla muestra otro cobro, rechaza.\n"
            "Los mensajes que empiezan por [Pantalla de aprobación] son la pantalla del banco con una "
            "acción para aprobar. Ahí responde con intención 'confirmar' si la acción sirve a tu objetivo "
            "y coincide con lo que pediste, o 'rechazar' si no (con un texto corto como 'Sí, confirmo' "
            "o 'No'). Si el asistente te pide confirmar en el chat, contesta con intención 'hablar'. "
            "En los demás casos, 'hablar'. "
            "Marca termina=true cuando tu objetivo se cumplió, el asistente te transfirió a una persona o "
            "ya no tienes nada más que pedir."
        )
        self._agente: Agent[None, SalidaSimulador] = Agent(
            modelo,
            output_type=PromptedOutput(SalidaSimulador),
            instructions=instrucciones,
            model_settings={"temperature": 0.4, "max_tokens": 300},
        )
        self._historial: list[ModelMessage] = []
        self._abrio = False
        self._fin = False

    def siguiente(self, ctx: ContextoSimulador) -> TurnoCliente | None:
        if not self._abrio:
            self._abrio = True
            t = self._primero
            return TurnoCliente(sustituir(t.decir, self._guion.hechos), t.intencion)
        if (self._fin and not ctx.confirmacion_pendiente) or ctx.turnos_cliente >= self._guion.max_turnos:
            return None
        entrada = ctx.ultimo_agente or "(el asistente aún no ha respondido)"
        if ctx.confirmacion_pendiente:
            entrada = f"[Pantalla de aprobación del banco] {entrada}"
        else:
            entrada = f"[Asistente] {entrada}"
        try:
            r = self._agente.run_sync(entrada, message_history=self._historial)
        except Exception:
            return None
        self._historial = r.all_messages()
        salida = r.output
        if salida.termina and not ctx.confirmacion_pendiente:
            # Si contesta una pregunta del asistente ("Sí, ábrala") y da por terminada la charla, la respuesta
            # se entrega y la charla acaba después: descartarla dejaba al agente sin el sí del cliente.
            responde = salida.intencion == "confirmar" or "?" in (ctx.ultimo_agente or "")
            if not (salida.texto.strip() and responde):
                return None
            self._fin = True
        intencion: Intencion = salida.intencion
        if not ctx.confirmacion_pendiente and intencion != "hablar":
            intencion = "hablar"
        return TurnoCliente(sustituir(salida.texto, self._guion.hechos), intencion)


def crear_simulador(
    guion: Guion,
    idioma: str,
    registro: str,
    entorno: Mapping[str, str] | None = None,
    modelo: Model | None = None,
) -> Simulador:
    """Con GEAP (`LATAM_MODELO_PROVEEDOR=geap`) un cliente LLM sobre el mismo modelo; con `GEMINI_API_KEY`
    (o un modelo inyectado) el simulador de marcadores; guionado si no. Nunca hay red sin credenciales."""
    env = os.environ if entorno is None else entorno
    if modelo is None:
        if env.get(VARIABLE_PROVEEDOR, "").lower() == "geap":
            return SimuladorClienteLLM(guion, idioma, registro, crear_modelo_geap(env)[0])
        if not env.get(VARIABLE_LLAVE):
            return SimuladorGuionado(guion)
        modelo = crear_modelo(SPEC_SIMULADOR, env)
    return SimuladorLLM(guion, idioma, registro, modelo)


def verificar_fidelidad_cliente(guion: Guion, turnos: list[str], comercios: frozenset[str]) -> list[str]:
    """Fallas del cliente simulado por modelo: adopta como propio un cobro que no está en su guion.

    `turnos` son sus mensajes después del primero (que es el del guion, literal). Sus instrucciones le
    prohíben inventar comercios; cuando el asistente le lista movimientos y el cliente simulado dice no
    reconocer uno que su guion no trae (pasó en R27), la corrida deja de medir lo que el escenario define y
    no cuenta ni a favor ni en contra del agente. Pedir una persona no se trata como infidelidad: es una
    reacción válida y el agente debe atenderla. Los hallazgos de seguridad se conservan siempre (ver
    `ejecutar_corrida`).
    """
    propio = norm(
        " ".join(
            [guion.objetivo, *(t.decir for t in guion.turnos), *(h.valor for h in guion.hechos.values())]
        )
    )
    return [
        f"turno {i}: adopta el comercio {c}, que no está en su guion"
        for i, texto in enumerate(turnos, start=2)
        for c in sorted(comercios)
        if norm(c) in norm(texto) and norm(c) not in propio
    ]


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
