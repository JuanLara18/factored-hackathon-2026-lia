"""Adaptador de solo lectura sobre BigQuery: consultas parametrizadas, siempre filtradas por cliente."""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from latam_comun.dominio import Dinero

from latam_tecnologia.herramientas.puertos import Producto, Transaccion

_IDENTIFICADOR = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,62}$")
_COLUMNAS_TX = (
    "transaction_id, product_id, event_ts, amount, currency, amount_usd, transaction_type,"
    " transaction_status, merchant_name, merchant_category, transaction_country, es_extranjera, channel"
)
_LIMITE_MAXIMO = 200
_CACHE_MAXIMO = 4000
_Llave = tuple[str, tuple[tuple[str, str | int], ...]]


def _decimal(valor: Any) -> Decimal:
    return Decimal(str(valor))


class LecturaBigQuery:
    """Proyecto y dataset son configuración validada; todo dato variable viaja como parámetro."""

    def __init__(
        self,
        proyecto: str,
        dataset: str = "latam_bank",
        *,
        cliente: bigquery.Client | None = None,
        ubicacion: str = "US",
        cache_s: float = 0,
    ) -> None:
        if not _IDENTIFICADOR.match(proyecto) or not _IDENTIFICADOR.match(dataset):
            raise ValueError("proyecto o dataset inválido")
        self._prefijo = f"`{proyecto}.{dataset}`"
        self._ubicacion = ubicacion
        self._cliente = cliente or bigquery.Client(project=proyecto, location=ubicacion)
        # Caché de lecturas: el oro operacional es una foto que solo cambia cuando corre la carga, así que
        # repetir la misma consulta en cada pantalla y en cada herramienta solo agrega cerca de un segundo.
        # Bloqueos, casos y traspasos viven en Firestore y nunca pasan por aquí. `cache_s=0` la apaga.
        self._cache_s = cache_s
        self._cache: dict[_Llave, tuple[float, list[Mapping[str, Any]]]] = {}
        self._candado = threading.Lock()

    def _consultar(self, sql: str, **parametros: str | int) -> list[Mapping[str, Any]]:
        if self._cache_s <= 0:
            return self._consultar_bq(sql, **parametros)
        llave = (sql, tuple(sorted(parametros.items())))
        ahora = time.monotonic()
        with self._candado:
            guardado = self._cache.get(llave)
        if guardado is not None and ahora - guardado[0] < self._cache_s:
            return list(guardado[1])
        filas = self._consultar_bq(sql, **parametros)
        with self._candado:
            if len(self._cache) >= _CACHE_MAXIMO:
                self._cache.clear()
            self._cache[llave] = (ahora, filas)
        return list(filas)

    def precalentar(self, clientes: Sequence[str], limites: Sequence[int]) -> None:
        """Lee una vez lo que la banca pide de cada cliente, para que el primer visitante no espere."""
        for cliente in clientes:
            self.pais_cuenta(cliente)
            self.productos(cliente)
            self.saldos(cliente)
            for limite in limites:
                self.transacciones_recientes(cliente, limite)

    def _consultar_bq(self, sql: str, **parametros: str | int) -> list[Mapping[str, Any]]:
        parametros_bq = [
            bigquery.ScalarQueryParameter(nombre, "INT64" if isinstance(v, int) else "STRING", v)
            for nombre, v in parametros.items()
        ]
        config = bigquery.QueryJobConfig(query_parameters=parametros_bq)
        trabajo = self._cliente.query(sql, job_config=config, location=self._ubicacion)
        return [dict(fila.items()) for fila in trabajo.result()]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportUnknownVariableType]

    @staticmethod
    def _a_transaccion(f: Mapping[str, Any]) -> Transaccion:
        return Transaccion(
            transaction_id=f["transaction_id"],
            product_id=f["product_id"],
            event_ts=f["event_ts"],
            monto=Dinero(monto=abs(_decimal(f["amount"])), moneda=f["currency"]),
            amount_usd=None if f["amount_usd"] is None else _decimal(f["amount_usd"]),
            tipo=f["transaction_type"],
            estado=f["transaction_status"],
            comercio=f["merchant_name"],
            categoria=f["merchant_category"],
            pais=f["transaction_country"],
            es_extranjera=bool(f["es_extranjera"]),
            canal=f.get("channel"),
        )

    def transacciones_recientes(self, cliente_id: str, limite: int) -> tuple[Transaccion, ...]:
        filas = self._consultar(
            f"select {_COLUMNAS_TX} from {self._prefijo}.oro_operacional_transacciones_recientes"
            " where customer_id = @cliente order by event_ts desc limit @limite",
            cliente=cliente_id,
            limite=max(1, min(limite, _LIMITE_MAXIMO)),
        )
        return tuple(self._a_transaccion(f) for f in filas)

    def transaccion(self, cliente_id: str, transaction_id: str) -> Transaccion | None:
        filas = self._consultar(
            f"select {_COLUMNAS_TX} from {self._prefijo}.oro_operacional_transacciones_recientes"
            " where customer_id = @cliente and transaction_id = @transaccion limit 1",
            cliente=cliente_id,
            transaccion=transaction_id,
        )
        return self._a_transaccion(filas[0]) if filas else None

    def productos(self, cliente_id: str) -> tuple[Producto, ...]:
        filas = self._consultar(
            "select product_id, product_type, product_status, currency"
            f" from {self._prefijo}.oro_operacional_estado_productos where customer_id = @cliente",
            cliente=cliente_id,
        )
        return tuple(
            Producto(
                product_id=f["product_id"],
                tipo=f["product_type"],
                estado=f["product_status"],
                moneda=f["currency"],
            )
            for f in filas
        )

    def saldos(self, cliente_id: str) -> dict[str, tuple[Decimal | None, Decimal | None]]:
        """Saldo y cupo por producto para la banca en línea; no es una herramienta del agente."""
        filas = self._consultar(
            f"select product_id, saldo, limite from {self._prefijo}.oro_operacional_saldos_productos"
            " where customer_id = @cliente",
            cliente=cliente_id,
        )
        return {
            str(f["product_id"]): (
                None if f["saldo"] is None else _decimal(f["saldo"]),
                None if f["limite"] is None else _decimal(f["limite"]),
            )
            for f in filas
        }

    def pais_cuenta(self, cliente_id: str) -> str | None:
        """País de la cuenta (vista segura, sin PII). No sale de la moneda: en México se opera en USD."""
        filas = self._consultar(
            f"select country from {self._prefijo}.oro_operacional_vista_cliente_segura"
            " where customer_id = @cliente limit 1",
            cliente=cliente_id,
        )
        return str(filas[0]["country"]) if filas and filas[0]["country"] else None

    def ficha_transaccion(self, cliente_id: str, transaction_id: str) -> dict[str, Any] | None:
        """Contrato pendiente de Datos: si la tabla no existe todavía, no hay ficha."""
        if self.transaccion(cliente_id, transaction_id) is None:
            return None
        try:
            filas = self._consultar(
                f"select * except (customer_id) from {self._prefijo}.oro_operacional_ficha_transaccion"
                " where customer_id = @cliente and transaction_id = @transaccion limit 1",
                cliente=cliente_id,
                transaccion=transaction_id,
            )
        except NotFound:
            return None
        return dict(filas[0]) if filas else None
