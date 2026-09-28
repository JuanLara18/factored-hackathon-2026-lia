from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from latam_comun.dominio import (
    Canal,
    Dinero,
    EventoTraza,
    NivelAcr,
    SesionAutenticada,
    TurnoEntrante,
)
from pydantic import ValidationError

AHORA = datetime(2026, 6, 17, 12, tzinfo=UTC)


def test_dinero_exige_moneda_valida() -> None:
    with pytest.raises(ValidationError):
        Dinero(monto=Decimal("10"), moneda="EUR")  # type: ignore[arg-type]


def test_dinero_no_negativo() -> None:
    with pytest.raises(ValidationError):
        Dinero(monto=Decimal("-1"), moneda="COP")


def test_tipos_inmutables() -> None:
    d = Dinero(monto=Decimal("5"), moneda="USD")
    with pytest.raises(ValidationError):
        d.monto = Decimal("6")  # type: ignore[misc]


def test_sesion_expirada_no_permite_nada() -> None:
    s = SesionAutenticada(id_sesion="s", cliente_id="c", nivel=NivelAcr.ACCION, expira=AHORA)
    assert not s.permite(NivelAcr.CONSULTA, AHORA)


def test_consulta_no_alcanza_para_accion() -> None:
    s = SesionAutenticada(
        id_sesion="s", cliente_id="c", nivel=NivelAcr.CONSULTA, expira=AHORA + timedelta(minutes=5)
    )
    assert s.permite(NivelAcr.CONSULTA, AHORA)
    assert not s.permite(NivelAcr.ACCION, AHORA)


def test_confianza_de_reconocimiento_solo_en_voz() -> None:
    with pytest.raises(ValidationError):
        TurnoEntrante(canal=Canal.CHAT, texto="hola", confianza_reconocimiento=0.9, recibido=AHORA)
    TurnoEntrante(canal=Canal.VOZ_TELEFONO, texto="hola", confianza_reconocimiento=0.9, recibido=AHORA)


def test_dtmf_solo_digitos() -> None:
    with pytest.raises(ValidationError):
        TurnoEntrante(canal=Canal.VOZ_TELEFONO, texto="", dtmf="1a", recibido=AHORA)


@given(st.integers(min_value=1, max_value=10_000))
def test_traza_no_termina_antes_de_empezar(segundos: int) -> None:
    with pytest.raises(ValidationError):
        EventoTraza(id_conversacion="c", etapa="motor", inicio=AHORA, fin=AHORA - timedelta(seconds=segundos))
