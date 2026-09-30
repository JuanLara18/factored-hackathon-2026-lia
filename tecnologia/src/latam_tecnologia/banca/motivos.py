"""Motivos de traspaso de la definición de Clientes (2.5.1): lista cerrada, prioridad P1 a P4 y texto llano.

La prioridad de un traspaso es la mayor entre la de su motivo y la del caso en curso. Los disparadores y
umbrales salen de `policy/v1`; aquí solo se traduce el motivo que trae el motor a su código cerrado.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Motivo:
    codigo: str
    prioridad: int
    texto: str
    especialidad: str
    disparador: str | None  # id de policy/v1 (traspaso.yaml o escalamiento.yaml); None si no hay
    pasos: tuple[str, ...]


def _m(codigo: str, prio: int, texto: str, esp: str, disp: str | None, *pasos: str) -> Motivo:
    return Motivo(codigo, prio, texto, esp, disp, pasos)


MOTIVOS: dict[str, Motivo] = {
    m.codigo: m
    for m in (
        _m(
            "URGENCIA_TRANSFERENCIA",
            1,
            "Transferencia inmediata que el cliente no reconoce: solo cuentan los minutos",
            "fraude",
            "TRA-01",
            "Reportar la transferencia a la entidad receptora.",
            "Contactar al cliente en este mismo hilo.",
        ),
        _m(
            "SUPLANTACION_DEL_BANCO",
            1,
            "El cliente dice que lo llamaron del banco: posible suplantación",
            "fraude",
            "TRA-01",
            "Reportar la transferencia a la entidad receptora.",
            "Dar la frase de seguridad y confirmar que no compartió códigos.",
        ),
        _m(
            "FRAUDE_EN_CURSO",
            1,
            "Fraude en curso: siguen llegando cargos",
            "fraude",
            "TRA-01",
            "Confirmar que la tarjeta esté bloqueada y revisar los cargos posteriores.",
        ),
        _m("CRISIS", 1, "El cliente muestra señales de crisis personal", "servicio", None),
        _m(
            "MONTO_SOBRE_UMBRAL",
            2,
            "El monto del cargo supera el umbral de la política: lo revisa una persona",
            "disputas",
            "ESC-04",
            "Revisar el historial del comercio antes de resolver.",
            "Confirmar que el crédito provisional, si aplica, quedó registrado en el caso.",
        ),
        _m(
            "CONFLICTO_CON_HISTORIAL",
            2,
            "Lo declarado por el cliente difiere del registro",
            "disputas",
            None,
            "Revisar los conflictos declarado frente a registro antes de responder.",
        ),
        _m("PUNTO_COMUN_DE_COMPROMISO", 2, "Señal de punto común de compromiso", "fraude", None),
        _m(
            "CAMBIO_DATOS_CONTACTO",
            2,
            "Cambio de datos de contacto: exige verificación adicional",
            "servicio",
            None,
        ),
        _m(
            "CLIENTE_PIDE_PERSONA",
            3,
            "El cliente pidió hablar con una persona",
            "servicio",
            "TRA-04",
            "Preguntar en qué puede ayudar y qué movimiento le preocupa.",
        ),
        _m("FRUSTRACION", 3, "El cliente muestra frustración con el asistente", "servicio", None),
        _m(
            "BAJA_CONFIANZA",
            3,
            "El asistente no tuvo confianza suficiente para seguir",
            "disputas",
            "TRA-06",
            "Confirmar con el cliente el movimiento y el motivo del reclamo.",
        ),
        _m("FUERA_DE_RUTINA", 3, "Caso fuera de la rutina del asistente", "disputas", None),
        _m("CUENTA_NO_ACTIVA", 3, "El producto no está activo", "servicio", None),
        _m("FUERA_DE_PLAZO", 3, "Reclamo posiblemente fuera de plazo", "disputas", "TRA-07"),
        _m(
            "DATO_INCONSISTENTE",
            3,
            "Un dato no pudo verificarse en la base",
            "disputas",
            "ESC-03",
            "Verificar el producto o el movimiento con el back office.",
        ),
        _m("FALLA_DE_HERRAMIENTA", 4, "Falló una herramienta del asistente", "servicio", None),
        _m("TRANSACCION_NO_VISIBLE", 4, "El movimiento aún no se ve en el registro", "servicio", None),
        _m(
            "TRANSACCION_NO_DISPUTABLE",
            3,
            "El cargo está rechazado, fallido o revertido y el cliente insiste en disputarlo",
            "disputas",
            "TRA-02",
            "Explicar con la ficha del movimiento por qué no hubo cobro.",
        ),
    )
}

# Motivos con que llegan el botón de persona y el modelo (texto libre del motor) a su código cerrado.
ALIAS = {
    "urgente": "URGENCIA_TRANSFERENCIA",
    "transaccion_no_disputable": "TRANSACCION_NO_DISPUTABLE",
    "producto_no_encontrado": "DATO_INCONSISTENTE",
    "monto_sobre_umbral": "MONTO_SOBRE_UMBRAL",
    "cliente_pidio_persona": "CLIENTE_PIDE_PERSONA",
    "cliente_pide_persona": "CLIENTE_PIDE_PERSONA",
    "fraude_en_curso": "FRAUDE_EN_CURSO",
    "suplantacion": "SUPLANTACION_DEL_BANCO",
}

# Atención en vivo por prioridad, en segundos (PROVISIONAL: la definición no fija el acuerdo de servicio).
SLA_S = {1: 120, 2: 900, 3: 1200, 4: 3600}
ESPECIALIDAD_FRANJA = {1: "24 horas", 2: "turno de tarde", 3: "turno de tarde", 4: "horario hábil"}


def motivo_de(texto: str, urgente: bool) -> Motivo:
    """Código cerrado del motivo del motor; urgente manda y lo desconocido es `FUERA_DE_RUTINA`."""
    if urgente:
        return MOTIVOS["URGENCIA_TRANSFERENCIA"]
    clave = texto.strip().lower()
    codigo = ALIAS.get(clave) or clave.upper()
    return MOTIVOS.get(codigo) or MOTIVOS["FUERA_DE_RUTINA"]
