"""Punto de entrada del pipeline de ingesta, pensado para un Cloud Run Job (configuración por entorno).

    LATAM_GCP_PROJECT   proyecto de Google Cloud
    LATAM_GCS_ESPEJO    bucket de aterrizaje (copia de S3 por Storage Transfer Service)
    LATAM_GCP_LOCATION  ubicación de BigQuery (por defecto us-central1)

Órdenes: `espejo` (inventario), `bronce` (lotes y reglas Q-BRZ) y `todo`. Código de salida 1 si algún lote
queda bloqueado, para que el Job falle y alerte.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from latam_datos.bronce import ResultadoBronce, construir_bronce
from latam_datos.config import Configuracion
from latam_datos.espejo import Almacen, AlmacenGCS, crear_inventario, espejar
from latam_datos.motor import Motor
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import Hallazgo, evaluar_globales, reportar


def corrida_id_de(ahora: datetime) -> str:
    return ahora.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def correr_espejo(almacen: Almacen, motor: Motor, ahora: datetime) -> int:
    return len(espejar(almacen, motor, corrida_id_de(ahora), ahora))


def correr_bronce(almacen: Almacen, motor: Motor, ahora: datetime) -> tuple[ResultadoBronce, list[Hallazgo]]:
    """Construye bronce, evalúa Q-BRZ-01 a 11 y escribe el reporte. Los bloqueos no lanzan: se devuelven."""
    crear_inventario(motor)
    res = construir_bronce(almacen, motor, ahora)
    hallazgos = [*res.hallazgos, *evaluar_globales(motor)]
    reportar(motor, corrida_id_de(ahora), hallazgos, ahora)
    return res, hallazgos


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="latam_datos")
    p.add_argument("orden", choices=["espejo", "bronce", "todo"])
    orden = p.parse_args(argv).orden
    try:
        cfg = Configuracion.desde_entorno()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    from google.cloud import bigquery, storage  # type: ignore[attr-defined]  # importación tardía

    almacen = AlmacenGCS(storage.Client(project=cfg.proyecto), cfg.bucket)
    motor = MotorBigQuery(bigquery.Client(project=cfg.proyecto), cfg.proyecto, cfg.ubicacion)
    ahora = datetime.now(UTC)
    if orden in ("espejo", "todo"):
        print(f"{correr_espejo(almacen, motor, ahora)} objetos inventariados")
    if orden in ("bronce", "todo"):
        res, hallazgos = correr_bronce(almacen, motor, ahora)
        avisos = sum(1 for h in hallazgos if h.resultado in ("aviso", "cuarentena"))
        print(
            f"lotes aplicados {len(res.aplicados)}, ignorados {len(res.ignorados)}, "
            f"bloqueados {len(res.bloqueados)}, avisos {avisos}"
        )
        return 1 if res.bloqueados else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
