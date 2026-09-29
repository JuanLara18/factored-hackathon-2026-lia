"""Motor BigQuery. El cliente se inyecta; las consultas son de una sola pasada y determinísticas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from google.cloud import bigquery  # pyright: ignore[reportUnknownVariableType]

from latam_datos.motor import NULO_CSV, Logico, Valor

_TIPOS: dict[Logico, str] = {
    "texto": "STRING",
    "entero": "INT64",
    "fecha_hora": "TIMESTAMP",
    "booleano": "BOOL",
}


class MotorBigQuery:
    def __init__(self, cliente: Any, proyecto: str, ubicacion: str = "us-central1") -> None:
        self.cliente = cliente
        self.proyecto = proyecto
        self.ubicacion = ubicacion

    def t(self, nombre: str) -> str:
        dataset, tabla = nombre.split(".")
        return f"`{self.proyecto}.{dataset}.{tabla}`"

    def ident(self, columna: str) -> str:
        return f"`{columna}`"

    def tipo(self, logico: Logico) -> str:
        return _TIPOS[logico]

    def lit(self, valor: Valor) -> str:
        if valor is None:
            return "NULL"
        if isinstance(valor, bool):
            return "TRUE" if valor else "FALSE"
        if isinstance(valor, int):
            return str(valor)
        if isinstance(valor, datetime):
            return f"TIMESTAMP '{valor.replace(tzinfo=None).isoformat(sep=' ')}'"
        if isinstance(valor, date):
            return f"DATE '{valor.isoformat()}'"
        return "'" + valor.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"

    def ejecutar(self, sql: str) -> None:
        self.cliente.query(sql, location=self.ubicacion).result()

    def consultar(self, sql: str) -> list[tuple[Any, ...]]:
        return [tuple(fila.values()) for fila in self.cliente.query(sql, location=self.ubicacion).result()]

    def configuracion_de_carga(self, columnas: list[str]) -> Any:
        """Todo STRING: nada se interpreta ni se corrige en bronce."""
        return bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=[bigquery.SchemaField(c, "STRING") for c in columnas],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            null_marker=NULO_CSV,
            allow_quoted_newlines=True,
            allow_jagged_rows=False,
            max_bad_records=0,
            encoding="UTF-8",
        )

    def cargar_csv(self, uri: str, tabla: str, columnas: list[str]) -> None:
        dataset, nombre = tabla.split(".")
        trabajo = self.cliente.load_table_from_uri(
            uri,
            f"{self.proyecto}.{dataset}.{nombre}",
            job_config=self.configuracion_de_carga(columnas),
            location=self.ubicacion,
        )
        trabajo.result()

    def sha256(self, expr: str) -> str:
        return f"TO_HEX(SHA256({expr}))"

    def agregar_texto(self, expr: str, separador: str, orden: str) -> str:
        return f"STRING_AGG({expr}, {separador} ORDER BY {orden})"

    def fecha_segura(self, expr: str) -> str:
        return f"SAFE_CAST({expr} AS DATE)"

    def dia_semana(self, expr: str) -> str:
        return f"EXTRACT(DAYOFWEEK FROM {expr})"

    def percentil(self, expr: str, p: float, particion: str) -> str:
        return f"PERCENTILE_CONT({expr}, {p}) OVER (PARTITION BY {particion})"

    def serie_de_dias(self, inicio: date, fin: date) -> str:
        return f"SELECT dia FROM UNNEST(GENERATE_DATE_ARRAY(DATE '{inicio}', DATE '{fin}')) AS dia"
