"""Spike S4: un caso empezado en chat se retoma por voz con un solo efecto por llave."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from latam_comun.dominio import AccionVerificada, Canal, Confirmacion, NivelAcr, SesionAutenticada
from latam_tecnologia.motor.retoma import (
    Almacen,
    Conversacion,
    RetomaNegada,
    ejecutar_una_vez,
    llave_efecto,
    retomar,
)
from latam_tecnologia.servicios.almacen import AlmacenMemoria, AlmacenPostgres

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def _conversacion() -> Conversacion:
    return Conversacion(id="k1", cliente_ref="c1", canal_actual=Canal.CHAT, estado="informando")


def _sesion(cliente: str = "c1", nivel: NivelAcr = NivelAcr.ACCION, minutos: int = 10) -> SesionAutenticada:
    return SesionAutenticada(
        id_sesion="s", cliente_id=cliente, nivel=nivel, expira=AHORA + timedelta(minutes=minutos)
    )


def _confirmacion(canal: Canal, accion: str = "bloquear_tarjeta") -> Confirmacion:
    return Confirmacion(accion=accion, canal=canal, evidencia="boton", nonce="n1")


def _ejecutor(contador: list[str]) -> Callable[[str], AccionVerificada]:
    def _hacer(llave: str) -> AccionVerificada:
        contador.append(llave)
        return AccionVerificada(
            accion="bloquear_tarjeta", exito=True, resultado_releido="bloqueada", hora=AHORA
        )

    return _hacer


def _pedir_bloqueo(almacen: Almacen, canal: Canal, efectos: list[str]) -> tuple[AccionVerificada, bool]:
    return ejecutar_una_vez(
        almacen,
        conversacion_id="k1",
        numero_transicion=3,
        tipo="bloquear_tarjeta",
        recurso="tarjeta-9",
        confirmacion=_confirmacion(canal),
        ejecutor=_ejecutor(efectos),
    )


def escenario(almacen: Almacen) -> None:
    almacen.crear_conversacion(_conversacion())
    efectos: list[str] = []
    accion, ejecutada = _pedir_bloqueo(almacen, Canal.CHAT, efectos)
    assert ejecutada and accion.exito

    resumen = retomar(almacen, "k1", _sesion(), Canal.VOZ_TELEFONO, AHORA)
    assert resumen.canal_anterior is Canal.CHAT and resumen.canal_nuevo is Canal.VOZ_TELEFONO
    assert resumen.acciones_hechas == (accion,)

    # por voz el motor vuelve a pedir la misma acción: no se ejecuta otra vez
    repetida, ejecutada = _pedir_bloqueo(almacen, Canal.VOZ_TELEFONO, efectos)
    assert not ejecutada and repetida == accion
    assert len(efectos) == 1
    cargada = almacen.cargar("k1")
    assert cargada is not None and cargada.canal_actual is Canal.VOZ_TELEFONO


def test_llave_determinista_y_sensible_a_cada_campo() -> None:
    base = llave_efecto("k", 1, "t", "r")
    assert base == llave_efecto("k", 1, "t", "r")
    otras = {
        llave_efecto("x", 1, "t", "r"),
        llave_efecto("k", 2, "t", "r"),
        llave_efecto("k", 1, "u", "r"),
        llave_efecto("k", 1, "t", "s"),
    }
    assert base not in otras and len(otras) == 4
    assert llave_efecto("a", 1, "bc", "r") != llave_efecto("ab", 1, "c", "r")


def test_retoma_sin_repetir_en_memoria() -> None:
    escenario(AlmacenMemoria())


def test_retoma_negada_para_otro_cliente_nivel_bajo_o_sesion_vencida() -> None:
    almacen = AlmacenMemoria()
    almacen.crear_conversacion(_conversacion())
    for sesion in (_sesion("otro"), _sesion(nivel=NivelAcr.CONSULTA), _sesion(minutos=-1)):
        with pytest.raises(RetomaNegada):
            retomar(almacen, "k1", sesion, Canal.VOZ_NAVEGADOR, AHORA)


def test_confirmacion_de_otra_accion_no_ejecuta() -> None:
    almacen = AlmacenMemoria()
    almacen.crear_conversacion(_conversacion())
    efectos: list[str] = []
    with pytest.raises(ValueError):
        ejecutar_una_vez(
            almacen,
            conversacion_id="k1",
            numero_transicion=1,
            tipo="bloquear_tarjeta",
            recurso="r",
            confirmacion=_confirmacion(Canal.CHAT, "radicar_caso"),
            ejecutor=_ejecutor(efectos),
        )
    assert efectos == []


def test_retoma_sin_repetir_en_postgres(dsn_postgres: str) -> None:
    almacen = AlmacenPostgres(dsn_postgres)
    try:
        escenario(almacen)
    finally:
        almacen.cerrar()
