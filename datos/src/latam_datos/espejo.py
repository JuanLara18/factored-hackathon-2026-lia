"""DAT-1.1: espejo local del bucket. Sincroniza por etag y deja el listado completo en platino.

El cliente S3 se inyecta: en producción es `crear_cliente()` con el perfil `latam-organizador` (la llave
vive solo en la máquina de ingesta); en las pruebas es moto. Cada objeto se descarga una sola vez por etag.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import boto3
import duckdb

from latam_datos.config import PERFIL_AWS, PREFIJO_AUTORIZADO

INDICE = "_indice_etags.json"

_DDL_INVENTARIO = """
CREATE TABLE IF NOT EXISTS platino.inventario_bucket (
    corrida_id VARCHAR, source_key VARCHAR, etag VARCHAR, tamano BIGINT,
    last_modified TIMESTAMP, autorizado BOOLEAN, listado_en TIMESTAMP
)
"""


@dataclass(frozen=True)
class ObjetoS3:
    key: str
    etag: str
    tamano: int
    last_modified: datetime

    @property
    def autorizado(self) -> bool:
        """Fuente autorizada: `data/<tabla>/...`. La raíz y otros prefijos solo se registran (Q-BRZ-09)."""
        return self.key.startswith(PREFIJO_AUTORIZADO) and self.key.count("/") >= 2


@dataclass(frozen=True)
class ResultadoSync:
    descargados: tuple[str, ...]
    sin_cambio: tuple[str, ...]


def crear_cliente(perfil: str = PERFIL_AWS) -> Any:
    """Cliente S3 con el perfil del organizador. Las credenciales las resuelve boto3, nunca este código."""
    return cast(Any, boto3.Session(profile_name=perfil)).client("s3")


def listar_bucket(cliente: Any, bucket: str, prefijo: str = "") -> list[ObjetoS3]:
    """Listado completo y paginado, ordenado por llave."""
    objetos: list[ObjetoS3] = []
    for pagina in cliente.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefijo):
        for o in pagina.get("Contents", []):
            if o["Key"].endswith("/"):
                continue
            objetos.append(
                ObjetoS3(
                    key=o["Key"],
                    etag=str(o["ETag"]).strip('"'),
                    tamano=int(o["Size"]),
                    last_modified=o["LastModified"],
                )
            )
    return sorted(objetos, key=lambda o: o.key)


def leer_indice(espejo: Path) -> dict[str, dict[str, Any]]:
    ruta = espejo / INDICE
    if not ruta.exists():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def sincronizar(cliente: Any, bucket: str, espejo: Path, objetos: list[ObjetoS3]) -> ResultadoSync:
    """Descarga solo los objetos autorizados cuyo etag local no coincide. Escritura atómica por objeto."""
    espejo.mkdir(parents=True, exist_ok=True)
    indice = leer_indice(espejo)
    bajados: list[str] = []
    iguales: list[str] = []
    for o in objetos:
        if not o.autorizado:
            continue
        destino = espejo / o.key
        if indice.get(o.key, {}).get("etag") == o.etag and destino.exists():
            iguales.append(o.key)
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(destino.suffix + ".parte")
        cliente.download_file(bucket, o.key, str(temporal))
        os.replace(temporal, destino)
        indice[o.key] = {
            "etag": o.etag,
            "tamano": o.tamano,
            "last_modified": o.last_modified.astimezone(UTC).isoformat(),
        }
        bajados.append(o.key)
    (espejo / INDICE).write_text(json.dumps(indice, indent=1, sort_keys=True), encoding="utf-8")
    return ResultadoSync(tuple(bajados), tuple(iguales))


def registrar_inventario(
    platino: duckdb.DuckDBPyConnection, corrida_id: str, objetos: list[ObjetoS3], listado_en: datetime
) -> int:
    """Agrega una instantánea completa del listado (autorizados y no) a `platino.inventario_bucket`."""
    platino.execute(_DDL_INVENTARIO)
    filas = [
        (
            corrida_id,
            o.key,
            o.etag,
            o.tamano,
            o.last_modified.astimezone(UTC).replace(tzinfo=None),
            o.autorizado,
            listado_en.astimezone(UTC).replace(tzinfo=None),
        )
        for o in objetos
    ]
    platino.executemany("INSERT INTO platino.inventario_bucket VALUES (?, ?, ?, ?, ?, ?, ?)", filas)
    return len(filas)


def espejar(
    cliente: Any,
    bucket: str,
    espejo: Path,
    platino: duckdb.DuckDBPyConnection,
    corrida_id: str,
    ahora: datetime,
) -> tuple[list[ObjetoS3], ResultadoSync]:
    """Lista todo el bucket, sincroniza lo autorizado y registra el inventario."""
    objetos = listar_bucket(cliente, bucket)
    resultado = sincronizar(cliente, bucket, espejo, objetos)
    registrar_inventario(platino, corrida_id, objetos, ahora)
    return objetos, resultado
