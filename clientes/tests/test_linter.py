import re

import pytest
from latam_clientes.contenido import (
    Matriz,
    Plantillas,
    cargar_estilo,
    cargar_matriz,
    cargar_plantillas,
    cargar_plantillas_pt,
    frases_prohibidas,
    renderizar,
)
from latam_clientes.linter import Hallazgo, verificar
from latam_comun.dominio.caso import Estado

MATRIZ = cargar_matriz()
ESTILO = cargar_estilo()
PLANTILLAS = cargar_plantillas()
PLANTILLAS_PT = cargar_plantillas_pt()


def _con(id_: str, **cambios: object) -> Plantillas:
    """Copia de las plantillas con una modificada."""
    nuevas = [p.model_copy(update=cambios) if p.id == id_ else p for p in PLANTILLAS.plantillas]
    return PLANTILLAS.model_copy(update={"plantillas": nuevas})


def _texto(id_: str, registro: str, texto: str) -> Plantillas:
    p = PLANTILLAS.por_id()[id_]
    return _con(id_, textos={**p.textos, registro: texto})


def _reglas(plantillas: Plantillas, matriz: Matriz = MATRIZ) -> set[str]:
    return {h.regla for h in verificar(matriz, ESTILO, plantillas)}


def test_el_contenido_real_no_tiene_hallazgos() -> None:
    assert [str(h) for h in verificar()] == []


def test_la_matriz_cubre_todos_los_estados_del_motor() -> None:
    assert set(MATRIZ.estados) == {e.value for e in Estado}
    for estado in MATRIZ.estados.values():
        assert set(estado.celdas) == set(MATRIZ.canales)
    assert MATRIZ.registros_exigidos("es") == ["usted", "vos"]
    assert MATRIZ.registros_exigidos("pt") == ["voce"]
    assert MATRIZ.registros_exigidos() == ["usted", "vos", "voce"]


def test_cada_celda_tiene_plantilla_en_cada_registro_exigido() -> None:
    por_id = PLANTILLAS.por_id()
    for e in MATRIZ.estados.values():
        for canal, celda in e.celdas.items():
            p = por_id[celda.plantilla]
            assert canal in p.canales
            for registro in MATRIZ.registros_exigidos("es"):
                assert p.textos[registro].strip()


def test_falta_un_estado_del_motor() -> None:
    estados = {k: v for k, v in MATRIZ.estados.items() if k != "negado"}
    assert "matriz_estados" in _reglas(PLANTILLAS, MATRIZ.model_copy(update={"estados": estados}))


def test_celda_sin_plantilla_o_sin_registro() -> None:
    sin_vos = _con("inicio.voz", textos={"usted": "Hola."})
    assert {"celda", "registro_faltante"} <= _reglas(sin_vos)
    quitada = PLANTILLAS.model_copy(
        update={"plantillas": [p for p in PLANTILLAS.plantillas if p.id != "inicio.voz"]}
    )
    assert "celda" in _reglas(quitada)


def test_frase_prohibida() -> None:
    assert "frase_prohibida" in _reglas(_texto("ejecutando.chat", "usted", "Listo, ya quedó."))
    assert "frase_prohibida" in _reglas(_texto("ejecutando.chat", "usted", "Le garantizo el resultado."))


def test_caracteres_y_cifras() -> None:
    assert "caracter_prohibido" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando, ¡ya!"))
    assert "caracter_prohibido" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando — ya."))
    assert "caracter_prohibido" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando \U0001f600"))
    assert "cifra_escrita" in _reglas(_texto("ejecutando.chat", "usted", "Le responderemos en 15 días."))


def test_marcadores_requeridos_y_declarados() -> None:
    assert "marcador_requerido" in _reglas(_con("plazo.respuesta.chat", marcadores=["norma", "n", "unidad"]))
    p = PLANTILLAS.por_id()["plazo.respuesta.chat"]
    assert "marcador" in _reglas(_texto(p.id, "usted", p.textos["usted"].replace("{fecha}", "mañana")))
    assert "marcador" in _reglas(_con("ejecutando.chat", marcadores=["inventado"]))


def test_monto_en_voz_exige_palabras() -> None:
    assert "marcador_requerido" in _reglas(
        _con("identificando.voz", marcadores=["cargo", "comercio", "fecha"])
    )


def test_consistencia_de_registro() -> None:
    assert "registro" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando tu solicitud."))
    assert "registro" in _reglas(_texto("ejecutando.chat", "vos", "Estoy procesando su solicitud."))
    assert "registro" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando, si querés esperar."))
    assert "registro" in _reglas(_texto("ejecutando.chat", "vos", "Estoy procesando, si quieres esperar."))


def test_longitud_por_canal() -> None:
    larga = "Estoy procesando su solicitud con mucho cuidado y atención para que todo salga bien esta vez."
    assert "longitud" in _reglas(_texto("ejecutando.voz", "usted", larga))
    assert "longitud" in _reglas(_texto("ejecutando.chat", "usted", "Estoy procesando. " * 40))


def test_vocabulario_por_canal_y_por_pais() -> None:
    assert "vocabulario_canal" in _reglas(
        _texto("ejecutando.voz", "usted", "Toque el botón, estoy procesando.")
    )
    assert "vocabulario_pais" in _reglas(_texto("ejecutando.chat", "usted", "Estoy revisando su extracto."))


def test_frases_obligatorias() -> None:
    assert "frase_obligatoria" in _reglas(_texto("inicio.voz", "usted", "Hola, ¿en qué le ayudo?"))
    assert "frase_obligatoria" in _reglas(_texto("negado.todos", "usted", "Con eso no le puedo ayudar."))
    assert "frase_obligatoria" in _reglas(
        _texto("seguridad.frase.voz", "vos", "Tené cuidado con tu tarjeta.")
    )


def test_render_falla_si_faltan_marcadores() -> None:
    p = PLANTILLAS.por_id()["plazo.respuesta.chat"]
    with pytest.raises(ValueError, match="faltan"):
        renderizar(p, "usted", {"norma": "x"})


def test_la_lista_de_prohibidas_se_comparte_con_ia() -> None:
    prompt = frases_prohibidas(ESTILO, "prompt")
    assert any(r.search("Le devolveremos su dinero") for r in prompt)
    assert not any(r.search("Los hechos verificados llegan como marcadores") for r in prompt)


def test_paises_con_registro_valido() -> None:
    assert {p: v.registro for p, v in ESTILO.paises.items()} == {"MX": "usted", "CO": "usted", "AR": "vos"}
    assert all(v.registro in MATRIZ.registros_exigidos("es") for v in ESTILO.paises.values())


def test_hallazgo_legible() -> None:
    assert str(Hallazgo("regla", "x.chat", "detalle", "usted")) == "regla: x.chat[usted]: detalle"
    assert re.compile(ESTILO.frases_prohibidas[0].patron)


# Portugués (CLI-1.5)


def _con_pt(id_: str, **cambios: object) -> Plantillas:
    nuevas = [p.model_copy(update=cambios) if p.id == id_ else p for p in PLANTILLAS_PT.plantillas]
    return PLANTILLAS_PT.model_copy(update={"plantillas": nuevas})


def _texto_pt(id_: str, texto: str) -> Plantillas:
    p = PLANTILLAS_PT.por_id()[id_]
    return _con_pt(id_, textos={**p.textos, "voce": texto})


def _reglas_pt(plantillas_pt: Plantillas) -> set[str]:
    return {h.regla for h in verificar(MATRIZ, ESTILO, PLANTILLAS, plantillas_pt=plantillas_pt)}


def test_el_catalogo_pt_cubre_cada_celda_y_calca_el_espanol() -> None:
    por_id = PLANTILLAS_PT.por_id()
    assert set(por_id) == set(PLANTILLAS.por_id())
    for e in MATRIZ.estados.values():
        for canal, celda in e.celdas.items():
            assert canal in por_id[celda.plantilla].canales
            assert por_id[celda.plantilla].textos["voce"].strip()
    assert all(p.retraduccion and p.retraduccion.strip() for p in PLANTILLAS_PT.plantillas)


def test_pt_falta_una_plantilla_o_la_retraduccion() -> None:
    sin = PLANTILLAS_PT.model_copy(
        update={"plantillas": [p for p in PLANTILLAS_PT.plantillas if p.id != "negado.todos"]}
    )
    assert {"celda", "paridad"} <= _reglas_pt(sin)
    assert "retraduccion" in _reglas_pt(_con_pt("negado.todos", retraduccion=None))
    assert "retraduccion" in _reglas_pt(_con_pt("verificando.chat", retraduccion="Estoy {inventado}."))


def test_pt_frases_prohibidas_y_caracteres() -> None:
    assert "frase_prohibida" in _reglas_pt(
        _texto_pt("ejecutando.chat", "Pronto, feito. Vamos estornar o valor.")
    )
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Eu garanto o resultado."))
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Isso é fraude."))
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Você fez a compra."))
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Responderemos o quanto antes."))
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Vale o Pix e o Procon."))
    assert "frase_prohibida" in _reglas_pt(_texto_pt("ejecutando.chat", "Veja no seu telemóvel."))
    assert "caracter_prohibido" in _reglas_pt(_texto_pt("ejecutando.chat", "Estou processando!"))
    assert "cifra_escrita" in _reglas_pt(_texto_pt("ejecutando.chat", "Respondemos em 15 dias."))


def test_pt_registro_voce_sin_tuteo_ni_espanol_ni_trato_formal() -> None:
    assert "registro" in _reglas_pt(_texto_pt("ejecutando.chat", "Estou processando a tua solicitação."))
    assert "registro" in _reglas_pt(_texto_pt("ejecutando.chat", "Se quiseres esperar, podes ficar."))
    assert "registro" in _reglas_pt(_texto_pt("ejecutando.chat", "Estou processando su solicitud."))
    assert "registro" in _reglas_pt(_texto_pt("ejecutando.chat", "O senhor pode esperar."))


def test_pt_marcadores_longitud_y_vocabulario() -> None:
    p = PLANTILLAS_PT.por_id()["plazo.respuesta.chat"]
    assert "marcador" in _reglas_pt(_texto_pt(p.id, p.textos["voce"].replace("{fecha}", "amanhã")))
    assert "marcador_requerido" in _reglas_pt(_con_pt(p.id, marcadores=["norma", "n", "unidad"]))
    assert "cifra_escrita" in _reglas_pt(_texto_pt("ejecutando.chat", "Isso leva 15 dias."))
    larga = "Estou processando sua solicitação com muito cuidado e atenção para que tudo saia bem desta vez."
    assert "longitud" in _reglas_pt(_texto_pt("ejecutando.voz", larga))
    assert "longitud" in _reglas_pt(_texto_pt("ejecutando.chat", "Estou processando. " * 40))
    assert "vocabulario_canal" in _reglas_pt(
        _texto_pt("ejecutando.voz", "Toque no botão, estou processando.")
    )
    assert "vocabulario_pais" in _reglas_pt(_texto_pt("ejecutando.chat", "Estou revisando seu extrato."))


def test_pt_frases_obligatorias() -> None:
    assert "frase_obligatoria" in _reglas_pt(_texto_pt("inicio.voz", "Olá, em que posso ajudar?"))
    assert "frase_obligatoria" in _reglas_pt(_texto_pt("negado.todos", "Com isso não posso ajudar."))
    assert "frase_obligatoria" in _reglas_pt(_texto_pt("seguridad.frase.voz", "Cuidado com o seu cartão."))


def test_pt_render_con_marcadores_de_la_region() -> None:
    p = PLANTILLAS_PT.por_id()["identificando.chat"]
    texto = renderizar(
        p,
        "voce",
        {
            "cargo": "cobrança",
            "comercio": "Loja X",
            "fecha": "3 de outubro de 2026",
            "monto": "180.000,00",
            "moneda": "COP",
        },
    )
    assert "180.000,00 COP" in texto and "Brasil" not in texto
