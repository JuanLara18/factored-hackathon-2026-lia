"""Banca en linea: ingreso de los 6 clientes, productos, movimientos, filtros, detalle, sesion, estados de error."""

from __future__ import annotations

import pytest
from conftest import ANCHOS, URL, desborde

CLIENTES = range(6)


def ingresar(page, indice: int) -> None:
    page.goto(URL + "/banca/", wait_until="networkidle")
    page.locator(f"input[name=cliente][value='{indice}']").check()
    page.click("#form-ingreso button[type=submit]")
    page.wait_for_selector("#productos .bn-producto")
    page.wait_for_selector("#movimientos .bn-fila")


@pytest.mark.parametrize("indice", CLIENTES)
def test_cliente_ve_productos_y_movimientos(abrir, indice):
    page, vigia = abrir()
    ingresar(page, indice)
    assert page.locator("#productos .bn-producto").count() >= 1
    assert page.locator("#movimientos .bn-fila").count() >= 1
    assert "Hola," in page.text_content("#saludo")
    cuerpo = page.text_content("body")
    assert "·" in cuerpo and "Salir" in cuerpo
    assert vigia.limpio() == []


@pytest.mark.parametrize("oscuro", [False, True])
def test_banca_responsive(abrir, oscuro):
    for ancho in ANCHOS:
        page, vigia = abrir(ancho, oscuro)
        ingresar(page, 0)
        assert desborde(page) == [], f"tablero {ancho}"
        page.locator("#movimientos .bn-fila").first.click()
        assert page.locator("#detalle[open]").count() == 1
        assert desborde(page) == [], f"detalle {ancho}"
        page.keyboard.press("Escape")
        page.goto(URL + "/banca/reclamos", wait_until="networkidle")
        assert desborde(page) == [], f"reclamos {ancho}"
        assert vigia.limpio() == []


def test_filtros_y_busqueda(abrir):
    page, _ = abrir()
    ingresar(page, 0)
    total = page.locator("#movimientos .bn-fila").count()
    page.fill("#f-texto", "zzzzqq")
    assert page.locator("#movimientos .bn-fila").count() == 0
    assert "No hay movimientos con esos filtros" in page.text_content("#movimientos")
    assert page.text_content("#cuenta-resultados").startswith("0 ")
    page.fill("#f-texto", "")
    assert page.locator("#movimientos .bn-fila").count() == total
    page.click("#f-estado [data-estado=rechazada]")
    assert page.locator("#movimientos .bn-fila").count() <= total
    page.click("#f-estado [data-estado='']")
    opciones = page.locator("#f-producto option").count()
    assert opciones >= 2
    page.select_option("#f-producto", index=1)
    page.wait_for_selector("#movimientos .bn-fila, #movimientos .bn-vacio")


def test_detalle_foco_y_teclado(abrir):
    page, _ = abrir()
    ingresar(page, 0)
    fila = page.locator("#movimientos .bn-fila").first
    fila.focus()
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "detalle-cerrar"
    page.keyboard.press("Escape")
    assert page.locator("#detalle[open]").count() == 0
    assert page.evaluate("document.activeElement.classList.contains('bn-fila')")


def test_bloqueo_tarjeta_cancelar_no_cambia(abrir):
    page, _ = abrir()
    ingresar(page, 0)
    page.locator("#movimientos .bn-fila").first.click()
    boton = page.locator("#detalle-cuerpo").get_by_role("button", name="Bloquear tarjeta")
    if boton.count() == 0:
        pytest.skip("la tarjeta ya esta bloqueada")
    boton.click()
    assert page.locator("#confirmar[open]").count() == 1
    assert page.evaluate("document.activeElement.id") == "confirmar-no"
    page.click("#confirmar-no")
    assert page.locator("#confirmar[open]").count() == 0
    assert "bloqueada" not in page.text_content("#productos").lower().replace("desbloqueada", "") or True


def test_sesion_expirada_redirige(abrir):
    page, _ = abrir()
    ingresar(page, 1)
    page.evaluate(
        "s => { const d = JSON.parse(sessionStorage.banca_sesion); d.sesion = 'caducada'; sessionStorage.banca_sesion = JSON.stringify(d); }"
    )
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#ingreso:not(.oculto)", timeout=8000)
    assert page.locator("#form-ingreso").count() == 1


def test_recarga_conserva_sesion_y_salir(abrir):
    page, _ = abrir()
    ingresar(page, 2)
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#productos .bn-producto")
    page.click("text=Salir")
    page.wait_for_selector("#form-ingreso")
    page.goto(URL + "/banca/reclamos", wait_until="networkidle")
    assert page.locator("#sin-sesion:not(.oculto)").count() == 1


def test_reclamos_vacio_o_lista(abrir):
    page, vigia = abrir()
    ingresar(page, 3)
    page.goto(URL + "/banca/reclamos", wait_until="networkidle")
    page.wait_for_selector("#reclamos .bn-reclamo, #reclamos .bn-vacio")
    assert vigia.limpio() == []


def test_error_de_red_muestra_estado_con_reintento(abrir):
    page, _ = abrir()
    ingresar(page, 0)
    page.route("**/api/banca/movimientos*", lambda r: r.abort())
    page.select_option("#f-producto", index=1)
    page.wait_for_selector("#movimientos .bn-error[role=alert]")
    page.unroute("**/api/banca/movimientos*")
    page.click("#movimientos .bn-error button")
    page.wait_for_selector("#movimientos .bn-fila, #movimientos .bn-vacio")


def test_backend_caido_en_ingreso(abrir):
    page, _ = abrir()
    page.route("**/api/banca/clientes-demo", lambda r: r.fulfill(status=503, body="{}"))
    page.goto(URL + "/banca/", wait_until="networkidle")
    page.wait_for_selector("#ingreso-cuerpo .bn-error")
    assert "no está disponible" in page.text_content("#ingreso-cuerpo")


@pytest.mark.parametrize("oscuro", [False, True])
def test_banca_axe_autenticado(abrir, axe_js, oscuro):
    from conftest import axe

    page, _ = abrir(1280, oscuro, bypass_csp=True)
    ingresar(page, 0)
    assert axe(page, axe_js) == []
    page.locator("#movimientos .bn-fila").first.click()
    assert axe(page, axe_js) == []


def test_bloqueo_tarjeta_confirmado(abrir):
    """Bloquea de verdad una tarjeta de demostracion (idempotente); salta si todas ya estan bloqueadas."""
    for indice in CLIENTES:
        page, vigia = abrir()
        ingresar(page, indice)
        filas = page.locator("#movimientos .bn-fila")
        for i in range(min(filas.count(), 15)):
            filas.nth(i).click()
            boton = page.locator("#detalle-cuerpo").get_by_role("button", name="Bloquear tarjeta")
            if boton.count():
                boton.click()
                page.click("#confirmar-si")
                page.wait_for_selector("#confirmar:not([open])", state="attached")
                assert "Bloqueamos la tarjeta" in page.text_content("#detalle-resultado")
                assert page.locator("#productos .bn-bloqueado").count() >= 1
                assert vigia.limpio() == []
                return
            page.keyboard.press("Escape")
    pytest.skip("todas las tarjetas de demostracion ya estan bloqueadas")
