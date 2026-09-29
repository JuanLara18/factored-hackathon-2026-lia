from __future__ import annotations

import pytest
from doble_duckdb import MotorDuckDB


@pytest.fixture
def motor() -> MotorDuckDB:
    return MotorDuckDB()
