"""Materializa un escenario en las dobles en memoria de Tecnología: nada toca BigQuery ni un proveedor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from google.api_core.exceptions import ServiceUnavailable
from latam_comun.dominio import Canal, Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.herramientas.catalogo import Herramientas
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion
from latam_tecnologia.servicios.almacen import AlmacenMemoria

from latam_ia.evaluacion.esquema import (
    Escenario,
    Mundo,
    TransaccionMundo,
    cargar_mundo_base,
    combinar,
)
from latam_ia.evaluacion.traza import ServiciosBancoRegistrador

AHORA = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
CONVERSACION_ID = "conv-eval"


class Reloj:
    """Reloj de la corrida: fijo en `AHORA` hasta que un escenario de sesión vencida lo adelanta."""

    def __init__(self) -> None:
        self._desfase = timedelta(0)

    def __call__(self) -> datetime:
        return AHORA + self._desfase

    def adelantar(self, horas: int = 2) -> None:
        self._desfase = timedelta(hours=horas)


class LecturaOroCaida(LecturaOroFalsa):
    """BigQuery no disponible: toda lectura falla como lo haría `google.api_core` con un 503."""

    def transacciones_recientes(self, cliente_id: str, limite: int) -> tuple[Transaccion, ...]:
        raise ServiceUnavailable("BigQuery no disponible (falla inyectada)")

    def transaccion(self, cliente_id: str, transaction_id: str) -> Transaccion | None:
        raise ServiceUnavailable("BigQuery no disponible (falla inyectada)")

    def productos(self, cliente_id: str) -> tuple[Producto, ...]:
        raise ServiceUnavailable("BigQuery no disponible (falla inyectada)")

    def ficha_transaccion(self, cliente_id: str, transaction_id: str) -> dict[str, Any] | None:
        raise ServiceUnavailable("BigQuery no disponible (falla inyectada)")


class AlmacenCaido(AlmacenMemoria):
    """Firestore no disponible tras abrir la conversación: la retoma y los efectos fallan con un 503."""

    def __init__(self) -> None:
        super().__init__()
        self.caido = False

    def _vivo(self) -> None:
        if self.caido:
            raise ServiceUnavailable("Firestore no disponible (falla inyectada)")

    def cargar(self, conversacion_id: str) -> Conversacion | None:
        self._vivo()
        return super().cargar(conversacion_id)

    def actualizar(self, conversacion_id: str, estado: str, datos: dict[str, str]) -> None:
        self._vivo()
        super().actualizar(conversacion_id, estado, datos)

    def cambiar_canal(self, conversacion_id: str, canal: Canal) -> None:
        self._vivo()
        super().cambiar_canal(conversacion_id, canal)

    def reservar_efecto(self, llave: str, conversacion_id: str, numero: int, tipo: str) -> bool:
        self._vivo()
        return super().reservar_efecto(llave, conversacion_id, numero, tipo)


@dataclass
class MundoVivo:
    mundo: Mundo
    cliente: str
    sesion: SesionAutenticada
    herramientas: Herramientas
    banco: ServiciosBancoRegistrador
    almacen: AlmacenMemoria
    reloj: Reloj

    def canarios(self) -> frozenset[str]:
        """Datos de otros clientes: si aparecen en una respuesta o en una lectura, hay fuga."""
        tx = [t for t in self.mundo.transacciones if t.cliente != self.cliente]
        pr = [p for p in self.mundo.productos if p.cliente != self.cliente]
        propios = {t.comercio for t in self.mundo.transacciones if t.cliente == self.cliente}
        valores = {t.id for t in tx} | {t.comercio for t in tx if t.comercio not in propios}
        valores |= {p.id for p in pr}
        valores |= {c for c in {t.cliente for t in tx} | {p.cliente for p in pr}}
        return frozenset(valores)


def _transaccion(t: TransaccionMundo) -> Transaccion:
    return Transaccion(
        transaction_id=t.id,
        product_id=t.producto,
        event_ts=AHORA - timedelta(days=t.hace_dias),
        monto=Dinero(monto=Decimal(t.monto), moneda=t.moneda),
        amount_usd=None if t.usd is None else Decimal(t.usd),
        tipo="purchase",
        estado=t.estado,
        comercio=t.comercio,
        categoria=t.categoria,
        pais=t.pais,
        es_extranjera=t.pais not in ("CO", "MX", "AR"),
    )


def materializar(escenario: Escenario) -> MundoVivo:
    mundo = combinar(cargar_mundo_base(), escenario.mundo_extra)
    clase_lectura = LecturaOroCaida if escenario.fallo == "bigquery_caido" else LecturaOroFalsa
    lectura = clase_lectura(
        transacciones=[(t.cliente, _transaccion(t)) for t in mundo.transacciones],
        productos=[
            (
                p.cliente,
                Producto(product_id=p.id, tipo=p.tipo, estado=p.estado, moneda=p.moneda),
            )
            for p in mundo.productos
        ],
    )
    banco = ServiciosBancoRegistrador()
    for i, (cliente, tx) in enumerate(mundo.casos_previos, start=1):
        banco.casos[(cliente, tx)] = f"caso-previo-{i}"
    almacen = AlmacenCaido() if escenario.fallo == "firestore_caido" else AlmacenMemoria()
    reloj = Reloj()
    if escenario.fallo == "sesion_vencida_al_inicio":
        reloj.adelantar()
    herramientas = Herramientas(lectura, banco, almacen, reloj=reloj)
    sesion = SesionAutenticada(
        id_sesion="sesion-eval",
        cliente_id=escenario.cliente,
        nivel=NivelAcr.ACCION,
        expira=AHORA + timedelta(hours=1),
    )
    return MundoVivo(mundo, escenario.cliente, sesion, herramientas, banco, almacen, reloj)
