"""Arma el `PaqueteTraspaso` completo de 2.5.2 con hechos releídos de las fuentes y reglas de `policy/v1`.

Nada de lo que escribe el modelo entra como hecho: los hechos salen de la lectura del oro y del banco, con
su fuente y la hora de la lectura; motivo, prioridad y pasos salen de la política y de la lista cerrada.
No lleva nombre, documento, número de tarjeta, segmento, `fraud_score` ni razonamiento del modelo.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from latam_comun.dominio import (
    AccionNoRealizada,
    Canal,
    ColaDestino,
    Compromiso,
    Conflicto,
    Evidencia,
    HechoVerificado,
    Identidad,
    Idioma,
    PaqueteTraspaso,
    Plazo,
    PreguntaAbierta,
    ReglaAplicada,
    SesionAutenticada,
)
from latam_gobierno.politica import PoliticaV1
from opentelemetry import trace

from latam_tecnologia.banca.banco import Banco
from latam_tecnologia.banca.motivos import ESPECIALIDAD_FRANJA, SLA_S, motivo_de
from latam_tecnologia.banca.refs import ref
from latam_tecnologia.banca.vista import PAIS_POR_MONEDA, enmascarar, fecha, final, hora, monto
from latam_tecnologia.canales import textos
from latam_tecnologia.herramientas.puertos import LecturaOro, Transaccion
from latam_tecnologia.motor.retoma import Almacen

VENTANA_HISTORIAL = timedelta(days=90)
ESTADOS_ACTIVOS = ("active", "activa", "activo")
NO_DISPONIBLE = "no disponible"


def _traza_id(conversacion_id: str) -> str:
    contexto = trace.get_current_span().get_span_context()
    return f"{contexto.trace_id:032x}" if contexto.is_valid else conversacion_id


def _descripcion(tx: Transaccion) -> str:
    return textos.describir_comercio(tx.comercio, tx.tipo)


def construir_paquete(
    *,
    politica: PoliticaV1,
    lectura: LecturaOro,
    banco: Banco,
    almacen: Almacen,
    sesion: SesionAutenticada,
    conversacion_id: str,
    motivo: str,
    urgente: bool,
    ahora: datetime,
) -> PaqueteTraspaso:
    cliente = sesion.cliente_id
    conv = banco.conversacion(conversacion_id)
    registro = conv.registro if conv else "usted"
    m = motivo_de(motivo, urgente)
    recientes = lectura.transacciones_recientes(cliente, 50)
    productos = lectura.productos(cliente)

    # La transacción del contexto: la fijada por el servidor (reclamar) o la del caso abierto más reciente.
    casos = banco.casos_de(cliente)
    tx_id = conv.transaccion_id if conv and conv.transaccion_id else None
    if tx_id is None:
        abiertos = sorted((c for c in casos if c.estado == "abierto"), key=lambda c: c.abierto_en)
        tx_id = abiertos[-1].transaccion_id if abiertos else None
    tx = lectura.transaccion(cliente, tx_id) if tx_id else None
    caso = next((c for c in casos if tx is not None and c.transaccion_id == tx.transaction_id), None)
    producto = next((p for p in productos if tx is not None and p.product_id == tx.product_id), None)

    # Prioridad: la mayor entre la del motivo y la del caso en curso (2.5.1).
    prio = m.prioridad
    if urgente:
        prio = 1
    elif tx is not None and politica.escalar_tras_radicar(tx.monto.moneda, tx.amount_usd) is not None:
        prio = min(prio, 2)
    prioridad = f"P{prio}"

    # Hechos verificados, con fuente y hora de la lectura
    hechos: list[HechoVerificado[str]] = []
    conflictos: list[Conflicto] = []
    entidades: list[str] = []
    if tx is not None:
        hechos.append(
            HechoVerificado(
                valor=(
                    f"Cargo de {monto(tx.monto.monto, tx.monto.moneda)} {tx.monto.moneda} "
                    f"en {_descripcion(tx)} el "
                    f"{fecha(tx.event_ts)} a las {hora(tx.event_ts)}, estado {tx.estado or NO_DISPONIBLE}"
                    f" (movimiento {ref('tx', cliente, tx.transaction_id)})"
                ),
                fuente="transacciones",
                hora=ahora,
            )
        )
        entidades.append(f"comercio {_descripcion(tx)}")
        previas = [
            t
            for t in recientes
            if t.transaction_id != tx.transaction_id
            and t.comercio
            and t.comercio == tx.comercio
            and (t.estado or "").lower() in ("approved", "posted", "settled")
            and timedelta(0) <= tx.event_ts - t.event_ts <= VENTANA_HISTORIAL
            and not any(c.transaccion_id == t.transaction_id for c in casos)
        ]
        if previas:
            registro_previas = f"{len(previas)} compras anteriores no disputadas en este comercio en 90 días"
            hechos.append(HechoVerificado(valor=registro_previas, fuente="transacciones", hora=ahora))
            if conv is not None and conv.transaccion_id:  # el cliente dijo "no reconozco este cargo"
                conflictos.append(
                    Conflicto(
                        tipo="Compras previas en el mismo comercio",
                        declarado="no reconoce el cargo",
                        registro=f"{registro_previas} (transacciones, {hora(ahora)})",
                    )
                )
    if producto is not None:
        bloqueada = banco.bloqueado(cliente, producto.product_id)
        estado = "bloqueada" if bloqueada else (producto.estado or NO_DISPONIBLE)
        hechos.append(
            HechoVerificado(
                valor=f"Tarjeta terminada en {final(producto.product_id)} en estado {estado}",
                fuente="productos",
                hora=ahora,
            )
        )
        entidades.append(f"tarjeta terminada en {final(producto.product_id)}")
    if tx is not None:
        hechos.append(
            HechoVerificado(
                valor=(
                    f"Reclamo abierto por este movimiento ({caso.caso_ref})"
                    + (" con crédito provisional registrado" if caso.credito_provisional else "")
                    if caso is not None
                    else "Sin reclamo abierto por este movimiento"
                ),
                fuente="casos",
                hora=ahora,
            )
        )
    if not hechos:
        hechos.append(
            HechoVerificado(
                valor=f"{NO_DISPONIBLE}: el cliente no llegó a indicar un movimiento",
                fuente="conversacion",
                hora=ahora,
            )
        )

    acciones = almacen.acciones_hechas(conversacion_id)
    hechas = {a.accion for a in acciones if a.exito}
    razon = (
        "pidió persona antes de confirmar"
        if m.codigo == "CLIENTE_PIDE_PERSONA"
        else "no se confirmó la acción"
    )
    no_realizadas: list[AccionNoRealizada] = []
    if tx is not None and caso is None and "abrir_disputa" not in hechas:
        no_realizadas.append(AccionNoRealizada(accion="Radicar el reclamo", motivo=razon))
    if (
        producto is not None
        and "bloquear_tarjeta" not in hechas
        and not banco.bloqueado(cliente, producto.product_id)
    ):
        no_realizadas.append(AccionNoRealizada(accion="Bloquear la tarjeta", motivo=razon))
    no_realizadas.append(
        AccionNoRealizada(accion="Abonar el crédito provisional", motivo="lo mueve el back office (R-GOB-30)")
    )

    preguntas: list[PreguntaAbierta] = []
    if tx is None:
        preguntas.append(
            PreguntaAbierta(pregunta="¿Sobre qué movimiento es la consulta?", a_quien="cliente", bloquea=True)
        )
    if caso is not None and caso.credito_provisional:
        preguntas.append(
            PreguntaAbierta(
                pregunta="¿Se confirmó el abono del crédito provisional?",
                a_quien="back_office",
                bloquea=False,
            )
        )
    if m.prioridad == 1:
        preguntas.append(
            PreguntaAbierta(
                pregunta="¿El cliente compartió algún código con un tercero?",
                a_quien="cliente",
                bloquea=False,
            )
        )

    plazos = [
        Plazo(
            regla=f"Atención de P{prio} en vivo", inicio=ahora, vence=ahora + timedelta(seconds=SLA_S[prio])
        )
    ]
    if caso is not None and caso.plazo:
        plazos.append(
            Plazo(
                regla="Abono provisional en México (MX-06)",
                inicio=caso.abierto_en,
                vence=caso.abierto_en + timedelta(hours=48),
            )
        )

    # País de la cuenta (el de la conversación, que viene de la vista segura); el del movimiento puede ser
    # otro (compras en el exterior) y la moneda no lo dice (en México se opera en USD).
    pais = conv.pais if conv is not None and conv.pais else None
    if pais is None:
        pais = (tx.pais if tx and tx.pais else None) or (PAIS_POR_MONEDA.get(tx.monto.moneda) if tx else None)
    if pais is None and productos and productos[0].moneda:
        pais = PAIS_POR_MONEDA.get(productos[0].moneda)

    try:
        texto_compromiso = textos.plantilla("traspaso.chat", registro, rango_espera="unos minutos")
        plantillas = ("traspaso.chat",)
    except Exception:  # plantilla ausente: se declara, no se inventa
        texto_compromiso, plantillas = NO_DISPONIBLE, ()

    turnos_cliente = [t for t in (conv.transcripcion if conv else []) if t.autor == "cliente"]
    solicitud = (
        turnos_cliente[-1].texto
        if turnos_cliente
        else (conv.solicitud if conv and conv.solicitud else None)
        or (
            f"Reclamo desde la banca en línea: no reconoce el cargo de {_descripcion(tx)}"
            if tx is not None and conv is not None and conv.transaccion_id
            else NO_DISPONIBLE
        )
    )

    conocidas = {x.id for x in politica.traspaso.disparadores}
    conocidas |= {r.id for r in politica.escalamiento.reglas} | {politica.escalamiento.radicar_y_escalar.id}
    regla = ReglaAplicada(id=m.disparador, version=politica.referencia) if m.disparador in conocidas else None
    reglas = (regla,) if regla else ()
    return PaqueteTraspaso(
        solicitud=enmascarar(solicitud),
        hechos=tuple(hechos),
        interpretaciones=(),
        conflictos=tuple(conflictos),
        acciones=acciones,
        preguntas_abiertas=tuple(preguntas),
        motivo=m.codigo,
        idioma=Idioma.ES,
        prioridad=prioridad,  # pyright: ignore[reportArgumentType]
        hilo_id=conversacion_id,
        caso_id=caso.caso_ref if caso else None,
        motivo_texto=m.texto,
        regla=regla,
        cola_destino=ColaDestino(idioma="es", especialidad=m.especialidad, franja=ESPECIALIDAD_FRANJA[prio]),
        registro=registro,
        pais_cuenta=pais,
        canal_actual=Canal.CHAT,
        canales_usados=(Canal.CHAT,),
        identidad=Identidad(nivel=sesion.nivel, metodo="sesión de demostración", hora=ahora),
        acciones_no_realizadas=tuple(no_realizadas),
        plazos_en_curso=tuple(plazos),
        compromisos_comunicados=(Compromiso(texto=texto_compromiso, hora=ahora),),
        preferencias={"registro": registro, "canal_de_aviso": "chat"},
        evidencia=Evidencia(traza_id=_traza_id(conversacion_id), reglas=reglas, plantillas=plantillas),
        transcripcion_ref=f"conversaciones/{conversacion_id}/transcripcion",
        entidades=tuple(entidades),
    )
