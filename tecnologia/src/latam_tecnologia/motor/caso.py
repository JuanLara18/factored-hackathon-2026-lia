"""Motor del caso de disputa: estados de la definición (2.6.2) sobre la retoma idempotente del spike S4.

`transicionar` es pura y decide; `MotorCaso` es la cáscara que persiste el estado y ejecuta los efectos.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from latam_comun.dominio import AccionVerificada, Canal, Confirmacion, NivelAcr, SesionAutenticada
from latam_comun.dominio.caso import Estado, Evento
from latam_gobierno.politica import PoliticaV1, cargar

from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Almacen, Conversacion, EfectoIncierto

__all__ = [
    "TERMINALES",
    "TRANSICIONES",
    "Estado",
    "Evento",
    "MotorCaso",
    "Propuesta",
    "Resultado",
    "Transicion",
    "decidir",
    "transicionar",
]

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
class Propuesta:
    accion: str  # "abrir_disputa" o "escalar"
    motivo: str
    credito_provisional: bool = False
    escalar_despues: str | None = None  # motivo: se radica y luego se pasa a una persona (A-07)


def decidir(
    transaccion: Transaccion, productos: tuple[Producto, ...], urgente: bool, politica: PoliticaV1
) -> Propuesta:
    """Disputar o pasar a un humano según `policy/v1`. Puro: la ruta no la decide el modelo (P4)."""
    escalar = politica.escalar(
        urgente=urgente,
        estado_transaccion=transaccion.estado,
        producto_conocido=any(p.product_id == transaccion.product_id for p in productos),
    )
    if escalar is not None:
        return Propuesta("escalar", escalar.motivo)
    provisional = politica.credito_provisional_aplica(transaccion.monto.moneda, transaccion.amount_usd)
    tras = politica.escalar_tras_radicar(transaccion.monto.moneda, transaccion.amount_usd)
    return Propuesta("abrir_disputa", "cargo_no_reconocido", provisional, tras.motivo if tras else None)


@dataclass(frozen=True)
class Resultado:
    estado: Estado
    propuesta: Propuesta | None = None
    accion: AccionVerificada | None = None
    escalada: AccionVerificada | None = None


def _ahora() -> datetime:
    return datetime.now(UTC)


class MotorCaso:
    def __init__(
        self,
        almacen: Almacen,
        herramientas: Herramientas,
        politica: PoliticaV1 | None = None,
        reloj: Callable[[], datetime] = _ahora,
    ) -> None:
        self._almacen = almacen
        self._h = herramientas
        self._politica = politica or cargar()
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
            **({"escalar_despues": propuesta.escalar_despues} if propuesta.escalar_despues else {}),
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
        if not accion.exito:
            c = self._mover(c, Evento.EFECTO_FALLIDO)
            return Resultado(Estado(c.estado), accion=accion)
        c = self._mover(c, Evento.VERIFICADO)
        motivo = c.datos.get("escalar_despues")
        escalada = self._h.escalar(sesion, c.id, motivo, urgente=False)[0] if motivo else None
        return Resultado(Estado(c.estado), accion=accion, escalada=escalada)

    def cerrar(self, conversacion_id: str, sesion: SesionAutenticada) -> Resultado:
        c = self._cargar(conversacion_id, sesion)
        c = self._mover(c, Evento.INFORMADO)
        return Resultado(Estado(c.estado))
