"""Arnés de evaluación del agente de disputas (IA-5.1): escenarios, simulador, verificadores y reporte."""

from latam_ia.evaluacion.ejecutor import Corrida, ejecutar_corrida
from latam_ia.evaluacion.esquema import Escenario, cargar_escenarios
from latam_ia.evaluacion.reporte import ejecutar_suite

__all__ = ["Corrida", "Escenario", "cargar_escenarios", "ejecutar_corrida", "ejecutar_suite"]
