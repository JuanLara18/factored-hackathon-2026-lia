"""Tipos del dominio. Inmutables y validados: un dato que no puede construirse mal no se valida después."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Inmutable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Canal(StrEnum):
    CHAT = "chat"
    WHATSAPP = "whatsapp"
    VOZ_NAVEGADOR = "voz_navegador"
    VOZ_TELEFONO = "voz_telefono"


class Idioma(StrEnum):
    ES = "es"
    PT = "pt"


class Ruta(StrEnum):
    """Finales posibles de una conversación (interacciones, sección 2)."""

    R1_INFORMACION = "R1"
    R2_RADICADO = "R2"
    R3_CONTENIDO_Y_RADICADO = "R3"
    R4_ESCALADO_URGENTE = "R4"
    R5_ESCALADO = "R5"
    R6_ABSTENCION = "R6"
    R7_NEGADO = "R7"
    R8_FALLA_SEGURA = "R8"


class Motivo(StrEnum):
    """Taxonomía del componente aprendido (D-14)."""

    FRAUDE = "fraude"
    ERROR_PROCESAMIENTO = "error_procesamiento"
    DISPUTA_COMERCIAL = "disputa_comercial"
    ES_MIA_NO_LA_RECONOZCO = "es_mia_no_la_reconozco"
    NO_ES_DISPUTA = "no_es_disputa"
    FUERA_DE_ALCANCE = "fuera_de_alcance"


class NivelAcr(StrEnum):
    """Niveles de autenticación (D-20, DP-GOB-10): bloquear con consulta, radicar con acción."""

    CONSULTA = "acr1"
    ACCION = "acr2"


Moneda = Literal["MXN", "COP", "ARS", "USD", "BRL"]


class Dinero(_Inmutable):
    """Un monto nunca existe sin su moneda."""

    monto: Decimal = Field(ge=0)
    moneda: Moneda


class SesionAutenticada(_Inmutable):
    """La crea solo el servicio de identidad; el cliente sale de aquí, nunca de un argumento del modelo."""

    id_sesion: str
    cliente_id: str
    nivel: NivelAcr
    expira: datetime

    def vigente(self, ahora: datetime) -> bool:
        return ahora < self.expira

    def permite(self, requerido: NivelAcr, ahora: datetime) -> bool:
        orden = [NivelAcr.CONSULTA, NivelAcr.ACCION]
        return self.vigente(ahora) and orden.index(self.nivel) >= orden.index(requerido)


class TurnoEntrante(_Inmutable):
    """Lo que entrega una superficie al núcleo, igual para todos los canales."""

    canal: Canal
    texto: str
    idioma: Idioma | None = None
    confianza_reconocimiento: float | None = Field(default=None, ge=0, le=1)
    dtmf: str | None = Field(default=None, pattern=r"^[0-9*#]+$")
    id_sesion: str | None = None
    recibido: datetime

    @model_validator(mode="after")
    def _confianza_solo_en_voz(self) -> TurnoEntrante:
        es_voz = self.canal in (Canal.VOZ_NAVEGADOR, Canal.VOZ_TELEFONO)
        if self.confianza_reconocimiento is not None and not es_voz:
            raise ValueError("la confianza de reconocimiento solo existe en voz")
        return self


class Interpretacion(_Inmutable):
    """Lo que dice el modelo. Nunca es un hecho: la redacción no puede afirmarla como verdad."""

    motivo: Motivo
    urgente: bool
    confianza: float = Field(ge=0, le=1)
    entidades: dict[str, str] = Field(default_factory=dict[str, str])
    necesita_aclarar: bool = False


class HechoVerificado[T](_Inmutable):
    """Dato producido por una herramienta, con fuente y hora (P6)."""

    valor: T
    fuente: str
    hora: datetime


class ReglaDePolitica(_Inmutable):
    """Regla de `policy/v1` con su norma y la fecha en que se consultó (D-13)."""

    id: str
    version: str
    norma: str
    fecha_consulta: datetime


class Decision(_Inmutable):
    ruta: Ruta
    accion: str | None = None
    requiere_confirmacion: bool = False
    motivo: str
    reglas: tuple[str, ...] = ()


class Confirmacion(_Inmutable):
    """El asentimiento del cliente es un evento de la superficie, no texto libre del modelo."""

    accion: str
    monto: Dinero | None = None
    canal: Canal
    evidencia: Literal["boton", "si_explicito", "dtmf"]
    nonce: str


class AccionVerificada(_Inmutable):
    """Resultado de una acción releído después de ejecutarla; solo esto se informa como hecho."""

    accion: str
    exito: bool
    resultado_releido: str
    hora: datetime


class RespuestaTipada(_Inmutable):
    texto: str
    componentes: tuple[str, ...] = ()
    para_voz: bool = False


class Conflicto(_Inmutable):
    """Lo declarado frente al registro, en dos columnas y sin calificativos (2.5.2)."""

    tipo: str
    declarado: str
    registro: str


class AccionNoRealizada(_Inmutable):
    accion: str
    motivo: str


class PreguntaAbierta(_Inmutable):
    pregunta: str
    a_quien: Literal["cliente", "back_office", "red"]
    bloquea: bool


class Plazo(_Inmutable):
    regla: str
    inicio: datetime
    vence: datetime


class Compromiso(_Inmutable):
    texto: str
    hora: datetime


class ReglaAplicada(_Inmutable):
    id: str
    version: str


class ColaDestino(_Inmutable):
    idioma: str
    especialidad: str
    franja: str


class Identidad(_Inmutable):
    nivel: NivelAcr
    metodo: str
    hora: datetime


class Evidencia(_Inmutable):
    traza_id: str
    reglas: tuple[ReglaAplicada, ...] = ()
    plantillas: tuple[str, ...] = ()


class PaqueteTraspaso(_Inmutable):
    """Lo que recibe el experto humano (enunciado, criterio 3; definición de Clientes, 2.5.2).

    Los seis primeros campos son los de la primera versión y siguen igual; los demás completan los 19 de 2.5.2
    con valores por defecto para no romper a quien ya construía el paquete. No lleva nombre, documento, número
    completo de tarjeta, atributos protegidos, segmento, `fraud_score` en crudo ni el razonamiento del modelo.
    """

    solicitud: str
    hechos: tuple[HechoVerificado[str], ...]
    interpretaciones: tuple[Interpretacion, ...]
    conflictos: tuple[Conflicto | str, ...] = ()
    acciones: tuple[AccionVerificada, ...] = ()
    preguntas_abiertas: tuple[PreguntaAbierta | str, ...] = ()
    motivo: str
    idioma: Idioma
    prioridad: Literal["urgente", "normal", "P1", "P2", "P3", "P4"]
    id_traspaso: str = ""
    hilo_id: str = ""
    caso_id: str | None = None
    motivo_texto: str = ""
    regla: ReglaAplicada | None = None
    cola_destino: ColaDestino | None = None
    registro: str = "usted"
    pais_cuenta: str | None = None
    canal_actual: Canal = Canal.CHAT
    canales_usados: tuple[Canal, ...] = (Canal.CHAT,)
    identidad: Identidad | None = None
    acciones_no_realizadas: tuple[AccionNoRealizada, ...] = ()
    plazos_en_curso: tuple[Plazo, ...] = ()
    compromisos_comunicados: tuple[Compromiso, ...] = ()
    preferencias: dict[str, str] = Field(default_factory=dict[str, str])
    evidencia: Evidencia | None = None
    transcripcion_ref: str | None = None
    entidades: tuple[str, ...] = ()  # lo que la IA identificó (producto, comercio), como interpretación


class EventoTraza(_Inmutable):
    id_conversacion: str
    etapa: str
    inicio: datetime
    fin: datetime
    atributos: dict[str, str] = Field(default_factory=dict[str, str])

    @model_validator(mode="after")
    def _orden(self) -> EventoTraza:
        if self.fin < self.inicio:
            raise ValueError("la traza termina antes de empezar")
        return self
