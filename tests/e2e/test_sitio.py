"""Sitio publico: paginas, navegacion, selector de pais, ayuda, desborde y accesibilidad (axe)."""

from __future__ import annotations

import pytest
from conftest import ANCHOS, URL, axe, desborde

PAGINAS = [
    "/",
    "/productos",
    "/ayuda",
    "/seguridad",
    "/contacto",
    "/reclamos",
    "/transparencia",
    "/privacidad",
    "/chat",
]


@pytest.mark.parametrize("ruta", PAGINAS)
@pytest.mark.parametrize("oscuro", [False, True])
def test_pagina_sin_errores_ni_desborde(abrir, ruta, oscuro):
    for ancho in ANCHOS:
        page, vigia = abrir(ancho, oscuro)
        page.goto(URL + ruta, wait_until="networkidle")
        assert page.locator("h1").count() >= 1
        assert desborde(page) == [], f"{ruta} {ancho}px"
        assert vigia.limpio() == []


@pytest.mark.parametrize("ruta", PAGINAS + ["/banca/", "/banca/reclamos", "/operador/"])
@pytest.mark.parametrize("oscuro", [False, True])
def test_accesibilidad_axe(abrir, axe_js, ruta, oscuro):
    page, _ = abrir(1280, oscuro, bypass_csp=True)
    page.goto(URL + ruta, wait_until="networkidle")
    assert axe(page, axe_js) == []


def test_navegacion_enlaces_internos(abrir):
    page, vigia = abrir()
    page.goto(URL + "/", wait_until="networkidle")
    hrefs = page.eval_on_selector_all("a[href]", "els => [...new Set(els.map(e => e.href))]")
    for h in hrefs:
        if h.startswith(URL):
            r = page.request.get(h)
            assert r.status == 200, h
    assert vigia.limpio() == []


def test_selector_de_pais_persiste(abrir):
    page, _ = abrir()
    page.goto(URL + "/productos", wait_until="networkidle")
    page.select_option("#pais", "CO")
    antes = page.locator("[data-p]").first.text_content()
    page.goto(URL + "/ayuda", wait_until="networkidle")
    assert page.input_value("#pais") == "CO"
    page.reload(wait_until="networkidle")
    assert page.input_value("#pais") == "CO"
    assert page.evaluate("document.documentElement.dataset.pais") == "CO"
    assert antes


def test_ayuda_busqueda(abrir):
    page, _ = abrir()
    page.goto(URL + "/ayuda", wait_until="networkidle")
    total = page.locator(".faq").count()
    page.fill("#buscar", "tarjeta")
    visibles = page.locator(".faq:not(.oculto)").count()
    assert 0 < visibles <= total
    assert "encontrad" in page.text_content("#resultado")
    page.fill("#buscar", "zzzzqqq")
    assert page.locator("#sin-resultados:not(.oculto)").count() == 1
    assert page.locator(".faq:not(.oculto)").count() == 0
    page.fill("#buscar", "")
    assert page.locator(".faq:not(.oculto)").count() == total


def _esperar_trato(page, trato: str) -> None:
    page.wait_for_function(f"document.documentElement.dataset.trato === '{trato}'")


def test_brasil_pone_todo_el_sitio_en_portugues(abrir):
    """El país es la única elección: Brasil cambia el idioma en el sitio público y en la banca."""
    page, vigia = abrir()
    page.goto(URL + "/", wait_until="networkidle")
    assert page.evaluate("document.documentElement.lang") == "es"
    assert page.locator("#idioma").count() == 0  # ya no hay un selector de idioma aparte
    page.select_option("#pais", "BR")
    _esperar_trato(page, "voce")
    assert page.evaluate("document.documentElement.lang") == "pt-BR"
    assert "Se você não reconhece uma cobrança" in page.locator("h1").inner_text()
    page.goto(URL + "/productos", wait_until="networkidle")
    assert page.evaluate("document.documentElement.lang") == "pt-BR"
    assert page.input_value("#pais") == "BR"
    assert page.title() == "Produtos, LATAM Bank"
    page.goto(URL + "/banca/", wait_until="networkidle")
    assert page.evaluate("document.documentElement.lang") == "pt-BR"
    assert page.input_value("#pais") == "BR"
    page.goto(URL + "/privacidad", wait_until="networkidle")
    assert page.title() == "Aviso de privacidade, LATAM Bank"
    assert vigia.limpio() == []


def test_cada_pais_fija_su_idioma_y_trato(abrir):
    page, _ = abrir()
    page.goto(URL + "/", wait_until="networkidle")
    assert page.evaluate("document.documentElement.dataset.trato") == "usted"
    page.select_option("#pais", "AR")
    _esperar_trato(page, "vos")
    assert page.evaluate("document.documentElement.lang") == "es"
    assert "Si no reconocés un cargo" in page.locator("h1").inner_text()
    page.select_option("#pais", "CO")
    _esperar_trato(page, "usted")
    page.goto(URL + "/ayuda", wait_until="networkidle")
    assert page.evaluate("document.documentElement.dataset.trato") == "usted"
    assert page.input_value("#pais") == "CO"
