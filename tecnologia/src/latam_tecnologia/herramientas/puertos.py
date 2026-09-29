"""Puertos de la capa de herramientas: lectura del oro operacional y servicios del banco simulado."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from latam_comun.dominio import Dinero
from pydantic import BaseModel, ConfigDict


class _Inmutable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Transaccion(_Inmutable):
    """Fila de `oro_operacional_transacciones_recientes` sin `customer_id` (el cliente sale de la sesión)."""

    transaction_id: str
    product_id: str
    event_ts: datetime
    monto: Dinero
    amount_usd: Decimal | None
    tipo: str | None
    estado: str | None
    comercio: str | None
    categoria: str | None
    pais: str | None
    es_extranjera: bool


class Producto(_Inmutable):
    """Fila de `oro_operacional_estado_productos` sin `customer_id`."""

    product_id: str
    tipo: str | None
    estado: str | None
    moneda: str | None


class LecturaOro(Protocol):
    """Solo lectura. Toda consulta exige `cliente_id`; lo ajeno no existe para quien pregunta."""

    def transacciones_recientes(self, cliente_id: str, limite: int) -> tuple[Transaccion, ...]: ...

    def transaccion(self, cliente_id: str, transaction_id: str) -> Transaccion | None: ...

    def productos(self, cliente_id: str) -> tuple[Producto, ...]: ...

    def ficha_transaccion(self, cliente_id: str, transaction_id: str) -> dict[str, Any] | None:
        """Tabla aún no publicada por Datos: `None` si falta la tabla o la fila."""
        ...


class ServiciosBanco(Protocol):
    """Efectos sobre el banco simulado; cada método recibe `Idempotency-Key` y es idempotente por ella."""

    def abrir_caso(
        self,
        llave: str,
        cliente_id: str,
        transaccion_id: str,
        monto: Dinero,
        motivo: str,
        credito_provisional: bool,
    ) -> str: ...

    def bloquear_tarjeta(self, llave: str, cliente_id: str, producto_id: str) -> str: ...

    def encolar_traspaso(
        self, llave: str, cliente_id: str, conversacion_id: str, motivo: str, urgente: bool
    ) -> str: ...
