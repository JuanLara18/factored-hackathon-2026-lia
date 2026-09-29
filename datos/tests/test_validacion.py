from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from doble_duckdb import MotorDuckDB
from latam_datos.contrato import CONTRATO, TablaCruda
from latam_datos.corrida import main, validar
from latam_datos.motor_bigquery import MotorBigQuery
from latam_datos.reglas import REGLAS, Hallazgo, evaluar, sql_conteos_atipicos, sql_dias_faltantes

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
        "CREATE TABLE latam_bronce.customers (customer_id VARCHAR, document_type VARCHAR, n BIGINT)"
    )
    motor.ejecutar("INSERT INTO latam_bronce.customers VALUES ('1', 'DNI', 5)")
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
    assert [x.filas_afectadas for x in h] == [500]


def test_reporte_cubre_todas_las_reglas_y_persiste(motor: MotorDuckDB) -> None:
    motor.cruda("customers", ["customer_id", "document_type"], [("1", "DNI")])
    hallazgos = validar(motor, AHORA)
    assert any(h.resultado == "bloqueado" for h in hallazgos)  # el resto del contrato no existe
    reglas = {r for (r,) in motor.consultar("SELECT regla_id FROM latam_platino.reporte_calidad_corrida")}
    assert reglas == set(REGLAS)


def test_contrato_por_defecto_es_coherente() -> None:
    nombres = [t.nombre for t in CONTRATO]
    assert len(nombres) == len(set(nombres)) == 13
    assert all(t.llave is None or t.llave in t.requeridas for t in CONTRATO)


def test_sql_en_dialecto_bigquery() -> None:
    m = MotorBigQuery(MagicMock(), "proy")
    q1 = sql_dias_faltantes(m, HECHOS)
    assert "GENERATE_DATE_ARRAY(DATE '2023-06-17', DATE '2026-06-17')" in q1
    assert "SAFE_CAST(`process_date` AS DATE)" in q1 and "`proy.latam_bronce.ventas`" in q1
    q6 = sql_conteos_atipicos(m, HECHOS)
    assert "PERCENTILE_CONT(n, 0.01) OVER (PARTITION BY dow)" in q6 and "EXTRACT(DAYOFWEEK" in q6
    assert "INFORMATION_SCHEMA.COLUMNS" in m.columnas_de("latam_bronce")


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
