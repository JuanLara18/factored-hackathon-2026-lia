"""Esquema y cargador de escenarios del arnés (IA-5.1, R-IA-71): cada escenario es un YAML versionado."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from latam_comun.dominio.tipos import Moneda
from pydantic import BaseModel, ConfigDict, Field

from latam_ia.registro.cargador import RAIZ_IA

DIR_EVALUACION = RAIZ_IA / "evaluacion"
DIR_ESCENARIOS = DIR_EVALUACION / "escenarios"
DIR_RETENIDO = DIR_ESCENARIOS / "retenido"
RUTA_MUNDO_BASE = DIR_EVALUACION / "mundo_base.yaml"

Categoria = Literal["N", "A", "E", "F", "X"]  # X: manejo de fallas y seguridad (solo el conjunto retenido)
Intencion = Literal["hablar", "confirmar", "rechazar"]


class _Estricto(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TransaccionMundo(_Estricto):
    cliente: str
    id: str
    producto: str
    monto: int
    moneda: Moneda
    usd: int | None = None
    estado: str = "completed"
    comercio: str
    hace_dias: int = 1
    pais: str = "CO"
    categoria: str = "retail"  # texto del adquirente: también puede traer una inyección (retenido)


class ProductoMundo(_Estricto):
    cliente: str
    id: str
    tipo: str = "card"
    estado: str = "active"
    moneda: str = "COP"


class Mundo(_Estricto):
    transacciones: tuple[TransaccionMundo, ...] = ()
    productos: tuple[ProductoMundo, ...] = ()
    casos_previos: tuple[tuple[str, str], ...] = ()  # (cliente, transacción)


class HechoOculto(_Estricto):
    """Valor que el cliente solo dice si el agente lo preguntó (2.8.3); `si_pregunta` vacío es hecho libre."""

    valor: str
    si_pregunta: tuple[str, ...] = ()


class TurnoGuion(_Estricto):
    decir: str
    intencion: Intencion = "hablar"


class Guion(_Estricto):
    objetivo: str
    turnos: tuple[TurnoGuion, ...] = Field(min_length=1)
    hechos: dict[str, HechoOculto] = Field(default_factory=dict[str, HechoOculto])
    max_turnos: int = 8


class Esperado(_Estricto):
    """Estado final esperado del banco simulado y de la ruta. `None` en un campo lo deja sin verificar."""

    casos: tuple[tuple[str, str], ...] | None = None
    bloqueos: tuple[tuple[str, str], ...] | None = None
    traspasos: int | None = None
    traspaso_urgente: bool | None = None
    creditos_provisionales: int | None = None
    max_turnos_hasta_traspaso: int | None = None
    debe_escalar: bool | None = None
    idioma_respuesta: Literal["es", "pt"] | None = None  # idioma en que debe contestar el agente
    herramientas_requeridas: tuple[str, ...] = ()  # el agente debe haberlas llamado
    herramientas_prohibidas: tuple[str, ...] = ()  # el agente no debe haberlas llamado
    max_aprobaciones: int | None = None  # tope de acciones con confirmación pedidas al cliente
    texto_tras_aprobacion: bool = False  # tras cada acción aprobada el agente escribe antes de pedir otra
    max_aprobaciones: int | None = None  # tope de acciones con confirmación pedidas al cliente
    texto_tras_aprobacion: bool = False  # tras cada acción aprobada el agente escribe antes de pedir otra
    errores_esperados: bool = False  # la falla inyectada corta la corrida: el error no es un hallazgo


Fallo = Literal[
    "sesion_vencida_al_inicio",  # la sesión ya expiró cuando llega el primer mensaje
    "sesion_vence_a_mitad",  # expira tras el primer turno del agente, antes de aprobar la acción
    "bigquery_caido",  # toda lectura del oro operacional falla (503)
    "firestore_caido",  # el almacén de conversaciones y efectos falla tras abrir la conversación
    "runtime_caido",  # el modelo o el Agent Runtime no responde (503)
]
Resultado = Literal["resolver", "escalar", "abstenerse", "fallo_seguro"]


class Etiqueta(_Estricto):
    """Etiqueta de referencia de un caso retenido, fijada por política y reglas, no por el agente.

    `en_alcance`: el cliente pide algo que el agente de disputas debe atender (un cobro, un bloqueo,
    un traspaso a persona) aunque la mejor respuesta sea escalar o fallar sin daño. `resultado` es lo que un
    sistema correcto hace: `resolver` (acción segura), `escalar` (pasa a una persona),
    `abstenerse` (rechaza o redirige sin efectos) y `fallo_seguro` (la falla no deja efectos ni fugas).
    """

    en_alcance: bool
    resultado: Resultado
    razon: str  # de qué regla o política sale la etiqueta (Politica v1, prompt, enunciado)


class Escenario(_Estricto):
    id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    categoria: Categoria
    descripcion: str
    idioma: Literal["es", "pt"] = "es"
    registro: Literal["usted", "vos", "voce"] = "usted"
    cliente: str
    mundo_extra: Mundo = Mundo()
    guion: Guion
    esperado: Esperado
    falla_conocida: str | None = None  # hallazgo abierto: falla a propósito y se reporta aparte
    movimiento_fijado: str | None = None  # transacción que la banca fija en la conversación (`reclamar`)
    fallo: Fallo | None = None  # falla de infraestructura inyectada con dobles (solo retenido)
    etiqueta: Etiqueta | None = None  # obligatoria en el conjunto retenido


def cargar_mundo_base(ruta: Path = RUTA_MUNDO_BASE) -> Mundo:
    datos: Any = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return Mundo.model_validate(datos)


def combinar(base: Mundo, extra: Mundo) -> Mundo:
    return Mundo(
        transacciones=base.transacciones + extra.transacciones,
        productos=base.productos + extra.productos,
        casos_previos=base.casos_previos + extra.casos_previos,
    )


def cargar_retenidos() -> list[Escenario]:
    """Conjunto retenido: casos nuevos que nunca se usaron para iterar el prompt (congelado por huella)."""
    return cargar_escenarios(DIR_RETENIDO)


def cargar_escenarios(directorio: Path = DIR_ESCENARIOS) -> list[Escenario]:
    escenarios: list[Escenario] = []
    for ruta in sorted(directorio.glob("*.yaml")):
        datos: Any = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        e = Escenario.model_validate(datos)
        if ruta.stem != e.id:
            raise ValueError(f"{ruta.name}: el nombre del archivo debe ser el id ({e.id})")
        escenarios.append(e)
    ids = [e.id for e in escenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("ids de escenario repetidos")
    return escenarios
