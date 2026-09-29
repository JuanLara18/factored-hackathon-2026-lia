from latam_tecnologia import observabilidad
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


def test_sin_proyecto_no_hace_nada() -> None:
    assert observabilidad.configurar({}) is None


def test_spans_con_trabajador_y_sin_texto() -> None:
    exportador = InMemorySpanExporter()
    proveedor = observabilidad.crear_proveedor("disputas", "0.1.0", exportador, sincrono=True)
    observabilidad.instrumentar(proveedor)
    try:
        agente = Agent(TestModel())

        @agente.tool_plain
        def eco() -> str:  # pyright: ignore[reportUnusedFunction]
            return "resultado con 4111 1111 1111 1111"

        agente.run_sync("mensaje secreto con cedula 123456")
    finally:
        Agent.instrument_all(False)
    spans = exportador.get_finished_spans()
    nombres = {s.name for s in spans}
    assert any(n.startswith("invoke_agent") or n == "agent run" for n in nombres)
    assert any(n.startswith("chat") for n in nombres)
    assert any("eco" in n for n in nombres)
    for s in spans:
        assert s.attributes is not None
        assert s.attributes["latam.trabajador.id"] == "disputas"
        assert s.attributes["latam.trabajador.version"] == "0.1.0"
        assert "secreto" not in str(dict(s.attributes)) and "4111" not in str(dict(s.attributes))
