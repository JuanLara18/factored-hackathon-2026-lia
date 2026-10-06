"""Graba el producto real en producción para el video de la entrega. Deja webm y marcas de tiempo."""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://latam-bank-hackaton-2026.web.app"
API = "https://latam-chat-47808508188.us-central1.run.app"
COD = os.environ["LATAM_E2E_OPERADOR"]
AQUI = Path(__file__).parent
TAM = {"width": 1600, "height": 900}
marcas: dict[str, dict[str, float]] = {}


def restablecer():
    req = urllib.request.Request(
        API + "/api/demo/restablecer", data=json.dumps({"codigo": COD}).encode(), method="POST", headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=60).read()


class Reloj:
    def __init__(self, nombre):
        self.t0 = time.time()
        self.nombre = nombre
        marcas[nombre] = {}

    def marca(self, etiqueta):
        marcas[self.nombre][etiqueta] = round(time.time() - self.t0, 2)
        print(self.nombre, etiqueta, marcas[self.nombre][etiqueta], flush=True)


def ingresar(page, indice):
    page.goto(URL + "/banca/", wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.locator(f"input[name=cliente][value='{indice}']").check()
    page.wait_for_timeout(700)
    page.click("#form-ingreso button[type=submit]")
    page.wait_for_selector("#productos .bn-producto")
    page.wait_for_selector("#movimientos .bn-fila")


def abrir_reclamable(page):
    filas = page.locator("#movimientos .bn-fila")
    for i in range(min(filas.count(), 12)):
        filas.nth(i).scroll_into_view_if_needed()
        filas.nth(i).click()
        page.wait_for_timeout(900)
        boton = page.get_by_role("button", name="No reconozco este cargo")
        if boton.count() and boton.first.is_visible():
            page.wait_for_timeout(900)
            boton.first.click()
            return True
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    return False


def decir(page, texto):
    antes = page.locator("#asistente-log .bw-msg.asistente").count()
    page.click("#asistente-mensaje")
    page.type("#asistente-mensaje", texto, delay=28)
    page.wait_for_timeout(400)
    page.press("#asistente-mensaje", "Enter")
    return antes


def esperar_respuesta(page, antes, tope=120000):
    page.wait_for_function(
        "n => document.querySelectorAll('#asistente-log .bw-msg.asistente').length > n && !(document.querySelector('.bw-estado') || {textContent: ''}).textContent.trim()",
        arg=antes,
        timeout=tope,
    )


with sync_playwright() as p:
    nav = p.chromium.launch(headless=True)
    restablecer()

    # ---- cliente (Colombia)
    ctx = nav.new_context(viewport=TAM, record_video_dir=str(AQUI / "crudo_cliente"), record_video_size=TAM, locale="es-CO")
    cliente = ctx.new_page()
    r = Reloj("cliente")
    ingresar(cliente, 2)
    r.marca("banca_lista")
    cliente.wait_for_timeout(2500)
    assert abrir_reclamable(cliente), "sin movimiento reclamable"
    cliente.wait_for_selector("#asistente-panel:not(.oculto)")
    r.marca("asistente_abierto")
    cliente.wait_for_timeout(1500)
    try:
        cliente.locator(".bw-ficha button").last.click(timeout=20000)
    except Exception:
        decir(cliente, "No reconozco este cargo, yo no compré ahí")
    try:
        cliente.wait_for_selector("#aprobacion[open]", timeout=90000)
    except Exception:
        decir(cliente, "Sí, abra el reclamo")
        cliente.wait_for_selector("#aprobacion[open]", timeout=90000)
    r.marca("aprobacion_visible")
    cliente.wait_for_timeout(3500)
    antes = cliente.locator("#asistente-log .bw-msg.asistente").count()
    cliente.click("#aprobacion .primario")
    r.marca("aprobado")
    esperar_respuesta(cliente, antes)
    r.marca("reclamo_abierto")
    cliente.wait_for_timeout(5000)

    antes = decir(cliente, "Una duda: ¿el banco me abona algo mientras revisa el reclamo?")
    r.marca("pregunta_politica")
    esperar_respuesta(cliente, antes)
    r.marca("respuesta_politica")
    cliente.wait_for_timeout(6500)

    antes = decir(cliente, "¿Y me pueden subir el cupo de la tarjeta?")
    r.marca("pregunta_cupo")
    esperar_respuesta(cliente, antes)
    r.marca("respuesta_cupo")
    cliente.wait_for_timeout(4500)

    cliente.click(".bw-persona")
    r.marca("pide_persona")
    cliente.wait_for_selector("text=Esperando a una persona", timeout=60000)
    r.marca("esperando_persona")
    cliente.wait_for_timeout(2500)

    # ---- experto
    ctx2 = nav.new_context(viewport=TAM, record_video_dir=str(AQUI / "crudo_experto"), record_video_size=TAM, locale="es-CO")
    experto = ctx2.new_page()
    e = Reloj("experto")
    experto.goto(URL + "/operador", wait_until="networkidle")
    experto.fill("#op-codigo", COD)
    experto.press("#op-codigo", "Enter")
    experto.wait_for_selector("#op-lista .op-item-boton")
    e.marca("cola")
    experto.wait_for_timeout(2000)
    experto.locator("#op-lista .op-item-boton").first.click()
    experto.wait_for_selector("#op-tomar")
    e.marca("paquete")
    experto.wait_for_timeout(1500)
    for _ in range(4):
        experto.mouse.wheel(0, 420)
        experto.wait_for_timeout(1100)
    experto.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    experto.wait_for_timeout(1200)
    experto.click("#op-tomar")
    experto.wait_for_selector("#op-texto")
    e.marca("tomado")
    experto.locator("#op-sugerir").scroll_into_view_if_needed()
    experto.wait_for_timeout(1200)
    experto.click("#op-sugerir")
    e.marca("pide_borrador")
    experto.wait_for_selector("#op-borrador h5", timeout=60000)
    e.marca("borrador")
    experto.wait_for_timeout(5500)
    experto.click("#op-form-msg button[type=submit]")
    e.marca("enviado")
    experto.wait_for_timeout(3000)
    r.marca("mensaje_del_experto_enviado")
    cliente.wait_for_timeout(6000)
    r.marca("fin")
    ctx2.close()
    ctx.close()

    # ---- portugués (cliente de Argentina, conversación en portugués)
    ctx3 = nav.new_context(viewport=TAM, record_video_dir=str(AQUI / "crudo_pt"), record_video_size=TAM, locale="pt-BR")
    pt = ctx3.new_page()
    q = Reloj("pt")
    ingresar(pt, 4)
    q.marca("banca_lista")
    pt.wait_for_timeout(1500)
    pt.click("#asistente-lanzador")
    pt.wait_for_selector("#asistente-panel:not(.oculto)")
    pt.wait_for_timeout(1500)
    antes = decir(pt, "Olá, não reconheço uma cobrança no meu cartão. Pode me ajudar?")
    q.marca("pregunta")
    esperar_respuesta(pt, antes)
    q.marca("respuesta")
    pt.wait_for_timeout(6000)
    q.marca("fin")
    ctx3.close()
    nav.close()

restablecer()
(AQUI / "marcas.json").write_text(json.dumps(marcas, indent=1), encoding="utf-8")
print("listo", file=sys.stderr)
