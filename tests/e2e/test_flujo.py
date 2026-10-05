"""Flujo completo con el modelo real (una conversacion): reclamo, aprobacion, caso, persona, experto, resolucion.

Necesita LATAM_E2E_OPERADOR. Crea datos reales en Firestore de produccion (un caso y un traspaso de demostracion).
"""

from __future__ import annotations

import uuid

import pytest
from conftest import ANCHOS, CODIGO_OPERADOR, URL, axe, desborde
from playwright.sync_api import expect
from test_banca import ingresar


def _fila_reclamable(page):
    filas = page.locator("#movimientos .bn-fila")
    for i in range(min(filas.count(), 12)):
        f = filas.nth(i)
        if "Con reclamo" in (f.text_content() or ""):
            continue
        f.click()
        if page.get_by_role("button", name="No reconozco este cargo").count():
            return f
        page.keyboard.press("Escape")
    return None


@pytest.mark.llm
@pytest.mark.usefixtures("limpia_estado")
def test_reclamo_persona_experto_resolucion(abrir):
    if not CODIGO_OPERADOR:
        pytest.skip("falta LATAM_E2E_OPERADOR")
    cliente, v_cli = abrir(390)
    ingresar(cliente, 0)
    assert _fila_reclamable(cliente) is not None, "no hay movimiento reclamable sin caso"
    cliente.get_by_role("button", name="No reconozco este cargo").click()
    cliente.wait_for_selector("#asistente-panel:not(.oculto)")
    assert cliente.locator(".bw-ia").is_visible()  # aviso de IA fijo
    # ficha de la transaccion y aprobacion
    _esperar(cliente, ".bw-ficha", reintento="No reconozco este cargo")
    assert cliente.locator(".bw-ficha dd").filter(has_text="····").count() == 1
    cliente.locator(".bw-ficha button").last.click()  # "No la reconozco"
    _esperar(cliente, "#aprobacion[open]", reintento="Sí, bloquee la tarjeta y abra el reclamo")
    assert cliente.evaluate("document.activeElement.id") != "body"
    assert "vence en" in cliente.text_content("#ap-vence").lower()
    cliente.click("#aprobacion .primario")
    cliente.wait_for_selector("#asistente-log .bw-msg.asistente:nth-last-child(1)", timeout=120000)
    expect(cliente.locator(".bw-estado")).to_have_text("", timeout=120000)
    # Mis reclamos
    cliente.goto(URL + "/banca/reclamos", wait_until="networkidle")
    cliente.wait_for_selector("#reclamos .bn-reclamo")
    assert cliente.locator("#reclamos .bn-reclamo").count() >= 1
    # volver al tablero y pedir una persona
    cliente.goto(URL + "/banca", wait_until="networkidle")
    cliente.wait_for_selector("#movimientos .bn-fila")
    cliente.click("#asistente-lanzador")
    cliente.click(".bw-persona")
    cliente.wait_for_selector("text=Esperando a una persona")
    # experto
    experto, v_exp = abrir(1280)
    experto.goto(URL + "/operador", wait_until="networkidle")
    experto.fill("#op-codigo", CODIGO_OPERADOR)
    experto.press("#op-codigo", "Enter")
    experto.wait_for_selector("#op-lista .op-item-boton")
    # el traspaso mas reciente (menor tiempo en cola)
    items = experto.locator("#op-lista .op-item-boton")
    experto.locator("#op-lista .op-item-boton").first.focus()
    experto.keyboard.press("ArrowDown")
    assert experto.evaluate("document.activeElement.classList.contains('op-item-boton')")
    mejor, menor = 0, 10**9
    for i in range(items.count()):
        t = items.nth(i).locator(".op-sla").text_content() or ""
        seg = _segundos(t)
        if seg < menor:
            mejor, menor = i, seg
    items.nth(mejor).click()
    experto.wait_for_selector("#op-tomar")
    assert experto.evaluate("document.activeElement.id") == "op-caso-titulo"
    experto.click("#op-tomar")
    experto.wait_for_selector("#op-texto")
    marca = "QA-" + uuid.uuid4().hex[:6]
    experto.fill("#op-texto", f"Hola, soy del equipo. Revisando su caso {marca}")
    experto.click("#op-form-msg button")
    experto.wait_for_selector(f"#op-mensajes >> text={marca}")
    # el cliente lo ve en su widget (sondeo de 4 s)
    cliente.wait_for_selector(f"#asistente-log >> text={marca}", timeout=30000)
    # resolver
    experto.select_option("#op-resultado", "resuelto")
    experto.fill("#op-nota", "Prueba automatica de QA")
    experto.click("#op-form-resolver button[type=submit]")
    experto.wait_for_selector("text=Caso resuelto")
    assert v_cli.limpio(tolerar=("status of 409",)) == []
    assert v_exp.limpio() == []


def _esperar(page, selector: str, reintento: str, intentos: int = 3) -> None:
    """El modelo a veces falla un turno (llamada malformada): el widget muestra el aviso y se reintenta escribiendo."""
    for i in range(intentos):
        try:
            page.wait_for_selector(selector, timeout=60000)
            return
        except Exception:
            if i == intentos - 1 or not page.locator(".bw-msg.error").count():
                raise AssertionError(
                    f"{selector} no aparecio; registro: {page.inner_text('#asistente-log')!r} estado: {page.inner_text('.bw-estado')!r}"
                ) from None
            expect(page.locator(".bw-estado")).to_have_text("")
            page.fill("#asistente-mensaje", reintento)
            page.press("#asistente-mensaje", "Enter")


def _segundos(texto: str) -> int:
    try:
        parte = texto.split("En cola ")[1].split(" ")[0]
        n = [int(x) for x in parte.split(":")]
        return sum(v * 60**i for i, v in enumerate(reversed(n)))
    except (IndexError, ValueError):
        return 10**9


def test_operador_teclado_y_errores(abrir):
    if not CODIGO_OPERADOR:
        pytest.skip("falta LATAM_E2E_OPERADOR")
    page, vigia = abrir(1280)
    page.goto(URL + "/operador", wait_until="networkidle")
    assert page.evaluate("document.activeElement.id") == "op-codigo"
    page.fill("#op-codigo", "incorrecto")
    page.press("#op-codigo", "Enter")
    page.wait_for_selector("#op-error-ingreso:not(:empty)")
    assert "código" in page.text_content("#op-error-ingreso").lower()
    page.fill("#op-codigo", CODIGO_OPERADOR)
    page.press("#op-codigo", "Enter")
    page.wait_for_selector("#op-app:not(.oculto)")
    # Tab llega a la cola; flechas, Home y End mueven el foco
    page.wait_for_selector("#op-lista .op-item-boton, .op-vacio-cola")
    if page.locator("#op-lista .op-item-boton").count() > 1:
        page.locator("#op-lista .op-item-boton").first.focus()
        page.keyboard.press("End")
        ultimo = page.evaluate(
            "[...document.querySelectorAll('.op-item-boton')].indexOf(document.activeElement)"
        )
        assert ultimo == page.locator("#op-lista .op-item-boton").count() - 1
        page.keyboard.press("Home")
        assert (
            page.evaluate("[...document.querySelectorAll('.op-item-boton')].indexOf(document.activeElement)")
            == 0
        )
    # sesion vencida a mitad de camino: vuelve al ingreso con aviso
    page.route("**/api/operador/cola", lambda r: r.fulfill(status=401, body="{}"))
    page.click("#op-refrescar")
    page.wait_for_selector("#op-ingreso:not(.oculto)")
    assert "venció" in page.text_content("#op-error-ingreso")
    assert page.evaluate("document.activeElement.id") == "op-codigo"
    assert vigia.limpio(tolerar=("401", "incorrecto")) == []


@pytest.mark.parametrize("oscuro", [False, True])
def test_widget_abierto_axe_y_teclado(abrir, axe_js, oscuro):
    page, vigia = abrir(1280, oscuro, bypass_csp=True)
    ingresar(page, 1)
    page.click("#asistente-lanzador")
    page.wait_for_selector("#asistente-panel:not(.oculto)")
    page.wait_for_selector("#asistente-log .bw-msg")
    assert page.evaluate("document.activeElement.id") == "asistente-titulo"
    assert axe(page, axe_js) == []
    page.keyboard.press("Escape")
    assert page.locator("#asistente-panel.oculto").count() == 1
    assert page.evaluate("document.activeElement.id") == "asistente-lanzador"
    assert vigia.limpio() == []


def test_asistente_conversa_sin_abrir_un_movimiento(abrir):
    """Desde el botón flotante, sin movimiento abierto, el asistente responde (antes era un callejón sin salida)."""
    page, _ = abrir(1280)
    ingresar(page, 2)
    page.click("#asistente-lanzador")
    page.wait_for_selector(".bw-sugerida")
    antes = page.locator("#asistente-log .bw-msg.asistente").count()
    page.fill("#asistente-mensaje", "Hola, ¿en qué me puede ayudar?")
    page.press("#asistente-mensaje", "Enter")
    expect(page.locator(".bw-estado")).to_have_text("", timeout=120000)
    assert page.locator("#asistente-log .bw-msg.asistente").count() > antes
    assert page.locator(".bw-msg.error").count() == 0
    assert "Abra un movimiento" not in page.inner_text("#asistente-log")


def test_widget_movil_sin_desborde(abrir):
    for ancho in (390, 768):
        page, _ = abrir(ancho)
        ingresar(page, 1)
        page.click("#asistente-lanzador")
        page.wait_for_selector("#asistente-log .bw-msg")
        assert desborde(page) == [], ancho


@pytest.mark.parametrize("oscuro", [False, True])
def test_operador_axe_y_responsive(abrir, axe_js, oscuro):
    if not CODIGO_OPERADOR:
        pytest.skip("falta LATAM_E2E_OPERADOR")
    for ancho in ANCHOS:
        page, vigia = abrir(ancho, oscuro, bypass_csp=ancho == 1280)
        page.goto(URL + "/operador", wait_until="networkidle")
        assert desborde(page) == [], f"ingreso {ancho}"
        page.fill("#op-codigo", CODIGO_OPERADOR)
        page.press("#op-codigo", "Enter")
        page.wait_for_selector("#op-lista .op-item-boton, .op-vacio-cola")
        if page.locator("#op-lista .op-item-boton").count():
            page.locator("#op-lista .op-item-boton").first.click()
            page.wait_for_selector("#op-caso:not(.oculto) h2")
        assert desborde(page) == [], f"consola {ancho}"
        if ancho == 1280:
            assert axe(page, axe_js) == []
        else:
            assert vigia.limpio() == []
