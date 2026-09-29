"""Punto de entrada de la validación de bronce, pensado para un Cloud Run Job (configuración por entorno).

    LATAM_GCP_PROJECT   proyecto de Google Cloud
    LATAM_GCP_LOCATION  ubicación de BigQuery (por defecto US)

`python -m latam_datos validar` evalúa las reglas Q-BRZ sobre `latam_bank.bronce_*` y escribe el reporte en
`latam_bank.platino_reporte_calidad_corrida`. Sale con 1 si hay un hallazgo bloqueante, para que el Job falle.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime

from latam_datos.contrato import REPORTE
from latam_datos.motor import Motor
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import VERSION_REGLAS, Hallazgo, evaluar, reportar


def commit_actual() -> str:
    """`git rev-parse HEAD`; en el Job (sin git) viene de LATAM_COMMIT."""
    if valor := os.environ.get("LATAM_COMMIT"):
        return valor
    try:
        salida = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"
    return salida.stdout.strip() or "desconocido"


def corrida_id_de(ahora: datetime, commit: str = "desconocido") -> str:
    """Amarra la corrida al código que la produjo: marca de tiempo, commit corto y versión de las reglas."""
    marca = ahora.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{marca}-{commit[:7]}-v{VERSION_REGLAS}"


def validar(
    motor: Motor, ahora: datetime, commit: str | None = None, tabla_reporte: str = REPORTE
) -> list[Hallazgo]:
    commit = commit if commit is not None else commit_actual()
    hallazgos = evaluar(motor)
    reportar(motor, corrida_id_de(ahora, commit), hallazgos, ahora, commit, tabla_reporte)
    return hallazgos


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="latam_datos")
    p.add_argument("orden", choices=["validar"])
    p.parse_args(argv)
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        print("Falta LATAM_GCP_PROJECT.", file=sys.stderr)
        return 2
    from google.cloud import bigquery  # type: ignore[attr-defined]  # importación tardía

    ubicacion = os.environ.get("LATAM_GCP_LOCATION", "US")
    motor = MotorBigQuery(bigquery.Client(project=proyecto, location=ubicacion), proyecto, ubicacion)
    hallazgos = validar(motor, datetime.now(UTC))
    bloqueados = [h for h in hallazgos if h.resultado == "bloqueado"]
    print(f"hallazgos {len(hallazgos)}, bloqueantes {len(bloqueados)}")
    return 1 if bloqueados else 0


if __name__ == "__main__":
    raise SystemExit(main())
