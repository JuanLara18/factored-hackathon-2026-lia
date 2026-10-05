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
    for pais in ("MX", "CO", "AR", "BR"):
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


# --- Idioma: las ocho páginas públicas, en portugués y, donde hay usted, con vos ---------------------------

PUBLICAS = ["index", "productos", "reclamos", "seguridad", "ayuda", "contacto", "transparencia", "privacidad"]
_CADENA = '"(?:[^"' + chr(92) + chr(92) + "]|" + chr(92) + chr(92) + '.)*"'  # una cadena JSON con escapes
_LITERAL = re.compile(rf"^\s*({_CADENA})\s*:\s*({_CADENA}),?\s*$")
_SIN_TRADUCCION = {"LATAM", "Bank", "LATAM Bank"}  # la marca no se traduce
_VOID = {"meta", "link", "br", "img", "input", "hr", "use", "path", "circle", "rect", "ellipse", "source"}
_ATRIBUTOS = ("aria-label", "placeholder", "title", "alt")
# Formas de usted que el voseo cambia: pronombres y los imperativos que usan las páginas.
_USTED = re.compile(
    r"\b(usted|su|sus|suya|suyas|suyo|le|les|abra|elija|escriba|pruebe|vea|use|lea|entre|bloquee|"
    r"revise|reclame|señale|actúe|identifique|recorra|conozca|pida|salga|cuéntele|ábralo|"
    r"reconoce|reconozca|necesite|quiera|prefiera|confirme|abrió|entregó|cree)\b",
    re.IGNORECASE,
)


def _tabla(archivo: str, nombre: str) -> dict[str, str]:
    """Lee `var NOMBRE = { "es": "otro" };` de un .js, una entrada por línea (la última repetida manda)."""
    fuente = (SITIO / "assets" / archivo).read_text(encoding="utf-8")
    inicio = fuente.find(f"var {nombre} = {{")
    if inicio < 0:
        return {}
    tabla: dict[str, str] = {}
    for linea in fuente[inicio:].splitlines()[1:]:
        if linea.startswith("  };"):
            break
        m = _LITERAL.match(linea)
        if m:
            tabla[json.loads(m.group(1))] = json.loads(m.group(2))
    return tabla


class _Textos(HTMLParser):
    """Nodos de texto y atributos como los ve idioma.js; ignora script, estilo y lo que pais.js reescribe."""

    def __init__(self) -> None:
        super().__init__()
        self.items: set[str] = set()
        self._pila: list[tuple[str, bool]] = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str | None, str | None]]) -> None:
        self._atributos(tag, dict(attrs))

    def _atributos(self, tag: str, a: dict) -> None:
        for k in _ATRIBUTOS:
            if a.get(k):
                self.items.add(" ".join(a[k].split()))
        if tag == "meta" and a.get("name") == "description":
            self.items.add(" ".join(a["content"].split()))
        if a.get("data-buscar"):
            self.items.add("buscar:" + a["data-buscar"])

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        self._atributos(tag, a)
        if tag not in _VOID:
            self._pila.append((tag, "data-p" in a))

    def handle_endtag(self, tag: str) -> None:
        if self._pila and self._pila[-1][0] == tag:
            self._pila.pop()

    def handle_data(self, data: str) -> None:
        if any(t in ("script", "style") or dp for t, dp in self._pila):
            return
        texto = " ".join(data.split())
        if texto:
            self.items.add(texto)


def _textos(nombre: str) -> list[str]:
    p = _Textos()
    p.feed((SITIO / f"{nombre}.html").read_text(encoding="utf-8"))
    return sorted(
        t
        for t in p.items
        if re.search(r"[^\W\d_]", t) and t not in _SIN_TRADUCCION  # sin letras (cifras, signos) no se traduce
    )


PT = _tabla("idioma.js", "PT") | _tabla("idioma-sitio.js", "PT")
VOS = _tabla("idioma.js", "VOS") | _tabla("idioma-sitio.js", "VOS")


def test_las_tablas_de_idioma_se_leen() -> None:
    assert len(PT) > 300 and len(VOS) > 100


@pytest.mark.parametrize("nombre", PUBLICAS)
def test_pagina_publica_traducida_al_portugues(nombre: str) -> None:
    """Si se agrega o se cambia un texto visible y falta su entrada en portugués, esta prueba lo nombra."""
    faltan = [t for t in _textos(nombre) if not PT.get(t)]
    assert faltan == [], f"{nombre}.html: sin portugués en idioma-sitio.js: {faltan}"


@pytest.mark.parametrize("nombre", PUBLICAS)
def test_pagina_publica_con_vos_donde_hay_usted(nombre: str) -> None:
    """Aproximación: todo texto con pronombre o imperativo de usted conocido necesita su forma con vos."""
    faltan = [t for t in _textos(nombre) if _USTED.search(t) and not VOS.get(t)]
    assert faltan == [], f"{nombre}.html: sin vos en idioma-sitio.js: {faltan}"


def test_el_portugues_no_promete_devoluciones_ni_plazos() -> None:
    texto = " ".join(PT.values()).lower()
    for frase in ("devolveremos", "reembolsaremos", "garantimos", "em até"):
        assert frase not in texto


@pytest.mark.parametrize("nombre", PUBLICAS)
def test_pagina_publica_carga_idioma_antes_que_pais(nombre: str) -> None:
    html = (SITIO / f"{nombre}.html").read_text(encoding="utf-8")
    orden = [html.find(f'src="assets/{s}.js"') for s in ("idioma", "idioma-sitio", "pais")]
    assert all(i > 0 for i in orden) and orden == sorted(orden)
    # una sola elección, el país: fija también el idioma (Brasil es portugués) y no hay selector de idioma
    assert 'id="selector-idioma"' not in html
    assert all(f'<option value="{p}">' in html for p in ("MX", "CO", "AR", "BR"))


@pytest.mark.parametrize("pagina", BANCA, ids=lambda p: f"banca/{p.name}")
def test_banca_tiene_pais_e_idioma_en_la_franja(pagina: Path) -> None:
    html = pagina.read_text(encoding="utf-8")
    franja = html[html.find('class="bn-demo"') : html.find("</header>")]
    assert 'id="pais"' in franja and 'id="selector-idioma"' not in html
    assert html.find("idioma.js") < html.find("pais.js") < html.find("banca.js")
