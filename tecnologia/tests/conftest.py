import contextlib
from collections.abc import Iterator

import pytest


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


@pytest.fixture(scope="session")
def dsn_postgres() -> Iterator[str]:
    """Postgres real en contenedor (DP-TEC-06); se omite si Docker no está disponible."""
    try:
        from testcontainers.community.postgres import PostgresContainer

        contenedor = PostgresContainer("postgres:16", driver=None)
        contenedor.start()
    except Exception as error:
        pytest.skip(f"Docker no disponible: {error}")
    try:
        yield contenedor.get_connection_url()
    finally:
        contenedor.stop()
