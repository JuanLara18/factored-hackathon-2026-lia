"""Sitio público de LATAM Bank (tecnologia/web/sitio): estructura mínima, enlaces y lenguaje permitido."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from latam_clientes.contenido import cargar_estilo, frases_prohibidas

RAIZ = Path(__file__).resolve().parents[1]
SITIO = RAIZ / "tecnologia" / "web" / "sitio"
PAGINAS = sorted(SITIO.glob("*.html"))


class _Pagina(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = ""
        self.titulo = False
        self.h1 = 0
        self.viewport = False
        self.enlaces: list[str] = []
        self.recursos: list[str] = []
        self.script_en_linea = False
        self.estilo_en_linea = False
        self._en_script = False
        self._pila: list[str] = []
        self.texto: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "style" in a:
            self.estilo_en_linea = True
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self.titulo = True
        elif tag == "h1":
            self.h1 += 1
        elif tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        elif tag == "a" and "href" in a:
            self.enlaces.append(a["href"])
        elif tag == "link" and "href" in a:
            self.recursos.append(a["href"])
        elif tag == "script":
            if "src" in a:
                self.recursos.append(a["src"])
            self._en_script = "src" not in a
        elif tag == "style":
            self.estilo_en_linea = True
        self._pila.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._en_script = False
        if self._pila:
            self._pila.pop()

    def handle_data(self, data: str) -> None:
        if self._en_script and data.strip():
            self.script_en_linea = True
        elif not self._en_script:
            self.texto.append(data)


def _leer(p: Path) -> _Pagina:
    parser = _Pagina()
    parser.feed(p.read_text(encoding="utf-8"))
    return parser


def test_hay_paginas() -> None:
    nombres = {p.name for p in PAGINAS}
    assert {
        "index.html",
        "reclamos.html",
        "transparencia.html",
        "privacidad.html",
        "chat.html",
        "productos.html",
        "ayuda.html",
        "seguridad.html",
        "contacto.html",
    } <= nombres


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_estructura_minima(pagina: Path) -> None:
    p = _leer(pagina)
    assert p.lang == "es"
    assert p.titulo and p.viewport
    assert p.h1 == 1
    # La CSP del hosting no permite código ni estilos en línea.
    assert not p.script_en_linea
    assert not p.estilo_en_linea


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_enlaces_internos_existen(pagina: Path) -> None:
    p = _leer(pagina)
    for ref in p.enlaces + p.recursos:
        if re.match(r"^(https?:|mailto:|#)", ref):
            continue
        if ref.startswith("banca/"):
            continue  # la banca en línea la publica otra rama; se verifica en test_banca
        destino = (SITIO / ref.split("#")[0]).resolve()
        assert destino.is_file(), f"{pagina.name}: {ref} no existe"


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_textos_sin_frases_prohibidas(pagina: Path) -> None:
    texto = " ".join(_leer(pagina).texto)
    patrones = frases_prohibidas(cargar_estilo(), "plantilla")
    assert [f.pattern for f in patrones if f.search(texto)] == []


def test_firebase_publica_el_sitio_con_cabeceras_de_seguridad() -> None:
    config = json.loads((RAIZ / "firebase.json").read_text(encoding="utf-8"))
    hosting = config["hosting"]
    assert hosting["public"] == "tecnologia/web/sitio"
    cabeceras = {h["key"]: h["value"] for bloque in hosting["headers"] for h in bloque["headers"]}
    assert "unsafe-inline" not in cabeceras["Content-Security-Policy"]
    assert cabeceras["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_cabecera_comun_con_banca_y_pais(pagina: Path) -> None:
    p = _leer(pagina)
    assert "banca/index.html" in p.enlaces
    assert "assets/pais.js" in p.recursos
    html = pagina.read_text(encoding="utf-8")
    assert 'id="pais"' in html
    assert "banco ficticio" in html


def test_selector_de_pais_recuerda_con_localstorage_protegido() -> None:
    js = (SITIO / "assets" / "pais.js").read_text(encoding="utf-8")
    assert "localStorage" in js
    assert js.count("try {") >= 2
    for pais in ("MX", "CO", "AR"):
        assert pais in js


def test_ayuda_tiene_buscador_y_preguntas_clave() -> None:
    html = (SITIO / "ayuda.html").read_text(encoding="utf-8")
    assert 'id="buscar"' in html
    assert html.count('class="faq"') >= 8
    assert "bloqueo" in html.lower() or "bloqueo mi tarjeta" in html.lower()


def test_chat_apunta_a_banca_en_linea() -> None:
    html = (SITIO / "chat.html").read_text(encoding="utf-8")
    # la portada del chat invita a abrir el movimiento desde la banca
    assert '<a href="banca/index.html">Ábralo en Banca en línea</a>' in html


BANCA = sorted((SITIO / "banca").glob("*.html"))


def test_hay_paginas_de_banca() -> None:
    assert {"index.html", "reclamos.html"} <= {p.name for p in BANCA}


@pytest.mark.parametrize("pagina", BANCA, ids=lambda p: f"banca/{p.name}")
def test_banca_estructura_enlaces_y_lenguaje(pagina: Path) -> None:
    p = _leer(pagina)
    assert p.lang == "es"
    assert p.titulo and p.viewport
    assert p.h1 == 1
    assert not p.script_en_linea
    assert not p.estilo_en_linea
    for ref in p.enlaces + p.recursos:
        if re.match(r"^(https?:|mailto:|#)", ref):
            continue
        destino = (
            SITIO / ref.split("#")[0].lstrip("/")
            if ref.startswith("/")
            else pagina.parent / ref.split("#")[0]
        )
        assert destino.resolve().is_file(), f"{pagina.name}: {ref} no existe"
    texto = " ".join(p.texto)
    assert [f.pattern for f in frases_prohibidas(cargar_estilo(), "plantilla") if f.search(texto)] == []


@pytest.mark.parametrize("pagina", BANCA, ids=lambda p: f"banca/{p.name}")
def test_banca_enlaces_a_banca_son_absolutos(pagina: Path) -> None:
    """Con cleanUrls sin barra final, /banca resuelve contra la raiz: index.html relativo iria al inicio."""
    p = _leer(pagina)
    assert [r for r in p.enlaces if r in ("index.html", "reclamos.html")] == []


def test_banca_fixtures_siguen_el_contrato() -> None:
    fx = SITIO / "banca" / "fixtures"
    resumen = json.loads((fx / "resumen.json").read_text(encoding="utf-8"))
    assert {"producto_ref", "tipo", "etiqueta", "final", "estado", "moneda", "saldo", "limite"} <= set(
        resumen["productos"][0]
    )
    movs = json.loads((fx / "movimientos.json").read_text(encoding="utf-8"))["movimientos"]
    campos = {
        "tx_ref",
        "fecha",
        "hora",
        "descripcion",
        "categoria",
        "tipo",
        "canal",
        "monto",
        "moneda",
        "estado",
        "pais",
        "es_extranjera",
        "tarjeta_final",
        "reclamable",
        "caso_ref",
    }
    assert all(campos <= set(m) for m in movs)
    reclamos = json.loads((fx / "reclamos.json").read_text(encoding="utf-8"))
    assert {"caso_ref", "tx_ref", "estado", "credito_provisional", "plazo", "historial"} <= set(reclamos[0])


def test_banca_scripts_sin_innerhtml() -> None:
    for nombre in ("banca.js", "widget.js"):
        assert "innerHTML" not in (SITIO / "assets" / nombre).read_text(encoding="utf-8")
