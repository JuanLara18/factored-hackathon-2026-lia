"""Interfaz del motor SQL. La implementación real es BigQuery (`motor_bigquery`); las pruebas usan un doble
DuckDB con CSV sintéticos. El SQL de bronce se escribe una vez; las diferencias de dialecto viven aquí."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Protocol

NULO_CSV = "@@sin_nulos@@"
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

    def cargar_csv(self, uri: str, tabla: str, columnas: list[str]) -> None:
        """Carga un CSV con encabezado, todas las columnas STRING, reemplazando `tabla`."""
        ...

    def sha256(self, expr: str) -> str:
        """Huella hexadecimal en minúsculas."""
        ...

    def agregar_texto(self, expr: str, separador: str, orden: str) -> str: ...

    def fecha_segura(self, expr: str) -> str: ...

    def dia_semana(self, expr: str) -> str: ...

    def percentil(self, expr: str, p: float, particion: str) -> str: ...

    def serie_de_dias(self, inicio: date, fin: date) -> str:
        """Subconsulta con una columna `dia` DATE por cada día del rango."""
        ...


SEPARADOR = "\x1f"
