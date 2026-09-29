"""Dobles de prueba: motor DuckDB y almacén en disco. Solo para pruebas con CSV sintéticos (D-30)."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb
from latam_datos.config import PREFIJO_STAGING
from latam_datos.espejo import ObjetoGCS
from latam_datos.motor import NULO_CSV, Logico, Valor

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
        self.sentencias: list[str] = []

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
        self.sentencias.append(sql)
        self.con.execute(sql)

    def consultar(self, sql: str) -> list[tuple[Any, ...]]:
        return self.con.execute(sql).fetchall()

    def cargar_csv(self, uri: str, tabla: str, columnas: list[str]) -> None:
        tipos = ", ".join(f"'{c}': 'VARCHAR'" for c in columnas)
        self.con.execute(
            f"CREATE OR REPLACE TABLE {tabla} AS SELECT * FROM read_csv('{uri}', header=true, "
            f"columns={{{tipos}}}, nullstr='{NULO_CSV}')"
        )

    def sha256(self, expr: str) -> str:
        return f"sha256({expr})"

    def agregar_texto(self, expr: str, separador: str, orden: str) -> str:
        return f"string_agg({expr}, {separador} ORDER BY {orden})"

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


class AlmacenLocal:
    """Bucket simulado en un directorio."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz
        self._generacion = 0

    def poner(self, key: str, datos: bytes) -> None:
        ruta = self.raiz / key
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(datos)
        self._generacion += 1

    def listar(self) -> list[ObjetoGCS]:
        salida: list[ObjetoGCS] = []
        for ruta in sorted(self.raiz.rglob("*")):
            key = ruta.relative_to(self.raiz).as_posix()
            if ruta.is_file() and not key.startswith(PREFIJO_STAGING):
                datos = ruta.read_bytes()
                salida.append(
                    ObjetoGCS(
                        key,
                        self._generacion,
                        hashlib.md5(datos).hexdigest(),
                        "etag",
                        len(datos),
                        datetime(2026, 9, 1),
                    )
                )
        return salida

    def leer(self, key: str) -> bytes:
        return (self.raiz / key).read_bytes()

    def escribir(self, key: str, datos: bytes) -> str:
        ruta = self.raiz / key
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(datos)
        return ruta.as_posix()

    def borrar(self, key: str) -> None:
        (self.raiz / key).unlink()
