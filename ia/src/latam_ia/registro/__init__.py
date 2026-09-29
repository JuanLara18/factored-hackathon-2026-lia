"""Registro de la fuerza laboral digital (IA-7.1, R-IA-01 a R-IA-04)."""

from latam_ia.registro.cargador import cargar_registro, verificar_familias, verificar_prompts
from latam_ia.registro.esquema import Estado, Modelo, Proveedor, Registro, Riesgo, Rol, Trabajador
from latam_ia.registro.gateway import a_yaml, generar_config_gateway

__all__ = [
    "Estado",
    "Modelo",
    "Proveedor",
    "Registro",
    "Riesgo",
    "Rol",
    "Trabajador",
    "a_yaml",
    "cargar_registro",
    "generar_config_gateway",
    "verificar_familias",
    "verificar_prompts",
]
