"""Carga y validación de la matriz (CLI-1.1), la guía de estilo (CLI-1.2) y las plantillas (CLI-1.3).

Los tres son YAML bajo `clientes/`. La guía de estilo también la consume la biblioteca de prompts de IA:
`frases_prohibidas(estilo, "prompt")` es la única lista de frases prohibidas del repositorio.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

RAIZ_CLIENTES = Path(__file__).resolve().parents[2]
RUTA_MATRIZ = RAIZ_CLIENTES / "matriz" / "matriz.yaml"
RUTA_ESTILO = RAIZ_CLIENTES / "estilo" / "estilo.yaml"
RUTA_PLANTILLAS = RAIZ_CLIENTES / "plantillas" / "es.yaml"

MARCADOR = re.compile(r"\{([a-z_0-9]+)\}")


class ErrorContenido(ValueError):
    pass


class _Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# Matriz


class Registro(_Estricto):
    idioma: str
    exigido: bool
    pendiente: str | None = None


class Celda(_Estricto):
    intencion: str
    plantilla: str


class EstadoMatriz(_Estricto):
    nunca: str
    celdas: dict[str, Celda]


class Matriz(_Estricto):
    version: int
    canales: list[str]
    registros: dict[str, Registro]
    estados: dict[str, EstadoMatriz]

    def registros_exigidos(self) -> list[str]:
        return [r for r, v in self.registros.items() if v.exigido]


# Guía de estilo


class Pais(_Estricto):
    registro: str
    cargo: str
    documento_mensual: str
    pregunta_tipo: str | None = None


class LimitesCanal(_Estricto):
    max_palabras_frase: int
    max_caracteres: int
    vocabulario_prohibido: list[str]


class RequisitosTipo(_Estricto):
    todos: list[str] = []
    por_canal: dict[str, list[str]] = {}


class Regla(_Estricto):
    id: str
    patron: str
    motivo: str | None = None
    alternativa: str | None = None
    alcance: list[Literal["plantilla", "prompt"]] = ["plantilla"]


class AplicaA(_Estricto):
    estados: list[str] = []
    tipos: list[str] = []


class Obligatoria(_Estricto):
    id: str
    aplica_a: AplicaA
    patron: str
    motivo: str


class MarcasRegistro(_Estricto):
    tuteo: str
    voseo: str
    usted: str


class Estilo(_Estricto):
    version: int
    paises: dict[str, Pais]
    pais_neutro: Pais
    terminos_por_pais: list[str]
    canales: dict[str, LimitesCanal]
    marcadores: dict[str, str]
    tipos: dict[str, RequisitosTipo]
    frases_prohibidas: list[Regla]
    caracteres_prohibidos: list[Regla]
    frases_obligatorias: list[Obligatoria]
    marcas_registro: MarcasRegistro


# Plantillas


class Plantilla(_Estricto):
    id: str
    canales: list[str]
    tipos: list[str]
    marcadores: list[str]
    textos: dict[str, str]


class Plantillas(_Estricto):
    version: int
    idioma: str
    plantillas: list[Plantilla]

    def por_id(self) -> dict[str, Plantilla]:
        return {p.id: p for p in self.plantillas}


def _cargar[T: BaseModel](ruta: Path, modelo: type[T]) -> T:
    datos: Any = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    try:
        return modelo.model_validate(datos)
    except ValidationError as error:
        raise ErrorContenido(f"{ruta.name}: {error}") from error


def cargar_matriz(ruta: Path = RUTA_MATRIZ) -> Matriz:
    return _cargar(ruta, Matriz)


def cargar_estilo(ruta: Path = RUTA_ESTILO) -> Estilo:
    return _cargar(ruta, Estilo)


def cargar_plantillas(ruta: Path = RUTA_PLANTILLAS) -> Plantillas:
    return _cargar(ruta, Plantillas)


def frases_prohibidas(estilo: Estilo, alcance: Literal["plantilla", "prompt"]) -> list[re.Pattern[str]]:
    """Patrones prohibidos del alcance dado; es la lista que comparte la biblioteca de prompts de IA."""
    return [re.compile(r.patron, re.IGNORECASE) for r in estilo.frases_prohibidas if alcance in r.alcance]


def renderizar(plantilla: Plantilla, registro: str, valores: dict[str, str]) -> str:
    """Rellena los marcadores; falla si falta o sobra alguno."""
    texto = plantilla.textos[registro]
    usados = set(MARCADOR.findall(texto))
    if usados != set(valores):
        raise ErrorContenido(
            f"{plantilla.id}: faltan {sorted(usados - set(valores))} o sobran {sorted(set(valores) - usados)}"
        )
    return MARCADOR.sub(lambda m: valores[m.group(1)], texto)
