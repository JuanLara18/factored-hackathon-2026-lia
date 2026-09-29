"""Trazas OpenTelemetry a Cloud Trace (D-32, fase 1).

Sin `LATAM_GCP_PROJECT` no hace nada. PydanticAI emite un span por turno (`invoke_agent`), por llamada al
modelo (`chat <modelo>`) y por herramienta (`execute_tool`); aquí se instrumenta con `include_content=False`
(ni mensajes, ni argumentos, ni resultados) y se marca cada span con el id y la versión del trabajador del
registro. Solo viajan nombres, duraciones, conteo de tokens y esos dos atributos: nada de PII.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings

VARIABLE_PROYECTO = "LATAM_GCP_PROJECT"
ATRIBUTO_ID = "latam.trabajador.id"
ATRIBUTO_VERSION = "latam.trabajador.version"
TRABAJADOR_CHAT = "disputas"
VERSION_SIN_REGISTRO = "0.0.0"


class MarcaTrabajador(SpanProcessor):
    """Añade id y versión del trabajador a todo span que empieza."""

    def __init__(self, trabajador_id: str, version: str) -> None:
        self._atributos = {ATRIBUTO_ID: trabajador_id, ATRIBUTO_VERSION: version}

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        span.set_attributes(self._atributos)

    def on_end(self, span: ReadableSpan) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def version_del_registro(trabajador_id: str) -> str:
    """Versión del trabajador en `ia/agentes/trabajadores`; sin el paquete de IA, un valor neutro."""
    try:
        from latam_ia.registro.cargador import cargar_registro

        return cargar_registro().trabajadores[trabajador_id].version
    except (ImportError, KeyError):
        return VERSION_SIN_REGISTRO


def crear_proveedor(
    trabajador_id: str, version: str, exportador: SpanExporter, *, sincrono: bool = False
) -> TracerProvider:
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    proveedor = TracerProvider(resource=Resource.create({"service.name": "latam-bank-chat"}))
    proveedor.add_span_processor(MarcaTrabajador(trabajador_id, version))
    proveedor.add_span_processor(
        SimpleSpanProcessor(exportador) if sincrono else BatchSpanProcessor(exportador)
    )
    return proveedor


def instrumentar(proveedor: TracerProvider) -> None:
    Agent.instrument_all(InstrumentationSettings(tracer_provider=proveedor, include_content=False))


_activo: dict[str, Any] = {}


def configurar(env: Mapping[str, str], trabajador_id: str = TRABAJADOR_CHAT) -> TracerProvider | None:
    """Activa el envío a Cloud Trace si hay proyecto; idempotente. Devuelve el proveedor o `None`."""
    proyecto = env.get(VARIABLE_PROYECTO)
    if not proyecto:
        return None
    if "proveedor" in _activo:
        return _activo["proveedor"]  # type: ignore[no-any-return]
    from opentelemetry.exporter.cloud_trace import (  # pyright: ignore[reportMissingTypeStubs]
        CloudTraceSpanExporter,  # pyright: ignore[reportDeprecated]
    )

    exportador = CloudTraceSpanExporter(project_id=proyecto)  # pyright: ignore[reportDeprecated]
    proveedor = crear_proveedor(trabajador_id, version_del_registro(trabajador_id), exportador)
    instrumentar(proveedor)
    _activo["proveedor"] = proveedor
    return proveedor
