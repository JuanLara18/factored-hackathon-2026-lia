from __future__ import annotations

from pathlib import Path

import pytest
from doble_duckdb import AlmacenLocal, MotorDuckDB


@pytest.fixture
def almacen(tmp_path: Path) -> AlmacenLocal:
    return AlmacenLocal(tmp_path / "bucket")


@pytest.fixture
def motor() -> MotorDuckDB:
    return MotorDuckDB()
