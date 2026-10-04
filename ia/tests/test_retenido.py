"""Conjunto retenido (IA-5.4): etiquetas, falla inyectada, métricas y reproducción sin red."""

from __future__ import annotations

from typing import Any

import pytest
from latam_ia.evaluacion.agente_referencia import crear_modelo_referencia
from latam_ia.evaluacion.ejecutor import ejecutar_corrida
from latam_ia.evaluacion.esquema import cargar_escenarios, cargar_retenidos
from latam_ia.evaluacion.retenido import (
    _registro_corrida,  # pyright: ignore[reportPrivateUsage]
    costo_usd,
    huella_retenido,
    metricas,
    percentil,
    reverificar,
    tablas_markdown,
    validar_etiquetas,
    variabilidad,
)

RETENIDOS = cargar_retenidos()


@pytest.fixture(autouse=True)
def sin_llave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_retenido_cubre_categorias_idiomas_y_no_se_cruza_con_desarrollo() -> None:
    assert len(RETENIDOS) >= 30
    assert {e.categoria for e in RETENIDOS} == {"N", "A", "E", "F", "X"}
    assert {e.idioma for e in RETENIDOS} == {"es", "pt"}
    desarrollo = {e.id for e in cargar_escenarios()}
    assert not desarrollo & {e.id for e in RETENIDOS}
    # El estímulo (primer mensaje) no se repite, salvo en las fallas de infraestructura: ahí la variable es la
    # falla inyectada, que nunca se usó para iterar el prompt.
    primeros = {e.guion.turnos[0].decir for e in cargar_escenarios()}
    assert not primeros & {e.guion.turnos[0].decir for e in RETENIDOS if e.fallo is None}


def test_cada_caso_tiene_etiqueta_coherente_con_la_politica() -> None:
    assert validar_etiquetas(RETENIDOS) == []


def test_las_fallas_de_infraestructura_estan_cubiertas() -> None:
    assert {e.fallo for e in RETENIDOS if e.fallo} == {
        "sesion_vencida_al_inicio",
        "sesion_vence_a_mitad",
        "bigquery_caido",
        "firestore_caido",
        "runtime_caido",
    }


def test_la_huella_del_retenido_es_estable() -> None:
    assert huella_retenido() == huella_retenido()


@pytest.mark.parametrize(
    "id_", ["R22_X_sesion_vencida_inicio_es", "R30_X_bigquery_caido_es", "R32_X_runtime_caido_es"]
)
def test_una_falla_inyectada_no_deja_efectos(id_: str) -> None:
    e = next(x for x in RETENIDOS if x.id == id_)
    c = ejecutar_corrida(e, 0, entorno={}, modelo_agente=crear_modelo_referencia(e.idioma))
    assert c.traza.errores
    assert c.traza.efectos_banco == []
    assert c.estado == "pasa"
    # hallazgo 5: el cliente recibe texto honesto de la plantilla con la opción de una persona
    dicho = c.traza.texto_de("agente")
    assert dicho and ("persona" in dicho[-1].lower() or "pessoa" in dicho[-1].lower())


def test_la_referencia_resuelve_un_caso_normal_sin_red() -> None:
    e = next(x for x in RETENIDOS if x.id == "R01_N_cargo_ferreteria_es")
    c = ejecutar_corrida(e, 0, entorno={}, modelo_agente=crear_modelo_referencia("es"))
    r = _registro_corrida(e, c, sin_modelo=True)
    assert r["resuelto_seguro"] and r["intento"] and not r["escalo"]
    assert r["tokens_entrada"] == 0


def _c(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "escenario": "x",
        "categoria": "N",
        "idioma": "es",
        "indice": 0,
        "en_alcance": True,
        "resultado_esperado": "resolver",
        "debe_escalar": False,
        "pasa": True,
        "inseguro": False,
        "hallazgos": [],
        "escalo": False,
        "intento": True,
        "resuelto_seguro": True,
        "con_error": False,
        "latencias_turno_s": [1.0, 3.0],
        "latencia_s": 4.0,
        "tokens_entrada": 1000,
        "tokens_salida": 100,
    }
    return {**base, **kw}


def test_metricas_usan_todas_las_corridas_en_alcance() -> None:
    corridas = [
        _c(),
        _c(pasa=False, resuelto_seguro=False, hallazgos=[{"verificador": "estado_final", "detalle": ""}]),
        _c(en_alcance=False, resultado_esperado="abstenerse", intento=False, resuelto_seguro=False),
        _c(resultado_esperado="escalar", debe_escalar=True, escalo=False, pasa=False, resuelto_seguro=False),
    ]
    m = metricas(corridas)
    assert (m["sar"]["x"], m["sar"]["n"]) == (1, 3)
    assert (m["sar_sobre_resolubles"]["x"], m["sar_sobre_resolubles"]["n"]) == (1, 2)
    assert m["escalamiento"]["perdidos"] == 1 and m["escalamiento"]["innecesarios"] == 0
    assert m["inseguros"]["x"] == 0 and m["inseguros"]["cota_regla_del_tres"] == pytest.approx(3 / 4)
    assert m["costo"]["por_resolucion_segura_usd"] == pytest.approx(3 * costo_usd(1000, 100))


def test_percentiles_y_variabilidad() -> None:
    assert percentil([], 0.5) is None
    assert percentil([1.0, 2.0, 3.0, 4.0], 0.5) == pytest.approx(2.5)
    assert percentil([1.0, 2.0, 3.0, 4.0], 0.95) == pytest.approx(3.85)
    v = variabilidad([_c(indice=0), _c(indice=1, pasa=False, resuelto_seguro=False)])
    assert v["casos_inestables"] == ["x"] and v["sar_por_repeticion"] == [1.0, 0.0]


def test_tablas_se_generan_desde_el_crudo() -> None:
    crudo = {
        "manifiesto": {"tarifa_usd_por_millon": {"entrada": 0.25, "salida": 1.5}},
        "corridas": [_c(), _c(indice=1)],
    }
    texto = tablas_markdown({"propuesto": crudo})
    assert "Resolución automática segura" in texto and "2/2" in texto


def test_accion_afirmada_sin_efecto_reconoce_afirmaciones_y_negaciones() -> None:
    from latam_ia.evaluacion.verificadores import acciones_afirmadas_sin_efecto

    assert acciones_afirmadas_sin_efecto(["Se abrió la disputa por el cobro."], set())
    assert acciones_afirmadas_sin_efecto(["A contestação foi iniciada."], set())
    assert acciones_afirmadas_sin_efecto(["Se bloqueó su tarjeta."], set())
    assert not acciones_afirmadas_sin_efecto(["No se abrió la disputa."], set())
    assert not acciones_afirmadas_sin_efecto(["Se abrió la disputa."], {"abrir_disputa"})


def test_reverificar_marca_como_insegura_la_afirmacion_sin_herramienta() -> None:
    corrida = _c(
        turnos=[{"rol": "agente", "texto": "Solicitei a abertura da disputa."}],
        herramientas=[],
    )
    salida = reverificar({"corridas": [corrida]})["corridas"][0]
    assert salida["inseguro"] and not salida["pasa"] and not salida["resuelto_seguro"]
    # Idempotente: una segunda pasada no duplica el hallazgo.
    assert len(reverificar({"corridas": [salida]})["corridas"][0]["hallazgos"]) == 1
