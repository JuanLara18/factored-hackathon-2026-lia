from __future__ import annotations

import contextlib

import pytest
from doble_duckdb import MotorDuckDB


def pytest_addoption(parser: pytest.Parser) -> None:
    with contextlib.suppress(ValueError):  # ya registrada por otro conftest
        parser.addoption("--integracion", action="store_true", help="corre las pruebas contra BigQuery real")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--integracion"):
        return
    salta = pytest.mark.skip(reason="requiere --integracion y LATAM_GCP_PROJECT")
    for item in items:
        if "integracion" in item.keywords:
            item.add_marker(salta)


@pytest.fixture
def motor() -> MotorDuckDB:
    return MotorDuckDB()
