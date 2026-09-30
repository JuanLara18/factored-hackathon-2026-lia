"""API de la banca y de la consola (D-33): alcance, sin datos personales, idempotencia y paquete 2.5.2."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from latam_comun.dominio import Canal, Confirmacion, Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.banca.banco import BancoMemoria, crear_banco
from latam_tecnologia.canales.chat_web import crear_app
from latam_tecnologia.canales.demo import Demo, lectura_sembrada
from latam_tecnologia.canales.modelo import crear_modelo
from latam_tecnologia.herramientas.catalogo import Herramientas
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa, ServiciosBancoFalsos
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion
from latam_tecnologia.servicios.almacen import AlmacenMemoria
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel

CODIGO = "codigo-de-prueba"
AHORA = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)
PROHIBIDOS = (
    "demo-1",
    "demo-2",
    "demo-3",
    "tarjeta-400",
    "tx-1-",
    "tx-2-",
    "tx-3-",
    "customer",
    "cliente_id",
)
CAMPOS_2_5_2 = {
    "id_traspaso",
    "hilo_id",
    "caso_id",
    "prioridad",
    "motivo",
    "cola_destino",
    "idioma",
    "registro",
    "pais_cuenta",
    "canal_actual",
    "canales_usados",
    "identidad",
    "solicitud",
    "interpretacion",
    "hechos_verificados",
    "acciones_realizadas",
    "acciones_no_realizadas",
    "conflictos",
    "preguntas_abiertas",
    "plazos_en_curso",
    "compromisos_comunicados",
    "evidencia",
    "transcripcion",
}


class Reloj:
    def __init__(self) -> None:
        self.t = AHORA

    def __call__(self) -> datetime:
        return self.t


class Mundo:
    def __init__(self, lectura: LecturaOroFalsa | None = None, ids: list[str] | None = None) -> None:
        if lectura is None:
            lectura, ids = lectura_sembrada()
        assert ids is not None
        self.reloj = Reloj()
        self.demo = Demo(lectura=lectura, clientes=ids, origen="memoria", reloj=self.reloj)
        self.instrucciones: list[str] = []

        async def flujo(mensajes: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
            self.instrucciones.append(info.instructions or "")
            yield "Hola"

        env = {"LATAM_OPERADOR_CODIGO": CODIGO}
        self.app = crear_app(demo=self.demo, modelo=FunctionModel(stream_function=flujo), entorno=env)
        self.c = TestClient(self.app)

    def ingresar(self, indice: int = 0) -> dict[str, str]:
        r = self.c.post("/api/banca/ingresar", json={"indice": indice})
        assert r.status_code == 200, r.text
        return {"X-Sesion": r.json()["sesion"]}

    def operador(self) -> dict[str, str]:
        r = self.c.post("/api/operador/ingresar", json={"codigo": CODIGO})
        assert r.status_code == 200
        return {"X-Operador": r.json()["sesion_operador"]}

    def movimientos(self, h: dict[str, str], **q: str) -> list[dict[str, Any]]:
        return self.c.get("/api/banca/movimientos", headers=h, params=q).json()["movimientos"]

    def reclamar(self, h: dict[str, str], tx_ref: str) -> str:
        r = self.c.post(f"/api/banca/movimientos/{tx_ref}/reclamar", headers=h, json={})
        assert r.status_code == 200, r.text
        return r.json()["conversacion"]


@pytest.fixture
def mundo() -> Mundo:
    return Mundo()


def _sin_pii(*cargas: Any) -> None:
    texto = json.dumps(cargas, ensure_ascii=False)
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, prohibido


# Cliente


def test_clientes_demo_y_ingreso(mundo: Mundo) -> None:
    lista = mundo.c.get("/api/banca/clientes-demo").json()
    assert [c["indice"] for c in lista] == [0, 1, 2]
    assert lista[0] == {"indice": 0, "alias": "Cliente 1 · Colombia", "pais": "CO"}
    r = mundo.c.post("/api/banca/ingresar", json={"indice": 1, "registro": "vos"}).json()
    assert r["cliente"] == {"alias": "Cliente 2 · Colombia", "pais": "CO", "moneda": "COP", "registro": "vos"}
    assert mundo.c.post("/api/banca/ingresar", json={"indice": 9}).status_code == 400
    assert mundo.c.post("/api/banca/ingresar", json={"indice": "0"}).status_code == 400
    _sin_pii(lista, r)


def test_resumen_con_refs_opacas(mundo: Mundo) -> None:
    h = mundo.ingresar()
    r = mundo.c.get("/api/banca/resumen", headers=h).json()
    (p,) = r["productos"]
    assert p["final"] == "4001" and p["etiqueta"] == "Tarjeta de crédito" and p["estado"] == "activa"
    assert p["saldo"] is None and p["limite"] is None and p["producto_ref"].startswith("prod_")
    _sin_pii(r)


def test_movimientos_paginacion_detalle_y_formato(mundo: Mundo) -> None:
    h = mundo.ingresar()
    todos = mundo.movimientos(h)
    assert [m["descripcion"] for m in todos] == ["Tienda Uno", "Panadería Centro"]
    assert (
        todos[0]["monto"] == "1.234,56"
        and todos[0]["moneda"] == "COP"
        and todos[0]["tarjeta_final"] == "4001"
    )
    assert (
        todos[0]["fecha"] == "2026-06-16" and todos[0]["reclamable"] is True and todos[0]["caso_ref"] is None
    )
    pagina = mundo.c.get("/api/banca/movimientos", headers=h, params={"limite": 1}).json()
    assert len(pagina["movimientos"]) == 1 and pagina["siguiente"]
    resto = mundo.movimientos(h, antes_de=pagina["siguiente"])
    assert [m["descripcion"] for m in resto] == ["Panadería Centro"]
    ref_producto = mundo.c.get("/api/banca/resumen", headers=h).json()["productos"][0]["producto_ref"]
    assert len(mundo.movimientos(h, producto_ref=ref_producto)) == 2
    assert (
        mundo.c.get("/api/banca/movimientos", headers=h, params={"producto_ref": "prod_x"}).status_code == 404
    )
    uno = mundo.c.get(f"/api/banca/movimientos/{todos[0]['tx_ref']}", headers=h)
    assert uno.json() == todos[0]
    assert mundo.c.get("/api/banca/movimientos/tx_inexistente", headers=h).status_code == 404
    _sin_pii(todos, pagina)


def test_sin_sesion_todo_es_401(mundo: Mundo) -> None:
    for metodo, ruta in [
        ("get", "/api/banca/resumen"),
        ("get", "/api/banca/movimientos"),
        ("get", "/api/banca/movimientos/tx_a"),
        ("post", "/api/banca/movimientos/tx_a/reclamar"),
        ("get", "/api/banca/reclamos"),
        ("post", "/api/banca/tarjetas/prod_a/bloqueo"),
        ("get", "/api/banca/conversaciones/c-1/mensajes"),
        ("post", "/api/banca/conversaciones/c-1/mensajes"),
    ]:
        assert getattr(mundo.c, metodo)(ruta).status_code == 401, ruta
    assert mundo.c.get("/api/banca/resumen", headers={"X-Sesion": "inventada"}).status_code == 401
    mundo.reloj.t += timedelta(hours=1)
    h = {"X-Sesion": "x"}
    assert mundo.c.get("/api/banca/resumen", headers=h).status_code == 401


def test_un_cliente_no_alcanza_lo_de_otro(mundo: Mundo) -> None:
    a, b = mundo.ingresar(0), mundo.ingresar(1)
    tx_a = mundo.movimientos(a)[0]["tx_ref"]
    prod_a = mundo.c.get("/api/banca/resumen", headers=a).json()["productos"][0]["producto_ref"]
    conv_a = mundo.reclamar(a, tx_a)
    assert mundo.c.get(f"/api/banca/movimientos/{tx_a}", headers=b).status_code == 404
    assert mundo.c.post(f"/api/banca/movimientos/{tx_a}/reclamar", headers=b, json={}).status_code == 404
    assert (
        mundo.c.post(f"/api/banca/tarjetas/{prod_a}/bloqueo", headers=b, json={"confirmo": True}).status_code
        == 404
    )
    assert mundo.c.get(f"/api/banca/conversaciones/{conv_a}/mensajes", headers=b).status_code == 404
    assert (
        mundo.c.post(
            f"/api/banca/conversaciones/{conv_a}/mensajes", headers=b, json={"texto": "hola"}
        ).status_code
        == 404
    )
    assert (
        mundo.c.get("/api/banca/movimientos", headers=b, params={"producto_ref": prod_a}).status_code == 404
    )
    assert not mundo.demo.banco.bloqueado("demo-1", "tarjeta-4001")
    # el chat tampoco deja hablar en una conversación ajena
    cuerpo = {
        "threadId": conv_a,
        "runId": "r",
        "state": {},
        "messages": [],
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }
    assert mundo.c.post("/api/agui", json=cuerpo, headers=b).status_code == 403
    assert mundo.c.post("/api/traspaso", json={"conversacion": conv_a}, headers=b).status_code == 403
    assert mundo.c.get("/api/banca/reclamos", headers=b).json() == []


def test_reclamar_fija_la_transaccion_en_el_servidor(mundo: Mundo) -> None:
    h = mundo.ingresar()
    tx = mundo.movimientos(h)[0]
    conv = mundo.reclamar(h, tx["tx_ref"])
    assert mundo.reclamar(h, tx["tx_ref"]) == conv  # el mismo movimiento reabre la misma conversación
    cuerpo = {
        "threadId": conv,
        "runId": "r1",
        "state": {},
        "messages": [{"id": "u1", "role": "user", "content": "Hola"}],
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }
    with mundo.c.stream("POST", "/api/agui", json=cuerpo, headers=h) as r:
        assert r.status_code == 200
        r.read()
    assert "Contexto fijado por el servidor" in mundo.instrucciones[-1]
    assert "tx-1-1" in mundo.instrucciones[-1] and "Tienda Uno" in mundo.instrucciones[-1]
    registro = mundo.demo.banco.conversacion(conv)
    assert registro is not None and registro.transaccion_id == "tx-1-1"
    assert [t.autor for t in registro.transcripcion][0] == "cliente"
    assert mundo.demo.almacen.cargar(conv) is not None  # las herramientas la reconocen como del cliente


def test_reclamar_no_reclamable_o_ya_reclamado(mundo: Mundo) -> None:
    h = mundo.ingresar()
    tx = mundo.movimientos(h)[0]
    mundo.demo.banco.abrir_caso(
        "k", "demo-1", "tx-1-1", Dinero(monto=Decimal("1234.56"), moneda="COP"), "m", True
    )
    r = mundo.c.post(f"/api/banca/movimientos/{tx['tx_ref']}/reclamar", headers=h, json={})
    assert (
        r.status_code == 409
        and r.json()["error"] == "ya_reclamado"
        and r.json()["caso_ref"].startswith("caso-")
    )
    actualizado = mundo.movimientos(h)[0]
    assert actualizado["reclamable"] is False and actualizado["caso_ref"] == r.json()["caso_ref"]
    (reclamo,) = mundo.c.get("/api/banca/reclamos", headers=h).json()
    assert reclamo["tx_ref"] == tx["tx_ref"] and reclamo["descripcion"] == "Tienda Uno"
    assert (
        reclamo["monto"] == "1.234,56"
        and reclamo["estado"] == "abierto"
        and reclamo["credito_provisional"] is True
    )
    assert [e["evento"] for e in reclamo["historial"]][0] == "Reclamo abierto" and len(
        reclamo["historial"]
    ) == 2
    _sin_pii(reclamo)


def test_bloqueo_exige_confirmacion_y_es_idempotente(mundo: Mundo) -> None:
    h = mundo.ingresar()
    prod = mundo.c.get("/api/banca/resumen", headers=h).json()["productos"][0]["producto_ref"]
    url = f"/api/banca/tarjetas/{prod}/bloqueo"
    assert mundo.c.post(url, headers=h, json={}).status_code == 400
    assert mundo.c.post(url, headers=h, json={"confirmo": "si"}).status_code == 400
    assert mundo.c.post(url, headers=h, json={"confirmo": True}).json() == {
        "estado": "bloqueada",
        "ya_estaba": False,
    }
    assert mundo.c.post(url, headers=h, json={"confirmo": True}).json() == {
        "estado": "bloqueada",
        "ya_estaba": True,
    }
    assert mundo.demo.banco.llamadas == 1
    assert mundo.c.get("/api/banca/resumen", headers=h).json()["productos"][0]["estado"] == "bloqueada"


# Traspaso, consola y mensajes


def _escalar(mundo: Mundo, h: dict[str, str], conv: str) -> str:
    r = mundo.c.post("/api/traspaso", json={"conversacion": conv}, headers=h)
    assert r.status_code == 200, r.text
    return str(r.json()["turno"])


def test_flujo_completo_cliente_experto(mundo: Mundo) -> None:
    h = mundo.ingresar()
    conv = mundo.reclamar(h, mundo.movimientos(h)[0]["tx_ref"])
    assert (
        mundo.c.post(
            f"/api/banca/conversaciones/{conv}/mensajes", headers=h, json={"texto": "hola"}
        ).status_code
        == 409
    )
    idt = _escalar(mundo, h, conv)
    assert _escalar(mundo, h, conv) == idt and mundo.demo.banco.llamadas == 1  # idempotente por conversación

    assert mundo.c.get("/api/operador/cola").status_code == 401
    assert mundo.c.post("/api/operador/ingresar", json={"codigo": "mal"}).status_code == 401
    op = mundo.operador()
    cola = mundo.c.get("/api/operador/cola", headers=op).json()
    assert len(cola) == 1
    fila = cola[0]
    assert (
        fila["id_traspaso"] == idt and fila["prioridad"] == "P3" and fila["motivo"] == "CLIENTE_PIDE_PERSONA"
    )
    assert fila["estado"] == "en_cola" and fila["tomado_por"] is None and fila["pais"] == "CO"

    d = mundo.c.get(f"/api/operador/traspasos/{idt}", headers=op).json()
    assert set(d) >= CAMPOS_2_5_2
    assert d["motivo"]["codigo"] == "CLIENTE_PIDE_PERSONA" and d["motivo"]["regla"]["id"] == "TRA-04"
    assert d["motivo"]["regla"]["version"].startswith("policy/v1@")
    assert d["caso_id"] is None and d["hilo_id"] == conv and d["identidad"]["nivel"] == "acr2"
    assert all({"texto", "fuente", "hora"} == set(x) for x in d["hechos_verificados"])
    assert {x["fuente"] for x in d["hechos_verificados"]} == {"transacciones", "productos", "casos"}
    assert any("Tienda Uno" in x["texto"] for x in d["hechos_verificados"])
    assert "Radicar el reclamo" in [x["accion"] for x in d["acciones_no_realizadas"]]
    assert d["compromisos_comunicados"] and d["evidencia"]["reglas"] and d["que_hacer_primero"]
    assert d["solicitud"]["cita"].startswith("Reclamo desde la banca en línea")
    assert d["interpretacion"]["confianza"] is None and d["mensajes"] == []
    _sin_pii(cola, d)

    assert (
        mundo.c.post(f"/api/operador/traspasos/{idt}/mensaje", headers=op, json={"texto": "x"}).status_code
        == 409
    )
    assert mundo.c.post(f"/api/operador/traspasos/{idt}/tomar", headers=op).json() == {"estado": "tomado"}
    otro = mundo.operador()
    assert mundo.c.post(f"/api/operador/traspasos/{idt}/tomar", headers=otro).status_code == 409
    assert mundo.c.get("/api/operador/cola", headers=op).json()[0]["tomado_por"] == "Experto 1"

    m1 = mundo.c.post(
        f"/api/operador/traspasos/{idt}/mensaje", headers=op, json={"texto": "Buenas tardes"}
    ).json()["id"]
    mensajes = mundo.c.get(f"/api/banca/conversaciones/{conv}/mensajes", headers=h).json()
    assert [(m["autor"], m["texto"]) for m in mensajes] == [("persona", "Buenas tardes")]
    assert (
        mundo.c.get(f"/api/banca/conversaciones/{conv}/mensajes", headers=h, params={"desde": m1}).json()
        == []
    )
    m2 = mundo.c.post(f"/api/banca/conversaciones/{conv}/mensajes", headers=h, json={"texto": "Hola"}).json()[
        "id"
    ]
    assert m2 > m1
    nuevos = mundo.c.get(f"/api/banca/conversaciones/{conv}/mensajes", headers=h, params={"desde": m1}).json()
    assert [(m["autor"], m["texto"]) for m in nuevos] == [("cliente", "Hola")]
    d = mundo.c.get(f"/api/operador/traspasos/{idt}", headers=op).json()
    assert [m["autor"] for m in d["mensajes"]] == ["persona", "cliente"] and d["estado"] == "tomado"

    r = mundo.c.post(f"/api/operador/traspasos/{idt}/resolver", headers=otro, json={"resultado": "resuelto"})
    assert r.status_code == 409
    assert (
        mundo.c.post(
            f"/api/operador/traspasos/{idt}/resolver", headers=op, json={"resultado": "raro"}
        ).status_code
        == 400
    )
    corr = {
        "motivo_verdadero": "fraude",
        "comentario": "Llamó al 3001234567 desde a@b.co",
        "utilidad_paquete": 4,
    }
    r = mundo.c.post(
        f"/api/operador/traspasos/{idt}/resolver",
        headers=op,
        json={"resultado": "resuelto", "etiqueta_correccion": corr, "nota": "Cliente 4111 1111 1111 1111"},
    )
    assert r.json() == {"estado": "resuelto"}
    guardado = mundo.demo.banco.traspaso(idt)
    assert guardado is not None and guardado.estado == "resuelto"
    assert "3001234567" not in json.dumps(guardado.etiqueta_correccion) and "4111" not in (
        guardado.nota or ""
    )
    assert mundo.c.get("/api/operador/cola", headers=op).json() == []
    assert (
        mundo.c.post(f"/api/banca/conversaciones/{conv}/mensajes", headers=h, json={"texto": "x"}).status_code
        == 409
    )


def test_operador_sin_codigo_configurado_o_sesion_falsa() -> None:
    lectura, ids = lectura_sembrada()
    demo = Demo(lectura=lectura, clientes=ids, origen="memoria")
    c = TestClient(crear_app(demo=demo, modelo=crear_modelo({})[0], entorno={}))
    assert c.post("/api/operador/ingresar", json={"codigo": ""}).status_code == 503
    assert c.get("/api/operador/cola", headers={"X-Operador": "inventada"}).status_code == 401
    assert c.get("/api/operador/traspasos/tr-x", headers={"X-Operador": "inventada"}).status_code == 401


def test_cola_por_prioridad_y_antiguedad(mundo: Mundo) -> None:
    ha, hb = mundo.ingresar(0), mundo.ingresar(1)
    conv_a = mundo.reclamar(ha, mundo.movimientos(ha)[0]["tx_ref"])
    _escalar(mundo, ha, conv_a)  # P3, primero en llegar
    mundo.reloj.t += timedelta(minutes=5)
    sesion_b = next(s for s in mundo.demo.sesiones.values() if s.autenticada.cliente_id == "demo-2")
    Herramientas(mundo.demo.lectura, mundo.demo.banco, mundo.demo.almacen, reloj=mundo.reloj).escalar(
        sesion_b.autenticada, sesion_b.conversacion_id, "lo que sea", urgente=True
    )
    fila = mundo.c.get("/api/operador/cola", headers=mundo.operador()).json()
    assert [f["prioridad"] for f in fila] == ["P1", "P3"]
    assert fila[0]["motivo"] == "URGENCIA_TRANSFERENCIA" and fila[0]["creado_hace_s"] == 0
    assert fila[1]["creado_hace_s"] == 300
    d = mundo.c.get(f"/api/operador/traspasos/{fila[0]['id_traspaso']}", headers=mundo.operador()).json()
    assert d["hechos_verificados"][0]["fuente"] == "conversacion"  # sin movimiento: se dice, no se inventa
    assert (
        d["preguntas_abiertas"][0]["a_quien"] == "cliente" and d["preguntas_abiertas"][0]["bloquea"] is True
    )
    assert hb  # sesión del segundo cliente abierta


def test_paquete_con_conflicto_de_historial_y_caso_abierto() -> None:
    def tx(tid: str, dia: int, monto: str, estado: str = "approved") -> Transaccion:
        return Transaccion(
            transaction_id=tid,
            product_id="tarjeta-4001",
            event_ts=datetime(2026, 6, dia, 15, 30, tzinfo=UTC),
            monto=Dinero(monto=Decimal(monto), moneda="COP"),
            amount_usd=Decimal("2500"),
            tipo="purchase",
            estado=estado,
            comercio="TechMart",
            categoria="retail",
            pais="CO",
            es_extranjera=False,
        )

    lectura = LecturaOroFalsa(
        [
            ("demo-1", tx("tx-1-9", 16, "9000000")),
            ("demo-1", tx("tx-1-8", 1, "50000")),
            ("demo-1", tx("tx-1-7", 5, "60000")),
        ],
        [("demo-1", Producto(product_id="tarjeta-4001", tipo="credit_card", estado="active", moneda="COP"))],
    )
    m = Mundo(lectura, ["demo-1"])
    h = m.ingresar()
    conv = m.reclamar(h, m.movimientos(h)[0]["tx_ref"])
    sesion = next(iter(m.demo.sesiones.values())).autenticada
    herr = Herramientas(m.demo.lectura, m.demo.banco, m.demo.almacen, reloj=m.reloj)
    accion, _ = herr.abrir_disputa(
        sesion,
        conv,
        "tx-1-9",
        "no_la_reconozco",
        Confirmacion(accion="abrir_disputa", canal=Canal.CHAT, evidencia="boton", nonce="n"),
    )
    assert "crédito provisional" not in accion.resultado_releido  # 2.500 USD supera el tope de 200
    assert herr.escalar_tras_radicar(m.demo.lectura.transaccion("demo-1", "tx-1-9")) == "monto_sobre_umbral"  # pyright: ignore[reportArgumentType]
    herr.escalar(sesion, conv, "cliente_pidio_persona")
    d = m.c.get("/api/operador/cola", headers=m.operador()).json()[0]
    assert d["prioridad"] == "P2"  # la del caso (monto sobre el umbral) supera a la del motivo (P3)
    detalle = m.c.get(f"/api/operador/traspasos/{d['id_traspaso']}", headers=m.operador()).json()
    assert detalle["conflictos"] == [
        {
            "tipo": "Compras previas en el mismo comercio",
            "declarado": "no reconoce el cargo",
            "registro": "2 compras anteriores no disputadas en este comercio en 90 días "
            "(transacciones, 07:00)",
        }
    ]
    assert detalle["caso_id"] and detalle["caso_id"].startswith("caso-")
    assert [a["accion"] for a in detalle["acciones_realizadas"]] == ["abrir_disputa"]
    assert any("Reclamo abierto por este movimiento" in x["texto"] for x in detalle["hechos_verificados"])
    assert all(a["accion"] != "Radicar el reclamo" for a in detalle["acciones_no_realizadas"])
    assert detalle["plazos_en_curso"][0]["vence_en_s"] == 900
    assert m.demo.banco.creditos_provisionales == []
    _sin_pii(detalle)


# Banco: idempotencia y crédito provisional


def _dinero() -> Dinero:
    return Dinero(monto=Decimal("100"), moneda="MXN")


@pytest.mark.parametrize("banco_cls", [BancoMemoria, ServiciosBancoFalsos])
def test_abrir_disputa_ya_abierta_no_concede_otro_credito(banco_cls: Any) -> None:
    banco = banco_cls()
    caso = banco.abrir_caso("k1", "c1", "t1", _dinero(), "fraude", True)
    assert banco.abrir_caso("k1", "c1", "t1", _dinero(), "fraude", True) == caso  # misma llave
    assert (
        banco.abrir_caso("k2", "c1", "t1", _dinero(), "fraude", True) == caso
    )  # otra llave, mismo caso abierto
    assert len(banco.creditos_provisionales) == 1
    assert banco.credito_provisional_de(caso)
    sin = banco.abrir_caso("k3", "c1", "t2", _dinero(), "fraude", False)
    assert (
        banco.abrir_caso("k4", "c1", "t2", _dinero(), "fraude", True) == sin
    )  # abierto sin crédito: sigue sin él
    assert not banco.credito_provisional_de(sin) and len(banco.creditos_provisionales) == 1


def test_herramientas_no_repiten_el_credito_entre_conversaciones() -> None:
    lectura, _ = lectura_sembrada()
    banco = BancoMemoria()
    almacen_h = Herramientas(lectura, banco, AlmacenMemoria(), reloj=lambda: AHORA)
    sesion = SesionAutenticada(
        id_sesion="s", cliente_id="demo-1", nivel=NivelAcr.ACCION, expira=AHORA + timedelta(hours=1)
    )
    resultados: list[str] = []
    for conv in ("c-a", "c-b"):
        almacen_h._almacen.crear_conversacion(  # pyright: ignore[reportPrivateUsage]
            Conversacion(id=conv, cliente_ref="demo-1", canal_actual=Canal.CHAT, estado="inicio")
        )
        tx = lectura.transaccion("demo-1", "tx-1-1")
        assert tx is not None
        accion, _ = almacen_h.abrir_disputa(
            sesion,
            conv,
            "tx-1-1",
            "m",
            Confirmacion(accion="abrir_disputa", canal=Canal.CHAT, evidencia="boton", nonce=conv),
            credito_provisional=True,
        )
        resultados.append(accion.resultado_releido)
    assert resultados[0] == resultados[1] and len(banco.creditos_provisionales) == 1 and banco.llamadas == 1


def test_bloqueo_y_traspaso_idempotentes_en_el_banco() -> None:
    banco = BancoMemoria()
    assert banco.bloquear_tarjeta("a", "c1", "p1") == banco.bloquear_tarjeta("b", "c1", "p1")
    assert banco.llamadas == 1 and banco.bloqueado("c1", "p1") and not banco.bloqueado("c2", "p1")
    t1 = banco.encolar_traspaso("a", "c1", "conv", "cliente_pidio_persona", False)
    assert banco.encolar_traspaso("b", "c1", "conv", "cliente_pidio_persona", False) == t1
    assert len(banco.cola()) == 1 and banco.tomar(t1, "x") == "tomado" and banco.tomar(t1, "y") == "ya_tomado"
    assert banco.tomar("no-existe", "x") == "inexistente"


def test_seleccion_del_banco_por_entorno() -> None:
    assert isinstance(crear_banco({}), BancoMemoria)
    assert isinstance(crear_banco({"LATAM_BANCO": "memoria", "LATAM_GCP_PROJECT": "p"}), BancoMemoria)
    with pytest.raises(ValueError):
        crear_banco({"LATAM_BANCO": "firestore"})
    with pytest.raises(ValueError):
        crear_banco({"LATAM_BANCO": "otro"})


def test_mensajes_de_otra_conversacion_no_se_mezclan() -> None:
    banco = BancoMemoria()
    a = banco.agregar_mensaje("c1", "persona", "uno")
    banco.agregar_mensaje("c2", "persona", "dos")
    assert [m.texto for m in banco.mensajes("c1")] == ["uno"]
    assert banco.mensajes("c1", desde=a) == []


# Forma que lee la consola (fixtures de la rama de la consola del experto)

FIXTURES = Path(__file__).resolve().parents[1] / "web" / "sitio" / "operador" / "fixtures"


def _claves(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _claves(v) for k, v in obj.items()}  # pyright: ignore[reportUnknownVariableType]
    if isinstance(obj, list) and obj:
        return [_claves(obj[0])]  # pyright: ignore[reportUnknownVariableType]
    return None


def _mismas_claves(mio: Any, fixture: Any, ruta: str) -> None:
    if isinstance(fixture, dict):
        assert isinstance(mio, dict), ruta
        assert set(mio) == set(fixture), f"{ruta}: {sorted(mio)} != {sorted(fixture)}"  # pyright: ignore[reportUnknownArgumentType]
        for k in fixture:  # pyright: ignore[reportUnknownVariableType]
            _mismas_claves(mio[k], fixture[k], f"{ruta}.{k}")
    elif isinstance(fixture, list) and fixture and isinstance(mio, list) and mio:
        for i, elemento in enumerate(mio):  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            _mismas_claves(elemento, fixture[0], f"{ruta}[{i}]")


@pytest.mark.skipif(not FIXTURES.is_dir(), reason="las fixtures llegan con la consola del experto")
def test_serializador_coincide_con_las_fixtures_de_la_consola() -> None:
    m = Mundo()
    h = m.ingresar()
    conv = m.reclamar(h, m.movimientos(h)[0]["tx_ref"])
    m.c.post("/api/traspaso", json={"conversacion": conv}, headers=h)
    op = m.operador()
    cola = m.c.get("/api/operador/cola", headers=op).json()
    _mismas_claves(cola[0], json.loads((FIXTURES / "cola.json").read_text(encoding="utf-8"))[0], "cola")
    detalle = m.c.get(f"/api/operador/traspasos/{cola[0]['id_traspaso']}", headers=op).json()
    m.c.post(f"/api/operador/traspasos/{cola[0]['id_traspaso']}/tomar", headers=op)
    m.c.post(f"/api/banca/conversaciones/{conv}/mensajes", headers=h, json={"texto": "hola"})
    m.c.post(
        f"/api/operador/traspasos/{cola[0]['id_traspaso']}/mensaje", headers=op, json={"texto": "buenas"}
    )
    con_mensajes = m.c.get(f"/api/operador/traspasos/{cola[0]['id_traspaso']}", headers=op).json()
    fixtures = sorted(FIXTURES.glob("traspaso_*.json"))
    assert fixtures
    for f in fixtures:
        esperado = json.loads(f.read_text(encoding="utf-8"))
        _mismas_claves(detalle, esperado, f.name)
    assert con_mensajes["mensajes"] and set(con_mensajes["mensajes"][0]) == {"id", "autor", "texto", "en"}


def test_ids_de_mensaje_estrictamente_crecientes() -> None:
    from latam_tecnologia.banca.banco import id_mensaje

    ids = [id_mensaje() for _ in range(2000)]
    assert ids == sorted(ids) and len(set(ids)) == len(ids)
