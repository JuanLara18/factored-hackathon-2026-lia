"""Carga supuesta por D-30: CSV del espejo local a tablas crudas `latam_bank.bronce_<archivo>`.

No es parte del pipeline. La corre una persona una vez, después de
`aws s3 sync s3://<bucket>/data/ data/espejo/ --profile latam-organizador`.
Cada CSV queda como una tabla con su nombre y todas las columnas como texto.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from google.cloud import bigquery

# Las capas son prefijos de tabla dentro de `latam_bank`; `latam_seguridad` guarda la llave de tokenización.
DATASETS = ("latam_bank", "latam_seguridad")


def encabezado(ruta: Path) -> list[str]:
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def crear_datasets(cliente: bigquery.Client, ubicacion: str) -> None:
    for nombre in DATASETS:
        ds = bigquery.Dataset(f"{cliente.project}.{nombre}")
        ds.location = ubicacion
        ds.labels = {"proyecto": "latam-bank"}
        cliente.create_dataset(ds, exists_ok=True)


def cargar_csv(cliente: bigquery.Client, ruta: Path) -> int:
    tabla = f"{cliente.project}.latam_bank.bronce_{ruta.stem}"
    config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=[bigquery.SchemaField(c, "STRING") for c in encabezado(ruta)],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
        encoding="UTF-8",
    )
    with ruta.open("rb") as f:
        trabajo = cliente.load_table_from_file(f, tabla, job_config=config)
    trabajo.result()
    return cliente.get_table(tabla).num_rows or 0


def main() -> int:
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        print("falta LATAM_GCP_PROJECT", file=sys.stderr)
        return 2
    espejo = Path(os.environ.get("LATAM_ESPEJO", "data/espejo"))
    ubicacion = os.environ.get("LATAM_GCP_LOCATION", "US")
    archivos = sorted(espejo.glob("*.csv"))
    if not archivos:
        print(f"no hay CSV en {espejo}", file=sys.stderr)
        return 2
    cliente = bigquery.Client(project=proyecto)
    crear_datasets(cliente, ubicacion)
    for ruta in archivos:
        print(f"{ruta.stem}: {cargar_csv(cliente, ruta)} filas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
