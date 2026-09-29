"""Traza de una corrida: lo que dijeron las partes, las herramientas llamadas y el estado final del banco."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from latam_comun.dominio import Dinero
from latam_tecnologia.herramientas.falsos import ServiciosBancoFalsos

Rol = Literal["cliente", "agente", "interfaz"]
Aprobacion = Literal["explicita", "implicita", "rechazada", "ninguna"]

# Herramientas con efecto y las que exigen confirmación explícita del cliente (escalar no perjudica: 2.6.4).
EFECTOS = frozenset({"abrir_disputa", "bloquear_tarjeta", "escalar"})
EFECTOS_CON_CONFIRMACION = frozenset({"abrir_disputa", "bloquear_tarjeta"})


@dataclass(frozen=True)
class Turno:
    rol: Rol
    texto: str


@dataclass(frozen=True)
class LlamadaHerramienta:
    nombre: str
    args: dict[str, object]
    retorno: str
    tool_call_id: str
    ejecutada: bool
    aprobacion: Aprobacion
    turno_cliente: int  # cuántos turnos del cliente llevaba la conversación cuando se llamó


@dataclass(frozen=True)
class EfectoBanco:
    tipo: str
    cliente: str
    recurso: str
    nuevo: bool


@dataclass(frozen=True)
class EstadoFinal:
    casos: frozenset[tuple[str, str]]
    bloqueos: frozenset[tuple[str, str]]
    traspasos: tuple[tuple[str, str, bool], ...]
    creditos_provisionales: int


@dataclass
class Traza:
    turnos: list[Turno] = field(default_factory=list[Turno])
    herramientas: list[LlamadaHerramienta] = field(default_factory=list[LlamadaHerramienta])
    efectos_banco: list[EfectoBanco] = field(default_factory=list[EfectoBanco])
    errores: list[str] = field(default_factory=list[str])
    estado_final: EstadoFinal = EstadoFinal(frozenset(), frozenset(), (), 0)

    def texto_de(self, *roles: Rol) -> list[str]:
        return [t.texto for t in self.turnos if t.rol in roles]


class ServiciosBancoRegistrador(ServiciosBancoFalsos):
    """El banco en memoria más una bitácora de cada efecto, con si esa llamada lo produjo o repitió otro."""

    def __init__(self) -> None:
        super().__init__()
        self.bitacora: list[EfectoBanco] = []

    def _anotar(self, tipo: str, cliente: str, recurso: str, antes: int) -> None:
        self.bitacora.append(EfectoBanco(tipo, cliente, recurso, nuevo=self.llamadas > antes))

    def abrir_caso(
        self,
        llave: str,
        cliente_id: str,
        transaccion_id: str,
        monto: Dinero,
        motivo: str,
        credito_provisional: bool,
    ) -> str:
        antes = self.llamadas
        salida = super().abrir_caso(llave, cliente_id, transaccion_id, monto, motivo, credito_provisional)
        self._anotar("abrir_disputa", cliente_id, transaccion_id, antes)
        return salida

    def bloquear_tarjeta(self, llave: str, cliente_id: str, producto_id: str) -> str:
        antes = self.llamadas
        salida = super().bloquear_tarjeta(llave, cliente_id, producto_id)
        self._anotar("bloquear_tarjeta", cliente_id, producto_id, antes)
        return salida

    def encolar_traspaso(
        self, llave: str, cliente_id: str, conversacion_id: str, motivo: str, urgente: bool
    ) -> str:
        antes = self.llamadas
        salida = super().encolar_traspaso(llave, cliente_id, conversacion_id, motivo, urgente)
        self._anotar("escalar", cliente_id, conversacion_id, antes)
        return salida

    def estado_final(self) -> EstadoFinal:
        return EstadoFinal(
            casos=frozenset(self.casos),
            bloqueos=frozenset(self.bloqueos),
            traspasos=tuple(self.traspasos),
            creditos_provisionales=len(self.creditos_provisionales),
        )
