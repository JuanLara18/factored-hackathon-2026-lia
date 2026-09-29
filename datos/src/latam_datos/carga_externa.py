"""Carga supuesta por D-30: CSV del espejo local a tablas crudas `latam_bank.bronce_<archivo>`.

No es parte del pipeline. La corre una persona una vez, después de
`aws s3 sync s3://<bucket>/data/ data/espejo/`. Cada CSV suelto y cada carpeta particionada por
fecha quedan como una tabla con todas las columnas como texto. Con argumentos, carga solo esas tablas.
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path
from typing import cast

from google.cloud import bigquery

from latam_datos.manifiesto import contar_filas

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


def fuentes(espejo: Path) -> dict[str, list[Path]]:
    """Una tabla por CSV suelto en la raíz y una por carpeta particionada (`<tabla>/year=/month=/day=/`)."""
    tablas = {ruta.stem: [ruta] for ruta in sorted(espejo.glob("*.csv"))}
    for carpeta in sorted(p for p in espejo.iterdir() if p.is_dir()):
        partes = sorted(carpeta.rglob("*.csv"))
        if partes:
            tablas[carpeta.name] = partes
    return tablas


def unir(partes: list[Path], destino: Path) -> list[str]:
    """Concatena las particiones en un solo CSV con un encabezado; exige el mismo encabezado en todas."""
    columnas = encabezado(partes[0])
    with destino.open("w", encoding="utf-8", newline="") as salida:
        escritor = csv.writer(salida)
        escritor.writerow(columnas)
        for parte in partes:
            with parte.open(encoding="utf-8-sig", newline="") as f:
                lector = csv.reader(f)
                if next(lector) != columnas:
                    raise ValueError(f"encabezado distinto en {parte}")
                escritor.writerows(lector)
    return columnas


def cargar_tabla(cliente: bigquery.Client, nombre: str, partes: list[Path]) -> tuple[int, str]:
    """Carga a `bronce_<nombre>_nuevo`, exige que las filas sean las de los CSV y solo entonces reemplaza.

    Devuelve las filas y el job_id de la carga. Si no cuadran, borra `_nuevo` y falla sin tocar la vigente.
    """
    tabla = f"{cliente.project}.latam_bank.bronce_{nombre}"
    nuevo = f"{tabla}_nuevo"
    esperadas = sum(contar_filas(p) for p in partes)
    with tempfile.TemporaryDirectory() as tmp:
        unido = Path(tmp) / f"{nombre}.csv"
        columnas = unir(partes, unido)
        config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=[bigquery.SchemaField(c, "STRING") for c in columnas],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            allow_quoted_newlines=True,
            encoding="UTF-8",
        )
        with unido.open("rb") as f:
            trabajo = cliente.load_table_from_file(f, nuevo, job_config=config)
        trabajo.result()
    cargadas = cliente.get_table(nuevo).num_rows or 0
    if cargadas != esperadas:
        cliente.delete_table(nuevo, not_found_ok=True)
        raise ValueError(
            f"bronce_{nombre}: {cargadas} filas cargadas y {esperadas} en los CSV; no se reemplaza"
        )
    copia = bigquery.CopyJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    cliente.copy_table(nuevo, tabla, job_config=copia).result()
    cliente.delete_table(nuevo, not_found_ok=True)
    return cargadas, cast(str, trabajo.job_id)  # pyright: ignore[reportUnknownMemberType]


def main() -> int:
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        print("falta LATAM_GCP_PROJECT", file=sys.stderr)
        return 2
    espejo = Path(os.environ.get("LATAM_ESPEJO", "data/espejo"))
    ubicacion = os.environ.get("LATAM_GCP_LOCATION", "US")
    tablas = fuentes(espejo) if espejo.is_dir() else {}
    solo = set(sys.argv[1:])
    if solo:
        tablas = {k: v for k, v in tablas.items() if k in solo}
    if not tablas:
        print(f"no hay CSV en {espejo}", file=sys.stderr)
        return 2
    cliente = bigquery.Client(project=proyecto)
    crear_datasets(cliente, ubicacion)
    from latam_datos.evidencia import generar_manifiesto  # importación tardía: evidencia importa este módulo

    job_ids: dict[str, str | None] = {}
    for nombre, partes in tablas.items():
        filas, job_ids[nombre] = cargar_tabla(cliente, nombre, partes)
        print(f"bronce_{nombre}: {filas} filas de {len(partes)} archivos", flush=True)
    carpeta = Path(os.environ.get("LATAM_MANIFIESTOS", "datos/manifiestos"))
    generar_manifiesto(cliente, espejo, carpeta, job_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
