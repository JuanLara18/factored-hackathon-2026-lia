"""Ejecutor: corre un escenario contra el agente de disputas de Tecnología y devuelve la traza verificada.

Evalúa por la misma superficie que un cliente (R-IA-69): turnos de texto hacia `crear_agente_disputas`, y
las aprobaciones de las acciones las da el simulador, no el arnés. Estado del banco y herramientas se
leen solo para verificar.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from latam_comun.dominio import Canal
from latam_tecnologia.canales.geap import VARIABLE_PROVEEDOR, crear_modelo_geap
from latam_tecnologia.herramientas.agente import ContextoAgente, crear_agente_disputas
from latam_tecnologia.motor.caso import MotorCaso
from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolDenied
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import Model

from latam_ia.evaluacion.agente_referencia import crear_modelo_referencia
from latam_ia.evaluacion.esquema import Escenario
from latam_ia.evaluacion.mundo import AHORA, CONVERSACION_ID, MundoVivo, materializar
from latam_ia.evaluacion.simulador import (
    ContextoSimulador,
    Simulador,
    TurnoCliente,
    crear_simulador,
    verificar_fidelidad,
)
from latam_ia.evaluacion.traza import (
    EFECTOS_CON_CONFIRMACION,
    Aprobacion,
    LlamadaHerramienta,
    Traza,
    Turno,
)
from latam_ia.evaluacion.verificadores import (
    EMAIL,
    TARJETA,
    ContextoVerificacion,
    Hallazgo,
    es_de_seguridad,
    verificar,
)
from latam_ia.modelos import VARIABLE_LLAVE, crear_modelo
from latam_ia.registro.esquema import Modelo, Proveedor

MAX_PASOS = 60
SPEC_AGENTE = Modelo(
    proveedor=Proveedor.GEMINI_API,
    familia="google",
    id="gemini-2.5-flash-lite",
    temperatura=0.0,
    max_salida=400,
)
Estado = Literal["pasa", "falla", "falla_simulador"]


@dataclass
class Corrida:
    escenario_id: str
    indice: int
    estado: Estado
    inseguro: bool
    hallazgos: list[Hallazgo]
    fallas_simulador: list[str]
    reintentos_simulador: int
    modo_simulador: str
    traza: Traza = field(repr=False)


def elegir_modelo_agente(escenario: Escenario, entorno: Mapping[str, str] | None = None) -> tuple[Model, str]:
    """GEAP si se pide (`LATAM_MODELO_PROVEEDOR=geap`), Gemini con llave, o la política de referencia."""
    env = os.environ if entorno is None else entorno
    if env.get(VARIABLE_PROVEEDOR, "").lower() == "geap":
        return crear_modelo_geap(env)
    if env.get(VARIABLE_LLAVE):
        return crear_modelo(SPEC_AGENTE, env), f"gemini:{SPEC_AGENTE.id}"
    return crear_modelo_referencia(escenario.idioma), "referencia-guionada"


def _texto_confirmacion(escenario: Escenario, mv: MundoVivo, llamadas: list[ToolCallPart]) -> str:
    """Lectura de vuelta de la interfaz desde la base (V2), no desde el modelo."""
    partes: list[str] = []
    for c in llamadas:
        args = c.args_as_dict()
        if c.tool_name == "abrir_disputa":
            tx = next(
                (
                    t
                    for t in mv.mundo.transacciones
                    if t.cliente == mv.cliente and t.id == args.get("transaction_id")
                ),
                None,
            )
            que = f"{tx.monto} {tx.moneda} en {tx.comercio}" if tx else "la transacción indicada"
            partes.append(f"disputar {que}" if escenario.idioma == "es" else f"contestar {que}")
        elif c.tool_name == "bloquear_tarjeta":
            partes.append("bloquear su tarjeta" if escenario.idioma == "es" else "bloquear o seu cartão")
    unidas = " y ".join(partes)
    if escenario.idioma == "es":
        return f"Voy a {unidas}. ¿Confirma?"
    return f"Vou {unidas}. Você confirma?"


def _llamadas(historial: list[ModelMessage], aprobaciones: dict[str, Aprobacion]) -> list[LlamadaHerramienta]:
    """Llamadas de herramienta de la conversación con su retorno y su aprobación, en orden."""
    retornos: dict[str, ToolReturnPart] = {}
    for m in historial:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, ToolReturnPart):
                    retornos[p.tool_call_id] = p
    salida: list[LlamadaHerramienta] = []
    turnos_cliente = 0
    for m in historial:
        if isinstance(m, ModelRequest):
            turnos_cliente += sum(isinstance(p, UserPromptPart) for p in m.parts)
        else:
            for p in m.parts:
                if not isinstance(p, ToolCallPart):
                    continue
                r = retornos.get(p.tool_call_id)
                salida.append(
                    LlamadaHerramienta(
                        nombre=p.tool_name,
                        args=dict(p.args_as_dict()),
                        retorno="" if r is None else str(r.content),
                        tool_call_id=p.tool_call_id,
                        ejecutada=r is not None and r.outcome == "success",
                        aprobacion=aprobaciones.get(p.tool_call_id, "ninguna"),
                        turno_cliente=turnos_cliente,
                    )
                )
    return salida


def _correr(
    escenario: Escenario, mv: MundoVivo, modelo: Model, sim: Simulador
) -> tuple[Traza, list[tuple[str | None, str]]]:
    traza = Traza()
    pares: list[tuple[str | None, str]] = []
    MotorCaso(mv.almacen, mv.herramientas, reloj=lambda: AHORA).abrir(CONVERSACION_ID, mv.sesion, Canal.CHAT)
    agente = crear_agente_disputas(modelo)
    deps = ContextoAgente(mv.herramientas, mv.sesion, CONVERSACION_ID, Canal.CHAT, escenario.registro)
    historial: list[ModelMessage] = []
    aprobaciones: dict[str, Aprobacion] = {}
    ultimo: str | None = None
    n_cliente = 0
    pendiente: DeferredToolRequests | None = None
    en_cola: TurnoCliente | None = None

    def registrar(turno: TurnoCliente) -> None:
        nonlocal n_cliente
        n_cliente += 1
        traza.turnos.append(Turno("cliente", turno.texto))
        pares.append((ultimo, turno.texto))

    for _ in range(MAX_PASOS):
        try:
            if pendiente is None:
                turno = en_cola or sim.siguiente(ContextoSimulador(ultimo, False, n_cliente))
                if turno is None:
                    break
                if en_cola is None:
                    registrar(turno)
                en_cola = None
                res = agente.run_sync(turno.texto, message_history=historial, deps=deps)
            else:
                pedidas = [c for c in pendiente.approvals if c.tool_name in EFECTOS_CON_CONFIRMACION]
                confirma = False
                if pedidas:
                    ultimo = _texto_confirmacion(escenario, mv, pedidas)
                    traza.turnos.append(Turno("interfaz", ultimo))
                    respuesta = sim.siguiente(ContextoSimulador(ultimo, True, n_cliente))
                    if respuesta is not None:
                        registrar(respuesta)
                        confirma = respuesta.intencion == "confirmar"
                        if respuesta.intencion == "hablar":
                            en_cola = respuesta
                resultados = DeferredToolResults()
                for c in pendiente.approvals:
                    if c.tool_name in EFECTOS_CON_CONFIRMACION and not confirma:
                        resultados.approvals[c.tool_call_id] = ToolDenied()
                        aprobaciones[c.tool_call_id] = "rechazada"
                    else:
                        resultados.approvals[c.tool_call_id] = True
                        aprobaciones[c.tool_call_id] = (
                            "explicita" if c.tool_name in EFECTOS_CON_CONFIRMACION else "implicita"
                        )
                res = agente.run_sync(
                    None, message_history=historial, deferred_tool_results=resultados, deps=deps
                )
        except Exception as error:
            traza.errores.append(f"{type(error).__name__}: {error}")
            break
        historial = res.all_messages()
        if isinstance(res.output, DeferredToolRequests):
            pendiente = res.output
        else:
            pendiente = None
            ultimo = res.output
            traza.turnos.append(Turno("agente", res.output))
    traza.herramientas = _llamadas(historial, aprobaciones)
    traza.efectos_banco = list(mv.banco.bitacora)
    traza.estado_final = mv.banco.estado_final()
    return traza, pares


def _pii_del_cliente(traza: Traza) -> tuple[str, ...]:
    hallado: list[str] = []
    for texto in traza.texto_de("cliente"):
        hallado += [m.group(0) for m in EMAIL.finditer(texto)]
        for m in TARJETA.finditer(texto):
            hallado += [m.group(0), "".join(c for c in m.group(0) if c.isdigit())]
    return tuple(hallado)


def ejecutar_corrida(
    escenario: Escenario,
    indice: int = 0,
    *,
    entorno: Mapping[str, str] | None = None,
    modelo_agente: Model | None = None,
    modelo_simulador: Model | None = None,
) -> Corrida:
    """Una corrida con el mundo en memoria recién materializado. Reintenta una vez si falla el simulador."""
    reintentos = 0
    while True:
        mv = materializar(escenario)
        modelo = modelo_agente or elegir_modelo_agente(escenario, entorno)[0]
        sim = crear_simulador(
            escenario.guion, escenario.idioma, escenario.registro, entorno, modelo_simulador
        )
        traza, pares = _correr(escenario, mv, modelo, sim)
        # El cliente LLM no sigue un guion turno a turno: se juzgan los resultados, no la fidelidad al guion.
        fallas = [] if sim.modo == "llm_cliente" else verificar_fidelidad(escenario.guion, pares)
        if not fallas or reintentos >= 1:
            break
        reintentos += 1
    ctx = ContextoVerificacion(mv.cliente, mv.canarios(), escenario.esperado, _pii_del_cliente(traza))
    hallazgos = verificar(traza, ctx)
    estado: Estado = "falla_simulador" if fallas else ("falla" if hallazgos else "pasa")
    return Corrida(
        escenario_id=escenario.id,
        indice=indice,
        estado=estado,
        inseguro=any(es_de_seguridad(h) for h in hallazgos),
        hallazgos=hallazgos,
        fallas_simulador=fallas,
        reintentos_simulador=reintentos,
        modo_simulador=sim.modo,
        traza=traza,
    )


__all__ = ["Corrida", "ejecutar_corrida", "elegir_modelo_agente"]
