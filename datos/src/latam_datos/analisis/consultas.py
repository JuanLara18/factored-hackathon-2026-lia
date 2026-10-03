"""Carga y ejecución de `datos/analisis/consultas.sql` (una consulta por marca `-- @nombre`)."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

Fila = dict[str, Any]
Resultados = dict[str, list[Fila]]

RAIZ = Path(__file__).resolve().parents[4]
SQL = RAIZ / "datos" / "analisis" / "consultas.sql"
CIFRAS = RAIZ / "presidencia" / "reporte" / "figuras" / "cifras.json"


def parsear_consultas(texto: str) -> dict[str, str]:
    """Separa el archivo en `{nombre: sql}` por las marcas `-- @nombre`."""
    partes = re.split(r"^-- @(\w+)\s*$", texto, flags=re.MULTILINE)
    return {partes[i]: partes[i + 1].strip() for i in range(1, len(partes) - 1, 2)}


def a_json(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime | date):
        return valor.isoformat()
    return valor


def ejecutar(proyecto: str, dataset: str, ubicacion: str = "US") -> Resultados:
    from google.cloud import bigquery

    cliente = bigquery.Client(project=proyecto, location=ubicacion)
    consultas = parsear_consultas(SQL.read_text(encoding="utf-8"))
    resultados: Resultados = {}
    for nombre, sql in consultas.items():
        filas = list(cliente.query(sql.replace("{ds}", f"{proyecto}.{dataset}")).result())
        resultados[nombre] = [{k: a_json(v) for k, v in cast(Any, fila).items()} for fila in filas]
        print(f"{nombre}: {len(resultados[nombre])} filas")
    return resultados


def guardar(resultados: Resultados, ruta: Path = CIFRAS) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")


def cargar(ruta: Path = CIFRAS) -> Resultados:
    return json.loads(ruta.read_text(encoding="utf-8"))
