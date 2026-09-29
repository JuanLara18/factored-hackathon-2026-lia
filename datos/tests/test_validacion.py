from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from doble_duckdb import MotorDuckDB
from latam_datos.contrato import CONTRATO, Relacion, TablaCruda
from latam_datos.corrida import main, validar
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import (
    REGLAS,
    VERSION_REGLAS,
    Hallazgo,
    evaluar,
    sql_conteos_atipicos,
    sql_dias_faltantes,
)

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
CLIENTES = TablaCruda("customers", "customer_id", ("customer_id", "document_type"))
HECHOS = TablaCruda("ventas", "id", ("id", "process_date"), "process_date", True)


def _por_regla(hallazgos: list[Hallazgo], regla: str) -> list[Hallazgo]:
    return [h for h in hallazgos if h.regla_id == regla]


def test_tabla_ok_no_da_hallazgos(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type", "x"], [("1", "DNI", "a"), ("2", "CC", "b")])
    assert evaluar(motor, (CLIENTES,)) == []


def test_tabla_ausente_y_columna_faltante_bloquean(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id"], [("1",)])
    h = evaluar(motor, (CLIENTES, TablaCruda("products", "product_id", ("product_id",))))
    assert [(x.tabla, x.resultado) for x in _por_regla(h, "Q-BRZ-03")] == [
        ("customers", "bloqueado"),
        ("products", "bloqueado"),
    ]
    assert "document_type" in h[0].detalle


def test_columna_no_texto_avisa(motor: MotorDuckDB) -> None:
    motor.ejecutar(
        "CREATE TABLE latam_bank.bronce_customers (customer_id VARCHAR, document_type VARCHAR, n BIGINT)"
    )
    motor.ejecutar("INSERT INTO latam_bank.bronce_customers VALUES ('1', 'DNI', 5)")
    h = _por_regla(evaluar(motor, (CLIENTES,)), "Q-BRZ-03")
    assert [x.resultado for x in h] == ["aviso"] and "n" in h[0].detalle


def test_tabla_vacia(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [])
    assert [h.regla_id for h in evaluar(motor, (CLIENTES,))] == ["Q-BRZ-11"]


def test_llave_vacia_duplicada_y_vacios_requeridos(motor: MotorDuckDB) -> None:
    filas = [("1", "DNI"), ("1", "CC"), ("", "DNI"), ("3", " "), ("4", "DNI")]
    motor.cruda("customers", ["customer_id", "document_type"], filas)
    h = evaluar(motor, (CLIENTES,))
    assert [(x.regla_id, x.filas_afectadas) for x in h] == [
        ("Q-BRZ-05", 1),
        ("Q-BRZ-12", 1),
        ("Q-BRZ-13", 1),
        ("Q-BRZ-13", 1),
    ]
    assert "2 llaves" not in h[1].detalle and "1 llaves repetidas, 1 filas sobrantes" in h[1].detalle


def test_cobertura_de_fechas_y_fechas_ilegibles(motor: MotorDuckDB) -> None:
    motor.cruda(
        "ventas", ["id", "process_date"], [("1", "2023-06-17"), ("2", "2023-06-19"), ("3", "17/06/2023")]
    )
    h = evaluar(motor, (HECHOS,))
    assert [x.filas_afectadas for x in _por_regla(h, "Q-BRZ-01")] == [1095]
    assert [x.filas_afectadas for x in _por_regla(h, "Q-BRZ-05")] == [1]


def test_conteo_diario_fuera_de_percentiles(motor: MotorDuckDB) -> None:
    lunes = date(2025, 1, 6)
    filas: list[tuple[str, ...]] = []
    for i in range(26):
        dia = (lunes + timedelta(weeks=i)).isoformat()
        filas += [(f"{i}-{j}", dia) for j in range(500 if i == 25 else 10)]
    motor.cruda("ventas", ["id", "process_date"], filas)
    h = _por_regla(evaluar(motor, (HECHOS,)), "Q-BRZ-06")
    assert [x.filas_afectadas for x in h] == [1] and "2025-06-30 500 filas" in h[0].detalle


def test_reporte_cubre_todas_las_reglas_y_persiste(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI")])
    hallazgos = validar(motor, AHORA)
    assert any(h.resultado == "bloqueado" for h in hallazgos)  # el resto del contrato no existe
    reglas = {
        r for (r,) in motor.consultar("SELECT regla_id FROM latam_bank.platino_reporte_calidad_corrida")
    }
    assert reglas == set(REGLAS)


def test_contrato_por_defecto_es_coherente() -> None:
    nombres = [t.nombre for t in CONTRATO]
    assert len(nombres) == len(set(nombres)) == 13
    assert all(t.llave is None or t.llave in t.requeridas for t in CONTRATO)


def test_sql_en_dialecto_bigquery() -> None:
    m = MotorBigQuery(MagicMock(), "proy")
    q1 = sql_dias_faltantes(m, HECHOS)
    assert "GENERATE_DATE_ARRAY(DATE '2023-06-17', DATE '2026-06-17')" in q1
    assert "SAFE_CAST(`process_date` AS DATE)" in q1 and "`proy.latam_bank.bronce_ventas`" in q1
    q6 = sql_conteos_atipicos(m, HECHOS)
    assert "PERCENTILE_CONT(n, 0.5) OVER (PARTITION BY dow)" in q6 and "EXTRACT(DAYOFWEEK" in q6
    assert "PERCENTILE_CONT(dev, 0.5) OVER (PARTITION BY dow)" in q6
    assert "INFORMATION_SCHEMA.COLUMNS" in m.columnas_de("latam_bank")


def test_motor_bigquery_ejecuta_y_consulta_con_ubicacion() -> None:
    cliente = MagicMock()
    fila = MagicMock()
    fila.values.return_value = ["a", 1]
    cliente.query.return_value.result.return_value = [fila]
    m = MotorBigQuery(cliente, "p", "us-central1")
    assert m.consultar("SELECT 1") == [("a", 1)]
    m.ejecutar("SELECT 2")
    assert cliente.query.call_args.kwargs == {"location": "us-central1"}
    assert m.lit("it's \\ x") == "'it\\'s \\\\ x'" and m.lit(None) == "NULL" and m.lit(True) == "TRUE"


def test_cli_sin_proyecto_sale_con_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LATAM_GCP_PROJECT", raising=False)
    assert main(["validar"]) == 2


def _hechos_semanales(motor: MotorDuckDB, n_por_semana: dict[int, int], base: int = 100) -> None:
    """26 lunes con `base` filas (ruido de +-2); `n_por_semana` fija el conteo de la semana i."""
    lunes = date(2025, 1, 6)
    filas: list[tuple[str, ...]] = []
    for i in range(26):
        dia = (lunes + timedelta(weeks=i)).isoformat()
        filas += [(f"{i}-{j}", dia) for j in range(n_por_semana.get(i, base + (i % 5) - 2))]
    motor.cruda("ventas", ["id", "process_date"], filas)


def test_caida_de_un_dia_se_reporta_en_una_sola_fila_por_tabla(motor: MotorDuckDB) -> None:
    _hechos_semanales(motor, {7: 20, 12: 3, 20: 300})
    (h,) = _por_regla(evaluar(motor, (HECHOS,)), "Q-BRZ-06")
    assert h.tabla == "ventas" and h.filas_afectadas == 3
    assert h.detalle.index("2025-03-31 3 filas") < h.detalle.index("2025-02-24 20 filas")


def test_ruido_normal_no_marca_ningun_dia(motor: MotorDuckDB) -> None:
    _hechos_semanales(motor, {})
    assert _por_regla(evaluar(motor, (HECHOS,)), "Q-BRZ-06") == []


def test_solo_reporta_los_cinco_peores_dias(motor: MotorDuckDB) -> None:
    _hechos_semanales(motor, {i: 10 for i in range(0, 16, 2)})
    (h,) = _por_regla(evaluar(motor, (HECHOS,)), "Q-BRZ-06")
    assert h.filas_afectadas == 8 and h.detalle.count(" filas vs mediana ") == 5


def test_filas_completas_duplicadas_sin_llave(motor: MotorDuckDB) -> None:
    sin_llave = TablaCruda("eventos", None, ())
    motor.cruda("eventos", ["a", "b"], [("1", "x"), ("1", "x"), ("1", "x"), ("2", "y"), ("2", "z")])
    (h,) = _por_regla(evaluar(motor, (sin_llave,), ()), "Q-BRZ-14")
    assert h.filas_afectadas == 2 and "1 filas repetidas" in h.detalle and "40.00%" in h.detalle


def test_huerfanos_cuentan_solo_valores_no_vacios(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI"), ("2", "CC")])
    filas = [("a", "1"), ("b", "9"), ("c", "8"), ("d", ""), ("e", "2")]
    motor.cruda("products", ["product_id", "customer_id"], filas)
    rel = (Relacion("products", "customer_id", "customers", "customer_id"),)
    (h,) = _por_regla(evaluar(motor, (), rel), "Q-BRZ-15")
    assert h.tabla == "products" and h.filas_afectadas == 2 and "2 de 4 (50.00%)" in h.detalle
    assert evaluar(motor, (), (Relacion("products", "nada", "customers", "customer_id"),)) == []


def test_contrato_exige_monto_usd_y_fraude() -> None:
    (tx,) = [t for t in CONTRATO if t.nombre == "transactions"]
    assert {"amount_usd", "is_fraud"} <= set(tx.requeridas)


REPORTE_SQL = "latam_bank.platino_reporte_calidad_corrida"


def _hallazgos_del_reporte(motor: MotorDuckDB) -> list[tuple[Any, ...]]:
    return motor.consultar(
        "SELECT regla_id, resultado, tabla, filas_afectadas, detalle, commit, version_reglas, umbral "
        f"FROM {REPORTE_SQL} ORDER BY 1, 3, 5"
    )


def test_validar_es_idempotente_salvo_el_id_de_corrida(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI"), ("1", "CC"), ("", "DNI")])
    motor.cruda("products", ["product_id", "customer_id"], [("a", "1"), ("b", "7")])
    validar(motor, AHORA, "abc1234def")
    primera = _hallazgos_del_reporte(motor)
    motor.ejecutar(f"DELETE FROM {REPORTE_SQL}")
    validar(motor, AHORA + timedelta(hours=3), "abc1234def")
    assert primera and _hallazgos_del_reporte(motor) == primera


def test_reporte_lleva_commit_version_umbral_y_corrida_id(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI")])
    validar(motor, AHORA, "abc1234def")
    filas = motor.consultar(f"SELECT DISTINCT corrida_id, commit, version_reglas FROM {REPORTE_SQL}")
    assert filas == [(f"20260928T120000Z-abc1234-v{VERSION_REGLAS}", "abc1234def", VERSION_REGLAS)]
    umbrales = dict(motor.consultar(f"SELECT DISTINCT regla_id, umbral FROM {REPORTE_SQL}"))
    assert "3.5" in umbrales["Q-BRZ-06"] and set(umbrales) == set(REGLAS)


def test_reporte_antiguo_recibe_las_columnas_nuevas(motor: MotorDuckDB) -> None:
    motor.ejecutar(
        f"CREATE TABLE {REPORTE_SQL} (corrida_id VARCHAR, zona VARCHAR, regla_id VARCHAR, dimension VARCHAR, "
        "severidad VARCHAR, resultado VARCHAR, tabla VARCHAR, filas_afectadas BIGINT, detalle VARCHAR, "
        "evaluado_en TIMESTAMP)"
    )
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI")])
    validar(motor, AHORA, "c0ffee0")
    assert motor.consultar(f"SELECT DISTINCT commit FROM {REPORTE_SQL}") == [("c0ffee0",)]


@pytest.mark.integracion
def test_validar_contra_el_dataset_real() -> None:
    """Humo contra BigQuery: solo con --integracion y LATAM_GCP_PROJECT. Escribe a una tabla temporal."""
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        pytest.skip("falta LATAM_GCP_PROJECT")
    from google.cloud import bigquery  # type: ignore[attr-defined]

    ubicacion = os.environ.get("LATAM_GCP_LOCATION", "US")
    motor = MotorBigQuery(bigquery.Client(project=proyecto, location=ubicacion), proyecto, ubicacion)
    tabla = f"latam_bank.tmp_reporte_calidad_{os.getpid()}"
    try:
        hallazgos = validar(motor, datetime.now(UTC), tabla_reporte=tabla)
        reglas = {r for (r,) in motor.consultar(f"SELECT regla_id FROM {motor.t(tabla)}")}
        assert reglas == set(REGLAS)
        assert not [h for h in hallazgos if h.resultado == "bloqueado"]
    finally:
        motor.ejecutar(f"DROP TABLE IF EXISTS {motor.t(tabla)}")
