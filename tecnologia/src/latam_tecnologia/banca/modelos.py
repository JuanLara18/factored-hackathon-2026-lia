"""Registros que guarda el banco: casos, traspasos, conversaciones y mensajes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from latam_comun.dominio import PaqueteTraspaso
from pydantic import BaseModel, ConfigDict, Field


class _Registro(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evento(_Registro):
    fecha: datetime
    evento: str


class Caso(_Registro):
    caso_ref: str
    cliente_id: str
    transaccion_id: str
    monto: Decimal
    moneda: str
    motivo: str
    estado: Literal["abierto", "cerrado"] = "abierto"
    abierto_en: datetime
    credito_provisional: bool = False
    plazo: str | None = None
    historial: list[Evento] = Field(default_factory=list[Evento])


class Mensaje(_Registro):
    id: str
    autor: Literal["cliente", "asistente", "persona"]
    texto: str
    en: datetime


class RegistroConversacion(_Registro):
    id: str
    cliente_id: str
    registro: str = "usted"
    pais: str | None = None
    transaccion_id: str | None = None
    solicitud: str | None = None
    creada_en: datetime
    transcripcion: list[Mensaje] = Field(default_factory=list[Mensaje])  # enmascarada


class Traspaso(_Registro):
    id_traspaso: str
    cliente_id: str
    conversacion_id: str
    prioridad: Literal["P1", "P2", "P3", "P4"]
    estado: Literal["en_cola", "tomado", "resuelto"] = "en_cola"
    creado_en: datetime
    tomado_por: str | None = None
    resultado: str | None = None
    etiqueta_correccion: dict[str, Any] | str | None = None
    nota: str | None = None
    paquete: PaqueteTraspaso
