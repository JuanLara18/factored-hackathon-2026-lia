"""Esquema de la hoja de vida de un trabajador digital: subconjunto operativo de la sección 2.2.2."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID_TRABAJADOR = re.compile(r"^[a-z][a-z0-9-]*$")
REF_PROMPT = re.compile(r"^[a-z][a-z0-9_]*/[a-z][a-z0-9_]*@\d+\.\d+\.\d+$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


class _Estricto(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Estado(StrEnum):
    PROPUESTO = "propuesto"
    EN_DESARROLLO = "en_desarrollo"
    HABILITADO_DESARROLLO = "habilitado_desarrollo"
    CANDIDATO = "candidato"
    HABILITADO = "habilitado"
    SUSPENDIDO = "suspendido"
    RETIRADO = "retirado"
    EXPERIMENTAL = "experimental"
    NO_DESPLEGABLE = "no_desplegable"


class Riesgo(StrEnum):
    """Nivel asignado por Gobierno (R-GOB-05)."""

    MODERADO = "moderado"
    ALTO = "alto"
    NO_APLICA = "no_aplica"


class Rol(StrEnum):
    """Rol frente a R-IA-09: cuatro familias distintas entre estos roles."""

    SISTEMA = "sistema"
    GENERADOR = "generador"
    SIMULADOR = "simulador"
    JUEZ = "juez"
    VERIFICADOR = "verificador"
    OTRO = "otro"


class Proveedor(StrEnum):
    GEMINI_API = "gemini_api"  # nivel gratuito de AI Studio (D-30), llave en GEMINI_API_KEY
    VERTEX_AI = "vertex_ai"  # destino cuando se reabra la facturación (D-29)


class Persona(_Estricto):
    cara: str
    gerencia: str | None = None
    persona: str | None = None


class Modelo(_Estricto):
    proveedor: Proveedor
    familia: str
    id: str = Field(min_length=1)
    temperatura: float = Field(default=0.0, ge=0.0, le=2.0)
    max_salida: int = Field(gt=0)


class Presupuestos(_Estricto):
    max_entrada: int = Field(gt=0)
    max_salida: int = Field(gt=0)
    llamadas_por_conversacion: int = Field(gt=0)
    usd_diario: float = Field(ge=0)


ESTADOS_SIN_MODELO = {Estado.PROPUESTO, Estado.RETIRADO, Estado.NO_DESPLEGABLE}
ESTADOS_SIN_GATEWAY = ESTADOS_SIN_MODELO | {Estado.SUSPENDIDO}


class Trabajador(_Estricto):
    id: str
    version: str
    estado: Estado
    tipo: str
    rol: Rol = Rol.OTRO
    proposito: str = Field(min_length=10)
    usos_prohibidos: list[str] = Field(min_length=1)
    supervisor: Persona
    duenio_tecnico: Persona
    riesgo: Riesgo
    herramientas: list[str] = Field(default_factory=list)
    prompt: str | None = None
    modelo: Modelo | None = None
    presupuestos: Presupuestos | None = None
    entornos: list[Literal["local", "ci", "dev", "demo"]] = Field(default_factory=lambda: ["dev"])

    @model_validator(mode="after")
    def _reglas(self) -> Trabajador:
        if not ID_TRABAJADOR.match(self.id):
            raise ValueError(f"id inválido: {self.id!r}")
        if not SEMVER.match(self.version):
            raise ValueError(f"{self.id}: la versión debe ser semver (R-IA-06)")
        if self.prompt is not None and not REF_PROMPT.match(self.prompt):
            raise ValueError(f"{self.id}: referencia de prompt inválida {self.prompt!r}")
        if self.tipo.startswith("lenguaje") and self.herramientas and self.id != "frontend-nativo":
            raise ValueError(f"{self.id}: los trabajadores de lenguaje no tienen herramientas (R-IA-03)")
        if self.estado not in ESTADOS_SIN_MODELO and self.modelo is not None:
            if self.presupuestos is None:
                raise ValueError(f"{self.id}: un trabajador con modelo declara presupuestos (R-IA-02)")
            if self.presupuestos.max_salida < self.modelo.max_salida:
                raise ValueError(f"{self.id}: max_salida del modelo excede el presupuesto")
        return self


class Registro(_Estricto):
    trabajadores: dict[str, Trabajador]

    @property
    def ids(self) -> list[str]:
        return sorted(self.trabajadores)
