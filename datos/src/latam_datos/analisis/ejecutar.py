"""Punto de entrada: consulta BigQuery (o lee la caché), calcula, dibuja y redacta el informe."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from latam_datos.analisis import consultas, figuras, informe, metricas

RAIZ_REPORTE = consultas.RAIZ / "presidencia" / "reporte"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m latam_datos.analisis", description=__doc__)
    ap.add_argument(
        "--desde-cache", action="store_true", help="usa figuras/cifras.json y no consulta BigQuery"
    )
    args = ap.parse_args(argv)
    if args.desde_cache:
        resultados = consultas.cargar()
    else:
        proyecto = os.environ.get("LATAM_GCP_PROJECT", "latam-bank-hackaton-2026")
        dataset = os.environ.get("LATAM_BQ_DATASET", "latam_bank")
        resultados = consultas.ejecutar(proyecto, dataset, os.environ.get("LATAM_GCP_LOCATION", "US"))
        consultas.guardar(resultados)
    m = metricas.calcular(resultados)
    hechas = figuras.generar(m, RAIZ_REPORTE / "figuras")
    ruta: Path = RAIZ_REPORTE / "01_problema.md"
    ruta.write_text(informe.redactar(m), encoding="utf-8", newline="\n")
    print(f"{len(hechas)} figuras y {ruta}")
    return 0
