"""Herramientas conectadas al agente PydanticAI. Las de efecto piden aprobación explícita del cliente."""

from __future__ import annotations

from dataclasses import dataclass

from latam_comun.dominio import Canal, Confirmacion, SesionAutenticada
from pydantic import TypeAdapter
from pydantic_ai import Agent, DeferredToolRequests, RunContext
from pydantic_ai.models import Model

from latam_tecnologia.herramientas.catalogo import Herramientas
from latam_tecnologia.herramientas.puertos import CasoAbierto, Producto, Transaccion

INSTRUCCIONES = (
    "Eres el asistente de disputas de un banco. Consulta con las herramientas, nunca inventes cifras "
    "y pide aprobación del cliente antes de cualquier acción."
)


AVISO_ESCALAR = " Siguiente paso obligatorio: llamar a escalar con motivo {motivo}."


@dataclass
class ContextoAgente:
    """El cliente sale de la sesión; el modelo no puede nombrarlo ni cambiarlo."""

    herramientas: Herramientas
    sesion: SesionAutenticada
    conversacion_id: str
    canal: Canal


def _confirmacion(ctx: RunContext[ContextoAgente], accion: str) -> Confirmacion:
    return Confirmacion(
        accion=accion, canal=ctx.deps.canal, evidencia="boton", nonce=ctx.tool_call_id or "sin_id"
    )


def crear_agente_disputas(modelo: Model | str) -> Agent[ContextoAgente, str | DeferredToolRequests]:
    agente: Agent[ContextoAgente, str | DeferredToolRequests] = Agent(
        modelo,
        deps_type=ContextoAgente,
        output_type=[str, DeferredToolRequests],
        instructions=INSTRUCCIONES,
    )

    @agente.tool
    def listar_transacciones(ctx: RunContext[ContextoAgente], limite: int = 10) -> str:  # pyright: ignore[reportUnusedFunction]
        """Últimas transacciones del cliente de la sesión."""
        hecho = ctx.deps.herramientas.transacciones_recientes(ctx.deps.sesion, limite)
        return TypeAdapter(tuple[Transaccion, ...]).dump_json(hecho.valor).decode()

    @agente.tool
    def consultar_transaccion(ctx: RunContext[ContextoAgente], transaction_id: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Una transacción del cliente de la sesión; vacío si no existe o no es suya."""
        hecho = ctx.deps.herramientas.transaccion(ctx.deps.sesion, transaction_id)
        return "null" if hecho.valor is None else hecho.valor.model_dump_json()

    @agente.tool
    def estado_productos(ctx: RunContext[ContextoAgente]) -> str:  # pyright: ignore[reportUnusedFunction]
        """Productos del cliente y si están bloqueados."""
        hecho = ctx.deps.herramientas.estado_productos(ctx.deps.sesion)
        return TypeAdapter(tuple[Producto, ...]).dump_json(hecho.valor).decode()

    @agente.tool
    def casos_abiertos(ctx: RunContext[ContextoAgente]) -> str:  # pyright: ignore[reportUnusedFunction]
        """Casos de disputa ya abiertos del cliente. Consultar antes de abrir uno, para no duplicarlo."""
        hecho = ctx.deps.herramientas.casos_abiertos(ctx.deps.sesion)
        return TypeAdapter(tuple[CasoAbierto, ...]).dump_json(hecho.valor).decode()

    @agente.tool(requires_approval=True)
    def abrir_disputa(  # pyright: ignore[reportUnusedFunction]
        ctx: RunContext[ContextoAgente], transaction_id: str, motivo: str
    ) -> str:
        """Abre la disputa de una transacción del cliente. Idempotente."""
        d = ctx.deps
        transaccion = d.herramientas.transaccion(d.sesion, transaction_id).valor
        provisional = transaccion is not None and d.herramientas.credito_provisional(transaccion)
        accion, _ = d.herramientas.abrir_disputa(
            d.sesion,
            d.conversacion_id,
            transaction_id,
            motivo,
            _confirmacion(ctx, "abrir_disputa"),
            credito_provisional=provisional,
        )
        tras = None if transaccion is None else d.herramientas.escalar_tras_radicar(transaccion)
        if tras is None:
            return accion.resultado_releido
        return accion.resultado_releido + AVISO_ESCALAR.format(motivo=tras)

    @agente.tool(requires_approval=True)
    def bloquear_tarjeta(ctx: RunContext[ContextoAgente], product_id: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Bloquea una tarjeta del cliente. Idempotente."""
        d = ctx.deps
        accion, _ = d.herramientas.bloquear_tarjeta(
            d.sesion, d.conversacion_id, product_id, _confirmacion(ctx, "bloquear_tarjeta")
        )
        return accion.resultado_releido

    @agente.tool(requires_approval=True)
    def escalar(ctx: RunContext[ContextoAgente], motivo: str, urgente: bool = False) -> str:  # pyright: ignore[reportUnusedFunction]
        """Pasa el caso a un experto humano. Idempotente."""
        d = ctx.deps
        accion, _ = d.herramientas.escalar(d.sesion, d.conversacion_id, motivo, urgente)
        return accion.resultado_releido

    return agente
