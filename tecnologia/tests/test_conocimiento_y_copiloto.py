"""Recuperación de política para el cliente y copiloto del experto."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from latam_tecnologia.banca.copiloto import RESPALDO, sugerir
from latam_tecnologia.canales.frases import filtrar_frase
from latam_tecnologia.herramientas.conocimiento import (
    RUTA_ARTICULOS,
    RUTA_VECTORES,
    Articulo,
    Busqueda,
    Hallazgo,
    RecuperadorLexico,
    RecuperadorVectorial,
    cargar_articulos,
    cargar_config,
    cargar_vectores,
    crear_recuperador,
)

ARTICULOS = cargar_articulos()


def test_la_base_esta_completa_y_cada_articulo_nombra_sus_reglas() -> None:
    assert len(ARTICULOS) == 16 and len({a.id for a in ARTICULOS}) == 16
    for a in ARTICULOS:
        assert a.reglas and set(a.textos) == {"es", "pt"} and all(a.textos.values()), a.id
        assert a.pais in (None, "MX", "CO", "AR"), a.id


@pytest.mark.parametrize("articulo", ARTICULOS, ids=lambda a: a.id)
def test_el_filtro_de_salida_no_bloquea_el_texto_de_un_articulo(articulo: Articulo) -> None:
    """Si el asistente repite la fuente, el canal no debe cambiarla por el texto de respaldo."""
    for idioma, texto in articulo.textos.items():
        assert not filtrar_frase(texto).bloqueada, (articulo.id, idioma)


def test_los_vectores_guardados_son_de_esta_version_de_los_articulos() -> None:
    manifiesto, vectores = cargar_vectores()
    assert manifiesto["huella_articulos"] == hashlib.sha256(RUTA_ARTICULOS.read_bytes()).hexdigest()
    assert set(vectores) == {a.id for a in ARTICULOS}
    assert all(len(v[i]) == manifiesto["dimension"] for v in vectores.values() for i in ("es", "pt"))
    assert cargar_config()["huella_articulos"] == manifiesto["huella_articulos"]
    assert RUTA_VECTORES.stat().st_size < 600_000


def test_lexico_encuentra_el_articulo_y_respeta_el_pais() -> None:
    lexico = RecuperadorLexico(ARTICULOS)
    assert (
        lexico.buscar("¿Bloquear la tarjeta cancela los cobros ya hechos?").hallazgos[0].articulo.id == "K-11"
    )
    assert lexico.buscar("zzz qqq").hallazgos == ()
    for pregunta in ("abono provisional plazo de referencia 48 horas", "crédito provisional"):
        ids = {h.articulo.id for h in lexico.buscar(pregunta, pais="CO", k=5).hallazgos}
        assert "K-02" not in ids and "K-04" not in ids  # los de México y Argentina no valen para Colombia
    assert lexico.buscar("abono provisional 48 horas", pais="MX").hallazgos[0].articulo.id == "K-02"


def _vectorial(incrustar: Any, umbral: float = 0.5) -> RecuperadorVectorial:
    vectores = {a.id: {"es": [1.0, 0.0], "pt": [0.9, 0.1]} for a in ARTICULOS}
    vectores["K-05"] = {"es": [0.0, 1.0], "pt": [0.1, 0.9]}
    return RecuperadorVectorial(
        ARTICULOS, vectores, incrustar, umbral=umbral, margen=0.0, respaldo=RecuperadorLexico(ARTICULOS)
    )


def test_vectorial_cita_sobre_el_umbral_y_se_abstiene_debajo() -> None:
    arriba = _vectorial(lambda _: [0.0, 1.0]).buscar("lo que sea")
    assert [h.articulo.id for h in arriba.hallazgos] == ["K-05"] and arriba.metodo == "vectorial"
    assert arriba.reglas() == ("ESC-04",)
    assert _vectorial(lambda _: [-1.0, -1.0]).buscar("lo que sea").hallazgos == ()


def test_si_el_servicio_de_vectores_falla_responde_el_lexico() -> None:
    def roto(_: str) -> Sequence[float]:
        raise TimeoutError("sin red")

    b = _vectorial(roto).buscar("¿Bloquear la tarjeta cancela los cobros ya hechos?")
    assert b.metodo == "lexico" and b.hallazgos[0].articulo.id == "K-11"


def test_sin_proyecto_el_recuperador_es_el_lexico() -> None:
    assert isinstance(crear_recuperador({}), RecuperadorLexico)
    assert isinstance(
        crear_recuperador({"LATAM_GCP_PROJECT": "p", "LATAM_RECUPERADOR": "lexico"}), RecuperadorLexico
    )


# Copiloto

VISTA: dict[str, Any] = {
    "registro": "usted",
    "pais_cuenta": "CO",
    "prioridad": "P3",
    "motivo": {"texto": "El cliente pidió una persona"},
    "solicitud": {"cita": "Quiero hablar con alguien por un cobro alto"},
    "hechos_verificados": [{"texto": "Cargo de 120.000 COP en Tienda Uno"}],
    "acciones_realizadas": [],
    "acciones_no_realizadas": [],
    "preguntas_abiertas": [{"pregunta": "¿Reconoce el comercio?"}],
    "compromisos_comunicados": [],
    "transcripcion": [{"autor": "cliente", "texto": "Quiero hablar con alguien"}],
}


class _Fijo:
    def buscar(self, pregunta: str, pais: str | None = None, k: int = 2) -> Busqueda:
        return Busqueda((Hallazgo(next(a for a in ARTICULOS if a.id == "K-05"), 0.9),), "vectorial")


def _generador(respuesta: str) -> Any:
    def generar(instruccion: str, contexto: str) -> Mapping[str, str]:
        assert "Tienda Uno" in contexto and "ESC-04" in contexto  # ve los hechos y la fuente
        return {
            "resumen": "Pide una persona por un cobro. Falta saber si reconoce el comercio.",
            "respuesta": respuesta,
        }

    return generar


def test_borrador_del_modelo_con_sus_fuentes() -> None:
    b = sugerir(VISTA, _generador("Hola, soy del equipo. Voy a revisar el cargo con usted."), _Fijo())
    assert b.origen == "modelo" and b.fuentes == ["ESC-04"] and b.aviso is None
    assert b.respuesta.startswith("Hola, soy del equipo")


def test_un_borrador_que_afirma_una_accion_no_llega_a_la_consola() -> None:
    b = sugerir(VISTA, _generador("Listo, su tarjeta fue bloqueada y el dinero será reembolsado."), _Fijo())
    assert b.origen == "plantilla" and b.respuesta == RESPALDO["usted"] and b.aviso and "filtro" in b.aviso


def test_sin_modelo_o_con_falla_queda_la_plantilla(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("latam_tecnologia.banca.copiloto.time.sleep", lambda _: None)
    assert sugerir(VISTA, None).origen == "plantilla"

    def roto(instruccion: str, contexto: str) -> Mapping[str, str]:
        raise RuntimeError("503")

    b = sugerir({**VISTA, "registro": "voce"}, roto, _Fijo())
    assert b.origen == "plantilla" and b.respuesta == RESPALDO["voce"] and b.aviso
    largo = sugerir(VISTA, _generador("x" * 2000), _Fijo())
    assert largo.origen == "plantilla"
