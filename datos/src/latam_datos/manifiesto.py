"""Manifiesto de carga encadenado (DAT-1.6, PD6): qué archivos entraron a qué tabla y si los conteos cuadran.

Un registro por archivo fuente (`platino_manifiesto_carga`) y uno por tabla (`platino_manifiesto_tablas`).
Los de tabla forman una cadena: `huella_cadena = sha256(huella_previa + JSON canónico del registro)`.
Editar un manifiesto viejo cambia su huella y rompe todas las siguientes; `verificar_cadena` lo detecta.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
_CAMPOS_CADENA = (
    "manifiesto_id",
    "tabla",
    "archivos",
    "filas_csv",
    "filas_bigquery",
    "coincide",
    "job_id",
    "huella_archivos",
)


@dataclass(frozen=True)
class Archivo:
    clave_s3: str  # ruta relativa a `s3://<bucket>/data/`
    bytes: int
    sha256: str
    filas_csv: int  # filas de datos, sin encabezado
    tabla_destino: str


def sha256_de(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def contar_filas(ruta: Path) -> int:
    """Registros CSV de datos (sin encabezado), con la semántica de comillas de la unión."""
    datos = ruta.read_bytes()
    if b'"' not in datos:
        lineas = [ln for ln in datos.splitlines() if ln]
        return max(len(lineas) - 1, 0)
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        next(lector, None)
        return sum(1 for _ in lector)


def describir(ruta: Path, espejo: Path, tabla: str) -> Archivo:
    return Archivo(
        clave_s3=ruta.relative_to(espejo).as_posix(),
        bytes=ruta.stat().st_size,
        sha256=sha256_de(ruta),
        filas_csv=contar_filas(ruta),
        tabla_destino=f"bronce_{tabla}",
    )


def huella_de_archivos(archivos: list[Archivo]) -> str:
    h = hashlib.sha256()
    for a in sorted(archivos, key=lambda x: x.clave_s3):
        h.update(f"{a.clave_s3}|{a.bytes}|{a.sha256}|{a.filas_csv}\n".encode())
    return h.hexdigest()


def huella_de_registro(previa: str, registro: dict[str, Any]) -> str:
    cuerpo = json.dumps({k: registro[k] for k in _CAMPOS_CADENA}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((previa + cuerpo).encode()).hexdigest()


def encadenar(
    previa: str,
    manifiesto_id: str,
    generado_en: str,
    por_tabla: dict[str, list[Archivo]],
    filas_bigquery: dict[str, int],
    job_ids: dict[str, str | None],
) -> list[dict[str, Any]]:
    """Un registro por tabla, en orden alfabético, cada uno encadenado al anterior."""
    registros: list[dict[str, Any]] = []
    for tabla in sorted(por_tabla):
        archivos = por_tabla[tabla]
        filas_csv = sum(a.filas_csv for a in archivos)
        reg: dict[str, Any] = {
            "manifiesto_id": manifiesto_id,
            "generado_en": generado_en,
            "tabla": f"bronce_{tabla}",
            "archivos": len(archivos),
            "filas_csv": filas_csv,
            "filas_bigquery": filas_bigquery[tabla],
            "coincide": filas_csv == filas_bigquery[tabla],
            "job_id": job_ids.get(tabla),
            "huella_archivos": huella_de_archivos(archivos),
            "huella_previa": previa,
        }
        reg["huella_cadena"] = huella_de_registro(previa, reg)
        previa = reg["huella_cadena"]
        registros.append(reg)
    return registros


def verificar_cadena(registros: list[dict[str, Any]]) -> list[str]:
    """Errores encontrados al recomputar la cadena; lista vacía si está íntegra."""
    errores: list[str] = []
    previa = GENESIS
    for i, r in enumerate(registros):
        if r["huella_previa"] != previa:
            errores.append(f"{i} {r['tabla']}: la huella previa no es la del registro anterior")
        esperada = huella_de_registro(r["huella_previa"], r)
        if r["huella_cadena"] != esperada:
            errores.append(f"{i} {r['tabla']}: el contenido no corresponde a su huella")
        previa = r["huella_cadena"]
    return errores


def leer_cadena(carpeta: Path) -> list[dict[str, Any]]:
    """Registros de todos los `manifiesto_carga_*.json` de la carpeta, en orden de generación."""
    registros: list[dict[str, Any]] = []
    for ruta in sorted(carpeta.glob("manifiesto_carga_*.json")):
        registros.extend(json.loads(ruta.read_text(encoding="utf-8"))["tablas"])
    return registros


def escribir_resumen(carpeta: Path, manifiesto_id: str, registros: list[dict[str, Any]]) -> Path:
    """Resumen por tabla, sin PII ni filas: solo conteos y huellas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"manifiesto_carga_{manifiesto_id}.json"
    cuerpo = {"manifiesto_id": manifiesto_id, "tablas": registros}
    ruta.write_text(json.dumps(cuerpo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ruta


def ahora_id() -> tuple[str, str]:
    t = datetime.now(UTC)
    return t.strftime("%Y%m%dT%H%M%SZ"), t.isoformat(timespec="seconds")
