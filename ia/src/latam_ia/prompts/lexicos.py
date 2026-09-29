"""Léxicos prohibidos de 2.5.5: lector delgado de `clientes/estilo/estilo.yaml` (alcance `respuesta`)."""

from __future__ import annotations

import re

from latam_clientes.contenido import Estilo, cargar_estilo


def cargar_lexicos(estilo: Estilo | None = None) -> dict[str, tuple[re.Pattern[str], ...]]:
    """Clase de léxico (promesa, acusacion, asesoria, identidad, ...) a sus patrones de respuesta."""
    estilo = estilo or cargar_estilo()
    clases: dict[str, list[re.Pattern[str]]] = {}
    for r in estilo.frases_prohibidas:
        if "respuesta" in r.alcance:
            clases.setdefault(r.clase or r.id, []).append(re.compile(r.patron, re.IGNORECASE))
    return {c: tuple(ps) for c, ps in clases.items()}


def frases_prohibidas(estilo: Estilo | None = None) -> tuple[re.Pattern[str], ...]:
    return tuple(p for ps in cargar_lexicos(estilo).values() for p in ps)
