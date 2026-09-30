"""Consola del experto (sitio/operador): estructura, CSP, enlaces y muestras sin datos personales."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SITIO = RAIZ / "tecnologia" / "web" / "sitio"
OPERADOR = SITIO / "operador"
FIXTURES = OPERADOR / "fixtures"

CAMPOS_PROHIBIDOS = {
    "nombre",
    "apellido",
    "documento",
    "numero_documento",
    "cedula",
    "curp",
    "cuit",
    "correo",
    "email",
    "telefono",
    "tarjeta",
    "numero_tarjeta",
    "pan",
    "cliente_id",
    "customer_id",
    "fraud_score",
    "segmento",
    "edad",
    "genero",
    "estado_civil",
    "educacion",
    "razonamiento",
}
CAMPOS_PAQUETE = {
    "id_traspaso",
    "hilo_id",
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


class _Pagina(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts_en_linea = 0
        self.estilos_en_linea = 0
        self.recursos: list[str] = []
        self.h1 = 0
        self.ids: set[str] = set()
        self._script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "style" in a or tag == "style":
            self.estilos_en_linea += 1
        if any(k.startswith("on") for k in a):
            self.scripts_en_linea += 1
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "script":
            if "src" in a:
                self.recursos.append(a["src"])
            else:
                self._script = True
        if tag == "link" and "href" in a:
            self.recursos.append(a["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._script = False

    def handle_data(self, data: str) -> None:
        if self._script and data.strip():
            self.scripts_en_linea += 1


def _pagina() -> _Pagina:
    p = _Pagina()
    p.feed((OPERADOR / "index.html").read_text(encoding="utf-8"))
    return p


def test_estructura_y_csp() -> None:
    html = (OPERADOR / "index.html").read_text(encoding="utf-8")
    p = _pagina()
    assert '<html lang="es">' in html and 'name="viewport"' in html and "<title>" in html
    assert p.scripts_en_linea == 0
    assert p.estilos_en_linea == 0
    assert p.h1 >= 1


def test_recursos_existen() -> None:
    for ref in _pagina().recursos:
        if re.match(r"^(https?:|#)", ref):
            continue
        assert (OPERADOR / ref).resolve().is_file(), ref


def test_js_no_usa_html_dinamico_ni_eval() -> None:
    js = (SITIO / "assets" / "operador.js").read_text(encoding="utf-8")
    for prohibido in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
    ):
        assert prohibido not in js
    # Todos los ids que el script busca existen en la página o los crea él mismo.
    usados = set(re.findall(r'\$\("([\w-]+)"\)', js))
    creados = set(re.findall(r'id: "([\w-]+)"', js)) | set(
        re.findall(r'campo(?:Select|SiNo)\(\s*"([\w-]+)"', js)
    )
    assert usados <= _pagina().ids | creados, usados - _pagina().ids - creados


def test_css_sin_estilos_en_linea_y_usa_variables_del_sitio() -> None:
    css = (SITIO / "assets" / "operador.css").read_text(encoding="utf-8")
    assert "var(--acento)" in css and "var(--borde)" in css
    assert "@import" not in css


def test_orden_fijo_de_la_vista() -> None:
    js = (SITIO / "assets" / "operador.js").read_text(encoding="utf-8")
    ids = re.findall(r'seccion\((\d+), "([^"]+)", "(\w+)"\)', js)
    assert [int(n) for n, _, _ in ids] == list(range(2, 13))
    orden = [i for _, _, i in ids]
    assert orden == [
        "primero",
        "compromisos",
        "solicitud",
        "hechos",
        "acciones",
        "conflictos",
        "preguntas",
        "plazos",
        "evidencia",
        "transcripcion",
        "panel",
    ]
    for etiqueta in ("Verificado", "Dicho por el cliente", "Interpretación de la IA"):
        assert etiqueta in js


def _claves(obj: object) -> set[str]:
    if isinstance(obj, dict):
        d = cast("dict[str, object]", obj)
        return {k.lower() for k in d} | {c for v in d.values() for c in _claves(v)}
    if isinstance(obj, list):
        return {c for v in cast("list[object]", obj) for c in _claves(v)}
    return set()


def _textos(obj: object) -> list[str]:
    if isinstance(obj, dict):
        return [t for v in cast("dict[str, object]", obj).values() for t in _textos(v)]
    if isinstance(obj, list):
        return [t for v in cast("list[object]", obj) for t in _textos(v)]
    return [obj] if isinstance(obj, str) else []


MUESTRAS = sorted(FIXTURES.glob("traspaso_*.json"))


def test_muestras_cubren_p1_p2_p3() -> None:
    paquetes = [json.loads(m.read_text(encoding="utf-8")) for m in MUESTRAS]
    assert {p["prioridad"] for p in paquetes} >= {"P1", "P2", "P3"}
    por_motivo = {p["motivo"]["codigo"]: p for p in paquetes}
    assert por_motivo["FRAUDE_EN_CURSO"]["prioridad"] == "P1"
    assert por_motivo["MONTO_SOBRE_UMBRAL"]["conflictos"]
    assert por_motivo["CLIENTE_PIDE_PERSONA"]["prioridad"] == "P3"
    cola = json.loads((FIXTURES / "cola.json").read_text(encoding="utf-8"))
    assert {c["id_traspaso"] for c in cola} == {p["id_traspaso"] for p in paquetes}


@pytest.mark.parametrize("muestra", MUESTRAS, ids=lambda p: p.name)
def test_paquete_completo_y_sin_datos_personales(muestra: Path) -> None:
    p = json.loads(muestra.read_text(encoding="utf-8"))
    assert set(p) >= CAMPOS_PAQUETE
    assert _claves(p).isdisjoint(CAMPOS_PROHIBIDOS)
    for texto in _textos(p):
        assert not re.search(r"\b\d{13,19}\b", texto), texto
        assert not re.search(r"[\w.]+@[\w.]+\.\w+", texto), texto
    for h in p["hechos_verificados"]:
        assert h["fuente"] and h["hora"]
    for c in p["conflictos"]:
        assert c["declarado"] and c["registro"]
    for q in p["preguntas_abiertas"]:
        assert q["a_quien"] and isinstance(q["bloquea"], bool)


def test_cola_sin_datos_personales() -> None:
    cola = json.loads((FIXTURES / "cola.json").read_text(encoding="utf-8"))
    assert _claves(cola).isdisjoint(CAMPOS_PROHIBIDOS)
    assert [c["prioridad"] for c in cola] == sorted(c["prioridad"] for c in cola)
