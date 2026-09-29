"""Motor del caso de disputa: estados de la definición (2.6.2) sobre la retoma idempotente del spike S4.

`transicionar` es pura y decide; `MotorCaso` es la cáscara que persiste el estado y ejecuta los efectos.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Final

from latam_comun.dominio import AccionVerificada, Canal, Confirmacion, NivelAcr, SesionAutenticada

from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Almacen, Conversacion, EfectoIncierto


class Estado(StrEnum):
    INICIO = "inicio"
    IDENTIFICANDO_TRANSACCION = "identificando_transaccion"
    CONFIRMANDO_ACCION = "confirmando_accion"
    EJECUTANDO = "ejecutando"
    VERIFICANDO = "verificando"
    INFORMANDO = "informando"
    TRASPASO = "traspaso"
    CIERRE = "cierre"
    FALLA_SEGURA = "falla_segura"
    NEGADO = "negado"


class Evento(StrEnum):
    ABRIR = "abrir"
    TRANSACCION_ENCONTRADA = "transaccion_encontrada"
    TRANSACCION_NO_ENCONTRADA = "transaccion_no_encontrada"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"
    EFECTO_HECHO = "efecto_hecho"
    EFECTO_FALLIDO = "efecto_fallido"
    VERIFICADO = "verificado"
    ESCALAR = "escalar"
    INFORMADO = "informado"
    ACCESO_DENEGADO = "acceso_denegado"


TERMINALES: Final = frozenset({Estado.CIERRE, Estado.FALLA_SEGURA, Estado.NEGADO})

TRANSICIONES: Final[dict[tuple[Estado, Evento], Estado]] = {
    (Estado.INICIO, Evento.ABRIR): Estado.IDENTIFICANDO_TRANSACCION,
    (Estado.IDENTIFICANDO_TRANSACCION, Evento.TRANSACCION_ENCONTRADA): Estado.CONFIRMANDO_ACCION,
    (Estado.IDENTIFICANDO_TRANSACCION, Evento.TRANSACCION_NO_ENCONTRADA): Estado.IDENTIFICANDO_TRANSACCION,
    (Estado.CONFIRMANDO_ACCION, Evento.CONFIRMADA): Estado.EJECUTANDO,
    (Estado.CONFIRMANDO_ACCION, Evento.RECHAZADA): Estado.CIERRE,
    (Estado.EJECUTANDO, Evento.EFECTO_HECHO): Estado.VERIFICANDO,
    (Estado.EJECUTANDO, Evento.EFECTO_FALLIDO): Estado.FALLA_SEGURA,
    (Estado.VERIFICANDO, Evento.VERIFICADO): Estado.INFORMANDO,
    (Estado.INFORMANDO, Evento.INFORMADO): Estado.CIERRE,
    (Estado.TRASPASO, Evento.INFORMADO): Estado.CIERRE,
    **{
        (e, Evento.ESCALAR): Estado.TRASPASO
        for e in (Estado.IDENTIFICANDO_TRANSACCION, Estado.CONFIRMANDO_ACCION)
    },
    **{(e, Evento.ACCESO_DENEGADO): Estado.NEGADO for e in Estado if e not in TERMINALES},
}


@dataclass(frozen=True)
class Transicion:
    desde: Estado
    hacia: Estado
    evento: Evento
    listada: bool


def transicionar(estado: Estado, evento: Evento) -> Transicion:
    """Pura. Lo no listado lleva a `FALLA_SEGURA` (R-TEC-46); los terminales no se mueven."""
    if estado in TERMINALES:
        return Transicion(estado, estado, evento, listada=False)
    hacia = TRANSICIONES.get((estado, evento))
    if hacia is None:
        return Transicion(estado, Estado.FALLA_SEGURA, evento, listada=False)
    return Transicion(estado, hacia, evento, listada=True)


@dataclass(frozen=True)
class Politica:
    """Reglas de decisión del caso; los valores marcados [S] son supuestos a reemplazar por `policy/v1`."""

    estados_no_disputables: frozenset[str] = frozenset({"declined", "failed", "reversed"})  # [S]
    umbral_credito_provisional_usd: Decimal = Decimal(200)  # [S]


@dataclass(frozen=True)
class Propuesta:
    accion: str  # "abrir_disputa" o "escalar"
    motivo: str
    credito_provisional: bool = False


def decidir(
    transaccion: Transaccion, productos: tuple[Producto, ...], urgente: bool, politica: Politica
) -> Propuesta:
    """Disputar o pasar a un humano. Puro: toda ruta se decide aquí y no en el modelo (P4)."""
    if urgente:
        return Propuesta("escalar", "urgente")
    if transaccion.estado is not None and transaccion.estado.lower() in politica.estados_no_disputables:
        return Propuesta("escalar", "transaccion_no_disputable")
    if all(p.product_id != transaccion.product_id for p in productos):
        return Propuesta("escalar", "producto_no_encontrado")
    provisional = (
        transaccion.amount_usd is not None
        and transaccion.amount_usd <= politica.umbral_credito_provisional_usd
    )
    return Propuesta("abrir_disputa", "cargo_no_reconocido", provisional)


@dataclass(frozen=True)
class Resultado:
    estado: Estado
    propuesta: Propuesta | None = None
    accion: AccionVerificada | None = None


def _ahora() -> datetime:
    return datetime.now(UTC)


class MotorCaso:
    def __init__(
        self,
        almacen: Almacen,
        herramientas: Herramientas,
        politica: Politica | None = None,
        reloj: Callable[[], datetime] = _ahora,
    ) -> None:
        self._almacen = almacen
        self._h = herramientas
        self._politica = politica or Politica()
        self._reloj = reloj

    def _cargar(self, conversacion_id: str, sesion: SesionAutenticada) -> Conversacion:
        conversacion = self._almacen.cargar(conversacion_id)
        if conversacion is None or conversacion.cliente_ref != sesion.cliente_id:
            raise AccesoDenegado("la conversación no es del cliente de la sesión")
        return conversacion

    def _mover(self, c: Conversacion, evento: Evento, **datos: str) -> Conversacion:
        t = transicionar(Estado(c.estado), evento)
        nuevos = {**c.datos, **datos}
        self._almacen.actualizar(c.id, t.hacia.value, nuevos)
        return c.model_copy(update={"estado": t.hacia.value, "datos": nuevos})

    def abrir(self, conversacion_id: str, sesion: SesionAutenticada, canal: Canal) -> Resultado:
        if not sesion.permite(NivelAcr.CONSULTA, self._reloj()):
            raise AccesoDenegado("sesión vencida o de nivel insuficiente")
        c = self._almacen.cargar(conversacion_id)
        if c is None:
            c = Conversacion(
                id=conversacion_id, cliente_ref=sesion.cliente_id, canal_actual=canal, estado=Estado.INICIO
            )
            self._almacen.crear_conversacion(c)
        elif c.cliente_ref != sesion.cliente_id:
            raise AccesoDenegado("la conversación no es del cliente de la sesión")
        if Estado(c.estado) is Estado.INICIO:
            c = self._mover(c, Evento.ABRIR)
        return Resultado(Estado(c.estado))

    def identificar(
        self,
        conversacion_id: str,
        sesion: SesionAutenticada,
        transaction_id: str,
        *,
        urgente: bool = False,
    ) -> Resultado:
        """Ubica la transacción del cliente y propone la acción; escalar se ejecuta sin confirmar."""
        c = self._cargar(conversacion_id, sesion)
        if Estado(c.estado) is not Estado.IDENTIFICANDO_TRANSACCION:
            c = self._mover(c, Evento.TRANSACCION_ENCONTRADA)  # evento fuera de lugar: falla segura
            return Resultado(Estado(c.estado))
        transaccion = self._h.transaccion(sesion, transaction_id).valor
        if transaccion is None:
            c = self._mover(c, Evento.TRANSACCION_NO_ENCONTRADA)
            return Resultado(Estado(c.estado))
        productos = self._h.estado_productos(sesion).valor
        propuesta = decidir(transaccion, productos, urgente, self._politica)
        if propuesta.accion == "escalar":
            c = self._mover(c, Evento.ESCALAR, transaccion=transaction_id, urgente=str(urgente))
            accion, _ = self._h.escalar(sesion, c.id, propuesta.motivo, urgente)
            return Resultado(Estado(c.estado), propuesta, accion)
        c = self._mover(
            c,
            Evento.TRANSACCION_ENCONTRADA,
            transaccion=transaction_id,
            accion=propuesta.accion,
            motivo=propuesta.motivo,
            provisional=str(propuesta.credito_provisional),
        )
        return Resultado(Estado(c.estado), propuesta)

    def confirmar(
        self, conversacion_id: str, sesion: SesionAutenticada, confirmacion: Confirmacion | None
    ) -> Resultado:
        """`None` es un rechazo del cliente; con confirmación ejecuta y deja el caso en `informando`."""
        c = self._cargar(conversacion_id, sesion)
        if Estado(c.estado) is not Estado.CONFIRMANDO_ACCION:
            c = self._mover(c, Evento.CONFIRMADA)  # fuera de lugar: falla segura
            return Resultado(Estado(c.estado))
        if confirmacion is None:
            c = self._mover(c, Evento.RECHAZADA)
            return Resultado(Estado(c.estado))
        if confirmacion.accion != c.datos.get("accion"):
            raise ValueError("la confirmación no corresponde a la acción propuesta")
        c = self._mover(c, Evento.CONFIRMADA)
        try:
            accion, _ = self._h.abrir_disputa(
                sesion,
                c.id,
                c.datos["transaccion"],
                c.datos["motivo"],
                confirmacion,
                credito_provisional=c.datos.get("provisional") == "True",
            )
        except (EfectoIncierto, ConnectionError, TimeoutError):
            c = self._mover(c, Evento.EFECTO_FALLIDO)
            return Resultado(Estado(c.estado))
        c = self._mover(c, Evento.EFECTO_HECHO)
        c = self._mover(c, Evento.VERIFICADO) if accion.exito else self._mover(c, Evento.EFECTO_FALLIDO)
        return Resultado(Estado(c.estado), accion=accion)

    def cerrar(self, conversacion_id: str, sesion: SesionAutenticada) -> Resultado:
        c = self._cargar(conversacion_id, sesion)
        c = self._mover(c, Evento.INFORMADO)
        return Resultado(Estado(c.estado))
