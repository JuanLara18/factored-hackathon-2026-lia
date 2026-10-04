"""E2E con navegador real contra produccion. Se omite salvo LATAM_E2E=1.

Uso: LATAM_E2E=1 uv run --with playwright pytest tests/e2e -x -q
Variables: LATAM_E2E_URL (por defecto el arbol local en :5000; pon la URL de produccion para probar lo desplegado), LATAM_E2E_OPERADOR (codigo del experto; con el, el estado de demostracion se restablece antes y despues), LATAM_E2E_API (backend, por defecto el de produccion), LATAM_E2E_HEADED=1.
Las pruebas con LLM real (marca `llm`) gastan conversaciones: se excluyen con -m "not llm".
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

ACTIVO = os.environ.get("LATAM_E2E") == "1"
collect_ignore_glob = [] if ACTIVO else ["test_*.py"]

PRODUCCION = "https://latam-bank-hackaton-2026.web.app"
# Por defecto se sirve el arbol de trabajo en http://localhost:5000 (origen permitido por el CORS del backend de produccion).
URL = os.environ.get("LATAM_E2E_URL", "http://localhost:5000").rstrip("/")
CODIGO_OPERADOR = os.environ.get("LATAM_E2E_OPERADOR", "")
API = os.environ.get("LATAM_E2E_API", "https://latam-chat-47808508188.us-central1.run.app").rstrip("/")
ANCHOS = (390, 768, 1280)
AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "llm: usa el modelo real (gasta conversaciones)")


class Vigia:
    """Junta errores de consola, excepciones, peticiones fallidas y violaciones de CSP de una pagina."""

    def __init__(self, page) -> None:
        self.problemas: list[str] = []
        page.on(
            "console",
            lambda m: (
                self.problemas.append(f"console.{m.type}: {m.text}")
                if m.type in ("error", "warning")
                else None
            ),
        )
        page.on("pageerror", lambda e: self.problemas.append(f"pageerror: {e}"))
        page.on("requestfailed", lambda r: self.problemas.append(f"requestfailed: {r.url} {r.failure}"))
        page.on(
            "response",
            lambda r: self.problemas.append(f"http {r.status}: {r.url}") if r.status >= 400 else None,
        )

    def limpio(self, tolerar: tuple[str, ...] = ()) -> list[str]:
        return [p for p in self.problemas if not any(t in p for t in tolerar)]


def restablecer_demo() -> bool:
    """POST /api/demo/restablecer con el codigo del experto; sin LATAM_E2E_OPERADOR no hace nada."""
    if not CODIGO_OPERADOR:
        return False
    peticion = urllib.request.Request(  # noqa: S310
        API + "/api/demo/restablecer",
        data=json.dumps({"codigo": CODIGO_OPERADOR}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=60) as r:  # noqa: S310
            return r.status == 200
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"aviso: no se pudo restablecer la demo ({type(error).__name__})", file=sys.stderr)
        return False


@pytest.fixture(scope="session", autouse=True)
def demo_limpia():
    """Estado de demostracion limpio al empezar y al terminar la suite, para no ensuciar produccion."""
    restablecer_demo()
    yield
    restablecer_demo()


@pytest.fixture
def limpia_estado():
    """Para pruebas que bloquean tarjetas o abren reclamos: restablece al terminar."""
    yield
    restablecer_demo()


@pytest.fixture(scope="session", autouse=True)
def sitio_local():
    if URL.startswith("http://localhost:5000"):
        import servidor

        srv = servidor.arrancar(5000)
        yield
        srv.shutdown()
    else:
        yield


@pytest.fixture(scope="session")
def navegador():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(headless=os.environ.get("LATAM_E2E_HEADED") != "1")
        yield b
        b.close()


@pytest.fixture
def abrir(navegador):
    """Fabrica de paginas (contexto nuevo cada una): abrir(ancho=1280, oscuro=False) -> (page, vigia)."""
    contextos = []

    def _abrir(ancho: int = 1280, oscuro: bool = False, bypass_csp: bool = False):
        ctx = navegador.new_context(
            viewport={"width": ancho, "height": 900 if ancho > 500 else 800},
            color_scheme="dark" if oscuro else "light",
            locale="es-CO",
            bypass_csp=bypass_csp,
        )
        contextos.append(ctx)
        page = ctx.new_page()
        page.set_default_timeout(20000)
        return page, Vigia(page)

    yield _abrir
    for c in contextos:
        c.close()


@pytest.fixture(scope="session")
def axe_js() -> str:
    with urllib.request.urlopen(AXE_URL, timeout=30) as r:  # noqa: S310
        return r.read().decode()


def desborde(page) -> list[str]:
    """Elementos que se salen del ancho de la ventana (desborde horizontal)."""
    return page.evaluate(
        """() => {
          const w = document.documentElement.clientWidth, malos = [];
          if (document.documentElement.scrollWidth > w + 1) malos.push('pagina scrollWidth=' + document.documentElement.scrollWidth);
          const dentroDeScroll = (e) => { for (let a = e.parentElement; a && a !== document.body; a = a.parentElement) { const o = getComputedStyle(a).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
          for (const e of document.querySelectorAll('body *')) {
            const r = e.getBoundingClientRect();
            if (r.width && r.right > w + 2 && !e.closest('.oculto, [hidden], dialog:not([open])') && !dentroDeScroll(e)) {
              const cs = getComputedStyle(e);
              if (cs.position !== 'fixed' && cs.visibility !== 'hidden') malos.push(e.tagName + '.' + e.className + ' right=' + Math.round(r.right));
            }
          }
          return malos.slice(0, 8);
        }"""
    )


def axe(page, axe_source: str) -> list[str]:
    page.evaluate(axe_source)
    r = page.evaluate(
        "async () => (await axe.run(document, {runOnly: ['wcag2a','wcag2aa','wcag21aa']})).violations.map(v => v.id + ': ' + v.nodes.slice(0,3).map(n => n.target.join(' ')).join(' | '))"
    )
    return r
