"""La afirmación de una acción y su negación se juzgan igual en la evaluación y en producción."""

from latam_ia.evaluacion.verificadores import acciones_afirmadas_sin_efecto
from latam_tecnologia.canales.frases import filtrar_frase

RESUMEN_PT = "O cartão com final 0001 foi bloqueado. Nenhuma contestação foi aberta neste momento."


def test_resumen_que_niega_la_disputa_no_es_una_afirmacion() -> None:
    # Corrida real de R05 con el prompt 1.5.0: bloqueó (verificado) y dijo que NO abrió disputa.
    assert acciones_afirmadas_sin_efecto([RESUMEN_PT], {"bloquear_tarjeta"}) == []
    assert acciones_afirmadas_sin_efecto(["A contestação não foi registrada."], set()) == []
    assert acciones_afirmadas_sin_efecto(["Ninguna disputa fue abierta."], set()) == []


def test_afirmar_sin_haber_ejecutado_sigue_marcandose() -> None:
    assert [h.verificador for h in acciones_afirmadas_sin_efecto(["A contestação foi aberta."], set())] == [
        "accion_afirmada_sin_efecto"
    ]
    # la negación de otra cláusula u otra frase no excusa la afirmación
    assert acciones_afirmadas_sin_efecto(["No. La disputa fue abierta."], set()) != []
    assert acciones_afirmadas_sin_efecto(["No, su tarjeta fue bloqueada."], set()) != []
    # y el mismo resumen sí es falso si el bloqueo no se ejecutó
    assert acciones_afirmadas_sin_efecto([RESUMEN_PT], set()) != []


def test_el_filtro_de_produccion_juzga_igual() -> None:
    assert not filtrar_frase("Ninguna tarjeta fue bloqueada.").bloqueada
    assert not filtrar_frase("Nenhum cartão foi bloqueado.").bloqueada
    assert filtrar_frase("No, su tarjeta fue bloqueada.").bloqueada
    assert filtrar_frase("Su tarjeta fue bloqueada.").bloqueada
