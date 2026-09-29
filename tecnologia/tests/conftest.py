from collections.abc import Iterator

import pytest


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
