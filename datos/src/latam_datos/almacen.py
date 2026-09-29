"""Acceso a las bases DuckDB de las zonas. El catálogo toma el nombre del archivo (`bronce`, `platino`)."""

from __future__ import annotations

from pathlib import Path

import duckdb


def abrir_zona(ruta: Path) -> duckdb.DuckDBPyConnection:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(ruta))
