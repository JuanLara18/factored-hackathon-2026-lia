"""Punto de entrada de la validación de bronce, pensado para un Cloud Run Job (configuración por entorno).

    LATAM_GCP_PROJECT   proyecto de Google Cloud
    LATAM_GCP_LOCATION  ubicación de BigQuery (por defecto us-central1)

`python -m latam_datos validar` evalúa las reglas Q-BRZ sobre `latam_bronce` y escribe el reporte en
`latam_platino.reporte_calidad_corrida`. Sale con 1 si hay un hallazgo bloqueante, para que el Job falle.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime

from latam_datos.motor import Motor
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import Hallazgo, evaluar, reportar


def corrida_id_de(ahora: datetime) -> str:
    return ahora.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def validar(motor: Motor, ahora: datetime) -> list[Hallazgo]:
    hallazgos = evaluar(motor)
    reportar(motor, corrida_id_de(ahora), hallazgos, ahora)
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

    ubicacion = os.environ.get("LATAM_GCP_LOCATION", "us-central1")
    motor = MotorBigQuery(bigquery.Client(project=proyecto, location=ubicacion), proyecto, ubicacion)
    hallazgos = validar(motor, datetime.now(UTC))
    bloqueados = [h for h in hallazgos if h.resultado == "bloqueado"]
    print(f"hallazgos {len(hallazgos)}, bloqueantes {len(bloqueados)}")
    return 1 if bloqueados else 0


if __name__ == "__main__":
    raise SystemExit(main())
