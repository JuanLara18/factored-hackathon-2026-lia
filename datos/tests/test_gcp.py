"""Pruebas de la ruta real con clientes de Google simulados: ninguna llamada a GCP."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from latam_datos.config import Configuracion
from latam_datos.corrida import main
from latam_datos.espejo import AlmacenGCS, ObjetoGCS, md5_hex, registrar_inventario
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import sql_conteos_atipicos, sql_dias_faltantes, sql_no_autorizados, sql_solapamiento

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
MD5_VACIO = "1B2M2Y8AsgTpgAmY7PhCfg=="


def _blob(nombre: str) -> MagicMock:
    b = MagicMock()
    b.name, b.generation, b.md5_hash, b.etag, b.size, b.updated = nombre, 7, MD5_VACIO, "CAE=", 10, AHORA
    return b


def test_lista_gcs_con_generation_md5_y_omite_staging() -> None:
    cliente = MagicMock()
    cliente.list_blobs.return_value = [
        _blob("data/t/b.csv"),
        _blob("_staging/x.csv"),
        _blob("a.csv"),
        _blob("data/"),
    ]
    objetos = AlmacenGCS(cliente, "bkt").listar()
    assert [o.key for o in objetos] == ["a.csv", "data/t/b.csv"]
    assert objetos[1].generation == 7
    assert objetos[1].md5 == md5_hex(MD5_VACIO) == "d41d8cd98f00b204e9800998ecf8427e"
    cliente.list_blobs.assert_called_once_with("bkt")


def test_inventario_va_a_latam_platino() -> None:
    cliente = MagicMock()
    motor = MotorBigQuery(cliente, "proy")
    objs = [ObjetoGCS("data/t/a.csv", 1, "ab", "e", 5, AHORA), ObjetoGCS("raiz.csv", 2, "cd", "e", 6, AHORA)]
    assert registrar_inventario(motor, "c1", objs, AHORA) == 2
    ddl, insercion = (c.args[0] for c in cliente.query.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS `proy.latam_platino.inventario_bucket`" in ddl and "INT64" in ddl
    assert insercion.startswith("INSERT INTO `proy.latam_platino.inventario_bucket` VALUES")
    assert "'data/t/a.csv', 1, 'ab'" in insercion and "TRUE" in insercion and "FALSE" in insercion


def test_configuracion_de_carga_todo_string() -> None:
    motor = MotorBigQuery(MagicMock(), "proy")
    cfg = motor.configuracion_de_carga(["id", "valor", "_linea"])
    assert [(f.name, f.field_type) for f in cfg.schema] == [
        ("id", "STRING"),
        ("valor", "STRING"),
        ("_linea", "STRING"),
    ]
    assert cfg.skip_leading_rows == 1 and cfg.max_bad_records == 0 and cfg.allow_jagged_rows is False
    assert cfg.write_disposition == "WRITE_TRUNCATE" and cfg.source_format == "CSV"


def test_cargar_csv_llama_a_load_table_from_uri() -> None:
    cliente = MagicMock()
    MotorBigQuery(cliente, "proy", "us-central1").cargar_csv(
        "gs://b/_staging/x.csv", "latam_bronce._stg_x", ["a"]
    )
    args, kwargs = cliente.load_table_from_uri.call_args
    assert args == ("gs://b/_staging/x.csv", "proy.latam_bronce._stg_x")
    assert kwargs["location"] == "us-central1"
    cliente.load_table_from_uri.return_value.result.assert_called_once()


def test_sql_de_reglas_en_dialecto_bigquery() -> None:
    m = MotorBigQuery(MagicMock(), "proy")
    q1 = sql_dias_faltantes(m)
    assert "GENERATE_DATE_ARRAY(DATE '2023-06-17', DATE '2026-06-17')" in q1
    assert "SAFE_CAST(process_date AS DATE)" in q1 and "`proy.latam_bronce._lotes`" in q1
    q6 = sql_conteos_atipicos(m)
    assert "PERCENTILE_CONT(filas, 0.01) OVER (PARTITION BY tabla, dow)" in q6 and "EXTRACT(DAYOFWEEK" in q6
    assert "`proy.latam_platino.inventario_bucket`" in sql_no_autorizados(m)
    q8 = sql_solapamiento(m, "latam_bronce._stg_x", "latam_bronce.ventas", "id", "abc")
    assert "`proy.latam_bronce._stg_x`" in q8 and "_lote_id = 'abc'" in q8


def test_literales_bigquery() -> None:
    m = MotorBigQuery(MagicMock(), "p")
    assert m.lit("it's \\ x") == "'it\\'s \\\\ x'"
    assert m.lit(None) == "NULL" and m.lit(True) == "TRUE" and m.lit(3) == "3"
    assert m.lit(date(2025, 1, 2)) == "DATE '2025-01-02'"


def test_configuracion_desde_entorno() -> None:
    assert Configuracion.desde_entorno({"LATAM_GCP_PROJECT": "p", "LATAM_GCS_ESPEJO": "b"}) == Configuracion(
        "p", "b"
    )
    with pytest.raises(ValueError, match="LATAM_GCS_ESPEJO"):
        Configuracion.desde_entorno({"LATAM_GCP_PROJECT": "p"})


def test_cli_sin_configuracion_sale_con_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LATAM_GCP_PROJECT", raising=False)
    monkeypatch.delenv("LATAM_GCS_ESPEJO", raising=False)
    assert main(["bronce"]) == 2
