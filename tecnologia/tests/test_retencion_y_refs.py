"""Clave de referencias cerrada por defecto en lo desplegado y vencimiento de los documentos de Firestore."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from latam_comun.dominio import Dinero
from latam_tecnologia.banca import refs
from latam_tecnologia.banca.banco import RETENCION_OPERATIVA, id_caso
from latam_tecnologia.banca.firestore import CAMPO_VENCIMIENTO, BancoFirestore, sin_vencimiento

AHORA = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def test_en_local_la_clave_de_demostracion_sirve() -> None:
    assert refs.secreto({}) == b"latam-demo-refs"
    assert refs.secreto({"LATAM_REF_SECRETO": "x"}) == b"x"


@pytest.mark.parametrize("entorno", [{"K_SERVICE": "latam-chat"}, {"LATAM_ENTORNO": "produccion"}])
def test_desplegado_sin_clave_no_firma_con_la_del_repositorio(entorno: dict[str, str]) -> None:
    with pytest.raises(refs.SecretoAusente):
        refs.secreto(entorno)
    assert refs.secreto({**entorno, "LATAM_REF_SECRETO": "real"}) == b"real"
    with pytest.raises(refs.SecretoAusente):  # vacío cuenta como ausente
        refs.secreto({**entorno, "LATAM_REF_SECRETO": ""})


class _Doc:
    def __init__(self, base: dict[str, dict[str, Any]], ruta: str) -> None:
        self._base, self._ruta = base, ruta

    @property
    def exists(self) -> bool:
        return self._ruta in self._base

    def to_dict(self) -> dict[str, Any]:
        return dict(self._base[self._ruta])

    def get(self, transaction: Any = None) -> _Doc:
        return self

    def create(self, datos: dict[str, Any]) -> None:
        self._base[self._ruta] = datos

    set = create

    def collection(self, nombre: str) -> _Coleccion:
        return _Coleccion(self._base, f"{self._ruta}/{nombre}")


class _Coleccion:
    def __init__(self, base: dict[str, dict[str, Any]], ruta: str) -> None:
        self._base, self._ruta = base, ruta

    def document(self, identificador: str) -> _Doc:
        return _Doc(self._base, f"{self._ruta}/{identificador}")

    def stream(self) -> list[_Doc]:
        prefijo = f"{self._ruta}/"
        return [
            _Doc(self._base, r) for r in self._base if r.startswith(prefijo) and "/" not in r[len(prefijo) :]
        ]


class _Transaccion:
    def set(self, documento: _Doc, datos: dict[str, Any]) -> None:
        documento.create(datos)


class _Cliente:
    def __init__(self) -> None:
        self.base: dict[str, dict[str, Any]] = {}

    def collection(self, nombre: str) -> _Coleccion:
        return _Coleccion(self.base, nombre)

    def transaction(self) -> _Transaccion:
        return _Transaccion()


@pytest.fixture
def banco(monkeypatch: pytest.MonkeyPatch) -> tuple[BancoFirestore, _Cliente]:
    from latam_tecnologia.banca import firestore as modulo

    # sin emulador: la transacción corre la función una vez sobre el doble
    monkeypatch.setattr(modulo.firestore, "transactional", lambda f: f)
    cliente = _Cliente()
    return BancoFirestore("p", cliente=cliente, reloj=lambda: AHORA), cliente


def test_todo_documento_nuevo_lleva_vencimiento_nativo(banco: tuple[BancoFirestore, _Cliente]) -> None:
    b, cliente = banco
    b.abrir_caso("k", "c1", "tx1", Dinero(monto=Decimal("10"), moneda="COP"), "fraude", False)
    b.bloquear_tarjeta("k", "c1", "p1")
    b.agregar_mensaje("conv1", "persona", "hola")
    assert len(cliente.base) == 3
    for ruta, datos in cliente.base.items():
        vence = datos[CAMPO_VENCIMIENTO]
        # el TTL de Firestore solo actúa sobre marcas de tiempo, no sobre texto ISO
        assert isinstance(vence, datetime) and vence == AHORA + RETENCION_OPERATIVA, ruta


def test_el_vencimiento_no_llega_a_los_modelos(banco: tuple[BancoFirestore, _Cliente]) -> None:
    b, _ = banco
    b.abrir_caso("k", "c1", "tx1", Dinero(monto=Decimal("10"), moneda="COP"), "fraude", False)
    b.agregar_mensaje("conv1", "persona", "hola")
    caso = b.caso(id_caso("c1", "tx1"))
    assert caso is not None and CAMPO_VENCIMIENTO not in caso.model_dump()
    assert [m.texto for m in b.mensajes("conv1")] == ["hola"]
    assert sin_vencimiento({"a": 1, CAMPO_VENCIMIENTO: AHORA}) == {"a": 1}
