from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import boto3
import duckdb
from latam_datos.config import Rutas
from latam_datos.espejo import espejar, listar_bucket
from moto import mock_aws

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
BUCKET = "bucket-sintetico"


def _bucket() -> Any:
    s3 = boto3.client("s3", region_name="us-east-2")
    s3.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "us-east-2"})
    s3.put_object(Bucket=BUCKET, Key="data/ventas/2025-01-01.csv", Body=b"id,v\n1,a\n")
    s3.put_object(Bucket=BUCKET, Key="data/ventas/2025-01-02.csv", Body=b"id,v\n2,b\n")
    s3.put_object(Bucket=BUCKET, Key="suelto.csv", Body=b"x\n1\n")
    s3.put_object(Bucket=BUCKET, Key="data_backup_20260831/ventas/2025-01-01.csv", Body=b"id,v\n9,z\n")
    return s3


def _platino() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("CREATE SCHEMA platino")
    return con


@mock_aws
def test_lista_completo_descarga_autorizados_e_inventaria(rutas: Rutas) -> None:
    s3 = _bucket()
    platino = _platino()
    objetos, res = espejar(s3, BUCKET, rutas.espejo, platino, "c1", AHORA)
    assert len(objetos) == 4
    assert sorted(res.descargados) == ["data/ventas/2025-01-01.csv", "data/ventas/2025-01-02.csv"]
    assert not (rutas.espejo / "suelto.csv").exists()
    filas = platino.execute(
        "SELECT autorizado, count(*) FROM platino.inventario_bucket GROUP BY 1 ORDER BY 1"
    ).fetchall()
    assert filas == [(False, 2), (True, 2)]


@mock_aws
def test_sincronizar_por_etag_no_redescarga_y_detecta_cambio(rutas: Rutas) -> None:
    s3 = _bucket()
    platino = _platino()
    espejar(s3, BUCKET, rutas.espejo, platino, "c1", AHORA)
    _, res = espejar(s3, BUCKET, rutas.espejo, platino, "c2", AHORA)
    assert res.descargados == ()
    assert len(res.sin_cambio) == 2
    s3.put_object(Bucket=BUCKET, Key="data/ventas/2025-01-01.csv", Body=b"id,v\n1,cambio\n")
    _, res = espejar(s3, BUCKET, rutas.espejo, platino, "c3", AHORA)
    assert res.descargados == ("data/ventas/2025-01-01.csv",)
    assert (rutas.espejo / "data/ventas/2025-01-01.csv").read_bytes().endswith(b"cambio\n")


@mock_aws
def test_listado_pagina() -> None:
    s3 = boto3.client("s3", region_name="us-east-2")
    s3.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "us-east-2"})
    for i in range(1105):
        s3.put_object(Bucket=BUCKET, Key=f"data/t/{i:05d}.csv", Body=b"a\n")
    assert len(listar_bucket(s3, BUCKET)) == 1105
