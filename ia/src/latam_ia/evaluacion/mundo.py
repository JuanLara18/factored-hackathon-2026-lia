"""Materializa un escenario en las dobles en memoria de Tecnología: nada toca BigQuery ni un proveedor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from latam_comun.dominio import Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.herramientas.catalogo import Herramientas
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
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


@dataclass
class MundoVivo:
    mundo: Mundo
    cliente: str
    sesion: SesionAutenticada
    herramientas: Herramientas
    banco: ServiciosBancoRegistrador
    almacen: AlmacenMemoria

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
        categoria="retail",
        pais=t.pais,
        es_extranjera=t.pais not in ("CO", "MX", "AR"),
    )


def materializar(escenario: Escenario) -> MundoVivo:
    mundo = combinar(cargar_mundo_base(), escenario.mundo_extra)
    lectura = LecturaOroFalsa(
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
    almacen = AlmacenMemoria()
    herramientas = Herramientas(lectura, banco, almacen, reloj=lambda: AHORA)
    sesion = SesionAutenticada(
        id_sesion="sesion-eval",
        cliente_id=escenario.cliente,
        nivel=NivelAcr.ACCION,
        expira=AHORA + timedelta(hours=1),
    )
    return MundoVivo(mundo, escenario.cliente, sesion, herramientas, banco, almacen)
