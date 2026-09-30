"""Agente propio de Agent Runtime y modo Agent Runtime del chat web, sin red (D-32 fase 2)."""

from __future__ import annotations

import asyncio
import functools
import json
from collections.abc import AsyncIterator, Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from latam_tecnologia.banca.banco import BancoMemoria
from latam_tecnologia.canales.chat_web import crear_app
from latam_tecnologia.canales.demo import Demo, lectura_sembrada
from latam_tecnologia.canales.runtime_cliente import ClienteAgentRuntime
from latam_tecnologia.runtime.agente import AgenteDisputasRuntime, SesionesMemoria
from pydantic_ai import ModelMessage, ModelRequest, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel

AHORA = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)


def sincrona(f: Callable[[], Coroutine[Any, Any, None]]) -> Callable[[], None]:
    """No hay plugin async en el proyecto: cada prueba corre su bucle."""

    @functools.wraps(f)
    def envoltura() -> None:
        asyncio.run(f())

    return envoltura


def _guion() -> FunctionModel:
    """Lista, pide abrir la disputa de la primera compra y cierra con lo que devolvió la herramienta."""

    async def flujo(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | DeltaToolCalls]:
        retornos = [
            p
            for m in messages
            if isinstance(m, ModelRequest)
            for p in m.parts
            if isinstance(p, ToolReturnPart)
        ]
        por_nombre = {r.tool_name: r for r in retornos}
        if "abrir_disputa" in por_nombre:
            r = por_nombre["abrir_disputa"]
            yield (
                "No se abrio ninguna disputa. "
                if r.outcome == "denied"
                else f"Quedo el reclamo {r.content}. "
            )
            return
        if "listar_transacciones" in por_nombre:
            tx = json.loads(str(por_nombre["listar_transacciones"].content))[0]
            args = {"transaction_id": tx["transaction_id"], "motivo": "no_la_reconozco"}
            yield {0: DeltaToolCall(name="abrir_disputa", json_args=json.dumps(args), tool_call_id="disputa")}
            return
        yield {0: DeltaToolCall(name="listar_transacciones", json_args='{"limite": 1}', tool_call_id="lista")}

    return FunctionModel(stream_function=flujo)


def _agente(sesiones: SesionesMemoria) -> tuple[AgenteDisputasRuntime, Any]:
    lectura, _ = lectura_sembrada()
    agente = AgenteDisputasRuntime(
        "p", modelo=_guion(), lectura=lectura, banco=BancoMemoria(), sesiones=sesiones, reloj=lambda: AHORA
    )
    agente.set_up()
    return agente, agente._banco  # pyright: ignore[reportPrivateUsage]


def _abrir(
    sesiones: SesionesMemoria, cliente: str = "demo-1", minutos: int = 30, sid: str = "c-1", uid: str = "u-1"
) -> None:
    sesiones.crear(
        sid,
        uid,
        {
            "cliente_id": cliente,
            "nivel": "acr2",
            "expira": (AHORA + timedelta(minutes=minutos)).isoformat(),
            "conversacion_id": sid,
        },
    )


async def _turno(agente: AgenteDisputasRuntime, **kw: Any) -> list[dict[str, Any]]:
    return [e async for e in agente.async_stream_query(user_id="u-1", session_id="c-1", **kw)]


@sincrona
async def test_disputa_completa_con_aprobacion_del_canal() -> None:
    sesiones = SesionesMemoria()
    _abrir(sesiones)
    agente, banco = _agente(sesiones)
    e1 = await _turno(agente, message="No reconozco un cargo")
    assert e1[-1]["tipo"] == "aprobacion" and banco.llamadas == 0  # nada se ejecuta sin aprobar
    pedida = e1[-1]["aprobaciones"][0]
    assert pedida["herramienta"] == "abrir_disputa" and pedida["args"]["transaction_id"] == "tx-1-1"
    e2 = await _turno(agente, aprobaciones={pedida["id"]: True})
    assert e2[-1]["tipo"] == "fin" and "caso-" in "".join(e.get("delta", "") for e in e2)
    assert banco.llamadas == 1 and [c.transaction_id for c in banco.casos_abiertos("demo-1")] == ["tx-1-1"]
    assert len(sesiones.eventos("c-1", "u-1")) == 2  # el historial vive en Sessions


@sincrona
async def test_rechazo_no_ejecuta() -> None:
    sesiones = SesionesMemoria()
    _abrir(sesiones)
    agente, banco = _agente(sesiones)
    e1 = await _turno(agente, message="No reconozco un cargo")
    e2 = await _turno(agente, aprobaciones={e1[-1]["aprobaciones"][0]["id"]: False})
    assert "No se abrio" in "".join(e.get("delta", "") for e in e2) and banco.llamadas == 0


@sincrona
async def test_el_cliente_sale_de_la_sesion_y_no_de_los_argumentos() -> None:
    sesiones = SesionesMemoria()
    _abrir(sesiones, cliente="demo-2")
    agente, _ = _agente(sesiones)
    e1 = await _turno(agente, message="No reconozco un cargo de demo-1")
    assert e1[-1]["aprobaciones"][0]["args"]["transaction_id"] == "tx-2-1"  # solo ve lo de demo-2
    with pytest.raises(TypeError):
        await _turno(agente, message="hola", cliente_id="demo-1")  # pyright: ignore[reportCallIssue]


@sincrona
async def test_errores_de_sesion_y_de_aprobacion() -> None:
    sesiones = SesionesMemoria()
    _abrir(sesiones)
    _abrir(sesiones, minutos=-1, sid="c-2")
    agente, banco = _agente(sesiones)
    assert (await _turno(agente, message="hola"))[-1]["tipo"] != "error"
    desconocida = [e async for e in agente.async_stream_query(user_id="u-1", session_id="nada", message="x")]
    vencida = [e async for e in agente.async_stream_query(user_id="u-1", session_id="c-2", message="x")]
    assert desconocida[-1]["codigo"] == "sesion_desconocida" and vencida[-1]["codigo"] == "sesion_vencida"
    # con una aprobación pendiente, ni un texto ni un id inventado la resuelven
    assert (await _turno(agente, message="sí, confirmo"))[-1]["codigo"] == "aprobacion_pendiente"
    assert (await _turno(agente, aprobaciones={"otra": True}))[-1]["codigo"] == "aprobacion_invalida"
    assert banco.llamadas == 0


def test_query_y_stream_query_sincronos_y_operaciones() -> None:
    sesiones = SesionesMemoria()
    _abrir(sesiones)
    agente, _ = _agente(sesiones)
    r = agente.query(user_id="u-1", session_id="c-1", message="No reconozco un cargo")
    assert r["tipo"] == "aprobacion"
    ev = list(
        agente.stream_query(user_id="u-1", session_id="c-1", aprobaciones={r["aprobaciones"][0]["id"]: True})
    )
    assert ev[-1] == {"tipo": "fin"}
    assert agente.register_operations()["stream"] == ["stream_query"]


def test_la_clase_se_serializa_por_valor_antes_de_set_up() -> None:
    cloudpickle = pytest.importorskip("cloudpickle")
    import latam_tecnologia.runtime.agente as modulo

    cloudpickle.register_pickle_by_value(modulo)
    try:
        copia = cloudpickle.loads(cloudpickle.dumps(AgenteDisputasRuntime("p", raiz_paquete="/x")))
    finally:
        cloudpickle.unregister_pickle_by_value(modulo)
    assert copia.proyecto == "p" and copia.raiz_paquete == "/x"


# Chat web reenviando al agente


class RuntimeEnProceso:
    """Cliente falso: el mismo agente, en proceso, con Sessions en memoria."""

    def __init__(self) -> None:
        self.sesiones = SesionesMemoria()
        self.agente, self.banco = _agente(self.sesiones)
        self.estados: list[dict[str, str]] = []

    def crear_sesion(self, *, user_id: str, session_id: str, estado: dict[str, str]) -> None:
        self.estados.append(estado)
        self.sesiones.crear(session_id, user_id, estado)

    def turno(self, **kw: Any) -> AsyncIterator[dict[str, Any]]:
        return self.agente.async_stream_query(
            user_id=kw["user_id"],
            session_id=kw["session_id"],
            message=kw["mensaje"],
            aprobaciones=kw["aprobaciones"],
            registro=kw["registro"],
        )


def _cliente_web(runtime: Any) -> TestClient:
    lectura, ids = lectura_sembrada()
    demo = Demo(lectura=lectura, clientes=ids, origen="memoria", reloj=lambda: AHORA)
    return TestClient(crear_app(demo=demo, runtime=runtime))


def _correr(
    c: TestClient, h: dict[str, str], conv: str, mensaje: str | None, resume: Any = None
) -> list[dict[str, Any]]:
    cuerpo: dict[str, Any] = {
        "threadId": conv,
        "runId": "r",
        "state": {},
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }
    cuerpo["messages"] = [{"id": "u", "role": "user", "content": mensaje}] if mensaje else []
    if resume:
        cuerpo["resume"] = resume
    with c.stream("POST", "/api/agui", json=cuerpo, headers=h) as r:
        assert r.status_code == 200, r.read()
        return [json.loads(ln[6:]) for ln in r.iter_lines() if ln.startswith("data: ")]


def test_chat_web_reenvia_al_runtime_con_aprobacion() -> None:
    rt = RuntimeEnProceso()
    c = _cliente_web(rt)
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    h, conv = {"X-Sesion": r["sesion"]}, r["conversacion"]
    assert rt.estados[0]["cliente_id"] == "demo-1" and rt.estados[0]["nivel"] == "acr2"
    e1 = _correr(c, h, conv, "No reconozco un cargo")
    i = e1[-1]["outcome"]["interrupts"][0]
    assert e1[-1]["outcome"]["type"] == "interrupt" and i["metadata"]["vigencia_s"] == 300
    assert "abrir un reclamo sobre el cargo de Tienda Uno, por 1.234,56 COP" in i["message"]
    assert rt.banco.llamadas == 0
    e2 = _correr(
        c, h, conv, None, [{"interruptId": i["id"], "status": "resolved", "payload": {"approved": True}}]
    )
    assert e2[-1]["outcome"]["type"] == "success" and rt.banco.llamadas == 1
    assert "caso-" in "".join(e["delta"] for e in e2 if e["type"] == "TEXT_MESSAGE_CONTENT")
    # la confirmación es de un solo uso también en este modo
    malo = c.post(
        "/api/agui",
        json={
            "threadId": conv,
            "runId": "r",
            "state": {},
            "messages": [],
            "tools": [],
            "context": [],
            "forwardedProps": {},
            "resume": [{"interruptId": i["id"], "status": "resolved", "payload": {"approved": True}}],
        },
        headers=h,
    )
    assert malo.status_code == 409 and rt.banco.llamadas == 1


def test_chat_web_falla_del_runtime_no_filtra_detalles() -> None:
    class Roto(RuntimeEnProceso):
        def turno(self, **kw: Any) -> AsyncIterator[dict[str, Any]]:
            raise RuntimeError("permiso denegado en projects/secreto")

    c = _cliente_web(Roto())
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    evs = _correr(c, {"X-Sesion": r["sesion"]}, r["conversacion"], "hola")
    assert evs[-1]["type"] == "RUN_ERROR" and "secreto" not in json.dumps(evs)


def test_recurso_del_entorno_activa_el_modo_y_se_valida() -> None:
    entorno = {"LATAM_AGENT_RUNTIME_RECURSO": "projects/p/locations/us-central1/reasoningEngines/123"}
    lectura, ids = lectura_sembrada()
    demo = Demo(lectura=lectura, clientes=ids, origen="memoria")
    app = crear_app(demo=demo, entorno=entorno)
    assert TestClient(app).get("/api/estado").json()["modelo"] == "agent_runtime"
    with pytest.raises(ValueError):
        ClienteAgentRuntime("no-es-un-recurso")


def test_desplegar_dry_run_arma_y_valida(capsys: pytest.CaptureFixture[str]) -> None:
    import importlib.util
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[1] / "infra" / "agent_runtime" / "desplegar.py"
    spec = importlib.util.spec_from_file_location("desplegar_agente", ruta)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    assert modulo.main(["--dry-run"]) == 0
    salida = capsys.readouterr().out
    assert (
        '"min_instances": 0' in salida
        and "LATAM_TRABAJADOR_VERSION" in salida
        and "dry-run correcto" in salida
    )


def _guion_ficha() -> FunctionModel:
    """Consulta una transacción y responde con texto."""

    async def flujo(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | DeltaToolCalls]:
        hay_retorno = any(
            isinstance(p, ToolReturnPart) for m in messages if isinstance(m, ModelRequest) for p in m.parts
        )
        if hay_retorno:
            yield "Este es el cargo. "
            return
        args = json.dumps({"transaction_id": "tx-1-1"})
        yield {0: DeltaToolCall(name="consultar_transaccion", json_args=args, tool_call_id="c1")}

    return FunctionModel(stream_function=flujo)


class RuntimeConFicha(RuntimeEnProceso):
    def __init__(self) -> None:
        self.sesiones = SesionesMemoria()
        lectura, _ = lectura_sembrada()
        self.agente = AgenteDisputasRuntime(
            "p",
            modelo=_guion_ficha(),
            lectura=lectura,
            banco=BancoMemoria(),
            sesiones=self.sesiones,
            reloj=lambda: AHORA,
        )
        self.agente.set_up()
        self.estados = []


@sincrona
async def test_agente_emite_herramienta_y_ficha_enmascarada() -> None:
    rt = RuntimeConFicha()
    _abrir(rt.sesiones)
    eventos = await _turno(rt.agente, message="Mi ultimo cargo")
    assert {"tipo": "herramienta", "nombre": "consultar_transaccion"} in eventos
    ficha = next(e["datos"] for e in eventos if e["tipo"] == "ficha")
    assert set(ficha) == {"comercio", "monto", "moneda", "fecha", "estado", "tarjeta_final"}
    assert (
        ficha["comercio"] == "Tienda Uno"
        and ficha["monto"] == "1.234,56"
        and len(ficha["tarjeta_final"]) == 4
    )
    assert "tx-1-1" not in json.dumps(eventos)  # sin ids en los eventos de herramienta ni en la ficha


def test_chat_web_dibuja_la_ficha_como_en_proceso() -> None:
    c = _cliente_web(RuntimeConFicha())
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    evs = _correr(c, {"X-Sesion": r["sesion"]}, r["conversacion"], "Mi ultimo cargo")
    tipos = [e["type"] for e in evs]
    assert tipos[-1] == "RUN_FINISHED" and tipos.index("TEXT_MESSAGE_END") < tipos.index("TOOL_CALL_START")
    nombres = [e["toolCallName"] for e in evs if e["type"] == "TOOL_CALL_START"]
    assert nombres == ["consultar_transaccion", "FichaTransaccion"]
    ids = [e["toolCallId"] for e in evs if e["type"] == "TOOL_CALL_START"]
    args = [e for e in evs if e["type"] == "TOOL_CALL_ARGS"]
    assert json.loads(args[0]["delta"]) == {} and args[0]["toolCallId"] == ids[0]
    ficha = json.loads(args[1]["delta"])
    assert ficha["comercio"] == "Tienda Uno" and ficha["tarjeta_final"].isdigit()
    assert tipos.count("TOOL_CALL_END") == 2


def _cargar_desplegar() -> Any:
    import importlib.util
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[1] / "infra" / "agent_runtime" / "desplegar.py"
    spec = importlib.util.spec_from_file_location("desplegar_agente", ruta)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_desplegar_dry_run_con_recurso_actualiza(capsys: pytest.CaptureFixture[str]) -> None:
    modulo = _cargar_desplegar()
    recurso = "projects/p/locations/us-central1/reasoningEngines/123"
    assert modulo.main(["--dry-run", "--recurso", recurso]) == 0
    assert f"actualizar {recurso}" in capsys.readouterr().out
    assert modulo.main(["--dry-run", "--recurso", "malo"]) == 1
    assert modulo.main(["--dry-run"]) == 0
    assert "crear un recurso nuevo" in capsys.readouterr().out


def test_desplegar_usa_update_con_recurso_y_create_sin_el(monkeypatch: pytest.MonkeyPatch) -> None:
    modulo = _cargar_desplegar()
    llamadas: list[tuple[str, dict[str, Any]]] = []

    class Api:
        def _r(self, nombre: str, kw: dict[str, Any]) -> Any:
            llamadas.append((nombre, kw))
            return type("R", (), {"api_resource": type("A", (), {"name": "projects/p/x"})()})()

        def create(self, **kw: Any) -> Any:
            return self._r("create", kw)

        def update(self, **kw: Any) -> Any:
            return self._r("update", kw)

    cliente = type("C", (), {"agent_engines": Api()})()
    monkeypatch.setattr(modulo, "_cliente", lambda p, u: (cliente, object()))
    config = {"env_vars": {"LATAM_GCP_PROJECT": "p"}}
    recurso = "projects/p/locations/l/reasoningEngines/9"
    modulo.desplegar(config, "p", "l", recurso)
    modulo.desplegar(config, "p", "l")
    assert [n for n, _ in llamadas] == ["update", "create"]
    assert llamadas[0][1]["name"] == recurso and "name" not in llamadas[1][1]
