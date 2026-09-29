"""DAT-1.1: lector del bucket de aterrizaje en Cloud Storage y su inventario en `latam_platino`.

La copia de S3 a Cloud Storage la hace Storage Transfer Service (Terraform, D-30); aquí solo se lista y
se lee.
La identidad de un lote es el contenido (`md5`), no la `generation`, que cambia si la transferencia reescribe
el objeto sin cambiar su contenido.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from latam_datos.config import INVENTARIO, PREFIJO_AUTORIZADO, PREFIJO_STAGING
from latam_datos.motor import Logico, Motor


@dataclass(frozen=True)
class ObjetoGCS:
    key: str
    generation: int
    md5: str  # hexadecimal
    etag: str
    tamano: int
    actualizado: datetime

    @property
    def autorizado(self) -> bool:
        """Fuente autorizada: `data/<tabla>/...`. La raíz y otros prefijos solo se registran (Q-BRZ-09)."""
        return self.key.startswith(PREFIJO_AUTORIZADO) and self.key.count("/") >= 2


class Almacen(Protocol):
    def listar(self) -> list[ObjetoGCS]: ...

    def leer(self, key: str) -> bytes: ...

    def escribir(self, key: str, datos: bytes) -> str:
        """Devuelve el URI del objeto escrito."""
        ...

    def borrar(self, key: str) -> None: ...


def md5_hex(md5_base64: str | None) -> str:
    return base64.b64decode(md5_base64).hex() if md5_base64 else ""


class AlmacenGCS:
    """Bucket de aterrizaje. `cliente` es `google.cloud.storage.Client`."""

    def __init__(self, cliente: Any, bucket: str) -> None:
        self.cliente = cliente
        self.nombre = bucket

    def listar(self) -> list[ObjetoGCS]:
        objetos = [
            ObjetoGCS(
                key=str(b.name),
                generation=int(b.generation),
                md5=md5_hex(b.md5_hash),
                etag=str(b.etag),
                tamano=int(b.size),
                actualizado=b.updated,
            )
            for b in self.cliente.list_blobs(self.nombre)  # la paginación es transparente
            if not str(b.name).endswith("/") and not str(b.name).startswith(PREFIJO_STAGING)
        ]
        return sorted(objetos, key=lambda o: o.key)

    def leer(self, key: str) -> bytes:
        return self.cliente.bucket(self.nombre).blob(key).download_as_bytes()

    def escribir(self, key: str, datos: bytes) -> str:
        self.cliente.bucket(self.nombre).blob(key).upload_from_string(datos, content_type="text/csv")
        return f"gs://{self.nombre}/{key}"

    def borrar(self, key: str) -> None:
        self.cliente.bucket(self.nombre).blob(key).delete()


_COLUMNAS_INVENTARIO: tuple[tuple[str, Logico], ...] = (
    ("corrida_id", "texto"),
    ("source_key", "texto"),
    ("generation", "entero"),
    ("md5", "texto"),
    ("etag", "texto"),
    ("tamano", "entero"),
    ("actualizado", "fecha_hora"),
    ("autorizado", "booleano"),
    ("listado_en", "fecha_hora"),
)


def crear_inventario(motor: Motor) -> None:
    cols = ", ".join(f"{c} {motor.tipo(t)}" for c, t in _COLUMNAS_INVENTARIO)
    motor.ejecutar(f"CREATE TABLE IF NOT EXISTS {motor.t(INVENTARIO)} ({cols})")


def registrar_inventario(
    motor: Motor, corrida_id: str, objetos: list[ObjetoGCS], listado_en: datetime, lote: int = 500
) -> int:
    """Agrega una instantánea completa del listado (autorizados y no) a `latam_platino.inventario_bucket`."""
    crear_inventario(motor)
    filas = [
        "("
        + ", ".join(
            motor.lit(v)
            for v in (
                corrida_id,
                o.key,
                o.generation,
                o.md5,
                o.etag,
                o.tamano,
                o.actualizado.astimezone(UTC),
                o.autorizado,
                listado_en.astimezone(UTC),
            )
        )
        + ")"
        for o in objetos
    ]
    for i in range(0, len(filas), lote):
        motor.ejecutar(f"INSERT INTO {motor.t(INVENTARIO)} VALUES " + ", ".join(filas[i : i + lote]))
    return len(filas)


def espejar(almacen: Almacen, motor: Motor, corrida_id: str, ahora: datetime) -> list[ObjetoGCS]:
    """Lista todo el bucket de aterrizaje y registra el inventario."""
    objetos = almacen.listar()
    registrar_inventario(motor, corrida_id, objetos, ahora)
    return objetos
