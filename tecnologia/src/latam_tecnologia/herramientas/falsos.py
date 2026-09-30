"""Dobles en memoria de los puertos, para pruebas y ejecución local sin BigQuery."""

from __future__ import annotations

from typing import Any

from latam_comun.dominio import Dinero

from latam_tecnologia.herramientas.puertos import CasoAbierto, Producto, Transaccion


class LecturaOroFalsa:
    def __init__(
        self,
        transacciones: list[tuple[str, Transaccion]] | None = None,
        productos: list[tuple[str, Producto]] | None = None,
        fichas: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._tx = transacciones or []
        self._prod = productos or []
        self._fichas = fichas or {}

    def transacciones_recientes(self, cliente_id: str, limite: int) -> tuple[Transaccion, ...]:
        propias = sorted((t for c, t in self._tx if c == cliente_id), key=lambda t: t.event_ts, reverse=True)
        return tuple(propias[:limite])

    def transaccion(self, cliente_id: str, transaction_id: str) -> Transaccion | None:
        return next((t for c, t in self._tx if c == cliente_id and t.transaction_id == transaction_id), None)

    def productos(self, cliente_id: str) -> tuple[Producto, ...]:
        return tuple(p for c, p in self._prod if c == cliente_id)

    def ficha_transaccion(self, cliente_id: str, transaction_id: str) -> dict[str, Any] | None:
        if self.transaccion(cliente_id, transaction_id) is None:
            return None
        return self._fichas.get(transaction_id)


class ServiciosBancoFalsos:
    """Idempotente por llave y, para casos, por (cliente, transacción) mientras el caso siga abierto."""

    def __init__(self) -> None:
        self.respuestas: dict[str, str] = {}
        self.casos: dict[tuple[str, str], str] = {}
        self.bloqueos: list[tuple[str, str]] = []
        self.traspasos: list[tuple[str, str, bool]] = []
        self.creditos_provisionales: list[str] = []
        self.llamadas = 0

    def abrir_caso(
        self,
        llave: str,
        cliente_id: str,
        transaccion_id: str,
        monto: Dinero,
        motivo: str,
        credito_provisional: bool,
    ) -> str:
        if llave in self.respuestas:
            return self.respuestas[llave]
        self.llamadas += 1
        existente = self.casos.get((cliente_id, transaccion_id))
        caso = existente or f"caso-{len(self.casos) + 1}"
        self.casos[(cliente_id, transaccion_id)] = caso
        if existente is None and credito_provisional:  # un caso ya abierto no vuelve a recibir crédito
            self.creditos_provisionales.append(caso)
        self.respuestas[llave] = caso
        return caso

    def credito_provisional_de(self, caso: str) -> bool:
        return caso in self.creditos_provisionales

    def casos_abiertos(self, cliente_id: str) -> tuple[CasoAbierto, ...]:
        return tuple(
            CasoAbierto(transaction_id=tx, caso=caso)
            for (c, tx), caso in self.casos.items()
            if c == cliente_id
        )

    def bloquear_tarjeta(self, llave: str, cliente_id: str, producto_id: str) -> str:
        if llave in self.respuestas:
            return self.respuestas[llave]
        self.llamadas += 1
        self.bloqueos.append((cliente_id, producto_id))
        self.respuestas[llave] = f"bloqueada:{producto_id}"
        return self.respuestas[llave]

    def encolar_traspaso(
        self, llave: str, cliente_id: str, conversacion_id: str, motivo: str, urgente: bool
    ) -> str:
        if llave in self.respuestas:
            return self.respuestas[llave]
        self.llamadas += 1
        self.traspasos.append((cliente_id, conversacion_id, urgente))
        self.respuestas[llave] = f"traspaso-{len(self.traspasos)}"
        return self.respuestas[llave]
