"""Motor del caso de disputa, herramientas con alcance por cliente y agente con TestModel."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from latam_comun.dominio import Canal, Confirmacion, Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.herramientas.agente import ContextoAgente, crear_agente_disputas
from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa, ServiciosBancoFalsos
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.caso import Estado, Evento, MotorCaso, transicionar
from latam_tecnologia.servicios.almacen import AlmacenMemoria
from pydantic_ai import DeferredToolRequests
from pydantic_ai.models.test import TestModel

AHORA = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def _tx(id_: str, estado: str = "completed", usd: str = "50", producto: str = "p1") -> Transaccion:
    return Transaccion(
        transaction_id=id_,
        product_id=producto,
        event_ts=AHORA - timedelta(days=1),
        monto=Dinero(monto=Decimal("120000"), moneda="COP"),
        amount_usd=Decimal(usd),
        tipo="purchase",
        estado=estado,
        comercio="Tienda Uno",
        categoria="retail",
        pais="CO",
        es_extranjera=False,
    )


def _sesion(cliente: str = "c1", nivel: NivelAcr = NivelAcr.ACCION) -> SesionAutenticada:
    return SesionAutenticada(
        id_sesion="s", cliente_id=cliente, nivel=nivel, expira=AHORA + timedelta(minutes=10)
    )


class Mundo:
    def __init__(self) -> None:
        self.lectura = LecturaOroFalsa(
            transacciones=[
                ("c1", _tx("t1")),
                ("c1", _tx("t2", estado="declined")),
                ("c1", _tx("t3", usd="900")),
                ("c2", _tx("t9", producto="p9")),
            ],
            productos=[
                ("c1", Producto(product_id="p1", tipo="card", estado="active", moneda="COP")),
                ("c2", Producto(product_id="p9", tipo="card", estado="active", moneda="COP")),
            ],
        )
        self.banco = ServiciosBancoFalsos()
        self.almacen = AlmacenMemoria()
        self.h = Herramientas(self.lectura, self.banco, self.almacen, reloj=lambda: AHORA)
        self.motor = MotorCaso(self.almacen, self.h, reloj=lambda: AHORA)


def _conf(accion: str = "abrir_disputa") -> Confirmacion:
    return Confirmacion(accion=accion, canal=Canal.CHAT, evidencia="boton", nonce="n1")


def test_flujo_feliz_abre_disputa_con_credito_provisional() -> None:
    m = Mundo()
    s = _sesion()
    assert m.motor.abrir("k1", s, Canal.CHAT).estado is Estado.IDENTIFICANDO_TRANSACCION
    r = m.motor.identificar("k1", s, "t1")
    assert r.estado is Estado.CONFIRMANDO_ACCION
    assert r.propuesta is not None and r.propuesta.credito_provisional
    r = m.motor.confirmar("k1", s, _conf())
    assert r.estado is Estado.INFORMANDO and r.accion is not None and r.accion.exito
    assert m.motor.cerrar("k1", s).estado is Estado.CIERRE
    assert m.banco.casos == {("c1", "t1"): "caso-1"}
    assert m.banco.creditos_provisionales == ["caso-1"]


def test_monto_alto_sin_credito_provisional() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    r = m.motor.identificar("k1", s, "t3")
    assert r.propuesta is not None and not r.propuesta.credito_provisional


def test_transaccion_no_disputable_escala_a_humano() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    r = m.motor.identificar("k1", s, "t2")
    assert r.estado is Estado.TRASPASO and r.accion is not None
    assert len(m.banco.traspasos) == 1
    assert m.motor.cerrar("k1", s).estado is Estado.CIERRE


def test_urgente_escala_y_no_abre_disputa() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    r = m.motor.identificar("k1", s, "t1", urgente=True)
    assert r.estado is Estado.TRASPASO
    assert m.banco.casos == {} and m.banco.traspasos == [("c1", "k1", True)]


def test_transaccion_inexistente_permanece_identificando() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    assert m.motor.identificar("k1", s, "nada").estado is Estado.IDENTIFICANDO_TRANSACCION


def test_rechazo_del_cliente_cierra_sin_efectos() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    m.motor.identificar("k1", s, "t1")
    assert m.motor.confirmar("k1", s, None).estado is Estado.CIERRE
    assert m.banco.llamadas == 0


def test_transicion_no_listada_lleva_a_falla_segura_y_terminales_no_se_mueven() -> None:
    t = transicionar(Estado.INICIO, Evento.CONFIRMADA)
    assert t.hacia is Estado.FALLA_SEGURA and not t.listada
    assert transicionar(Estado.CIERRE, Evento.ABRIR).hacia is Estado.CIERRE
    assert transicionar(Estado.EJECUTANDO, Evento.ACCESO_DENEGADO).hacia is Estado.NEGADO


def test_confirmar_fuera_de_orden_es_falla_segura() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    assert m.motor.confirmar("k1", s, _conf()).estado is Estado.FALLA_SEGURA
    assert m.banco.llamadas == 0


def test_confirmacion_de_otra_accion_se_rechaza() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    m.motor.identificar("k1", s, "t1")
    with pytest.raises(ValueError):
        m.motor.confirmar("k1", s, _conf("bloquear_tarjeta"))


def test_estado_persiste_y_se_retoma_por_otro_canal() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    m.motor.identificar("k1", s, "t1")
    voz = Confirmacion(accion="abrir_disputa", canal=Canal.VOZ_TELEFONO, evidencia="dtmf", nonce="n2")
    motor2 = MotorCaso(m.almacen, m.h, reloj=lambda: AHORA)  # proceso nuevo: solo cuenta lo persistido
    assert motor2.confirmar("k1", s, voz).estado is Estado.INFORMANDO


def test_idempotencia_del_efecto_doble_confirmacion() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    m.motor.identificar("k1", s, "t1")
    m.motor.confirmar("k1", s, _conf())
    a1, ejecutada1 = m.h.abrir_disputa(s, "k1", "t1", "cargo_no_reconocido", _conf())
    a2, ejecutada2 = m.h.abrir_disputa(s, "k1", "t1", "cargo_no_reconocido", _conf())
    assert not ejecutada1 and not ejecutada2 and a1 == a2
    assert m.banco.llamadas == 1


def test_idempotencia_bloqueo_y_escalado() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    c = _conf("bloquear_tarjeta")
    _, primera = m.h.bloquear_tarjeta(s, "k1", "p1", c)
    _, segunda = m.h.bloquear_tarjeta(s, "k1", "p1", c)
    m.h.escalar(s, "k1", "x")
    m.h.escalar(s, "k1", "x")
    assert (primera, segunda) == (True, False)
    assert m.banco.bloqueos == [("c1", "p1")] and len(m.banco.traspasos) == 1


def test_cliente_no_ve_datos_de_otro_cliente() -> None:
    m = Mundo()
    s = _sesion("c1")
    assert m.h.transaccion(s, "t9").valor is None
    assert {t.transaction_id for t in m.h.transacciones_recientes(s).valor} == {"t1", "t2", "t3"}
    assert m.h.ficha_transaccion(s, "t9").valor is None
    assert all(p.product_id != "p9" for p in m.h.estado_productos(s).valor)


def test_efectos_sobre_recursos_de_otro_cliente_se_niegan() -> None:
    m = Mundo()
    s = _sesion("c1")
    m.motor.abrir("k1", s, Canal.CHAT)
    with pytest.raises(AccesoDenegado):
        m.h.abrir_disputa(s, "k1", "t9", "fraude", _conf())
    with pytest.raises(AccesoDenegado):
        m.h.bloquear_tarjeta(s, "k1", "p9", _conf("bloquear_tarjeta"))
    otra = _sesion("c2")
    with pytest.raises(AccesoDenegado):
        m.h.abrir_disputa(otra, "k1", "t9", "fraude", _conf())  # conversación ajena
    with pytest.raises(AccesoDenegado):
        m.motor.identificar("k1", otra, "t9")
    assert m.banco.llamadas == 0


def test_nivel_y_vigencia() -> None:
    m = Mundo()
    with pytest.raises(AccesoDenegado):
        m.h.transacciones_recientes(_sesion().model_copy(update={"expira": AHORA - timedelta(seconds=1)}))
    m.motor.abrir("k1", _sesion(), Canal.CHAT)
    with pytest.raises(AccesoDenegado):
        m.h.bloquear_tarjeta(_sesion(nivel=NivelAcr.CONSULTA), "k1", "p1", _conf("bloquear_tarjeta"))


def test_agente_testmodel_lee_solo_lo_del_cliente() -> None:
    m = Mundo()
    agente = crear_agente_disputas(TestModel(call_tools=["listar_transacciones", "estado_productos"]))
    deps = ContextoAgente(m.h, _sesion("c1"), "k1", Canal.CHAT)
    r = agente.run_sync("no reconozco un cargo", deps=deps)
    assert isinstance(r.output, str)
    assert "t9" not in r.output and "t1" in r.output


def test_agente_pide_aprobacion_antes_de_cualquier_efecto() -> None:
    m = Mundo()
    m.motor.abrir("k1", _sesion(), Canal.CHAT)
    agente = crear_agente_disputas(TestModel(call_tools=["abrir_disputa"]))
    deps = ContextoAgente(m.h, _sesion("c1"), "k1", Canal.CHAT)
    r = agente.run_sync("disputa t1", deps=deps)
    assert isinstance(r.output, DeferredToolRequests)
    assert m.banco.llamadas == 0
