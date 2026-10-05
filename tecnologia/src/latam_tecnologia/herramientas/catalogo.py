"""Herramientas tipadas del agente. El cliente sale siempre de la sesión, nunca de un argumento."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from latam_comun.dominio import AccionVerificada, Confirmacion, HechoVerificado, NivelAcr, SesionAutenticada
from latam_gobierno.politica import PoliticaV1, cargar

from latam_tecnologia.banca.banco import Banco
from latam_tecnologia.banca.paquete import construir_paquete
from latam_tecnologia.herramientas.puertos import (
    CasoAbierto,
    LecturaOro,
    Producto,
    ServiciosBanco,
    Transaccion,
)
from latam_tecnologia.motor.retoma import Almacen, ejecutar_una_vez

# Número de transición de cada efecto: fijo por acción, para que la llave sea igual en cualquier canal.
NUM_ABRIR_DISPUTA = 4
NUM_BLOQUEAR_TARJETA = 50
NUM_ESCALAR = 100


NO_DISPUTABLES = ("declined", "failed", "reversed")  # ESC-02 de policy/v1


LIMITE_DEFECTO = 50  # la línea de reglas lee 50; con 10 el cobro de hace cuatro días quedaba fuera (R07)
LIMITE_MAXIMO = 200


def _coincide(
    t: Transaccion, comercio: str | None, monto: Decimal | None, desde: date | None, hasta: date | None
) -> bool:
    if comercio and comercio.strip().lower() not in (t.comercio or "").lower():
        return False
    if monto is not None and abs(t.monto.monto - monto) > monto * Decimal("0.01"):
        return False
    dia = t.event_ts.date()
    return not ((desde and dia < desde) or (hasta and dia > hasta))


class NoDisputable(Exception):
    """El movimiento está en un estado que no admite disputa (rechazado, fallido o revertido)."""


class EscalacionRequerida(Exception):
    """`policy/v1` manda pasar el caso a una persona en vez de radicar (producto desconocido, ESC-03)."""

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class TarjetaFueraDelMovimiento(Exception):
    """La conversación tiene un movimiento fijado y la tarjeta pedida no es la de ese movimiento."""


class AccesoDenegado(Exception):
    """Sesión vencida, nivel insuficiente o recurso que no es del cliente de la sesión."""


def _ahora() -> datetime:
    return datetime.now(UTC)


class Herramientas:
    def __init__(
        self,
        lectura: LecturaOro,
        banco: ServiciosBanco,
        almacen: Almacen,
        reloj: Callable[[], datetime] = _ahora,
        politica: PoliticaV1 | None = None,
    ) -> None:
        self._politica = politica or cargar()
        self._lectura = lectura
        self._banco = banco
        self._almacen = almacen
        self._reloj = reloj

    def _exigir(self, sesion: SesionAutenticada, accion: str) -> datetime:
        """El nivel mínimo de cada acción sale de `policy/v1` (R-GOB-25)."""
        nivel = NivelAcr(self._politica.acr_requerido(accion))
        ahora = self._reloj()
        if not sesion.permite(nivel, ahora):
            raise AccesoDenegado("sesión vencida o de nivel insuficiente")
        return ahora

    def _exigir_conversacion(self, sesion: SesionAutenticada, conversacion_id: str) -> None:
        conversacion = self._almacen.cargar(conversacion_id)
        if conversacion is None or conversacion.cliente_ref != sesion.cliente_id:
            raise AccesoDenegado("la conversación no es del cliente de la sesión")

    # Lectura (acr1)

    def transacciones_recientes(
        self,
        sesion: SesionAutenticada,
        limite: int = LIMITE_DEFECTO,
        *,
        comercio: str | None = None,
        monto: Decimal | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> HechoVerificado[tuple[Transaccion, ...]]:
        """Movimientos del cliente de la sesión, del más reciente al más antiguo, con tope duro.

        Con filtros (comercio por subcadena, monto exacto o con 1% de holgura, rango de fechas) se busca sobre
        el máximo de movimientos y se devuelven los que coinciden, para hallar el cobro descrito.
        """
        ahora = self._exigir(sesion, "transacciones_recientes")
        tope = max(1, min(limite, LIMITE_MAXIMO))
        filtrado = any(f is not None for f in (comercio, monto, desde, hasta))
        valor = self._lectura.transacciones_recientes(sesion.cliente_id, LIMITE_MAXIMO if filtrado else tope)
        if filtrado:
            valor = tuple(t for t in valor if _coincide(t, comercio, monto, desde, hasta))[:tope]
        return HechoVerificado(valor=valor, fuente="oro_operacional_transacciones_recientes", hora=ahora)

    def transaccion(
        self, sesion: SesionAutenticada, transaction_id: str
    ) -> HechoVerificado[Transaccion | None]:
        ahora = self._exigir(sesion, "transaccion")
        valor = self._lectura.transaccion(sesion.cliente_id, transaction_id)
        return HechoVerificado(valor=valor, fuente="oro_operacional_transacciones_recientes", hora=ahora)

    def estado_productos(self, sesion: SesionAutenticada) -> HechoVerificado[tuple[Producto, ...]]:
        ahora = self._exigir(sesion, "estado_productos")
        valor = self._lectura.productos(sesion.cliente_id)
        return HechoVerificado(valor=valor, fuente="oro_operacional_estado_productos", hora=ahora)

    def ficha_transaccion(
        self, sesion: SesionAutenticada, transaction_id: str
    ) -> HechoVerificado[dict[str, Any] | None]:
        ahora = self._exigir(sesion, "ficha_transaccion")
        valor = self._lectura.ficha_transaccion(sesion.cliente_id, transaction_id)
        return HechoVerificado(valor=valor, fuente="oro_operacional_ficha_transaccion", hora=ahora)

    def casos_abiertos(self, sesion: SesionAutenticada) -> HechoVerificado[tuple[CasoAbierto, ...]]:
        ahora = self._exigir(sesion, "casos_abiertos")
        valor = self._banco.casos_abiertos(sesion.cliente_id)
        return HechoVerificado(valor=valor, fuente="banco_simulado_casos", hora=ahora)

    def credito_provisional(self, transaccion: Transaccion) -> bool:
        """Lo que `policy/v1` decide para esa transacción; el modelo no lo elige."""
        return self._politica.credito_provisional_aplica(transaccion.monto.moneda, transaccion.amount_usd)

    def rutas_obligadas(
        self, sesion: SesionAutenticada, transacciones: tuple[Transaccion, ...]
    ) -> list[str | None]:
        """Por transacción, el motivo si `policy/v1` manda escalar en vez de radicar por el producto (ESC-03).

        El estado del movimiento (ESC-02) se trata aparte con `NoDisputable`. Una sola lectura de productos.
        """
        ids = {p.product_id for p in self._lectura.productos(sesion.cliente_id)}
        salida: list[str | None] = []
        for t in transacciones:
            d = self._politica.escalar(
                urgente=False, estado_transaccion=None, producto_conocido=t.product_id in ids
            )
            salida.append(None if d is None else d.motivo)
        return salida

    def ruta_obligada(self, sesion: SesionAutenticada, transaccion: Transaccion) -> str | None:
        return self.rutas_obligadas(sesion, (transaccion,))[0]

    def producto_del_movimiento(self, sesion: SesionAutenticada, conversacion_id: str) -> str | None:
        """Producto del movimiento que el servidor fijó en la conversación (`reclamar`); `None` si no hay.

        Sin movimiento fijado (el chat suelto) no hay restricción. El banco compartido guarda el registro.
        """
        leer = getattr(self._banco, "conversacion", None)
        registro = None if leer is None else leer(conversacion_id)
        fijada = getattr(registro, "transaccion_id", None)
        if not fijada:
            return None
        tx = self._lectura.transaccion(sesion.cliente_id, fijada)
        return None if tx is None else tx.product_id

    def escalar_tras_radicar(self, transaccion: Transaccion) -> str | None:
        """Motivo si `policy/v1` manda pasar el caso a una persona además de radicar (A-07); si no, `None`."""
        d = self._politica.escalar_tras_radicar(transaccion.monto.moneda, transaccion.amount_usd)
        return None if d is None else d.motivo

    # Efectos (bloquear con acr1, radicar con acr2; idempotentes por llave)

    def abrir_disputa(
        self,
        sesion: SesionAutenticada,
        conversacion_id: str,
        transaccion_id: str,
        motivo: str,
        confirmacion: Confirmacion,
        credito_provisional: bool = False,
    ) -> tuple[AccionVerificada, bool]:
        ahora = self._exigir(sesion, "abrir_disputa")
        self._exigir_conversacion(sesion, conversacion_id)
        transaccion = self._lectura.transaccion(sesion.cliente_id, transaccion_id)
        if transaccion is None:
            raise AccesoDenegado("la transacción no es del cliente de la sesión")
        if (transaccion.estado or "").lower() in NO_DISPUTABLES:
            raise NoDisputable(transaccion.estado)
        ruta = self.ruta_obligada(sesion, transaccion)
        if ruta is not None:  # lo hace cumplir la herramienta, no solo el prompt
            raise EscalacionRequerida(ruta)
        cliente = sesion.cliente_id

        def ejecutor(llave: str) -> AccionVerificada:
            caso = self._banco.abrir_caso(
                llave, cliente, transaccion_id, transaccion.monto, motivo, credito_provisional
            )
            # La bandera es la del caso, no la de esta llamada: un caso abierto no recibe crédito otra vez.
            sufijo = " con crédito provisional" if self._banco.credito_provisional_de(caso) else ""
            return AccionVerificada(
                accion="abrir_disputa", exito=True, resultado_releido=f"{caso}{sufijo}", hora=ahora
            )

        return ejecutar_una_vez(
            self._almacen,
            conversacion_id=conversacion_id,
            numero_transicion=NUM_ABRIR_DISPUTA,
            tipo="abrir_disputa",
            recurso=transaccion_id,
            confirmacion=confirmacion,
            ejecutor=ejecutor,
        )

    def bloquear_tarjeta(
        self,
        sesion: SesionAutenticada,
        conversacion_id: str,
        producto_id: str,
        confirmacion: Confirmacion,
    ) -> tuple[AccionVerificada, bool]:
        ahora = self._exigir(sesion, "bloquear_tarjeta")
        self._exigir_conversacion(sesion, conversacion_id)
        if all(p.product_id != producto_id for p in self._lectura.productos(sesion.cliente_id)):
            raise AccesoDenegado("el producto no es del cliente de la sesión")
        permitido = self.producto_del_movimiento(sesion, conversacion_id)
        if permitido is not None and permitido != producto_id:
            raise TarjetaFueraDelMovimiento(producto_id)  # sin efecto ni registro verificado
        cliente = sesion.cliente_id

        def ejecutor(llave: str) -> AccionVerificada:
            resultado = self._banco.bloquear_tarjeta(llave, cliente, producto_id)
            return AccionVerificada(
                accion="bloquear_tarjeta", exito=True, resultado_releido=resultado, hora=ahora
            )

        return ejecutar_una_vez(
            self._almacen,
            conversacion_id=conversacion_id,
            numero_transicion=NUM_BLOQUEAR_TARJETA,
            tipo="bloquear_tarjeta",
            recurso=producto_id,
            confirmacion=confirmacion,
            ejecutor=ejecutor,
        )

    def escalar(
        self, sesion: SesionAutenticada, conversacion_id: str, motivo: str, urgente: bool = False
    ) -> tuple[AccionVerificada, bool]:
        """Pasar a un humano no exige confirmación: nunca perjudica al cliente.

        La prioridad no es del modelo ni del cliente: el argumento `urgente` se ignora y la urgencia sale solo
        del motivo, si `policy/v1` (ESC-05) lo marca como urgente (R27).
        """
        urgente = self._politica.es_urgente(motivo)
        ahora = self._exigir(sesion, "escalar")
        self._exigir_conversacion(sesion, conversacion_id)
        cliente = sesion.cliente_id

        def ejecutor(llave: str) -> AccionVerificada:
            if isinstance(self._banco, Banco):  # el banco compartido recibe el paquete completo (2.5.2)
                paquete = construir_paquete(
                    politica=self._politica,
                    lectura=self._lectura,
                    banco=self._banco,
                    almacen=self._almacen,
                    sesion=sesion,
                    conversacion_id=conversacion_id,
                    motivo=motivo,
                    urgente=urgente,
                    ahora=ahora,
                )
                turno = self._banco.encolar_paquete(llave, cliente, conversacion_id, paquete)
            else:
                turno = self._banco.encolar_traspaso(llave, cliente, conversacion_id, motivo, urgente)
            return AccionVerificada(accion="escalar", exito=True, resultado_releido=turno, hora=ahora)

        return ejecutar_una_vez(
            self._almacen,
            conversacion_id=conversacion_id,
            numero_transicion=NUM_ESCALAR,
            tipo="escalar",
            recurso=conversacion_id,
            confirmacion=None,
            ejecutor=ejecutor,
        )
