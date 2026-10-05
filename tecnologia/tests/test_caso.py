"""Motor del caso de disputa, herramientas con alcance por cliente y agente con TestModel."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from latam_comun.dominio import Canal, Confirmacion, Dinero, NivelAcr, SesionAutenticada
from latam_tecnologia.herramientas.agente import ContextoAgente, crear_agente_disputas
from latam_tecnologia.herramientas.catalogo import (
    AccesoDenegado,
    EscalacionRequerida,
    Herramientas,
    TarjetaFueraDelMovimiento,
)
from latam_tecnologia.herramientas.falsos import LecturaOroFalsa, ServiciosBancoFalsos
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.caso import Estado, Evento, MotorCaso, transicionar
from latam_tecnologia.servicios.almacen import AlmacenMemoria
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
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
                ("c1", _tx("t4", usd="1500")),
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
    assert {t.transaction_id for t in m.h.transacciones_recientes(s).valor} == {"t1", "t2", "t3", "t4"}
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
    consulta = _sesion(nivel=NivelAcr.CONSULTA)
    accion, _ = m.h.bloquear_tarjeta(consulta, "k1", "p1", _conf("bloquear_tarjeta"))  # D-31: acr1 basta
    assert accion.exito
    with pytest.raises(AccesoDenegado):
        m.h.abrir_disputa(consulta, "k1", "t1", "fraude", _conf())  # radicar sigue en acr2


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


def test_monto_sobre_el_umbral_radica_y_luego_escala() -> None:
    m = Mundo()
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    r = m.motor.identificar("k1", s, "t4")
    assert r.estado is Estado.CONFIRMANDO_ACCION and r.propuesta is not None
    assert r.propuesta.escalar_despues == "monto_sobre_umbral"
    r = m.motor.confirmar("k1", s, _conf())
    assert r.accion is not None and r.accion.exito and r.escalada is not None
    assert m.banco.casos == {("c1", "t4"): "caso-1"} and len(m.banco.traspasos) == 1


# Hallazgos de la evaluación (5 oct): la política se hace cumplir en la herramienta, no en el prompt.


def _escalar_como_modelo(m: Mundo, motivo: str, urgente: bool) -> None:
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    m.h.escalar(s, "k1", motivo, urgente)


def test_r27_el_cliente_no_sube_su_propia_prioridad() -> None:
    m = Mundo()
    _escalar_como_modelo(m, "Solicitud de usuario", urgente=True)  # lo que hizo el modelo bajo inyección
    assert m.banco.traspasos == [("c1", "k1", False)]


def test_r27_solo_un_motivo_de_politica_es_urgente() -> None:
    m = Mundo()
    _escalar_como_modelo(m, "fraude_en_curso", urgente=False)
    assert m.banco.traspasos == [("c1", "k1", True)]


def test_r21_abrir_disputa_con_producto_desconocido_exige_escalar() -> None:
    m = Mundo()
    m.lectura._tx.append(("c1", _tx("t7", producto="p-fantasma")))  # pyright: ignore[reportPrivateUsage]
    s = _sesion()
    m.motor.abrir("k1", s, Canal.CHAT)
    with pytest.raises(EscalacionRequerida) as e:
        m.h.abrir_disputa(s, "k1", "t7", "fraude", _conf())
    assert e.value.motivo == "producto_no_encontrado" and m.banco.llamadas == 0


def test_r21_la_herramienta_del_agente_rechaza_antes_de_pedir_aprobacion() -> None:
    m = Mundo()
    m.lectura._tx.append(("c1", _tx("t7", producto="p-fantasma")))  # pyright: ignore[reportPrivateUsage]
    m.motor.abrir("k1", _sesion(), Canal.CHAT)

    def modelo(mensajes: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(mensajes) == 1:
            return ModelResponse(
                parts=[ToolCallPart("abrir_disputa", {"transaction_id": "t7", "motivo": "fraude"})]
            )
        return ModelResponse(parts=[TextPart("lo paso con una persona")])

    agente = crear_agente_disputas(FunctionModel(modelo))
    deps = ContextoAgente(m.h, _sesion(), "k1", Canal.CHAT)
    r = agente.run_sync("disputa t7", deps=deps)
    assert isinstance(r.output, DeferredToolRequests)  # la herramienta pide aprobación como siempre
    pedida = r.output.approvals[0]
    aprobada = DeferredToolResults(approvals={pedida.tool_call_id: True})
    r = agente.run_sync(None, message_history=r.all_messages(), deferred_tool_results=aprobada, deps=deps)
    retorno = next(p for x in r.all_messages() for p in x.parts if isinstance(p, ToolReturnPart))
    assert "llamar a escalar con motivo producto_no_encontrado" in str(retorno.content)
    assert m.banco.llamadas == 0 and m.banco.casos == {}


def test_r21_el_listado_marca_la_ruta_obligada() -> None:
    m = Mundo()
    m.lectura._tx.append(("c1", _tx("t7", producto="p-fantasma")))  # pyright: ignore[reportPrivateUsage]
    rutas = dict(
        zip(
            ("t7", "t1"),
            m.h.rutas_obligadas(_sesion(), (_tx("t7", producto="p-fantasma"), _tx("t1"))),
            strict=True,
        )
    )
    assert rutas == {"t7": "producto_no_encontrado", "t1": None}


def test_r07_listar_transacciones_alcanza_cobros_viejos_y_busca() -> None:
    m = Mundo()
    s = _sesion()
    for i in range(30):
        m.lectura._tx.append(  # pyright: ignore[reportPrivateUsage]
            (
                "c1",
                _tx(f"x{i}").model_copy(
                    update={"event_ts": AHORA - timedelta(hours=i + 2), "comercio": f"Local {i}"}
                ),
            )
        )
    assert len(m.h.transacciones_recientes(s).valor) == 34  # antes el límite era 10
    assert len(m.h.transacciones_recientes(s, 10_000).valor) == 34  # tope duro, pero alto
    assert len(m.h.transacciones_recientes(s, 5).valor) == 5
    hallado = m.h.transacciones_recientes(s, comercio="local 29").valor
    assert [t.transaction_id for t in hallado] == ["x29"]
    ayer = (AHORA - timedelta(days=1)).date()
    por_fecha = m.h.transacciones_recientes(s, desde=ayer, hasta=ayer, monto=Decimal("120000")).valor
    assert {t.transaction_id for t in por_fecha} >= {"t1"}
    assert all(t.transaction_id != "t9" for t in m.h.transacciones_recientes(s, comercio="Tienda").valor)


# Bloqueo de una sola tarjeta cuando el servidor fijó un movimiento (hallazgo de producción).


class _BancoConMovimiento(ServiciosBancoFalsos):
    def __init__(self, transaccion_id: str | None) -> None:
        super().__init__()
        self._tx = transaccion_id

    def conversacion(self, conversacion_id: str) -> object:
        return SimpleNamespace(transaccion_id=self._tx)


def _mundo_varias_tarjetas(transaccion_id: str | None) -> Mundo:
    m = Mundo()
    m.lectura._prod.append(  # pyright: ignore[reportPrivateUsage]
        ("c1", Producto(product_id="p2", tipo="card", estado="active", moneda="COP"))
    )
    m.banco = _BancoConMovimiento(transaccion_id)
    m.h = Herramientas(m.lectura, m.banco, m.almacen, reloj=lambda: AHORA)
    m.motor = MotorCaso(m.almacen, m.h, reloj=lambda: AHORA)
    m.motor.abrir("k1", _sesion(), Canal.CHAT)
    return m


def test_con_movimiento_fijado_solo_se_bloquea_la_tarjeta_del_movimiento() -> None:
    m = _mundo_varias_tarjetas("t1")  # t1 es de la tarjeta p1
    s = _sesion()
    with pytest.raises(TarjetaFueraDelMovimiento):
        m.h.bloquear_tarjeta(s, "k1", "p2", _conf("bloquear_tarjeta"))
    assert m.banco.bloqueos == []
    accion, _ = m.h.bloquear_tarjeta(s, "k1", "p1", _conf("bloquear_tarjeta"))
    assert accion.exito and m.banco.bloqueos == [("c1", "p1")]
    m.h.bloquear_tarjeta(s, "k1", "p1", _conf("bloquear_tarjeta"))  # idempotente
    assert len(m.banco.bloqueos) == 1


def test_sin_movimiento_fijado_el_chat_suelto_conserva_su_comportamiento() -> None:
    m = _mundo_varias_tarjetas(None)
    accion, _ = m.h.bloquear_tarjeta(_sesion(), "k1", "p2", _conf("bloquear_tarjeta"))
    assert accion.exito and m.banco.bloqueos == [("c1", "p2")]
    assert Mundo().h.producto_del_movimiento(_sesion(), "k1") is None


def test_la_herramienta_del_agente_responde_con_texto_y_marca_las_tarjetas() -> None:
    m = _mundo_varias_tarjetas("t1")
    deps = ContextoAgente(m.h, _sesion(), "k1", Canal.CHAT)

    def modelo(mensajes: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(mensajes) == 1:
            return ModelResponse(parts=[ToolCallPart("estado_productos", {})])
        if len(mensajes) == 3:
            return ModelResponse(parts=[ToolCallPart("bloquear_tarjeta", {"product_id": "p2"})])
        return ModelResponse(parts=[TextPart("listo")])

    agente = crear_agente_disputas(FunctionModel(modelo))
    r = agente.run_sync("me clonaron la tarjeta", deps=deps)
    assert isinstance(r.output, DeferredToolRequests)
    r = agente.run_sync(
        None,
        message_history=r.all_messages(),
        deferred_tool_results=DeferredToolResults(approvals={r.output.approvals[0].tool_call_id: True}),
        deps=deps,
    )
    retornos = [str(p.content) for x in r.all_messages() for p in x.parts if isinstance(p, ToolReturnPart)]
    assert '"bloqueable_aqui": false' in retornos[0] and '"bloqueable_aqui": true' in retornos[0]
    assert "Bloquear tarjeta" in retornos[1] and m.banco.bloqueos == []


def test_el_modelo_recibe_el_final_de_la_tarjeta_ya_calculado() -> None:
    """En producción el modelo inventó "terminada en 8245" para `PRD-0NIQ9GNSPUNF`: solo veía el id."""
    import json

    from latam_tecnologia.banca.vista import final
    from latam_tecnologia.canales.frases import enmascarar_identificadores
    from latam_tecnologia.herramientas.puertos import final_tarjeta

    # una sola regla en todas las capas
    for pid in ("PRD-0NIQ9GNSPUNF", "PRD-YOT0QLCN8E26", "PRD-632BHIER1IHK", "p1"):
        assert final_tarjeta(pid) == final(pid)
    assert final_tarjeta("PRD-0NIQ9GNSPUNF") == "0009"
    assert "terminada en 0009" in enmascarar_identificadores("la tarjeta PRD-0NIQ9GNSPUNF")

    m = Mundo()
    agente = crear_agente_disputas(TestModel(call_tools=["listar_transacciones", "estado_productos"]))
    r = agente.run_sync("no reconozco un cargo", deps=ContextoAgente(m.h, _sesion("c1"), "k1", Canal.CHAT))
    devueltos = {
        p.tool_name: json.loads(str(p.content))
        for msg in r.all_messages()
        for p in msg.parts
        if isinstance(p, ToolReturnPart)
    }
    # el listado de productos no lo trae: con él, el modelo preguntaba en texto antes de bloquear
    assert devueltos["estado_productos"] and all("final" not in f for f in devueltos["estado_productos"])
    assert devueltos["listar_transacciones"] and all(
        f["tarjeta_final"] == final_tarjeta(f["product_id"]) for f in devueltos["listar_transacciones"]
    )
