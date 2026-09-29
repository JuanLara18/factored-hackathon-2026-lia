"""Carga, huella y renderizado de prompts.

Archivo por versión: `ia/prompts/<grupo>/<nombre>@<semver>.yaml`. La huella es el SHA-256 de los bytes del
archivo, de modo que cualquier cambio (texto, metadatos) cambia la huella y se ve en la traza.

Los marcadores se escriben `${nombre}` y se declaran en `marcadores`; el renderizado falla si falta uno, si
sobra uno o si la plantilla usa uno no declarado. Ninguna regla de negocio va en un prompt (P4, R-IA-56):
los valores los pone el motor.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from string import Template
from typing import Any

import yaml
from latam_comun.dominio.tipos import Idioma
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

RAIZ_PROMPTS = Path(__file__).resolve().parents[3] / "prompts"
MARCADOR = re.compile(r"\$\{([a-z_][a-z0-9_]*)\}")

# Tratamiento por idioma (sección 2.5.3). El español admite usted y vos; el portugués, você.
REGISTROS_POR_IDIOMA: dict[str, set[str]] = {"es": {"usted", "vos"}, "pt": {"voce"}}


class ErrorPrompt(ValueError):
    pass


class Prompt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    trabajador: str
    descripcion: str
    marcadores: list[str] = Field(default_factory=list)
    plantillas: dict[str, dict[str, str]]
    huella: str = ""

    @property
    def referencia(self) -> str:
        return f"{self.id}@{self.version}"

    @model_validator(mode="after")
    def _plantillas(self) -> Prompt:
        for idioma, por_registro in self.plantillas.items():
            if idioma not in REGISTROS_POR_IDIOMA:
                raise ValueError(f"{self.referencia}: idioma no admitido {idioma!r}")
            if set(por_registro) != REGISTROS_POR_IDIOMA[idioma]:
                raise ValueError(
                    f"{self.referencia}: {idioma} exige los registros {REGISTROS_POR_IDIOMA[idioma]}"
                )
            for registro, texto in por_registro.items():
                usados = set(MARCADOR.findall(texto))
                if usados != set(self.marcadores):
                    raise ValueError(
                        f"{self.referencia}[{idioma}/{registro}]: marcadores {sorted(usados)} "
                        f"distintos de los declarados {sorted(self.marcadores)}"
                    )
        return self


class PromptRenderizado(BaseModel):
    model_config = ConfigDict(frozen=True)

    texto: str
    referencia: str
    huella: str
    idioma: str
    registro: str

    def atributos_span(self) -> dict[str, str]:
        """Atributos de traza de la sección 2.6.6 que salen del prompt."""
        return {
            "latam.prompt.id": self.referencia,
            "latam.prompt.huella": self.huella,
            "latam.prompt.idioma": self.idioma,
            "latam.prompt.registro": self.registro,
        }


class Biblioteca:
    def __init__(self, prompts: dict[str, Prompt]) -> None:
        self._prompts = prompts

    @property
    def referencias(self) -> set[str]:
        return set(self._prompts)

    def todos(self) -> list[Prompt]:
        return [self._prompts[r] for r in sorted(self._prompts)]

    def obtener(self, referencia: str) -> Prompt:
        try:
            return self._prompts[referencia]
        except KeyError:
            raise ErrorPrompt(f"prompt no registrado: {referencia}") from None

    def renderizar(
        self, referencia: str, idioma: Idioma | str, registro: str, valores: dict[str, str] | None = None
    ) -> PromptRenderizado:
        p = self.obtener(referencia)
        idioma = str(idioma)
        valores = valores or {}
        try:
            plantilla = p.plantillas[idioma][registro]
        except KeyError:
            raise ErrorPrompt(f"{referencia}: sin plantilla para {idioma}/{registro}") from None
        faltan, sobran = set(p.marcadores) - set(valores), set(valores) - set(p.marcadores)
        if faltan or sobran:
            raise ErrorPrompt(f"{referencia}: faltan {sorted(faltan)}, sobran {sorted(sobran)}")
        texto = Template(plantilla).substitute(valores)
        return PromptRenderizado(
            texto=texto, referencia=referencia, huella=p.huella, idioma=idioma, registro=registro
        )


def cargar_biblioteca(raiz: Path = RAIZ_PROMPTS) -> Biblioteca:
    prompts: dict[str, Prompt] = {}
    for ruta in sorted(raiz.glob("*/*.yaml")):
        crudo = ruta.read_bytes()
        datos: Any = yaml.safe_load(crudo)
        try:
            p = Prompt.model_validate({**datos, "huella": hashlib.sha256(crudo).hexdigest()})
        except ValidationError as error:
            raise ErrorPrompt(f"{ruta.name}: {error}") from error
        if ruta.stem != f"{p.id.split('/')[1]}@{p.version}" or ruta.parent.name != p.id.split("/")[0]:
            raise ErrorPrompt(f"{ruta}: la ruta no coincide con id y versión ({p.referencia})")
        prompts[p.referencia] = p
    return Biblioteca(prompts)
