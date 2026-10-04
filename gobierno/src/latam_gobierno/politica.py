"""Carga de `policy/v1` (R-GOB-12, R-GOB-19): esquema estricto, huella verificada y decisiones puras.

La política de negocio vive en `gobierno/politica/v1/*.yaml`; el motor la recibe inyectada y no arranca
con una política alterada. Cada regla lleva `fundamento` (regla o fila de la definición) y `razon`.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

RUTA_V1 = Path(__file__).resolve().parents[2] / "politica" / "v1"
ARCHIVOS = ("escalamiento", "credito_provisional", "riesgo", "autonomia", "traspaso")

Texto = Annotated[str, StringConstraints(min_length=3, strip_whitespace=True)]
Acr = Literal["acr1", "acr2"]
Banda = Literal["alto", "zona_gris", "sin_evidencia"]


class PoliticaInvalida(ValueError):
    """Esquema roto, huella que no coincide o un archivo de la política que falta."""


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Cita(_Modelo):
    fundamento: Texto
    razon: Texto


class ReglaEscalamiento(_Cita):
    id: Texto
    condicion: Literal["urgente", "estado_en", "producto_desconocido"]
    motivo: Texto
    estados: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _estados_solo_con_estado_en(self) -> Self:
        if (self.condicion == "estado_en") != bool(self.estados):
            raise ValueError("`estados` va si y solo si la condición es `estado_en`")
        return self


class TopeCredito(_Cita):
    limite_usd: Decimal = Field(ge=0)


class RadicarYEscalar(_Modelo):
    """Monto sobre el umbral (A-07): se radica la disputa y además se pasa el caso a una persona (R5)."""

    id: Texto
    motivo: Texto
    por_defecto: TopeCredito
    por_moneda: dict[str, TopeCredito] = {}


class Urgencia(_Cita):
    """Única vía para marcar P1 desde el agente: el motivo es un código cerrado, no la bandera del modelo."""

    id: Texto
    motivos: tuple[str, ...] = Field(min_length=1)


class Escalamiento(_Modelo):
    reglas: tuple[ReglaEscalamiento, ...] = Field(min_length=1)
    urgencia: Urgencia
    radicar_y_escalar: RadicarYEscalar


class CreditoProvisional(_Modelo):
    por_defecto: TopeCredito
    por_moneda: dict[str, TopeCredito] = {}


class Riesgo(_Cita):
    punto_operacion: Literal["conservador", "balanceado", "agresivo"]
    alto_sobre: Decimal
    zona_gris_desde: Decimal

    @model_validator(mode="after")
    def _orden(self) -> Self:
        if self.zona_gris_desde >= self.alto_sobre:
            raise ValueError("la zona gris debe empezar bajo el umbral alto")
        return self


class ReglaAcr(_Cita):
    acr: Acr


class Autonomia(_Modelo):
    acciones: dict[str, ReglaAcr] = Field(min_length=1)


class DisparadorTraspaso(_Cita):
    id: Texto
    evento: Texto
    prioridad: Literal["maxima", "normal"]
    en_motor: bool
    umbral: int | None = None


class Traspaso(_Modelo):
    disparadores: tuple[DisparadorTraspaso, ...] = Field(min_length=1)


class Manifiesto(_Modelo):
    version: Texto
    sintetica: Literal[True]
    fecha: Texto
    huella: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class Decision(_Modelo):
    """Resultado de escalar: la regla que coincidió."""

    id: str
    motivo: str


class PoliticaV1(_Modelo):
    manifiesto: Manifiesto
    escalamiento: Escalamiento
    credito_provisional: CreditoProvisional
    riesgo: Riesgo
    autonomia: Autonomia
    traspaso: Traspaso

    @property
    def huella(self) -> str:
        return self.manifiesto.huella

    @property
    def referencia(self) -> str:
        """Forma que se registra en la hoja de vida del agente: `policy/v1@<huella>`."""
        return f"policy/v1@{self.huella}"

    def escalar(
        self, *, urgente: bool, estado_transaccion: str | None, producto_conocido: bool
    ) -> Decision | None:
        """Primera regla que coincide, en el orden del archivo; `None` si no hay que escalar."""
        estado = estado_transaccion.lower() if estado_transaccion is not None else None
        for r in self.escalamiento.reglas:
            coincide = (
                (r.condicion == "urgente" and urgente)
                or (r.condicion == "estado_en" and estado is not None and estado in r.estados)
                or (r.condicion == "producto_desconocido" and not producto_conocido)
            )
            if coincide:
                return Decision(id=r.id, motivo=r.motivo)
        return None

    def es_urgente(self, motivo: str) -> bool:
        """Urgencia (P1) por política: solo un motivo de la lista cerrada; la orden del cliente no cuenta."""
        clave = "_".join(motivo.strip().lower().split())
        return clave in self.escalamiento.urgencia.motivos

    def escalar_tras_radicar(self, moneda: str, amount_usd: Decimal | None) -> Decision | None:
        """Monto sobre el umbral de la moneda: radica y luego escala. Sin monto en USD no se adivina."""
        r = self.escalamiento.radicar_y_escalar
        umbral = r.por_moneda.get(moneda, r.por_defecto).limite_usd
        if amount_usd is not None and amount_usd > umbral:
            return Decision(id=r.id, motivo=r.motivo)
        return None

    def limite_credito_usd(self, moneda: str) -> Decimal:
        return self.credito_provisional.por_moneda.get(
            moneda, self.credito_provisional.por_defecto
        ).limite_usd

    def credito_provisional_aplica(self, moneda: str, amount_usd: Decimal | None) -> bool:
        """Sin monto en USD no hay crédito provisional: no se adivina."""
        return amount_usd is not None and amount_usd <= self.limite_credito_usd(moneda)

    def banda_riesgo(self, fraud_score: Decimal | None) -> Banda:
        if fraud_score is None:
            return "zona_gris"
        if fraud_score > self.riesgo.alto_sobre:
            return "alto"
        if fraud_score >= self.riesgo.zona_gris_desde:
            return "zona_gris"
        return "sin_evidencia"

    def acr_requerido(self, accion: str) -> Acr:
        """Una acción sin regla no se ejecuta: falla cerrado."""
        regla = self.autonomia.acciones.get(accion)
        if regla is None:
            raise PoliticaInvalida(f"la acción {accion!r} no tiene nivel de autenticación en la política")
        return regla.acr


def huella_conjunto(directorio: Path) -> str:
    """SHA-256 de `nombre:huella` de cada archivo con saltos LF, en orden fijo; excluye el manifiesto."""
    partes: list[str] = []
    for nombre in ARCHIVOS:
        ruta = directorio / f"{nombre}.yaml"
        if not ruta.is_file():
            raise PoliticaInvalida(f"falta {ruta.name} en {directorio}")
        contenido = ruta.read_bytes().replace(b"\r\n", b"\n")
        partes.append(f"{nombre}:{hashlib.sha256(contenido).hexdigest()}")
    return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()


def _yaml(ruta: Path) -> dict[str, Any]:
    datos: Any = yaml.safe_load(ruta.read_bytes().decode("utf-8"))
    if not isinstance(datos, dict):
        raise PoliticaInvalida(f"{ruta.name}: se esperaba un mapa")
    return datos  # pyright: ignore[reportUnknownVariableType]


def cargar(directorio: Path = RUTA_V1) -> PoliticaV1:
    """Valida el esquema y la huella. Cualquier cambio a un YAML exige rehacer `manifest.yaml`."""
    try:
        manifiesto = Manifiesto.model_validate(_yaml(directorio / "manifest.yaml"))
        esperada = huella_conjunto(directorio)
        if manifiesto.huella != esperada:
            raise PoliticaInvalida(f"la huella del manifiesto no coincide (calculada {esperada})")
        return PoliticaV1(
            manifiesto=manifiesto,
            escalamiento=Escalamiento.model_validate(_yaml(directorio / "escalamiento.yaml")),
            credito_provisional=CreditoProvisional.model_validate(
                _yaml(directorio / "credito_provisional.yaml")
            ),
            riesgo=Riesgo.model_validate(_yaml(directorio / "riesgo.yaml")),
            autonomia=Autonomia.model_validate(_yaml(directorio / "autonomia.yaml")),
            traspaso=Traspaso.model_validate(_yaml(directorio / "traspaso.yaml")),
        )
    except PoliticaInvalida:
        raise
    except (OSError, ValueError) as e:
        raise PoliticaInvalida(str(e)) from e


def sellar(directorio: Path = RUTA_V1) -> str:
    """Reescribe `manifest.yaml` con la huella actual; lo corre Gobierno al aprobar un cambio."""
    huella = huella_conjunto(directorio)
    ruta = directorio / "manifest.yaml"
    previo = _yaml(ruta) if ruta.is_file() else {}
    texto = (
        f'version: "{previo.get("version", "1.0.0")}"\n'
        "sintetica: true\n"
        f'fecha: "{previo.get("fecha", "2026-09-29")}"\n'
        f'huella: "{huella}"\n'
    )
    ruta.write_bytes(texto.encode("utf-8"))
    return huella


if __name__ == "__main__":
    print(sellar())
