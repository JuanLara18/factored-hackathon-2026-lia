"""Spike S3: eventos AG-UI de PydanticAI con modelo simulado (sin llamadas de pago)."""

from __future__ import annotations

import json
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from latam_tecnologia.canales.chat_agui import Confirmaciones, crear_app
from latam_tecnologia.canales.frases import SegmentadorFrases, filtrar_frase

FICHA_TOOL = {
    "name": "FichaTransaccion",
    "description": "Dibuja la ficha de una transacción",
    "parameters": {"type": "object", "properties": {"comercio": {"type": "string"}}},
}


def _cuerpo(
    thread: str, run: str, messages: list[dict[str, Any]], resume: list[dict[str, Any]] | None = None
):
    cuerpo: dict[str, Any] = {
        "threadId": thread,
        "runId": run,
        "state": {},
        "messages": messages,
        "tools": [FICHA_TOOL],
        "context": [],
        "forwardedProps": {},
    }
    if resume:
        cuerpo["resume"] = resume
    return cuerpo


def _correr(cliente: TestClient, cuerpo: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    eventos: list[dict[str, Any]] = []
    primero = 0.0
    t0 = time.perf_counter()
    with cliente.stream("POST", "/agui", json=cuerpo) as r:
        assert r.status_code == 200
        for linea in r.iter_lines():
            if linea.startswith("data: "):
                e = json.loads(linea[6:])
                if e["type"] == "TEXT_MESSAGE_CONTENT" and not primero:
                    primero = time.perf_counter() - t0
                eventos.append(e)
    return eventos, primero


def _turno_uno(cliente: TestClient, thread: str = "t1"):
    msgs = [{"id": "u1", "role": "user", "content": "No reconozco un cargo"}]
    return _correr(cliente, _cuerpo(thread, "r1", msgs)), msgs


def _mensajes_de_vuelta(eventos: list[dict[str, Any]], previos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconstruye el historial como lo haría el navegador a partir de los eventos."""
    msgs = list(previos)
    texto: dict[str, str] = {}
    llamadas: dict[str, list[dict[str, Any]]] = {}
    orden: list[str] = []
    for e in eventos:
        t = e["type"]
        if t == "TEXT_MESSAGE_START":
            orden.append(e["messageId"])
            texto[e["messageId"]] = ""
        elif t == "TEXT_MESSAGE_CONTENT":
            texto[e["messageId"]] += e["delta"]
        elif t == "TOOL_CALL_START":
            llamadas.setdefault(e["parentMessageId"], []).append(
                {
                    "id": e["toolCallId"],
                    "type": "function",
                    "function": {"name": e["toolCallName"], "arguments": ""},
                }
            )
        elif t == "TOOL_CALL_ARGS":
            for lista in llamadas.values():
                for c in lista:
                    if c["id"] == e["toolCallId"]:
                        c["function"]["arguments"] += e["delta"]
        elif t == "TOOL_CALL_RESULT":
            fin = orden[-1]
            msgs.append(
                {"id": e["messageId"], "role": "tool", "toolCallId": e["toolCallId"], "content": e["content"]}
            )
            _ = fin
    # el orden importa: asistente antes de sus resultados
    asistentes = [
        {
            "id": mid,
            "role": "assistant",
            "content": texto[mid],
            **({"toolCalls": llamadas[mid]} if mid in llamadas else {}),
        }
        for mid in orden
    ]
    herramientas = [m for m in msgs if m["role"] == "tool" and m not in previos]
    base = [m for m in msgs if m in previos]
    return base + _intercalar(asistentes, herramientas)


def _intercalar(asistentes: list[dict[str, Any]], herramientas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    salida: list[dict[str, Any]] = []
    for a in asistentes:
        salida.append(a)
        ids = {c["id"] for c in a.get("toolCalls", [])}
        salida.extend(h for h in herramientas if h["toolCallId"] in ids)
    return salida


def _tipos(eventos: list[dict[str, Any]]) -> list[str]:
    return [e["type"] for e in eventos]


def test_turno_uno_emite_texto_por_frases_componente_e_interrupcion() -> None:
    cliente = TestClient(crear_app())
    (eventos, primero), _ = _turno_uno(cliente)
    tipos = _tipos(eventos)
    assert tipos[0] == "RUN_STARTED" and tipos[-1] == "RUN_FINISHED"
    contenidos = [e["delta"] for e in eventos if e["type"] == "TEXT_MESSAGE_CONTENT"]
    # el modelo simulado emite trozos de 6 caracteres; al cliente solo llegan frases completas
    assert contenidos == [
        "Encontré el cargo de $ 1.234,56 en Tienda Uno. ",
        "Necesito tu confirmación para continuar. ",
    ]
    ficha = next(
        e for e in eventos if e["type"] == "TOOL_CALL_START" and e["toolCallName"] == "FichaTransaccion"
    )
    args = "".join(
        e["delta"]
        for e in eventos
        if e["type"] == "TOOL_CALL_ARGS" and e["toolCallId"] == ficha["toolCallId"]
    )
    assert json.loads(args)["comercio"] == "Tienda Uno"
    final = eventos[-1]
    interrupciones = final["outcome"]["interrupts"]
    assert final["outcome"]["type"] == "interrupt"
    assert [i["toolCallId"] for i in interrupciones] == ["c-conf"]
    assert interrupciones[0]["responseSchema"]["required"] == ["approved"]
    assert primero < 1.0, f"primer texto {primero:.3f}s (R-TEC-79: p50 menor a 1 s)"


def test_aprobacion_con_nonce_de_ida_y_vuelta() -> None:
    cliente = TestClient(crear_app())
    (eventos, _), msgs = _turno_uno(cliente)
    historial = _mensajes_de_vuelta(eventos, msgs)
    historial.append({"id": "tf", "role": "tool", "toolCallId": "c-ficha", "content": '"dibujada"'})
    resume = [{"interruptId": "int-c-conf", "status": "resolved", "payload": {"approved": True}}]
    eventos2, _ = _correr(cliente, _cuerpo("t1", "r2", historial, resume))
    texto = "".join(e["delta"] for e in eventos2 if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert "Quedó confirmada la acción disputar_cargo por 1.234,56." in texto
    assert eventos2[-1]["outcome"]["type"] == "success"


def test_rechazo_no_ejecuta_la_accion() -> None:
    cliente = TestClient(crear_app())
    (eventos, _), msgs = _turno_uno(cliente)
    historial = _mensajes_de_vuelta(eventos, msgs)
    historial.append({"id": "tf", "role": "tool", "toolCallId": "c-ficha", "content": '"dibujada"'})
    resume = [{"interruptId": "int-c-conf", "status": "resolved", "payload": {"approved": False}}]
    eventos2, _ = _correr(cliente, _cuerpo("t1", "r2", historial, resume))
    assert not any("Quedó confirmada" in e.get("delta", "") for e in eventos2)


def test_nonce_de_otra_sesion_o_vencido_se_rechaza() -> None:
    reloj = [0.0]
    conf = Confirmaciones(reloj=lambda: reloj[0])
    cliente = TestClient(crear_app(confirmaciones=conf))
    (eventos, _), msgs = _turno_uno(cliente)
    historial = _mensajes_de_vuelta(eventos, msgs)
    historial.append({"id": "tf", "role": "tool", "toolCallId": "c-ficha", "content": '"dibujada"'})
    resume = [{"interruptId": "int-c-conf", "status": "resolved", "payload": {"approved": True}}]
    reloj[0] = 301.0  # pasaron más de 5 minutos
    eventos2, _ = _correr(cliente, _cuerpo("t1", "r2", historial, resume))
    texto = "".join(e["delta"] for e in eventos2 if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert "no es válida o venció" in texto


def test_nonce_de_un_solo_uso_y_de_la_misma_sesion() -> None:
    conf = Confirmaciones()
    nonce = conf.emitir("t1")
    assert not conf.consumir(nonce, "otra")  # otra sesión (y ya se gastó)
    nonce = conf.emitir("t1")
    assert conf.consumir(nonce, "t1")
    assert not conf.consumir(nonce, "t1")


def test_dato_sensible_a_mitad_de_frase_nunca_llega_al_cliente() -> None:
    app = crear_app(texto_inseguro=True)
    cliente = TestClient(app)
    (eventos, _), _ = _turno_uno(cliente)
    crudo = json.dumps(eventos)
    assert "4111 1111 1111 1111" not in crudo
    texto = "".join(e["delta"] for e in eventos if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert "**** 1111" in texto


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("El monto es 1.234,56 COP. Sigue", ["El monto es 1.234,56 COP."]),
        ("Hable con el Sr. Pérez. Gracias ", ["Hable con el Sr. Pérez."]),
        ("¿Lo reconoces? Sí; o no\nOtra ", ["¿Lo reconoces?", "Sí;", "o no"]),
    ],
)
def test_segmentador_no_corta_numeros_ni_abreviaturas(texto: str, esperado: list[str]) -> None:
    assert SegmentadorFrases().alimentar(texto) == esperado


def test_segmentador_corta_frases_largas_en_el_ultimo_espacio() -> None:
    frases = SegmentadorFrases().alimentar("palabra " * 40)
    assert frases and all(len(f) <= 200 for f in frases)


def test_afirmacion_de_accion_sin_verificar_se_bloquea_y_sale_la_plantilla() -> None:
    assert filtrar_frase("Tu caso quedó radicado.").bloqueada
    assert not filtrar_frase("Necesito tu confirmación.").bloqueada


def test_la_web_minima_se_sirve_y_declara_el_contrato() -> None:
    cliente = TestClient(crear_app())
    html = cliente.get("/").text
    assert "app.js" in html and "<script>" not in html  # sin scripts en línea (R-TEC-80)
    js = cliente.get("/app.js").text
    for marca in ("TOOL_CALL_START", "TEXT_MESSAGE_CONTENT", "interruptId", "FichaTransaccion"):
        assert marca in js


@pytest.mark.parametrize(
    ("entrada", "salida"),
    [
        ("Su tarjeta PRD-R7AEZL80P060 está activa.", "Su tarjeta terminada en 0060 está activa."),
        ("Bloqueo PRD-1 ahora.", "Bloqueo tarjeta terminada en 0001 ahora."),
        ("La tarjeta tarjeta-4001 y la compra.", "La tarjeta terminada en 4001 y la compra."),
        ("Cobro de Tienda Uno (TX-1001) por 120.000.", "Cobro de Tienda Uno por 120.000."),
        ("La transacción tx-1-1, del 3 de junio.", "La transacción, del 3 de junio."),
        ("Cobro de Café Norte por 48,90.", "Cobro de Café Norte por 48,90."),
    ],
)
def test_filtro_enmascara_identificadores_internos(entrada: str, salida: str) -> None:
    r = filtrar_frase(entrada)
    assert r.texto == salida and not r.bloqueada
