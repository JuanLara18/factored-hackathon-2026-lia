"""Comparación local de la generación de respaldo del organizador contra el espejo (DAT-1.4).

Por ruta relativa y SHA-256; donde el contenido difiere, también conteo de filas. Solo el resumen se guarda;
el respaldo no se carga a BigQuery.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from latam_datos.manifiesto import contar_filas, sha256_de


def _csvs(raiz: Path) -> dict[str, Path]:
    return {p.relative_to(raiz).as_posix(): p for p in sorted(raiz.rglob("*.csv"))}


def tabla_de(clave: str) -> str:
    return clave.split("/")[0].removesuffix(".csv")


def comparar(espejo: Path, respaldo: Path) -> list[dict[str, Any]]:
    """Una fila por tabla con idénticos, distintos, solo en cada lado y filas de los archivos distintos."""
    a, b = _csvs(espejo), _csvs(respaldo)
    filas: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "archivos_espejo": 0,
            "archivos_respaldo": 0,
            "identicos": 0,
            "distintos": 0,
            "solo_espejo": 0,
            "solo_respaldo": 0,
            "filas_espejo_distintos": 0,
            "filas_respaldo_distintos": 0,
        }
    )
    for clave in sorted(a.keys() | b.keys()):
        f = filas[tabla_de(clave)]
        f["archivos_espejo"] += clave in a
        f["archivos_respaldo"] += clave in b
        if clave not in b:
            f["solo_espejo"] += 1
        elif clave not in a:
            f["solo_respaldo"] += 1
        elif sha256_de(a[clave]) == sha256_de(b[clave]):
            f["identicos"] += 1
        else:
            f["distintos"] += 1
            f["filas_espejo_distintos"] += contar_filas(a[clave])
            f["filas_respaldo_distintos"] += contar_filas(b[clave])
    return [{"tabla": t, **f} for t, f in sorted(filas.items())]
