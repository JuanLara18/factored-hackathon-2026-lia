"""Doble de prueba: motor DuckDB con tablas sintéticas. Solo para pruebas (D-30)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import duckdb
from latam_datos.motor import Logico, Valor

_TIPOS: dict[Logico, str] = {
    "texto": "VARCHAR",
    "entero": "BIGINT",
    "fecha_hora": "TIMESTAMP",
    "booleano": "BOOLEAN",
}


class MotorDuckDB:
    def __init__(self) -> None:
        self.con = duckdb.connect()
        self.con.execute("CREATE SCHEMA latam_bronce")
        self.con.execute("CREATE SCHEMA latam_platino")

    def cruda(self, tabla: str, columnas: list[str], filas: list[tuple[str, ...]]) -> None:
        """Crea una tabla cruda todo texto en `latam_bronce`, como la dejaría el proceso externo."""
        defs = ", ".join(f'"{c}" VARCHAR' for c in columnas)
        self.con.execute(f"CREATE TABLE latam_bronce.{tabla} ({defs})")
        if filas:
            marcas = ", ".join("?" * len(columnas))
            self.con.executemany(f"INSERT INTO latam_bronce.{tabla} VALUES ({marcas})", filas)

    def t(self, nombre: str) -> str:
        return nombre

    def ident(self, columna: str) -> str:
        return f'"{columna}"'

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
        return "'" + valor.replace("'", "''") + "'"

    def ejecutar(self, sql: str) -> None:
        self.con.execute(sql)

    def consultar(self, sql: str) -> list[tuple[Any, ...]]:
        return self.con.execute(sql).fetchall()

    def columnas_de(self, dataset: str) -> str:
        return (
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            f"WHERE table_schema = '{dataset}' ORDER BY table_name, ordinal_position"
        )

    def fecha_segura(self, expr: str) -> str:
        return f"TRY_CAST({expr} AS DATE)"

    def dia_semana(self, expr: str) -> str:
        return f"dayofweek({expr})"

    def percentil(self, expr: str, p: float, particion: str) -> str:
        return f"quantile_cont({expr}, {p}) OVER (PARTITION BY {particion})"

    def serie_de_dias(self, inicio: date, fin: date) -> str:
        return (
            f"SELECT CAST(dia AS DATE) AS dia FROM generate_series(DATE '{inicio}', DATE '{fin}', "
            f"INTERVAL 1 DAY) AS t(dia)"
        )
