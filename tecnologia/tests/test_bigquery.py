"""Adaptador BigQuery: consultas parametrizadas (unitaria con cliente falso) y humo real opt-in."""

import os
from types import SimpleNamespace
from typing import Any

import pytest
from latam_tecnologia.herramientas.bigquery import LecturaBigQuery


class _ClienteFalso:
    def __init__(self) -> None:
        self.consultas: list[tuple[str, dict[str, Any]]] = []

    def query(self, sql: str, job_config: Any, location: str) -> Any:
        self.consultas.append((sql, {p.name: p.value for p in job_config.query_parameters}))
        return SimpleNamespace(result=lambda: [])


def test_consultas_parametrizadas_y_filtradas_por_cliente() -> None:
    falso = _ClienteFalso()
    lectura = LecturaBigQuery("proyecto-x", cliente=falso)  # pyright: ignore[reportArgumentType]
    malicioso = "c1' or '1'='1"
    lectura.transacciones_recientes(malicioso, 10)
    lectura.transaccion(malicioso, "t1")
    lectura.productos(malicioso)
    for sql, parametros in falso.consultas:
        assert "customer_id = @cliente" in sql
        assert malicioso not in sql and parametros["cliente"] == malicioso


def test_la_cache_evita_repetir_la_misma_consulta_y_no_mezcla_clientes() -> None:
    falso = _ClienteFalso()
    lectura = LecturaBigQuery("proyecto-x", cliente=falso, cache_s=60)  # pyright: ignore[reportArgumentType]
    lectura.productos("c1")
    lectura.productos("c1")
    lectura.transacciones_recientes("c1", 10)
    lectura.transacciones_recientes("c1", 10)
    assert len(falso.consultas) == 2
    lectura.productos("c2")  # otro cliente es otra consulta: la llave incluye los parámetros
    lectura.transacciones_recientes("c1", 20)
    assert len(falso.consultas) == 4
    sin_cache = LecturaBigQuery("proyecto-x", cliente=falso)  # pyright: ignore[reportArgumentType]
    sin_cache.productos("c1")
    sin_cache.productos("c1")
    assert len(falso.consultas) == 6


def test_identificadores_invalidos() -> None:
    with pytest.raises(ValueError):
        LecturaBigQuery("x`; drop", cliente=_ClienteFalso())  # pyright: ignore[reportArgumentType]


@pytest.mark.integracion
def test_humo_bigquery_real_solo_lectura() -> None:
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        pytest.skip("falta LATAM_GCP_PROJECT")
    lectura = LecturaBigQuery(proyecto)
    from google.cloud import bigquery

    cliente = bigquery.Client(project=proyecto, location="US")
    fila = next(
        iter(
            cliente.query(
                f"select customer_id from `{proyecto}.latam_bank"
                ".oro_operacional_transacciones_recientes` limit 1"
            ).result()
        )
    )
    cid: str = fila["customer_id"]
    recientes = lectura.transacciones_recientes(cid, 5)
    assert recientes
    assert lectura.transaccion(cid, recientes[0].transaction_id) == recientes[0]
    assert lectura.transaccion("cliente-inexistente", recientes[0].transaction_id) is None
    assert lectura.productos(cid)
