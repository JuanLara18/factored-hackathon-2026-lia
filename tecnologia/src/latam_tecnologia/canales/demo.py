"""Sesiones de demostración: clientes sembrados, del oro operacional si hay BigQuery y en memoria si no."""

from __future__ import annotations

import logging
import os
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from latam_comun.dominio import Canal, Dinero, NivelAcr, SesionAutenticada

from latam_tecnologia.banca.banco import Banco, BancoMemoria, crear_banco
from latam_tecnologia.banca.modelos import RegistroConversacion
from latam_tecnologia.banca.vista import PAIS_POR_MONEDA
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa
from latam_tecnologia.herramientas.puertos import LecturaOro, Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion
from latam_tecnologia.servicios.almacen import AlmacenMemoria

log = logging.getLogger(__name__)
VIGENCIA_SESION = timedelta(minutes=30)
MAX_CLIENTES_DEMO = 6


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
        # Clientes con historia para la demo: muchos movimientos, varios con comercio, repartidos por país.
        base = f"`{proyecto}.latam_bank"
        sql = f"""
            with ricos as (
              select t.customer_id, any_value(v.country) as pais, count(*) as n,
                     countif(t.merchant_name is not null) as con_comercio
              from {base}.oro_operacional_transacciones_recientes` t
              join {base}.oro_operacional_vista_cliente_segura` v using (customer_id)
              where v.country in ('MX', 'CO', 'AR')
              group by t.customer_id
              having n >= 15 and con_comercio >= 8
            )
            select customer_id from ricos
            qualify row_number() over (partition by pais order by con_comercio desc, customer_id) <= 2
            order by case pais when 'MX' then 1 when 'CO' then 2 else 3 end, con_comercio desc
            limit {MAX_CLIENTES_DEMO}
        """
        filas: list[Any] = list(cliente.query(sql, location="US").result())
        ids = [str(f["customer_id"]) for f in filas]
        if not ids:
            return None
        lectura = LecturaBigQuery(proyecto, cliente=cliente, cache_s=CACHE_LECTURA_S)

        def _precalentar() -> None:
            try:  # en segundo plano: el servicio ya atiende mientras se llenan las lecturas
                lectura.precalentar(ids, (200,))
            except Exception as error:
                log.warning("no se pudo precalentar la lectura (%s)", type(error).__name__)

        threading.Thread(target=_precalentar, name="precalentar-lectura", daemon=True).start()
        return lectura, ids
    except Exception as error:  # sin credenciales, sin red o sin tabla: se usa la siembra
        log.warning("BigQuery no disponible (%s); se usan clientes sembrados", type(error).__name__)
        return None


# Segundos que vive en memoria una lectura del oro operacional (foto que solo cambia con la carga).
CACHE_LECTURA_S = float(os.environ.get("LATAM_CACHE_LECTURA_S", "300"))


@dataclass
class Sesion:
    autenticada: SesionAutenticada
    conversacion_id: str
    registro: str = "usted"
    contextos: dict[str, str] = field(default_factory=dict[str, str])  # conversación -> contexto del servidor
    reclamos: dict[str, str] = field(default_factory=dict[str, str])  # tx_ref -> conversación de ese reclamo


@dataclass
class Demo:
    """Lectura, banco simulado, almacén y sesiones. Los clientes se nombran por número, nunca por id."""

    lectura: LecturaOro
    clientes: list[str]
    origen: str
    banco: Banco = None  # pyright: ignore[reportAssignmentType]  # `__post_init__` arma el doble
    almacen: AlmacenMemoria = field(default_factory=AlmacenMemoria)
    reloj: Callable[[], datetime] = lambda: datetime.now(UTC)
    sesiones: dict[str, Sesion] = field(default_factory=dict[str, Sesion])
    paises: dict[str, str] = field(default_factory=dict[str, str])

    def __post_init__(self) -> None:
        if self.banco is None:  # pyright: ignore[reportUnnecessaryComparison]
            self.banco = BancoMemoria(self.reloj)

    def pais_de(self, cliente_id: str) -> str:
        """País de la cuenta.

        El de la vista segura si la lectura lo ofrece; si no, el de la moneda de sus productos
        o el de su último movimiento.
        """
        if cliente_id not in self.paises:
            leer_pais = getattr(self.lectura, "pais_cuenta", None)
            leido: object = leer_pais(cliente_id) if callable(leer_pais) else None
            pais = leido if isinstance(leido, str) and leido else None
            for p in () if pais else self.lectura.productos(cliente_id):
                pais = PAIS_POR_MONEDA.get(p.moneda or "")
                if pais:
                    break
            if pais is None:
                for t in self.lectura.transacciones_recientes(cliente_id, 1):  # respaldo sin vista segura
                    pais = t.pais or PAIS_POR_MONEDA.get(t.monto.moneda)
            self.paises[cliente_id] = pais or "CO"
        return self.paises[cliente_id]

    def etiquetas_clientes(self) -> list[str]:
        return [f"Cliente {i}" for i in range(1, len(self.clientes) + 1)]

    def abrir(self, indice: int, registro: str) -> Sesion:
        cliente_id = self.clientes[indice]
        ahora = self.reloj()
        for vencida in [i for i, s in self.sesiones.items() if not s.autenticada.vigente(ahora)]:
            del self.sesiones[vencida]  # las sesiones vencidas no se quedan en memoria
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
        self.banco.registrar_conversacion(
            RegistroConversacion(
                id=conversacion_id,
                cliente_id=cliente_id,
                registro=registro,
                pais=self.pais_de(cliente_id),
                creada_en=ahora,
            )
        )
        return sesion


def crear_demo(entorno: dict[str, str] | None = None) -> Demo:
    env = os.environ if entorno is None else entorno
    proyecto = env.get("LATAM_GCP_PROJECT")
    real = _clientes_bigquery(proyecto) if proyecto else None

    def reloj() -> datetime:
        return datetime.now(UTC)

    try:
        banco = crear_banco(env, reloj)
    except Exception as error:  # sin credenciales de Firestore: solo se tolera si no se pidió explícitamente
        if env.get("LATAM_BANCO"):
            raise
        log.warning("Firestore no disponible (%s); el banco queda en memoria", type(error).__name__)
        banco = BancoMemoria(reloj)
    if real is not None:
        return Demo(lectura=real[0], clientes=real[1], origen="bigquery", banco=banco)
    lectura, ids = lectura_sembrada()
    return Demo(lectura=lectura, clientes=ids, origen="memoria", banco=banco)
