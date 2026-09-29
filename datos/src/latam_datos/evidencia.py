"""Evidencia de datos en platino: manifiesto de carga, comparación con el respaldo e inventario de insumos.

    python -m latam_datos.evidencia manifiesto | verificar-cadena | comparar-respaldo | inventario

Variables: LATAM_GCP_PROJECT, LATAM_ESPEJO (data/espejo), LATAM_RESPALDO (data/respaldo_20260831),
LATAM_MANIFIESTOS (datos/manifiestos). Solo escribe las tablas `latam_bank.platino_*` de esta evidencia.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.cloud import bigquery

from latam_datos import manifiesto as mf
from latam_datos.carga_externa import fuentes
from latam_datos.respaldo import comparar

DS = "latam_bank"
TABLAS_CON_FECHA = ("transactions", "call_center_interactions", "digital_events", "campaign_sends")
VENCIMIENTO = "2026-11-28"


def _esquema(**campos: str) -> list[bigquery.SchemaField]:
    return [bigquery.SchemaField(n, t) for n, t in campos.items()]


ESQ_ARCHIVOS = _esquema(
    manifiesto_id="STRING",
    generado_en="TIMESTAMP",
    clave_s3="STRING",
    bytes="INT64",
    sha256="STRING",
    filas_csv="INT64",
    tabla_destino="STRING",
)
ESQ_TABLAS = _esquema(
    manifiesto_id="STRING",
    generado_en="TIMESTAMP",
    tabla="STRING",
    archivos="INT64",
    filas_csv="INT64",
    filas_bigquery="INT64",
    coincide="BOOL",
    job_id="STRING",
    huella_archivos="STRING",
    huella_previa="STRING",
    huella_cadena="STRING",
)


def escribir(
    cli: bigquery.Client, nombre: str, filas: list[dict[str, Any]], esquema: Any, agregar: bool
) -> None:
    disp = bigquery.WriteDisposition.WRITE_APPEND if agregar else bigquery.WriteDisposition.WRITE_TRUNCATE
    cfg = bigquery.LoadJobConfig(schema=esquema, write_disposition=disp)
    cli.load_table_from_json(filas, f"{cli.project}.{DS}.{nombre}", job_config=cfg).result()


def filas_en_bigquery(cli: bigquery.Client, tabla: str) -> int:
    fila = next(iter(cli.query(f"SELECT COUNT(*) FROM `{cli.project}.{DS}.bronce_{tabla}`").result()))
    return int(fila[0])


def generar_manifiesto(
    cli: bigquery.Client, espejo: Path, carpeta: Path, job_ids: dict[str, str | None] | None = None
) -> list[dict[str, Any]]:
    por_tabla = {t: [mf.describir(p, espejo, t) for p in partes] for t, partes in fuentes(espejo).items()}
    en_bq = {t: filas_en_bigquery(cli, t) for t in por_tabla}
    previos = mf.leer_cadena(carpeta)
    previa = previos[-1]["huella_cadena"] if previos else mf.GENESIS
    mid, ahora = mf.ahora_id()
    registros = mf.encadenar(previa, mid, ahora, por_tabla, en_bq, job_ids or {})
    escribir(
        cli,
        "platino_manifiesto_carga",
        [
            {"manifiesto_id": mid, "generado_en": ahora, **asdict(a)}
            for lst in por_tabla.values()
            for a in lst
        ],
        ESQ_ARCHIVOS,
        agregar=True,
    )
    escribir(cli, "platino_manifiesto_tablas", registros, ESQ_TABLAS, agregar=True)
    mf.escribir_resumen(carpeta, mid, registros)
    return registros


def calcular_as_of(cli: bigquery.Client) -> str:
    """Mayor `process_date` de las tablas de hechos, leyendo solo esa columna."""
    partes = [
        f"SELECT MAX(SAFE_CAST(process_date AS DATE)) AS d FROM `{cli.project}.{DS}.bronce_{t}`"
        for t in TABLAS_CON_FECHA
    ]
    fila = next(iter(cli.query(f"SELECT MAX(d) FROM ({' UNION ALL '.join(partes)})").result()))
    return fila[0].isoformat()


def inventario(registros: list[dict[str, Any]], as_of: str) -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    for i, r in enumerate(registros, 1):
        filas.append(
            {
                "insumo_id": f"INS-D{i:02d}",
                "nombre": r["tabla"],
                "clase": "sintetico",
                "origen": "dataset del organizador (s3 factored-datathon-2026, prefijo data/)",
                "ubicacion": f"bigquery:{DS}.{r['tabla']}",
                "filas": r["filas_bigquery"],
                "huella": r["huella_archivos"],
                "vence": VENCIMIENTO,
                "as_of": as_of,
            }
        )
    filas.append(
        {
            "insumo_id": "INS-D14",
            "nombre": "respaldo_20260831",
            "clase": "sintetico",
            "origen": "generación de respaldo del organizador (data_backup_20260831)",
            "ubicacion": "local:data/respaldo_20260831 (no se carga a BigQuery)",
            "filas": None,
            "huella": None,
            "vence": None,
            "as_of": as_of,
        }
    )
    return filas


ESQ_INV = _esquema(
    insumo_id="STRING",
    nombre="STRING",
    clase="STRING",
    origen="STRING",
    ubicacion="STRING",
    filas="INT64",
    huella="STRING",
    vence="STRING",
    as_of="STRING",
)
ESQ_CMP = _esquema(
    tabla="STRING",
    archivos_espejo="INT64",
    archivos_respaldo="INT64",
    identicos="INT64",
    distintos="INT64",
    solo_espejo="INT64",
    solo_respaldo="INT64",
    filas_espejo_distintos="INT64",
    filas_respaldo_distintos="INT64",
    comparado_en="TIMESTAMP",
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    orden = args[0] if args else ""
    carpeta = Path(os.environ.get("LATAM_MANIFIESTOS", "datos/manifiestos"))
    if orden == "verificar-cadena":
        registros = mf.leer_cadena(carpeta)
        errores = mf.verificar_cadena(registros)
        print("\n".join(errores) or f"cadena íntegra: {len(registros)} registros")
        return 1 if errores or not registros else 0
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto or orden not in ("manifiesto", "comparar-respaldo", "inventario"):
        print(
            "uso: LATAM_GCP_PROJECT=... evidencia manifiesto|verificar-cadena|comparar-respaldo|inventario",
            file=sys.stderr,
        )
        return 2
    cli = bigquery.Client(project=proyecto)
    espejo = Path(os.environ.get("LATAM_ESPEJO", "data/espejo"))
    respaldo = Path(os.environ.get("LATAM_RESPALDO", "data/respaldo_20260831"))
    if orden == "manifiesto":
        regs = generar_manifiesto(cli, espejo, carpeta)
        for r in regs:
            print(f"{r['tabla']}: {r['filas_csv']} csv, {r['filas_bigquery']} bq, coincide={r['coincide']}")
        return 0 if all(r["coincide"] for r in regs) else 1
    ahora = datetime.now(UTC).isoformat(timespec="seconds")
    if orden == "comparar-respaldo":
        filas = [{**f, "comparado_en": ahora} for f in comparar(espejo, respaldo)]
        escribir(cli, "platino_comparacion_respaldo", filas, ESQ_CMP, agregar=False)
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "comparacion_respaldo.json").write_text(
            json.dumps({"comparado_en": ahora, "tablas": filas}, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(filas, indent=1))
        return 0
    as_of = calcular_as_of(cli)
    regs = mf.leer_cadena(carpeta)
    ultimo = regs[-len(fuentes(espejo)) :]
    filas = inventario(ultimo, as_of)
    escribir(cli, "platino_inventario_insumos", filas, ESQ_INV, agregar=False)
    print(f"AS_OF {as_of}, {len(filas)} insumos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
