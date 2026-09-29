"""Spike S4: retoma de un caso entre canales sin repetir una acción (2.6.4 y 2.6.5 de la definición).

El núcleo es puro: calcula la llave de idempotencia del efecto y decide si ejecutar o devolver lo ya hecho.
El almacén (memoria en pruebas unitarias, Postgres en integración) solo guarda y garantiza unicidad.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from latam_comun.dominio import (
    AccionVerificada,
    Canal,
    Confirmacion,
    NivelAcr,
    SesionAutenticada,
)
from pydantic import BaseModel, ConfigDict


class _Inmutable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RetomaNegada(Exception):
    """La sesión del canal nuevo no corresponde al cliente del caso o no alcanza el nivel exigido."""


class EfectoIncierto(Exception):
    """Un intento anterior no terminó: hay que reconsultar antes de afirmar nada (R-TEC-53)."""


class Conversacion(_Inmutable):
    id: str
    cliente_ref: str
    canal_actual: Canal
    estado: str


class ResumenRetoma(_Inmutable):
    """Se renderiza desde el estado tipado: qué se hizo (como hechos) y en qué canal sigue el caso."""

    conversacion_id: str
    canal_anterior: Canal
    canal_nuevo: Canal
    acciones_hechas: tuple[AccionVerificada, ...]
    estado: str


class Almacen(Protocol):
    def crear_conversacion(self, conversacion: Conversacion) -> None: ...

    def cargar(self, conversacion_id: str) -> Conversacion | None: ...

    def cambiar_canal(self, conversacion_id: str, canal: Canal) -> None: ...

    def reservar_efecto(self, llave: str, conversacion_id: str, numero: int, tipo: str) -> bool:
        """Verdadero solo para quien crea la reserva; la unicidad de la llave la garantiza el almacén."""
        ...

    def completar_efecto(self, llave: str, accion: AccionVerificada) -> None: ...

    def estado_efecto(self, llave: str) -> tuple[str, AccionVerificada | None] | None: ...

    def acciones_hechas(self, conversacion_id: str) -> tuple[AccionVerificada, ...]: ...


def llave_efecto(conversacion_id: str, numero_transicion: int, tipo: str, recurso: str) -> str:
    """SHA-256 de (conversación, transición, tipo de efecto, recurso); igual en cualquier canal."""
    base = "\x1f".join((conversacion_id, str(numero_transicion), tipo, recurso))
    return hashlib.sha256(base.encode()).hexdigest()


def ejecutar_una_vez(
    almacen: Almacen,
    *,
    conversacion_id: str,
    numero_transicion: int,
    tipo: str,
    recurso: str,
    confirmacion: Confirmacion,
    ejecutor: Callable[[str], AccionVerificada],
) -> tuple[AccionVerificada, bool]:
    """Ejecuta el efecto como máximo una vez por llave; devuelve la acción y si esta llamada la ejecutó."""
    if confirmacion.accion != tipo:
        raise ValueError("la confirmación no corresponde a la acción")
    llave = llave_efecto(conversacion_id, numero_transicion, tipo, recurso)
    if almacen.reservar_efecto(llave, conversacion_id, numero_transicion, tipo):
        accion = ejecutor(llave)
        almacen.completar_efecto(llave, accion)
        return accion, True
    registro = almacen.estado_efecto(llave)
    if registro is not None and registro[0] == "hecho" and registro[1] is not None:
        return registro[1], False
    raise EfectoIncierto(llave)


def retomar(
    almacen: Almacen, conversacion_id: str, sesion: SesionAutenticada, canal: Canal, ahora: datetime
) -> ResumenRetoma:
    """El canal nuevo exige su propia sesión `acr2` del mismo cliente; lo hecho no se repite."""
    conversacion = almacen.cargar(conversacion_id)
    if conversacion is None:
        raise KeyError(conversacion_id)
    if sesion.cliente_id != conversacion.cliente_ref or not sesion.permite(NivelAcr.ACCION, ahora):
        raise RetomaNegada(conversacion_id)
    almacen.cambiar_canal(conversacion_id, canal)
    return ResumenRetoma(
        conversacion_id=conversacion_id,
        canal_anterior=conversacion.canal_actual,
        canal_nuevo=canal,
        acciones_hechas=almacen.acciones_hechas(conversacion_id),
        estado=conversacion.estado,
    )
