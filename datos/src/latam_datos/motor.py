"""Interfaz del motor SQL. La implementación real es BigQuery (`motor_bigquery`); las pruebas usan un doble
DuckDB con tablas sintéticas. El SQL se escribe una vez; las diferencias de dialecto viven aquí."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Protocol

Logico = Literal["texto", "entero", "fecha_hora", "booleano"]
Valor = str | int | bool | datetime | date | None


class Motor(Protocol):
    def t(self, nombre: str) -> str:
        """Nombre calificado de una tabla `dataset.tabla`."""
        ...

    def ident(self, columna: str) -> str: ...

    def tipo(self, logico: Logico) -> str: ...

    def lit(self, valor: Valor) -> str: ...

    def ejecutar(self, sql: str) -> None: ...

    def consultar(self, sql: str) -> list[tuple[Any, ...]]: ...

    def columnas_de(self, dataset: str) -> str:
        """Consulta (tabla, columna, tipo) de todas las columnas de un dataset."""
        ...

    def fecha_segura(self, expr: str) -> str: ...

    def dia_semana(self, expr: str) -> str: ...

    def percentil(self, expr: str, p: float, particion: str) -> str: ...

    def serie_de_dias(self, inicio: date, fin: date) -> str:
        """Subconsulta con una columna `dia` DATE por cada día del rango."""
        ...
