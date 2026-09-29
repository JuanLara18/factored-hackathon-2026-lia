from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from latam_datos.config import Rutas

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


@pytest.fixture
def rutas(tmp_path: Path) -> Rutas:
    return Rutas(tmp_path / "data")
