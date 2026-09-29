import os
import re
from pathlib import Path

import pytest
from latam_clientes.contenido import cargar_estilo
from latam_clientes.contenido import frases_prohibidas as frases_estilo
from latam_ia.prompts import ErrorPrompt, cargar_biblioteca
from latam_ia.prompts.biblioteca import RAIZ_PROMPTS
from latam_ia.prompts.lexicos import cargar_lexicos
from latam_ia.registro.cargador import RAIZ_IA

BIB = cargar_biblioteca()
SNAPSHOTS = Path(__file__).parent / "snapshots"

# Una sola lista: `clientes/estilo/estilo.yaml`.
FRASES_PROHIBIDAS = frases_estilo(cargar_estilo(), "prompt")
# Frases del antiguo `lexicos_prohibidos.yaml` (2.5.5): 15 en 4 clases, ninguna se pierde al unificar.
LEXICO_HISTORICO = {
    "promesa": [
        "le devolveremos",
        "se le reembolsará",
        "no perderá su dinero",
        "garantizamos",
        "vamos devolver",
        "será reembolsado",
    ],
    "acusacion": ["usted hizo la compra", "fue usted", "foi você"],
    "asesoria": ["le conviene demandar", "le aprueban", "vale a pena processar"],
    "identidad": ["soy una persona", "sou uma pessoa", "mis instrucciones dicen"],
}
PATRONES_SECRETOS = [r"AIza[0-9A-Za-z_-]{20,}", r"sk-[A-Za-z0-9]{20,}", r"-----BEGIN", r"[\w.]+@[\w.]+\.\w+"]

REF_COMPRENSION = "comprension/clasificar_motivo@1.0.0"
REF_REDACCION = "redaccion/borrador_deslexicalizado@1.0.0"
REF_DISPUTAS = "disputas/agente@1.0.0"
VALORES: dict[str, dict[str, str]] = {
    REF_DISPUTAS: {},
    REF_COMPRENSION: {
        "mensaje_cliente": "[COMERCIO_1] me cobró algo que no hice",
        "motivos_permitidos": "fraude, error_procesamiento, disputa_comercial",
    },
    REF_REDACCION: {"ruta": "R2", "hechos_verificados": "{{monto}} en {{comercio}}"},
}


def _casos() -> list[tuple[str, str, str]]:
    return [
        (p.referencia, idioma, registro)
        for p in BIB.todos()
        for idioma, por_registro in p.plantillas.items()
        for registro in por_registro
    ]


def test_ninguna_frase_del_lexico_historico_se_perdio() -> None:
    lexicos = cargar_lexicos()
    assert sum(len(v) for v in LEXICO_HISTORICO.values()) == 15
    assert set(LEXICO_HISTORICO) <= set(lexicos)
    perdidas = [
        (c, f)
        for c, frases in LEXICO_HISTORICO.items()
        for f in frases
        if not any(p.search(f) for p in lexicos[c])
    ]
    assert perdidas == []


def test_hay_valores_de_muestra_para_cada_prompt() -> None:
    assert {p.referencia for p in BIB.todos()} == set(VALORES)


@pytest.mark.parametrize(("ref", "idioma", "registro"), _casos())
def test_snapshot(ref: str, idioma: str, registro: str) -> None:
    salida = BIB.renderizar(ref, idioma, registro, VALORES[ref]).texto
    ruta = SNAPSHOTS / f"{ref.replace('/', '__')}.{idioma}.{registro}.txt"
    if os.environ.get("ACTUALIZAR_SNAPSHOTS"):
        ruta.write_text(salida, encoding="utf-8", newline="\n")
    assert ruta.read_text(encoding="utf-8") == salida


@pytest.mark.parametrize(("ref", "idioma", "registro"), _casos())
def test_sin_frases_prohibidas_ni_cifras_ni_secretos(ref: str, idioma: str, registro: str) -> None:
    """R-IA-56 y R-IA-57: sin promesas, sin cifras de negocio y sin secretos en el texto fuente."""
    texto = BIB.obtener(ref).plantillas[idioma][registro]
    assert [f.pattern for f in FRASES_PROHIBIDAS if f.search(texto)] == []
    assert not re.search(r"\d", texto)
    assert [p for p in PATRONES_SECRETOS if re.search(p, texto)] == []


def test_marcadores_obligatorios() -> None:
    with pytest.raises(ErrorPrompt, match="faltan"):
        BIB.renderizar(REF_COMPRENSION, "es", "usted", {"mensaje_cliente": "x"})
    with pytest.raises(ErrorPrompt, match="sobran"):
        BIB.renderizar(REF_COMPRENSION, "es", "usted", {**VALORES[REF_COMPRENSION], "extra": "x"})


def test_registro_e_idioma_no_definidos() -> None:
    with pytest.raises(ErrorPrompt):
        BIB.renderizar(REF_COMPRENSION, "pt", "usted", VALORES[REF_COMPRENSION])
    with pytest.raises(ErrorPrompt):
        BIB.renderizar(REF_COMPRENSION, "es", "voce", VALORES[REF_COMPRENSION])


def test_registros_producen_textos_distintos() -> None:
    v = VALORES[REF_REDACCION]
    assert (
        BIB.renderizar(REF_REDACCION, "es", "usted", v).texto
        != BIB.renderizar(REF_REDACCION, "es", "vos", v).texto
    )


def test_huella_estable_y_en_atributos_de_traza() -> None:
    a = BIB.renderizar(REF_REDACCION, "pt", "voce", VALORES[REF_REDACCION])
    assert len(a.huella) == 64
    assert a.huella == cargar_biblioteca().obtener(REF_REDACCION).huella
    assert a.atributos_span()["latam.prompt.huella"] == a.huella


def test_huella_cambia_si_cambia_el_archivo(tmp_path: Path) -> None:
    (tmp_path / "comprension").mkdir()
    origen = RAIZ_PROMPTS / "comprension" / "clasificar_motivo@1.0.0.yaml"
    destino = tmp_path / "comprension" / origen.name
    destino.write_bytes(origen.read_bytes())
    h1 = cargar_biblioteca(tmp_path).obtener(REF_COMPRENSION).huella
    destino.write_text(origen.read_text(encoding="utf-8") + "\n# nota\n", encoding="utf-8")
    assert cargar_biblioteca(tmp_path).obtener(REF_COMPRENSION).huella != h1


def test_marcador_no_declarado_falla_al_cargar(tmp_path: Path) -> None:
    (tmp_path / "g").mkdir()
    (tmp_path / "g" / "p@1.0.0.yaml").write_text(
        "id: g/p\nversion: 1.0.0\ntrabajador: t\ndescripcion: d\nmarcadores: []\n"
        "plantillas:\n  pt:\n    voce: 'hola ${x}'\n",
        encoding="utf-8",
    )
    with pytest.raises(ErrorPrompt):
        cargar_biblioteca(tmp_path)


def test_ningun_prompt_como_cadena_en_el_codigo() -> None:
    """R-IA-50: el código no embebe prompts; solo la biblioteca los tiene."""
    for ruta in (RAIZ_IA / "src").rglob("*.py"):
        assert "Toda cifra, fecha o dato" not in ruta.read_text(encoding="utf-8")


def test_agente_disputas_carga_el_mismo_texto_que_la_biblioteca() -> None:
    from latam_tecnologia.herramientas.instrucciones import huella_prompt, instrucciones_disputas

    p = BIB.obtener(REF_DISPUTAS)
    assert huella_prompt() == p.huella
    for registro in ("usted", "vos"):
        assert instrucciones_disputas(registro) == p.plantillas["es"][registro]
    assert instrucciones_disputas("voce") == p.plantillas["pt"]["voce"]
    assert "casos_abiertos" in instrucciones_disputas("usted")
