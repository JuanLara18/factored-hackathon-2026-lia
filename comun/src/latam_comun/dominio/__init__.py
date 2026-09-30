"""Tipos del dominio de LATAM Bank (arquitectura, sección 5).

Son el contrato entre caras: las superficies producen `TurnoEntrante`, la comprensión produce
`Interpretacion`, las herramientas producen `HechoVerificado`, el motor produce `Decision` y la redacción
solo puede afirmar lo que llega como hecho verificado o regla de política (P6).
"""

from latam_comun.dominio.tipos import (
    AccionNoRealizada,
    AccionVerificada,
    Canal,
    ColaDestino,
    Compromiso,
    Confirmacion,
    Conflicto,
    Decision,
    Dinero,
    EventoTraza,
    Evidencia,
    HechoVerificado,
    Identidad,
    Idioma,
    Interpretacion,
    Motivo,
    NivelAcr,
    PaqueteTraspaso,
    Plazo,
    PreguntaAbierta,
    ReglaAplicada,
    ReglaDePolitica,
    RespuestaTipada,
    Ruta,
    SesionAutenticada,
    TurnoEntrante,
)

__all__ = [
    "AccionNoRealizada",
    "ColaDestino",
    "Compromiso",
    "Conflicto",
    "Evidencia",
    "Identidad",
    "Plazo",
    "PreguntaAbierta",
    "ReglaAplicada",
    "AccionVerificada",
    "Canal",
    "Confirmacion",
    "Decision",
    "Dinero",
    "EventoTraza",
    "HechoVerificado",
    "Idioma",
    "Interpretacion",
    "Motivo",
    "NivelAcr",
    "PaqueteTraspaso",
    "ReglaDePolitica",
    "RespuestaTipada",
    "Ruta",
    "SesionAutenticada",
    "TurnoEntrante",
]
