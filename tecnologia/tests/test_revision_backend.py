"""Regresiones de la revisión de backend del 30 de septiembre de 2026 (ver REVISION_BACKEND_2026-09-30.md)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from latam_comun.dominio import AccionVerificada, Canal, Confirmacion, Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.banca import vista
from latam_tecnologia.banca.banco import BancoMemoria
from latam_tecnologia.banca.modelos import RegistroConversacion
from latam_tecnologia.canales import chat_web, runtime_cliente
from latam_tecnologia.canales.demo import lectura_sembrada
from latam_tecnologia.herramientas.catalogo import Herramientas, NoDisputable
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion, ejecutar_una_vez
from latam_tecnologia.runtime.agente import AgenteDisputasRuntime, SesionesMemoria
from latam_tecnologia.servicios.almacen import AlmacenMemoria
from pydantic_ai.exceptions import ContentFilterError
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_agent_runtime import RuntimeEnProceso, _abrir, _cliente_web, _correr, sincrona
from test_banca import AHORA, CODIGO, Mundo

PRODUCTO = Producto(product_id="tarjeta-4001", tipo="credit_card", estado="active", moneda="COP")


def _tx(tid: str, ts: datetime, moneda: str = "COP", estado: str = "approved") -> Transaccion:
    return Transaccion(
        transaction_id=tid,
        product_id="tarjeta-4001",
        event_ts=ts,
        monto=Dinero(monto=Decimal("1250.5"), moneda=moneda),
        amount_usd=None,
        tipo="purchase",
        estado=estado,
        comercio="Tienda",
        categoria="retail",
        pais="MX" if moneda == "MXN" else "CO",
        es_extranjera=False,
    )


def _mundo(txs: list[Transaccion]) -> Mundo:
    lectura = LecturaOroFalsa([("demo-1", t) for t in txs], [("demo-1", PRODUCTO)])
    return Mundo(lectura, ["demo-1"])


# Montos, husos y paginación


def test_monto_por_pais() -> None:
    assert vista.monto("128482.28", "COP") == "128.482,28"
    assert vista.monto("128482.28", "ARS") == "128.482,28"
    assert vista.monto("128482.28", "MXN") == "128,482.28"
    assert vista.monto(Decimal("23.5"), "MXN") == "23.50"


def test_movimiento_mexicano_sale_con_punto_decimal_y_hora_de_bogota() -> None:
    # 02:30 UTC del 17 es 21:30 del 16 en Bogotá
    mundo = _mundo([_tx("tx-a", datetime(2026, 6, 17, 2, 30, tzinfo=UTC), "MXN")])
    (m,) = mundo.movimientos(mundo.ingresar())
    assert m["monto"] == "1,250.50" and m["moneda"] == "MXN"
    assert (m["fecha"], m["hora"]) == ("2026-06-16", "21:30")


def test_antes_de_acepta_zona_y_sin_zona_y_no_parte_empates() -> None:
    t0 = datetime(2026, 6, 10, 15, 0, tzinfo=UTC)
    mundo = _mundo([_tx(f"tx-{i}", t0 - timedelta(days=i // 2)) for i in range(6)])  # pares con la misma hora
    h = mundo.ingresar()
    p1 = mundo.c.get("/api/banca/movimientos", headers=h, params={"limite": 1}).json()
    assert len(p1["movimientos"]) == 2  # el empate del borde viaja junto
    vistos = {m["tx_ref"] for m in p1["movimientos"]}
    for corte in (p1["siguiente"], p1["siguiente"].replace("+00:00", "")):  # con y sin zona
        r = mundo.c.get("/api/banca/movimientos", headers=h, params={"limite": 10, "antes_de": corte})
        assert r.status_code == 200
        assert not vistos & {m["tx_ref"] for m in r.json()["movimientos"]}
        assert len(r.json()["movimientos"]) == 4
    assert mundo.c.get("/api/banca/movimientos", headers=h, params={"antes_de": "ayer"}).status_code == 400


def test_historial_mas_alla_de_cincuenta_se_puede_paginar() -> None:
    t0 = datetime(2026, 6, 10, 15, 0, tzinfo=UTC)
    mundo = _mundo([_tx(f"tx-{i}", t0 - timedelta(hours=i)) for i in range(120)])
    h = mundo.ingresar()
    total, corte = 0, None
    while True:
        q: dict[str, Any] = {"limite": 50, **({"antes_de": corte} if corte else {})}
        pagina = mundo.c.get("/api/banca/movimientos", headers=h, params=q).json()
        total += len(pagina["movimientos"])
        corte = pagina["siguiente"]
        if corte is None:
            break
    assert total == 120


# Consola


def test_sesion_de_operador_vence_y_los_alias_no_se_reusan() -> None:
    mundo = _mundo([])
    a = mundo.operador()
    assert mundo.c.get("/api/operador/cola", headers=a).status_code == 200
    mundo.reloj.t += timedelta(hours=9)
    assert mundo.c.get("/api/operador/cola", headers=a).status_code == 401
    b, c = mundo.operador(), mundo.operador()
    ids = []
    for h in (b, c):
        i = mundo.demo.banco.encolar_traspaso(
            "k" + h["X-Operador"], "demo-1", "c-" + h["X-Operador"], "FRUSTRACION", False
        )
        assert mundo.c.post(f"/api/operador/traspasos/{i}/tomar", headers=h).status_code == 200
        ids.append(i)
    tomados = {mundo.demo.banco.traspaso(i).tomado_por for i in ids}  # pyright: ignore[reportOptionalMemberAccess]
    assert tomados == {"Experto 2", "Experto 3"}  # el alias de la sesión vencida no se reutiliza


def test_codigo_de_operador_se_limita_tras_cinco_fallos() -> None:
    mundo = _mundo([])
    for _ in range(5):
        assert mundo.c.post("/api/operador/ingresar", json={"codigo": "mal"}).status_code == 401
    assert mundo.c.post("/api/operador/ingresar", json={"codigo": CODIGO}).status_code == 429
    mundo.reloj.t += timedelta(minutes=2)
    assert mundo.c.post("/api/operador/ingresar", json={"codigo": CODIGO}).status_code == 200


def test_resolver_dos_veces_conserva_la_primera_resolucion() -> None:
    banco = BancoMemoria(lambda: AHORA)
    i = banco.encolar_traspaso("k", "demo-1", "c-1", "CLIENTE_PIDE_PERSONA", False)
    banco.resolver(i, "resuelto", None, "primera")
    otra = banco.resolver(i, "escalado", None, "segunda")
    assert otra is not None and otra.resultado == "resuelto" and otra.nota == "primera"


# Entradas y errores


def test_cuerpos_malos_dan_400_no_500_y_los_grandes_413() -> None:
    mundo = _mundo([])
    c = mundo.c
    assert c.post("/api/sesion", content=b"no es json").status_code == 200  # `{}` toma el primer cliente
    assert c.post("/api/sesion", json={"cliente": "x"}).status_code == 400
    h = mundo.ingresar()
    assert c.post("/api/traspaso", content=b"[1,2]", headers=h).status_code == 200
    cuerpo = {"threadId": "x", "messages": "nada", "resume": "si"}
    assert c.post("/api/agui", json=cuerpo, headers=h).status_code == 403
    grande = c.post("/api/banca/ingresar", content=b"{" + b" " * 70_000 + b"}")
    assert grande.status_code == 413 and grande.json() == {"error": "cuerpo_demasiado_grande"}


def test_error_no_controlado_responde_json_sin_traza(monkeypatch: pytest.MonkeyPatch) -> None:
    mundo = _mundo([])
    h = mundo.ingresar()

    def roto(*a: Any, **k: Any) -> Any:
        raise RuntimeError("fallo en projects/secreto con 4111111111111111")

    monkeypatch.setattr(mundo.demo.lectura, "productos", roto)
    r = TestClient(mundo.app, raise_server_exceptions=False).get("/api/banca/resumen", headers=h)
    assert r.status_code == 500 and r.json() == {"error": "interno"}
    assert "secreto" not in r.text and "Traceback" not in r.text


def test_firestore_caido_responde_503(monkeypatch: pytest.MonkeyPatch) -> None:
    from google.api_core.exceptions import ServiceUnavailable

    mundo = _mundo([])
    h = mundo.ingresar()

    def cae(*a: Any, **k: Any) -> Any:
        raise ServiceUnavailable("firestore")

    monkeypatch.setattr(mundo.demo.banco, "casos_de", cae)
    r = TestClient(mundo.app, raise_server_exceptions=False).get("/api/banca/reclamos", headers=h)
    assert r.status_code == 503 and r.json() == {"error": "servicio_no_disponible"}


def test_mensaje_demasiado_largo_se_rechaza() -> None:
    c = _cliente_web(RuntimeEnProceso())
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    cuerpo: dict[str, Any] = {
        "threadId": r["conversacion"],
        "runId": "r",
        "state": {},
        "tools": [],
        "context": [],
        "forwardedProps": {},
        "messages": [{"id": "u", "role": "user", "content": "x" * 5000}],
    }
    resp = c.post("/api/agui", json=cuerpo, headers={"X-Sesion": r["sesion"]})
    assert resp.status_code == 413


# Agent Runtime


def test_runtime_que_no_responde_corta_con_aviso_claro(monkeypatch: pytest.MonkeyPatch) -> None:
    class Colgado(RuntimeEnProceso):
        async def _dormir(self) -> Any:
            await asyncio.sleep(30)
            yield {"tipo": "fin"}

        def turno(self, **kw: Any) -> Any:
            return self._dormir()

    monkeypatch.setattr(runtime_cliente, "TIEMPO_TURNO_S", 0.05)
    c = _cliente_web(Colgado())
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    evs = _correr(c, {"X-Sesion": r["sesion"]}, r["conversacion"], "hola")
    assert evs[-1]["type"] == "RUN_ERROR" and evs[-1]["code"] == "tiempo"
    assert "intenta de nuevo" in evs[-1]["message"].lower()


def test_sin_agente_no_se_abre_la_sesion() -> None:
    class SinAgente(RuntimeEnProceso):
        def crear_sesion(self, **kw: Any) -> None:
            raise runtime_cliente.AgenteNoDisponible

    c = _cliente_web(SinAgente())
    assert c.post("/api/sesion", json={"cliente": 0}).status_code == 503
    assert c.post("/api/banca/ingresar", json={"indice": 0}).status_code == 503


def test_aprobacion_se_puede_reintentar_si_el_turno_falla() -> None:
    rt = RuntimeEnProceso()
    c = _cliente_web(rt)
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    h, conv = {"X-Sesion": r["sesion"]}, r["conversacion"]
    e1 = _correr(c, h, conv, "No reconozco un cargo")
    iid = e1[-1]["outcome"]["interrupts"][0]["id"]
    resume = [{"interruptId": iid, "status": "resolved", "payload": {"approved": True}}]
    buena = rt.turno

    def cae(**kw: Any) -> Any:
        raise RuntimeError("red")

    rt.turno = cae  # type: ignore[method-assign]
    assert _correr(c, h, conv, None, resume)[-1]["type"] == "RUN_ERROR"
    rt.turno = buena  # type: ignore[method-assign]
    e3 = _correr(c, h, conv, None, resume)  # la aprobación sigue pendiente: la sesión no queda atascada
    assert e3[-1]["outcome"]["type"] == "success" and rt.banco.llamadas == 1


def _modelo_que_falla(veces: int) -> tuple[FunctionModel, list[int]]:
    llamadas: list[int] = []

    async def flujo(mensajes: list[ModelMessage], info: AgentInfo) -> Any:
        llamadas.append(1)
        if len(llamadas) <= veces:
            raise ContentFilterError(
                "Unexpected tool call: undeclared function default_api.listar_transacciones"
            )
        yield "Hola, ¿en qué le ayudo?"

    return FunctionModel(stream_function=flujo), llamadas


def _agente_con(modelo: FunctionModel) -> tuple[AgenteDisputasRuntime, SesionesMemoria]:
    sesiones = SesionesMemoria()
    _abrir(sesiones)
    lectura, _ = lectura_sembrada()
    agente = AgenteDisputasRuntime(
        "p", modelo=modelo, lectura=lectura, banco=BancoMemoria(), sesiones=sesiones, reloj=lambda: AHORA
    )
    agente.set_up()
    return agente, sesiones


@sincrona
async def test_error_del_modelo_se_reintenta_una_vez() -> None:
    modelo, llamadas = _modelo_que_falla(1)
    agente, _ = _agente_con(modelo)
    evs = [e async for e in agente.async_stream_query(user_id="u-1", session_id="c-1", message="hola")]
    assert evs[-1]["tipo"] == "fin" and len(llamadas) == 2


@sincrona
async def test_error_persistente_del_modelo_da_error_limpio_sin_historial_a_medias() -> None:
    modelo, llamadas = _modelo_que_falla(9)
    agente, sesiones = _agente_con(modelo)
    evs = [e async for e in agente.async_stream_query(user_id="u-1", session_id="c-1", message="hola")]
    assert evs == [{"tipo": "error", "codigo": "modelo"}] and len(llamadas) == 2
    assert sesiones.eventos("c-1", "u-1") == []


# Banco, efectos y herramientas


def test_contador_de_turnos_avanza_aunque_la_transcripcion_este_topada() -> None:
    banco = BancoMemoria(lambda: AHORA)
    banco.registrar_conversacion(RegistroConversacion(id="c-1", cliente_id="demo-1", creada_en=AHORA))
    for i in range(75):
        banco.agregar_transcripcion("c-1", "cliente", f"t{i}")
    c = banco.conversacion("c-1")
    assert c is not None and len(c.transcripcion) == 60 and c.turnos_guardados == 75


def test_transcripcion_del_chat_no_se_duplica_pasado_el_limite() -> None:
    mundo = _mundo([])
    h = mundo.ingresar()
    conv = mundo.demo.sesiones[h["X-Sesion"]].conversacion_id
    historial: list[dict[str, str]] = []
    for i in range(70):
        historial.append({"id": f"u{i}", "role": "user", "content": f"pregunta {i}"})
        cuerpo: dict[str, Any] = {
            "threadId": conv,
            "runId": "r",
            "state": {},
            "tools": [],
            "context": [],
            "forwardedProps": {},
            "messages": historial,
        }
        with mundo.c.stream("POST", "/api/agui", json=cuerpo, headers=h) as r:
            r.read()
        historial.append({"id": f"a{i}", "role": "assistant", "content": f"respuesta {i}"})
    registro = mundo.demo.banco.conversacion(conv)
    assert registro is not None
    textos = [t.texto for t in registro.transcripcion]
    assert len(textos) == len(set(textos)) == 60 and textos[-1] == "pregunta 69"


def test_efecto_que_falla_no_deja_la_llave_atascada() -> None:
    almacen = AlmacenMemoria()
    almacen.crear_conversacion(
        Conversacion(id="c-1", cliente_ref="demo-1", canal_actual=Canal.CHAT, estado="inicio")
    )
    intentos: list[int] = []

    def ejecutor(llave: str) -> AccionVerificada:
        intentos.append(1)
        if len(intentos) == 1:
            raise ConnectionError("firestore caído")
        return AccionVerificada(accion="escalar", exito=True, resultado_releido="tr-1", hora=AHORA)

    def correr() -> tuple[AccionVerificada, bool]:
        return ejecutar_una_vez(
            almacen,
            conversacion_id="c-1",
            numero_transicion=100,
            tipo="escalar",
            recurso="c-1",
            confirmacion=None,
            ejecutor=ejecutor,
        )

    with pytest.raises(ConnectionError):
        correr()
    accion, ejecutada = correr()
    assert ejecutada and accion.resultado_releido == "tr-1"
    assert correr()[1] is False


def test_no_se_abre_disputa_de_un_movimiento_rechazado() -> None:
    lectura = LecturaOroFalsa([("demo-1", _tx("tx-r", AHORA, estado="declined"))], [("demo-1", PRODUCTO)])
    almacen = AlmacenMemoria()
    almacen.crear_conversacion(
        Conversacion(id="c-1", cliente_ref="demo-1", canal_actual=Canal.CHAT, estado="inicio")
    )
    banco = BancoMemoria(lambda: AHORA)
    herramientas = Herramientas(lectura, banco, almacen, reloj=lambda: AHORA)
    sesion = SesionAutenticada(
        id_sesion="s", cliente_id="demo-1", nivel=NivelAcr.ACCION, expira=AHORA + timedelta(minutes=5)
    )
    conf = Confirmacion(accion="abrir_disputa", canal=Canal.CHAT, evidencia="boton", nonce="n")
    with pytest.raises(NoDisputable):
        herramientas.abrir_disputa(sesion, "c-1", "tx-r", "no_la_reconozco", conf)
    assert banco.llamadas == 0


def test_vencimientos_no_crecen_sin_limite() -> None:
    v = chat_web.Vencimientos(reloj=lambda: AHORA)
    for i in range(chat_web.MAX_VIVAS + 500):
        v.emitir("s", f"int-{i}")
    assert len(v._vivas) <= chat_web.MAX_VIVAS + 1  # pyright: ignore[reportPrivateUsage]


def test_turno_vacio_del_agente_se_informa_como_falla() -> None:
    class Mudo(RuntimeEnProceso):
        async def _nada(self) -> Any:
            if False:
                yield {}

        def turno(self, **kw: Any) -> Any:
            return self._nada()

    c = _cliente_web(Mudo())
    r = c.post("/api/sesion", json={"cliente": 0}).json()
    evs = _correr(c, {"X-Sesion": r["sesion"]}, r["conversacion"], "hola")
    assert evs[-1]["type"] == "RUN_ERROR" and evs[-1]["code"] == "vacio"


def test_tarjeta_en_espanol_y_montos_de_mexico() -> None:
    from latam_tecnologia.banca.vista import es_tarjeta, monto

    assert es_tarjeta("Tarjeta Crédito") and es_tarjeta("Tarjeta Débito") and es_tarjeta("credit_card")
    assert not es_tarjeta("Cuenta Ahorro") and not es_tarjeta(None)
    assert monto("1250", "USD", "MX") == "1,250.00"
    assert monto("1250", "COP", "CO") == "1.250,00"


def test_handlers_con_io_bloqueante_no_corren_en_el_bucle() -> None:
    """Con una instancia, un handler async que consulta BigQuery o Firestore congela a todos los demás."""
    import inspect

    from fastapi.routing import APIRoute

    app = _cliente_web(RuntimeEnProceso()).app
    sincronos = {
        "/api/sesion",
        "/api/traspaso",
        "/api/banca/ingresar",
        "/api/banca/resumen",
        "/api/banca/movimientos/{tx_ref}/reclamar",
        "/api/banca/reclamos",
        "/api/banca/tarjetas/{producto_ref}/bloqueo",
        "/api/banca/conversaciones/{conversacion}/mensajes",
        "/api/operador/ingresar",
        "/api/operador/traspasos/{identificador}/mensaje",
        "/api/operador/traspasos/{identificador}/resolver",
    }
    todas: list[Any] = []
    for r in app.routes:  # FastAPI reciente guarda los routers incluidos como `_IncludedRouter`
        todas += list(getattr(getattr(r, "original_router", None), "routes", [])) or [r]
    rutas = [r for r in todas if isinstance(r, APIRoute) and r.path in sincronos]
    assert {r.path for r in rutas} == sincronos
    assert [r.path for r in rutas if inspect.iscoroutinefunction(r.endpoint)] == []
