"""Formatos de la banca (montos del país, horas, enmascarado) y la vista del paquete para la consola."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from latam_tecnologia.banca.modelos import Mensaje, Traspaso
from latam_tecnologia.banca.motivos import Motivo

BOGOTA = timezone(timedelta(hours=-5))  # las horas se muestran en hora de Bogotá (sin cambio de horario)
PAISES = {"CO": "Colombia", "MX": "México", "AR": "Argentina"}
PAIS_POR_MONEDA = {"COP": "CO", "MXN": "MX", "ARS": "AR"}
_CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_NUMERO_LARGO = re.compile(r"(?<![\w])(?:\d[ -]?){6,}\d(?![\w])")


def monto(valor: Decimal | float | str) -> str:
    """`128482.28` como `128.482,28`."""
    entero, _, dec = f"{Decimal(str(valor)):,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{dec}"


def hora(t: datetime) -> str:
    return t.astimezone(BOGOTA).strftime("%H:%M")


def fecha(t: datetime) -> str:
    return t.astimezone(BOGOTA).strftime("%Y-%m-%d")


def enmascarar(texto: str, limite: int = 500) -> str:
    """Quita correos y números largos (documento, teléfono, tarjeta) antes de guardar o mostrar un texto."""
    sin = _NUMERO_LARGO.sub("[dato oculto]", _CORREO.sub("[correo oculto]", texto))
    return sin.strip()[:limite]


def final(product_id: str) -> str:
    return re.sub(r"\D", "", product_id).rjust(4, "0")[-4:]


def vista_paquete(
    t: Traspaso, ahora: datetime, transcripcion: list[Mensaje], mensajes: list[Mensaje], sugerencia: Motivo
) -> dict[str, Any]:
    """Serializa un `Traspaso` con los 19 campos de 2.5.2 en la forma que lee la consola.

    `sugerencia` es el `Motivo` de `motivos.py`: sus pasos salen de la política y se marcan con su regla.
    """
    p = t.paquete
    regla_ref = f"{p.regla.id}@{p.regla.version}" if p.regla else "no disponible"
    urgencia = {1: "alta", 2: "media"}.get(int(t.prioridad[1]), "baja")
    return {
        "id_traspaso": t.id_traspaso,
        "hilo_id": p.hilo_id,
        "caso_id": p.caso_id,
        "prioridad": t.prioridad,
        "motivo": {
            "codigo": p.motivo,
            "texto": p.motivo_texto,
            "regla": None if p.regla is None else {"id": p.regla.id, "version": p.regla.version},
        },
        "cola_destino": None if p.cola_destino is None else p.cola_destino.model_dump(mode="json"),
        "idioma": p.idioma.value,
        "registro": p.registro,
        "pais_cuenta": p.pais_cuenta,
        "canal_actual": p.canal_actual.value,
        "canales_usados": [c.value for c in p.canales_usados],
        "creado_hace_s": max(0, int((ahora - t.creado_en).total_seconds())),
        "estado": t.estado,
        "tomado_por": t.tomado_por,
        "identidad": None
        if p.identidad is None
        else {"nivel": p.identidad.nivel.value, "metodo": p.identidad.metodo, "hora": hora(p.identidad.hora)},
        "que_hacer_primero": [{"paso": paso, "regla": regla_ref} for paso in sugerencia.pasos],
        "compromisos_comunicados": [
            {"texto": c.texto, "hora": hora(c.hora)} for c in p.compromisos_comunicados
        ],
        "solicitud": {"cita": p.solicitud, "idioma": p.idioma.value},
        "interpretacion": {
            "motivo": p.motivo_texto,
            "urgencia": urgencia,
            "entidades": list(p.entidades),
            "confianza": p.interpretaciones[0].confianza if p.interpretaciones else None,
        },
        "hechos_verificados": [
            {"texto": h.valor, "fuente": h.fuente, "hora": hora(h.hora)} for h in p.hechos
        ],
        "acciones_realizadas": [
            {"accion": a.accion, "resultado": a.resultado_releido, "hora": hora(a.hora)} for a in p.acciones
        ],
        "acciones_no_realizadas": [a.model_dump(mode="json") for a in p.acciones_no_realizadas],
        "conflictos": [c.model_dump(mode="json") if not isinstance(c, str) else c for c in p.conflictos],
        "preguntas_abiertas": [
            {
                "pregunta": q.pregunta,
                "a_quien": q.a_quien.replace("_", " "),
                "bloquea": q.bloquea,
            }
            for q in p.preguntas_abiertas
            if not isinstance(q, str)
        ],
        "plazos_en_curso": [
            {
                "regla": z.regla,
                "inicio": hora(z.inicio),
                "vence_en_s": max(0, int((z.vence - ahora).total_seconds())),
            }
            for z in p.plazos_en_curso
        ],
        "evidencia": {
            "traza_url": _traza_url(p.evidencia.traza_id) if p.evidencia else None,
            "reglas": [f"{r.id}@{r.version}" for r in p.evidencia.reglas] if p.evidencia else [],
            "plantillas": list(p.evidencia.plantillas) if p.evidencia else [],
        },
        "transcripcion": [{"autor": m.autor, "texto": m.texto, "en": hora(m.en)} for m in transcripcion],
        "mensajes": [{"id": m.id, "autor": m.autor, "texto": m.texto, "en": hora(m.en)} for m in mensajes],
    }


def _traza_url(traza_id: str) -> str | None:
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto or not re.fullmatch(r"[0-9a-f]{32}", traza_id):
        return None
    return f"https://console.cloud.google.com/traces/list?project={proyecto}&tid={traza_id}"
