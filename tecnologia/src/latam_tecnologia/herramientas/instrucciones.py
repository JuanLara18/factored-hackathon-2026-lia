"""Instrucciones del agente de disputas: salen de `ia/prompts/disputas/agente@<versión>.yaml`.

Lee el YAML directamente y no importa `latam_ia`, que ya depende de Tecnología (mismo criterio que
`canales/textos.py`). La versión y la huella se registran en `ia/agentes/trabajadores/disputas.yaml`.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml

RUTA_PROMPT = Path(__file__).resolve().parents[4] / "ia" / "prompts" / "disputas" / "agente@1.5.0.yaml"
REFERENCIA = "disputas/agente@1.5.0"
IDIOMA_POR_REGISTRO = {"usted": "es", "vos": "es", "voce": "pt"}
RESPALDO = (
    "Usted es el asistente de inteligencia artificial de un banco. Trate a la persona de usted, consulte "
    "con las herramientas, nunca invente cifras, muestre las tarjetas como terminadas en sus cuatro "
    "últimos dígitos y pida aprobación antes de cualquier acción."
)


@lru_cache(maxsize=1)
def _cargar() -> tuple[dict[str, dict[str, str]], str] | None:
    try:
        crudo = RUTA_PROMPT.read_bytes()
    except OSError:
        return None
    datos = cast(dict[str, Any], yaml.safe_load(crudo))
    return cast(dict[str, dict[str, str]], datos["plantillas"]), hashlib.sha256(crudo).hexdigest()


def instrucciones_disputas(registro: str = "usted") -> str:
    """Texto del prompt para el registro; si el archivo no viaja en la imagen, un respaldo mínimo."""
    cargado = _cargar()
    if cargado is None:
        return RESPALDO
    plantillas, _ = cargado
    idioma = IDIOMA_POR_REGISTRO.get(registro, "es")
    return plantillas[idioma].get(registro) or plantillas["es"]["usted"]


def huella_prompt() -> str | None:
    cargado = _cargar()
    return None if cargado is None else cargado[1]
