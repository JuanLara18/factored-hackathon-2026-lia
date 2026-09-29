"""Carga y validación del registro: un YAML por trabajador en `ia/agentes/trabajadores/`."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from latam_ia.registro.esquema import ESTADOS_SIN_MODELO, Registro, Rol, Trabajador

RAIZ_IA = Path(__file__).resolve().parents[3]
DIR_TRABAJADORES = RAIZ_IA / "agentes" / "trabajadores"

ROLES_DISTINTOS = (Rol.SISTEMA, Rol.GENERADOR, Rol.SIMULADOR, Rol.JUEZ)


class ErrorRegistro(ValueError):
    pass


def cargar_registro(directorio: Path = DIR_TRABAJADORES) -> Registro:
    """Lee todos los YAML; el nombre del archivo debe ser el id del trabajador."""
    trabajadores: dict[str, Trabajador] = {}
    for ruta in sorted(directorio.glob("*.yaml")):
        datos: Any = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        try:
            t = Trabajador.model_validate(datos)
        except ValidationError as error:
            raise ErrorRegistro(f"{ruta.name}: {error}") from error
        if t.id != ruta.stem:
            raise ErrorRegistro(f"{ruta.name}: el id {t.id!r} no coincide con el archivo")
        trabajadores[t.id] = t
    return Registro(trabajadores=trabajadores)


def verificar_familias(registro: Registro) -> list[str]:
    """R-IA-09: sistema, generador, simulador y juez de familias distintas. Devuelve las violaciones.

    No se aplica al cargar: con el nivel gratuito de Gemini (D-30) todas las familias son `google`, y la
    violación es un hecho conocido que el informe debe mostrar, no ocultar.
    """
    por_familia: dict[str, set[Rol]] = defaultdict(set)
    for t in registro.trabajadores.values():
        if t.modelo is not None and t.estado not in ESTADOS_SIN_MODELO and t.rol in ROLES_DISTINTOS:
            por_familia[t.modelo.familia].add(t.rol)
    return [
        f"familia {fam} compartida por {sorted(r.value for r in roles)} (R-IA-09)"
        for fam, roles in sorted(por_familia.items())
        if len(roles) > 1
    ]


def verificar_prompts(registro: Registro, existentes: set[str]) -> list[str]:
    """Cada `prompt` del registro apunta a una versión que existe en la biblioteca."""
    return [
        f"{t.id}: prompt {t.prompt} no existe en la biblioteca"
        for t in registro.trabajadores.values()
        if t.prompt is not None and t.prompt not in existentes
    ]
