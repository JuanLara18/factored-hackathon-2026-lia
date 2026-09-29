"""Léxicos prohibidos de la biblioteca de prompts (2.5.5): fuente única para pruebas y verificadores."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from latam_ia.prompts.biblioteca import RAIZ_PROMPTS

RUTA_LEXICOS = RAIZ_PROMPTS / "lexicos_prohibidos.yaml"


def cargar_lexicos(ruta: Path = RUTA_LEXICOS) -> dict[str, tuple[str, ...]]:
    """Clase de léxico a sus frases en minúscula."""
    datos: Any = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    clases: dict[str, list[str]] = datos["clases"]
    return {clase: tuple(f.lower() for f in frases) for clase, frases in clases.items()}


def frases_prohibidas(ruta: Path = RUTA_LEXICOS) -> tuple[str, ...]:
    return tuple(f for frases in cargar_lexicos(ruta).values() for f in frases)
