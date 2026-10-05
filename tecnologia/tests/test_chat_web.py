"""Chat web (TEC-3): disputa con aprobación, botón de persona, sin datos personales, textos de plantilla."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from latam_tecnologia.canales import textos
from latam_tecnologia.canales.chat_web import crear_app
from latam_tecnologia.canales.demo import Demo, lectura_sembrada
from latam_tecnologia.canales.modelo import crear_modelo
from pydantic_ai.models.function import FunctionModel

FICHA_TOOL = {
    "name": "FichaTransaccion",
    "description": "Dibuja la ficha",
    "parameters": {"type": "object", "properties": {"comercio": {"type": "string"}}},
}
WEB = Path(__file__).resolve().parents[1] / "web" / "chat"
PLANTILLAS = yaml.safe_load(textos.RUTA_PLANTILLAS.read_text(encoding="utf-8"))["plantillas"]
PLANTILLAS_PT = yaml.safe_load(textos.RUTA_PLANTILLAS_PT.read_text(encoding="utf-8"))["plantillas"]


class Reloj:
    def __init__(self) -> None:
        self.t = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.t


Entorno = tuple[TestClient, Reloj, Demo]


def _demo(reloj: Reloj) -> Demo:
    lectura, ids = lectura_sembrada()
    return Demo(lectura=lectura, clientes=ids, origen="memoria", reloj=reloj)


def _cuerpo(n: Navegador, resume: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cuerpo: dict[str, Any] = {
        "threadId": n.conv,
        "runId": f"r{len(n.eventos)}",
        "state": {},
        "messages": n.historial,
        "tools": [FICHA_TOOL],
        "context": [],
        "forwardedProps": {},
    }
    if resume:
        cuerpo["resume"] = resume
    return cuerpo


class Navegador:
    """Hace lo que hace `chat.js`: sesión, historial reconstruido desde los eventos y `resume`."""

    def __init__(self, cliente: TestClient, registro: str = "usted", indice: int = 0) -> None:
        self.c = cliente
        r = self.c.post("/api/sesion", json={"cliente": indice, "registro": registro}).json()
        self.h = {"X-Sesion": r["sesion"], "X-Registro": registro}
        self.conv: str = r["conversacion"]
        self.historial: list[dict[str, Any]] = []
        self.eventos: list[dict[str, Any]] = []

    def correr(self, resume: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        with self.c.stream("POST", "/api/agui", json=_cuerpo(self, resume), headers=self.h) as r:
            assert r.status_code == 200, r.read()
            evs = [json.loads(ln[6:]) for ln in r.iter_lines() if ln.startswith("data: ")]
        self.eventos += evs
        self._historial(evs)
        return evs

    def _historial(self, evs: list[dict[str, Any]]) -> None:
        asis: dict[str, dict[str, Any]] = {}
        llamadas: dict[str, dict[str, Any]] = {}
        for e in evs:
            t = e["type"]
            if t == "TEXT_MESSAGE_START":
                asis[e["messageId"]] = {"id": e["messageId"], "role": "assistant", "content": ""}
            elif t == "TEXT_MESSAGE_CONTENT":
                asis[e["messageId"]]["content"] += e["delta"]
            elif t == "TOOL_CALL_START":
                llamadas[e["toolCallId"]] = {
                    "parent": e["parentMessageId"],
                    "name": e["toolCallName"],
                    "args": "",
                }
            elif t == "TOOL_CALL_ARGS":
                llamadas[e["toolCallId"]]["args"] += e["delta"]
            elif t == "TOOL_CALL_RESULT":
                if e["toolCallId"] in llamadas:
                    llamadas[e["toolCallId"]]["res"] = (e["messageId"], e["content"])
                else:  # la llamada nació en una corrida anterior (reanudación)
                    self.historial.append(
                        {
                            "id": e["messageId"],
                            "role": "tool",
                            "toolCallId": e["toolCallId"],
                            "content": e["content"],
                        }
                    )
        for a in asis.values():
            self.historial.append(a)
            propias = [(i, c) for i, c in llamadas.items() if c["parent"] == a["id"]]
            if propias:
                a["toolCalls"] = [
                    {"id": i, "type": "function", "function": {"name": c["name"], "arguments": c["args"]}}
                    for i, c in propias
                ]
            for i, c in propias:
                if "res" in c:
                    self.historial.append(
                        {"id": c["res"][0], "role": "tool", "toolCallId": i, "content": c["res"][1]}
                    )
        for i, c in llamadas.items():
            if c["name"] == "FichaTransaccion":
                self.historial.append(
                    {"id": f"t-{i}", "role": "tool", "toolCallId": i, "content": '"dibujada"'}
                )

    def decir(self, texto: str) -> list[dict[str, Any]]:
        self.historial.append({"id": f"u{len(self.historial)}", "role": "user", "content": texto})
        return self.correr()

    def resolver(self, evs: list[dict[str, Any]], aprobado: bool) -> list[dict[str, Any]]:
        i = evs[-1]["outcome"]["interrupts"][0]
        return self.correr(
            [{"interruptId": i["id"], "status": "resolved", "payload": {"approved": aprobado}}]
        )


def _texto(evs: list[dict[str, Any]]) -> str:
    return "".join(e["delta"] for e in evs if e["type"] == "TEXT_MESSAGE_CONTENT")


def _ficha(evs: list[dict[str, Any]]) -> dict[str, Any]:
    ini = next(e for e in evs if e["type"] == "TOOL_CALL_START" and e["toolCallName"] == "FichaTransaccion")
    args = "".join(
        e["delta"] for e in evs if e["type"] == "TOOL_CALL_ARGS" and e["toolCallId"] == ini["toolCallId"]
    )
    return json.loads(args)


@pytest.fixture
def entorno() -> Entorno:
    reloj = Reloj()
    demo = _demo(reloj)
    return TestClient(crear_app(demo=demo, modelo=crear_modelo({})[0])), reloj, demo


def test_disputa_completa_con_aprobacion(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente)
    e1 = n.decir("No reconozco un cargo")
    assert e1[0]["type"] == "RUN_STARTED" and e1[-1]["type"] == "RUN_FINISHED"
    ficha = _ficha(e1)
    assert ficha["comercio"] == "Tienda Uno" and ficha["monto"] == "1.234,56"
    assert ficha["tarjeta_final"] == "4001"
    assert set(ficha) <= {"comercio", "monto", "moneda", "fecha", "estado", "tarjeta_final"}
    assert "Encontré este cargo: Tienda Uno" in _texto(e1)

    e2 = n.decir("No la reconozco")
    interrupcion = e2[-1]["outcome"]["interrupts"][0]
    assert e2[-1]["outcome"]["type"] == "interrupt"
    # el monto y el comercio salen de la base, con la plantilla de confirmación
    assert "abrir un reclamo sobre el cargo de Tienda Uno, por 1.234,56 COP" in interrupcion["message"]
    assert interrupcion["expiresAt"] and interrupcion["metadata"]["vigencia_s"] == 300
    assert demo.banco.llamadas == 0  # nada se ejecutó antes de aprobar

    e3 = n.resolver(e2, aprobado=True)
    assert e3[-1]["outcome"]["type"] == "success"
    assert "quedó registrado el reclamo caso-" in _texto(e3)
    assert demo.banco.llamadas == 1 and [c.transaction_id for c in demo.banco.casos_abiertos("demo-1")] == [
        "tx-1-1"
    ]


def test_rechazo_no_ejecuta_y_usa_plantilla_sin_cambios(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente, registro="vos")
    n.decir("No reconozco un cargo")
    e2 = n.decir("No la reconozco")
    e3 = n.resolver(e2, aprobado=False)
    assert demo.banco.llamadas == 0
    assert _texto(e3).strip() == textos.plantilla("cierre.sin_cambios", "vos")


def test_confirmacion_vencida_se_rechaza_y_es_de_un_solo_uso(entorno: Entorno) -> None:
    cliente, reloj, demo = entorno
    n = Navegador(cliente)
    n.decir("No reconozco un cargo")
    e2 = n.decir("No la reconozco")
    i = e2[-1]["outcome"]["interrupts"][0]
    reloj.t += timedelta(minutes=5, seconds=1)
    cuerpo = _cuerpo(n, [{"interruptId": i["id"], "status": "resolved", "payload": {"approved": True}}])
    r = cliente.post("/api/agui", json=cuerpo, headers=n.h)
    assert r.status_code == 409 and r.json()["error"] == "confirmacion_vencida"
    assert demo.banco.llamadas == 0
    r = cliente.post("/api/agui", json=cuerpo, headers=n.h)  # ya gastada
    assert r.status_code == 409 and r.json()["error"] == "confirmacion_desconocida"


def test_sesion_ajena_o_ausente_no_entra_y_resume_invalido(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente)
    n.decir("No reconozco un cargo")
    n.decir("No la reconozco")  # queda una aprobación pendiente: un "sí" escrito no la resuelve
    n.decir("sí, confirmo")
    assert demo.banco.llamadas == 0
    otro = Navegador(cliente, indice=1)
    assert cliente.post("/api/agui", json=_cuerpo(n), headers=otro.h).status_code == 403
    assert cliente.post("/api/agui", json=_cuerpo(n)).status_code == 401
    malo = _cuerpo(n, [{"interruptId": "x-1", "status": "resolved", "payload": {"approved": True}}])
    assert cliente.post("/api/agui", json=malo, headers=n.h).status_code == 400


def test_boton_de_persona_traspasa_sin_pasar_por_el_modelo(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente)
    r = cliente.post("/api/traspaso", headers=n.h)
    assert r.status_code == 200
    assert r.json()["texto"] == textos.plantilla("traspaso.chat", "usted", rango_espera="unos minutos")
    assert demo.banco.traspaso_de_conversacion(n.conv) is not None
    cliente.post("/api/traspaso", headers=n.h)  # idempotente: no encola otro
    assert demo.banco.llamadas == 1
    assert cliente.post("/api/traspaso").status_code == 401


def test_sin_datos_personales_en_los_eventos(entorno: Entorno) -> None:
    cliente, _, _ = entorno
    n = Navegador(cliente)
    n.decir("No reconozco un cargo")
    e2 = n.decir("No la reconozco")
    n.resolver(e2, aprobado=True)
    crudo = json.dumps(
        [{k: v for k, v in e.items() if k != "timestamp"} for e in n.eventos], ensure_ascii=False
    )
    assert "demo-1" not in crudo  # ni el identificador del cliente
    assert n.h["X-Sesion"] not in crudo
    # Los identificadores de evento son UUID y a veces sus últimos grupos salen solo con dígitos
    # ("9165-667323872146"): se quitan antes de buscar números de tarjeta en todo lo demás.
    sin_uuid = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "", crudo)
    assert not re.search(r"\b(?:\d[ -]?){13,19}\b", sin_uuid)  # ningún número de tarjeta
    assert not re.search(r"[\w.]+@[\w.]+\.\w+", crudo)  # ningún correo


def test_gemini_solo_con_llave() -> None:
    assert crear_modelo({})[1] == "guionado"
    modelo, nombre = crear_modelo({"GEMINI_API_KEY": "x"})
    assert nombre.startswith("gemini:") and not isinstance(modelo, FunctionModel)


def test_textos_salen_de_las_plantillas() -> None:
    plantillas = {
        p["id"]: {**p["textos"], **pt["textos"]} for p, pt in zip(PLANTILLAS, PLANTILLAS_PT, strict=True)
    }
    for registro in textos.REGISTROS:
        cat = textos.catalogo_pagina(registro)
        assert cat["registro"] == registro
        for clave, pid in textos.PLANTILLAS_PAGINA.items():
            base = " ".join(plantillas[pid][registro].split())
            assert cat["textos"][clave] == base.replace("{rango_espera}", textos.rango_espera(registro))
        ia = "inteligência artificial" if registro == "voce" else "inteligencia artificial"
        assert cat["textos"]["aviso"].count(ia) == 1
    usted, vos = textos.catalogo_pagina("usted"), textos.catalogo_pagina("vos")
    assert "Si prefiere" in usted["textos"]["aviso"] and "Si preferís" in vos["textos"]["aviso"]


def test_etiquetas_respetan_limites_de_botones() -> None:
    for et in textos.ETIQUETAS.values():
        for clave in ("confirmo", "no", "reconozco", "no_reconozco", "renovar", "enviar"):
            assert len(et[clave]) <= 20, clave  # R-CLI-47
        assert any(w in et["persona"].lower() for w in ("persona", "pessoa"))  # R-CLI-48


def test_la_confirmacion_usa_la_plantilla_del_registro() -> None:
    v = textos.confirmacion("abrir_disputa", "vos", "sobre el cargo de X", "1,00", "COP")
    assert v.startswith("Voy a abrir un reclamo sobre el cargo de X, por 1,00 COP.") and "¿Lo confirmás?" in v
    assert "hablar con una persona" in textos.confirmacion("escalar", "usted", "una persona")


def test_pagina_estatica_accesible_y_sin_scripts_en_linea(entorno: Entorno) -> None:
    cliente, _, _ = entorno
    r = cliente.get("/")
    assert r.status_code == 200
    html = r.text
    assert '<html lang="es">' in html and 'name="viewport"' in html
    assert not re.search(r"<script(?![^>]*\bsrc=)", html)  # ningún script en línea
    assert " onclick=" not in html and "style=" not in html
    assert 'id="persona"' in html and 'role="log"' in html and "<dialog" in html
    assert "script-src 'self'" in r.headers["content-security-policy"]
    for control in re.findall(r'<(?:input|select)[^>]*id="(\w+)"', html):
        assert f'for="{control}"' in html
    js = (WEB / "chat.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js and "eval(" not in js  # solo textContent
    assert cliente.get("/api/estado").json()["clientes"] == ["Cliente 1", "Cliente 2", "Cliente 3"]


def test_cors_permite_el_sitio_y_no_otros_origenes(entorno: Entorno) -> None:
    cliente = entorno[0]
    sitio = "https://latam-bank-hackaton-2026.web.app"
    r = cliente.get("/api/estado", headers={"Origin": sitio})
    assert r.headers.get("access-control-allow-origin") == sitio
    r = cliente.get("/api/estado", headers={"Origin": "https://otro.example"})
    assert "access-control-allow-origin" not in r.headers


def test_sin_comercio_se_describe_por_el_tipo_y_el_estado_va_en_espanol() -> None:
    assert textos.describir_comercio(None, "Transfer") == "Transferencia"
    assert textos.describir_comercio("", "Withdrawal") == "Retiro"
    assert textos.describir_comercio("Tienda Uno", "Purchase") == "Tienda Uno"
    assert textos.describir_comercio(None, "Desconocido") == "Movimiento sin comercio"
    assert textos.estado_transaccion("Approved") == "Aprobada"


def test_modelo_geap_y_llave_de_muerte() -> None:
    proyecto = {"LATAM_GCP_PROJECT": "p"}
    modelo, nombre = crear_modelo(proyecto)
    assert nombre == "geap:gemini-3.1-flash-lite"
    assert modelo.model_name == "gemini-3.1-flash-lite"
    assert crear_modelo({**proyecto, "LATAM_MODELO": "gemini-3.1-flash-lite"})[1].startswith("geap:")
    assert crear_modelo({**proyecto, "LATAM_MODELO": "guionado"})[1] == "guionado"
    assert crear_modelo({**proyecto, "GEMINI_API_KEY": "x"})[1].startswith("gemini:")
    assert crear_modelo({"LATAM_MODELO_PROVEEDOR": "geap", "LATAM_GCP_PROJECT": "p"})[1].startswith("geap:")


# Portugués (CLI-1.5): registro voce de punta a punta


def test_voce_es_un_registro_valido_y_el_catalogo_sale_de_pt_yaml() -> None:
    assert textos.registro_valido("voce") == "voce" and textos.registro_valido("tu") == "usted"
    cat = textos.catalogo_pagina("voce")
    assert cat["idioma"] == "pt" and cat["registro"] == "voce"
    assert "sou a Lia, assistente virtual do LATAM Bank" in cat["textos"]["aviso"]
    assert cat["textos"]["aviso"].count("inteligência artificial") == 1
    assert "alguns minutos" in cat["textos"]["traspaso"]
    assert cat["etiquetas"]["persona"] == "Falar com uma pessoa"
    assert textos.describir_comercio(None, "Withdrawal", "voce") == "Saque"
    assert textos.estado_transaccion("Approved", "voce") == "Aprovada"


def test_la_confirmacion_en_portugues_usa_la_plantilla_y_la_base() -> None:
    objeto = textos.objeto_confirmacion("abrir_disputa", "voce", "Tienda Uno", None)
    v = textos.confirmacion("abrir_disputa", "voce", objeto, "1.234,56", "COP")
    assert v.startswith("Vou abrir uma contestação sobre a cobrança de Tienda Uno, no valor de 1.234,56 COP.")
    assert v.endswith("Você confirma?")
    tarjeta = textos.objeto_confirmacion("bloquear_tarjeta", "voce", None, "4001")
    assert "o cartão com final 4001" in textos.confirmacion("bloquear_tarjeta", "voce", tarjeta)
    assert "pessoa da equipe" in textos.confirmacion(
        "escalar", "voce", textos.objeto_confirmacion("escalar", "voce", None, None)
    )


def test_disputa_en_portugues_con_el_formato_de_la_cuenta(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente, registro="voce")
    e1 = n.decir("Não reconheço uma cobrança")
    assert "Encontrei esta cobrança: Tienda Uno" in _texto(e1)
    assert _ficha(e1)["monto"] == "1.234,56"  # el monto sigue el formato de la cuenta, no el de Brasil
    e2 = n.decir("Não reconheço")
    msg = e2[-1]["outcome"]["interrupts"][0]["message"]
    assert "Vou abrir uma contestação sobre a cobrança de Tienda Uno, no valor de 1.234,56 COP" in msg
    assert demo.banco.llamadas == 0
    e3 = n.resolver(e2, aprobado=True)
    assert "a contestação caso-" in _texto(e3) and "foi registrada" in _texto(e3)
    assert demo.banco.llamadas == 1


def test_rechazo_en_portugues_usa_la_plantilla_sin_cambios(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente, registro="voce")
    n.decir("Não reconheço uma cobrança")
    e3 = n.resolver(n.decir("Não reconheço"), aprobado=False)
    assert demo.banco.llamadas == 0
    assert _texto(e3).strip() == textos.plantilla("cierre.sin_cambios", "voce")


def test_traspaso_en_portugues_lleva_idioma_pt_en_el_paquete(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente, registro="voce")
    r = cliente.post("/api/traspaso", headers=n.h)
    assert r.json()["texto"] == textos.plantilla("traspaso.chat", "voce", rango_espera="alguns minutos")
    t = demo.banco.traspaso_de_conversacion(n.conv)
    assert t is not None
    assert t.paquete.idioma.value == "pt" and t.paquete.registro == "voce"
    assert t.paquete.cola_destino is not None and t.paquete.cola_destino.idioma == "pt"
    assert t.paquete.preferencias["registro"] == "voce"
    assert "alguns minutos" in t.paquete.compromisos_comunicados[0].texto


def test_el_paquete_en_espanol_sigue_en_es(entorno: Entorno) -> None:
    cliente, _, demo = entorno
    n = Navegador(cliente, registro="vos")
    cliente.post("/api/traspaso", headers=n.h)
    t = demo.banco.traspaso_de_conversacion(n.conv)
    assert t is not None and t.paquete.idioma.value == "es" and t.paquete.registro == "vos"


def test_cambiar_de_registro_a_mitad_de_la_conversacion(entorno: Entorno) -> None:
    cliente, _, _ = entorno
    n = Navegador(cliente, registro="usted")
    assert "Encontré este cargo" in _texto(n.decir("No reconozco un cargo"))
    n.h["X-Registro"] = "voce"  # el cliente elige Português en el selector
    e2 = n.decir("Não reconheço")
    assert "Vou abrir uma contestação" in e2[-1]["outcome"]["interrupts"][0]["message"]
    assert cliente.post("/api/traspaso", headers=n.h).json()["texto"].startswith("Já compartilhei")


def test_el_filtro_de_salida_responde_en_el_idioma_del_registro() -> None:
    from latam_tecnologia.canales.frases import falla_de, respaldo_de

    assert respaldo_de("voce").startswith("Vou analisar") and respaldo_de("vos").startswith("Voy a revisar")
    assert falla_de("voce").startswith("Não consegui") and falla_de("usted").startswith("No pude")


def _cliente_con_lectura_caida(registro: str) -> Navegador:
    from google.api_core.exceptions import ServiceUnavailable
    from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
    from pydantic_ai.models.function import AgentInfo

    def modelo(mensajes: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("listar_transacciones", {})])

    demo = _demo(Reloj())

    def caida(*a: object, **k: object) -> None:
        raise ServiceUnavailable("bigquery caido en projects/secreto")

    demo.lectura.transacciones_recientes = caida  # type: ignore[method-assign,assignment]
    app = crear_app(demo=demo, modelo=FunctionModel(modelo))
    n = Navegador(TestClient(app), registro)
    n.historial.append({"id": "u0", "role": "user", "content": "no reconozco un cobro"})
    return n


@pytest.mark.parametrize(
    ("registro", "persona"), [("usted", "hablar con una persona"), ("voce", "falar com uma pessoa")]
)
def test_falla_de_herramienta_en_proceso_dice_la_verdad_y_ofrece_una_persona(
    registro: str, persona: str
) -> None:
    n = _cliente_con_lectura_caida(registro)
    evs = n.correr()
    texto = _texto(evs)
    assert texto.strip() == textos.texto_falla(registro) and persona in texto.lower()
    assert "secreto" not in json.dumps(evs) and evs[-1]["type"] == "RUN_ERROR"
