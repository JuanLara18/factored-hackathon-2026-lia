"""Herramientas conectadas al agente PydanticAI. Las de efecto piden aprobación explícita del cliente."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from latam_comun.dominio import Canal, Confirmacion, SesionAutenticada
from pydantic import TypeAdapter
from pydantic_ai import Agent, DeferredToolRequests, RunContext
from pydantic_ai.models import Model

from latam_tecnologia.herramientas.catalogo import (
    LIMITE_DEFECTO,
    EscalacionRequerida,
    Herramientas,
    NoDisputable,
)
from latam_tecnologia.herramientas.instrucciones import instrucciones_disputas
from latam_tecnologia.herramientas.puertos import CasoAbierto, Producto, Transaccion

SIN_PRODUCTO = "No se abrió la disputa: el producto no se pudo verificar."
AVISO_ESCALAR = " Siguiente paso obligatorio: llamar a escalar con motivo {motivo}."


@dataclass
class ContextoAgente:
    """El cliente sale de la sesión; el modelo no puede nombrarlo ni cambiarlo."""

    herramientas: Herramientas
    sesion: SesionAutenticada
    conversacion_id: str
    canal: Canal
    registro: str = "usted"
    contexto: str = ""  # lo que el servidor fija sobre la conversación (p. ej. el movimiento reclamado)


def _confirmacion(ctx: RunContext[ContextoAgente], accion: str) -> Confirmacion:
    return Confirmacion(
        accion=accion, canal=ctx.deps.canal, evidencia="boton", nonce=ctx.tool_call_id or "sin_id"
    )


def _instrucciones(ctx: RunContext[ContextoAgente]) -> str:
    base = instrucciones_disputas(ctx.deps.registro)
    return f"{base}\n\n{ctx.deps.contexto}" if ctx.deps.contexto else base


def _con_ruta(ctx: RunContext[ContextoAgente], valor: tuple[Transaccion, ...]) -> str:
    """JSON de las transacciones; las que `policy/v1` manda escalar (ESC-03) llevan `ruta_obligada`."""
    d = ctx.deps
    filas: list[dict[str, Any]] = json.loads(TypeAdapter(tuple[Transaccion, ...]).dump_json(valor))
    for fila, ruta in zip(filas, d.herramientas.rutas_obligadas(d.sesion, valor), strict=True):
        if ruta is not None:
            fila["ruta_obligada"] = f"no abrir disputa: llamar a escalar con motivo {ruta}"
    return json.dumps(filas, ensure_ascii=False)


def crear_agente_disputas(modelo: Model | str) -> Agent[ContextoAgente, str | DeferredToolRequests]:
    agente: Agent[ContextoAgente, str | DeferredToolRequests] = Agent(
        modelo,
        deps_type=ContextoAgente,
        output_type=[str, DeferredToolRequests],
        instructions=_instrucciones,
    )

    @agente.tool
    def listar_transacciones(  # pyright: ignore[reportUnusedFunction]
        ctx: RunContext[ContextoAgente],
        limite: int = LIMITE_DEFECTO,
        comercio: str | None = None,
        monto: float | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> str:
        """Transacciones del cliente de la sesión, de la más reciente a la más antigua (hasta 200).

        Para hallar el cobro que la persona describe, filtre por `comercio` (parte del nombre), `monto`
        (en la moneda de la cuenta) o fechas `desde` y `hasta` (AAAA-MM-DD).
        """
        try:
            fechas = [None if f is None else date.fromisoformat(f) for f in (desde, hasta)]
        except ValueError:
            return "Fecha inválida: use el formato AAAA-MM-DD."
        hecho = ctx.deps.herramientas.transacciones_recientes(
            ctx.deps.sesion,
            limite,
            comercio=comercio,
            monto=None if monto is None else Decimal(str(monto)),
            desde=fechas[0],
            hasta=fechas[1],
        )
        return _con_ruta(ctx, hecho.valor)

    @agente.tool
    def consultar_transaccion(ctx: RunContext[ContextoAgente], transaction_id: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Una transacción del cliente de la sesión; vacío si no existe o no es suya."""
        hecho = ctx.deps.herramientas.transaccion(ctx.deps.sesion, transaction_id)
        return "null" if hecho.valor is None else _con_ruta(ctx, (hecho.valor,))[1:-1]

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
        try:
            accion, _ = d.herramientas.abrir_disputa(
                d.sesion,
                d.conversacion_id,
                transaction_id,
                motivo,
                _confirmacion(ctx, "abrir_disputa"),
                credito_provisional=provisional,
            )
        except EscalacionRequerida as esc:
            return SIN_PRODUCTO + AVISO_ESCALAR.format(motivo=esc.motivo)
        except NoDisputable as no:
            return f"No se abrió la disputa: el movimiento está {no} y por su estado no admite reclamo."
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
        """Pasa el caso a un experto humano. Idempotente.

        `motivo` es un código: transferencia_en_curso, fraude_en_curso, suplantacion (urgentes, solo si el
        cliente cuenta un hecho así), cliente_pide_persona, transaccion_no_disputable, producto_no_encontrado,
        monto_sobre_umbral u otro. La prioridad la fija la política según el motivo; `urgente` se ignora.
        """
        d = ctx.deps
        accion, _ = d.herramientas.escalar(d.sesion, d.conversacion_id, motivo, urgente)
        return accion.resultado_releido

    return agente
