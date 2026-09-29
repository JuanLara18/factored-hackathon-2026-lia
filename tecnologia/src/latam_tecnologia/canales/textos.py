"""Textos del chat: salen de `clientes/plantillas/es.yaml`, nunca del código (CLI-2.1, R-CLI-21).

Este módulo lee el YAML directamente y no importa `latam_clientes`, que ya depende de Tecnología.
Los valores de los marcadores (acción, objeto, consecuencia) son vocabulario del canal; las frases
completas son siempre de la plantilla.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml

RUTA_PLANTILLAS = Path(__file__).resolve().parents[4] / "clientes" / "plantillas" / "es.yaml"
REGISTROS = ("usted", "vos")
_MARCADOR = re.compile(r"\{([a-z_0-9]+)\}")

# Plantillas de chat que usa la página (id de plantilla por función).
PLANTILLAS_PAGINA = {
    "aviso": "inicio.chat",
    "procesando": "ejecutando.chat",
    "traspaso": "traspaso.chat",
    "falla": "falla_segura.chat",
    "sin_cambios": "cierre.sin_cambios",
}

# Etiquetas de los componentes (CLI-2.1 las llevará a la plantilla; hasta entonces viven aquí, cortas para
# respetar los 20 caracteres de R-CLI-47). Mismos textos en ambos registros salvo donde el verbo cambia.
ETIQUETAS: dict[str, dict[str, str]] = {
    "usted": {
        "persona": "Hablar con una persona",
        "confirmo": "Confirmo",
        "no": "No",
        "reconozco": "La reconozco",
        "no_reconozco": "No la reconozco",
        "renovar": "Volver a preguntar",
        "enviar": "Enviar",
        "escribir": "Escriba su mensaje",
        "ia": "Asistente de IA",
        "vence": "Esta confirmación vence en",
        "vencida": "La confirmación venció.",
        "vence_pronto": "Queda un minuto para confirmar.",
        "tarjeta": "Tarjeta terminada en",
        "registro": "Tratamiento",
        "cliente": "Cliente de demostración",
        "iniciar": "Iniciar conversación",
        "demo": "Demostración",
        "conversacion": "Conversación",
        "ir_mensaje": "Ir al campo de mensaje",
        "sesion_vencida": "La sesión terminó. Inicie una nueva conversación.",
        "error_red": "No pude conectarme.",
    },
    "vos": {
        "persona": "Hablar con una persona",
        "confirmo": "Confirmo",
        "no": "No",
        "reconozco": "La reconozco",
        "no_reconozco": "No la reconozco",
        "renovar": "Volver a preguntar",
        "enviar": "Enviar",
        "escribir": "Escribí tu mensaje",
        "ia": "Asistente de IA",
        "vence": "Esta confirmación vence en",
        "vencida": "La confirmación venció.",
        "vence_pronto": "Queda un minuto para confirmar.",
        "tarjeta": "Tarjeta terminada en",
        "registro": "Tratamiento",
        "cliente": "Cliente de demostración",
        "iniciar": "Iniciar conversación",
        "demo": "Demostración",
        "conversacion": "Conversación",
        "ir_mensaje": "Ir al campo de mensaje",
        "sesion_vencida": "La sesión terminó. Iniciá una nueva conversación.",
        "error_red": "No pude conectarme.",
    },
}

# Valores de marcadores para la confirmación de cada herramienta con efecto.
CONFIRMACION: dict[str, dict[str, str]] = {
    "abrir_disputa": {
        "accion": "abrir un reclamo",
        "consecuencia": "el banco revisará el cargo; bloquear la tarjeta es un paso aparte",
    },
    "bloquear_tarjeta": {
        "accion": "bloquear",
        "consecuencia": "la tarjeta no podrá usarse; abrir un reclamo es un paso aparte",
    },
    "escalar": {
        "accion": "pasar el caso a",
        "consecuencia": "una persona del equipo lo retomará sin que tenga que repetir nada",
    },
}


@lru_cache(maxsize=1)
def _plantillas() -> dict[str, dict[str, str]]:
    datos = cast(dict[str, Any], yaml.safe_load(RUTA_PLANTILLAS.read_text(encoding="utf-8")))
    filas = cast(list[dict[str, Any]], datos["plantillas"])
    return {str(f["id"]): cast(dict[str, str], f["textos"]) for f in filas}


def plantilla(plantilla_id: str, registro: str, **valores: str) -> str:
    """Rellena una plantilla; falla si faltan o sobran marcadores."""
    texto = " ".join(_plantillas()[plantilla_id][registro].split())
    usados = set(_MARCADOR.findall(texto))
    if usados != set(valores):
        raise KeyError(
            f"{plantilla_id}: faltan {sorted(usados - set(valores))} o sobran {sorted(set(valores) - usados)}"
        )
    return _MARCADOR.sub(lambda m: valores[m.group(1)], texto)


def registro_valido(registro: str | None) -> str:
    return registro if registro in REGISTROS else "usted"


def catalogo_pagina(registro: str) -> dict[str, Any]:
    """Todo lo que la página necesita mostrar, en el registro pedido."""
    r = registro_valido(registro)
    textos = {
        clave: plantilla(pid, r, **({"rango_espera": "unos minutos"} if pid == "traspaso.chat" else {}))
        for clave, pid in PLANTILLAS_PAGINA.items()
    }
    return {"registro": r, "textos": textos, "etiquetas": ETIQUETAS[r]}


def confirmacion(
    herramienta: str, registro: str, objeto: str, monto: str | None = None, moneda: str = ""
) -> str:
    """Texto de la confirmación; el monto, cuando hay, sale de la base (R-CLI-45)."""
    v = CONFIRMACION[herramienta]
    if monto is not None:
        return plantilla(
            "confirmacion.reclamo.chat",
            registro,
            accion=v["accion"],
            objeto=objeto,
            monto=monto,
            moneda=moneda,
            consecuencia=v["consecuencia"],
        )
    return plantilla(
        "confirmando.chat", registro, accion=v["accion"], objeto=objeto, consecuencia=v["consecuencia"]
    )
