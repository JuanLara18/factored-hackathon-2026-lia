"""Sesiones de demostración: clientes sembrados, del oro operacional si hay BigQuery y en memoria si no."""

from __future__ import annotations

import logging
import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from latam_comun.dominio import Canal, Dinero, NivelAcr, SesionAutenticada

from latam_tecnologia.herramientas.falsos import LecturaOroFalsa, ServiciosBancoFalsos
from latam_tecnologia.herramientas.puertos import LecturaOro, Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion
from latam_tecnologia.servicios.almacen import AlmacenMemoria

log = logging.getLogger(__name__)
VIGENCIA_SESION = timedelta(minutes=30)
MAX_CLIENTES_DEMO = 3


def _tx(tid: str, pid: str, dia: int, monto: str, comercio: str, cat: str) -> Transaccion:
    return Transaccion(
        transaction_id=tid,
        product_id=pid,
        event_ts=datetime(2026, 6, dia, 15, 30, tzinfo=UTC),
        monto=Dinero(monto=Decimal(monto), moneda="COP"),
        amount_usd=None,
        tipo="purchase",
        estado="approved",
        comercio=comercio,
        categoria=cat,
        pais="CO",
        es_extranjera=False,
    )


def lectura_sembrada() -> tuple[LecturaOroFalsa, list[str]]:
    """Tres clientes ficticios con productos y compras propias (sin datos reales)."""
    filas: list[tuple[str, Transaccion]] = []
    productos: list[tuple[str, Producto]] = []
    ids: list[str] = []
    datos = [
        ("Tienda Uno", "1234,56", "retail"),
        ("Café Norte", "48,90", "food"),
        ("Viajes Sur", "890,00", "travel"),
    ]
    for i, (comercio, monto, cat) in enumerate(datos, start=1):
        cid = f"demo-{i}"
        ids.append(cid)
        pid = f"tarjeta-{4000 + i}"
        productos.append((cid, Producto(product_id=pid, tipo="credit_card", estado="active", moneda="COP")))
        filas.append((cid, _tx(f"tx-{i}-1", pid, 16, monto.replace(",", "."), comercio, cat)))
        filas.append((cid, _tx(f"tx-{i}-0", pid, 10, "20.00", "Panadería Centro", "food")))
    return LecturaOroFalsa(filas, productos), ids


def _clientes_bigquery(proyecto: str) -> tuple[LecturaOro, list[str]] | None:
    """Toma pocos clientes del oro operacional; `None` si BigQuery no responde."""
    try:
        from google.cloud import bigquery

        from latam_tecnologia.herramientas.bigquery import LecturaBigQuery

        cliente = bigquery.Client(project=proyecto, location="US")
        sql = (
            f"select customer_id from `{proyecto}.latam_bank.oro_operacional_transacciones_recientes`"
            f" group by customer_id order by customer_id limit {MAX_CLIENTES_DEMO}"
        )
        filas: list[Any] = list(cliente.query(sql, location="US").result())
        ids = [str(f["customer_id"]) for f in filas]
        if not ids:
            return None
        return LecturaBigQuery(proyecto, cliente=cliente), ids
    except Exception as error:  # sin credenciales, sin red o sin tabla: se usa la siembra
        log.warning("BigQuery no disponible (%s); se usan clientes sembrados", type(error).__name__)
        return None


@dataclass
class Sesion:
    autenticada: SesionAutenticada
    conversacion_id: str
    registro: str = "usted"


@dataclass
class Demo:
    """Lectura, banco simulado, almacén y sesiones. Los clientes se nombran por número, nunca por id."""

    lectura: LecturaOro
    clientes: list[str]
    origen: str
    banco: ServiciosBancoFalsos = field(default_factory=ServiciosBancoFalsos)
    almacen: AlmacenMemoria = field(default_factory=AlmacenMemoria)
    reloj: Callable[[], datetime] = lambda: datetime.now(UTC)
    sesiones: dict[str, Sesion] = field(default_factory=dict[str, Sesion])

    def etiquetas_clientes(self) -> list[str]:
        return [f"Cliente {i}" for i in range(1, len(self.clientes) + 1)]

    def abrir(self, indice: int, registro: str) -> Sesion:
        cliente_id = self.clientes[indice]
        ahora = self.reloj()
        id_sesion = secrets.token_urlsafe(16)
        conversacion_id = f"c-{secrets.token_hex(6)}"
        self.almacen.crear_conversacion(
            Conversacion(id=conversacion_id, cliente_ref=cliente_id, canal_actual=Canal.CHAT, estado="inicio")
        )
        sesion = Sesion(
            SesionAutenticada(
                id_sesion=id_sesion,
                cliente_id=cliente_id,
                nivel=NivelAcr.ACCION,
                expira=ahora + VIGENCIA_SESION,
            ),
            conversacion_id,
            registro,
        )
        self.sesiones[id_sesion] = sesion
        return sesion


def crear_demo(entorno: dict[str, str] | None = None) -> Demo:
    env = os.environ if entorno is None else entorno
    proyecto = env.get("LATAM_GCP_PROJECT")
    real = _clientes_bigquery(proyecto) if proyecto else None
    if real is not None:
        return Demo(lectura=real[0], clientes=real[1], origen="bigquery")
    lectura, ids = lectura_sembrada()
    return Demo(lectura=lectura, clientes=ids, origen="memoria")
