"""Rutas y constantes de la ingesta. Nada de credenciales: el perfil de AWS vive fuera del repositorio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PERFIL_AWS = "latam-organizador"
PREFIJO_AUTORIZADO = "data/"
GENERACION_ACTUAL = "data"
GENERACION_RESPALDO = "respaldo"
PREFIJO_RESPALDO = "data_backup_20260831/"


@dataclass(frozen=True)
class Rutas:
    """Distribución de `data/` (definición, sección 2.2). Todo cuelga de una sola raíz ignorada por git."""

    raiz: Path

    @property
    def espejo(self) -> Path:
        return self.raiz / "espejo"

    @property
    def bronce(self) -> Path:
        return self.raiz / "bronce"

    @property
    def zonas(self) -> Path:
        return self.raiz / "zonas"

    @property
    def bronce_db(self) -> Path:
        return self.zonas / "bronce.duckdb"

    @property
    def platino_db(self) -> Path:
        return self.zonas / "platino.duckdb"


def rutas_por_defecto() -> Rutas:
    """La raíz sale de `LATAM_DATA_DIR` y, si no existe, de `./data`."""
    return Rutas(Path(os.environ.get("LATAM_DATA_DIR", "data")))
