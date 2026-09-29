"""Orquestación de la ingesta: espejo, bronce, reglas Q-BRZ y reporte. Punto de entrada de `just`."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from typing import Any

import duckdb

from latam_datos.almacen import abrir_zona
from latam_datos.bronce import ResultadoBronce, construir_bronce
from latam_datos.config import Rutas, rutas_por_defecto
from latam_datos.espejo import ObjetoS3, crear_cliente, espejar
from latam_datos.reglas import Hallazgo, evaluar_globales, reportar


def corrida_id_de(ahora: datetime) -> str:
    return ahora.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def inventario_ultimo(platino: duckdb.DuckDBPyConnection) -> list[ObjetoS3]:
    """Objetos de la última instantánea de `platino.inventario_bucket` (para Q-BRZ-09 sin red)."""
    try:
        filas = platino.execute(
            "SELECT source_key, etag, tamano, last_modified FROM platino.inventario_bucket "
            "WHERE corrida_id = (SELECT max(corrida_id) FROM platino.inventario_bucket)"
        ).fetchall()
    except duckdb.CatalogException:
        return []
    return [ObjetoS3(k, e, int(t), m.replace(tzinfo=UTC)) for k, e, t, m in filas]


def sincronizar_espejo(rutas: Rutas, cliente: Any, bucket: str, ahora: datetime) -> str:
    platino = abrir_zona(rutas.platino_db)
    try:
        corrida = corrida_id_de(ahora)
        objetos, res = espejar(cliente, bucket, rutas.espejo, platino, corrida, ahora)
        return (
            f"{len(objetos)} objetos listados, {len(res.descargados)} descargados, "
            f"{len(res.sin_cambio)} sin cambio"
        )
    finally:
        platino.close()


def correr_bronce(rutas: Rutas, ahora: datetime) -> tuple[ResultadoBronce, list[Hallazgo]]:
    """Construye bronce, evalúa Q-BRZ-01 a 11 y escribe el reporte. Los bloqueos no lanzan: se devuelven."""
    bronce = abrir_zona(rutas.bronce_db)
    platino = abrir_zona(rutas.platino_db)
    try:
        res = construir_bronce(rutas, bronce, ahora)
        hallazgos = [*res.hallazgos, *evaluar_globales(bronce, inventario_ultimo(platino))]
        reportar(platino, corrida_id_de(ahora), hallazgos, ahora)
        return res, hallazgos
    finally:
        bronce.close()
        platino.close()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="latam_datos")
    p.add_argument("orden", choices=["espejo", "bronce"])
    orden = p.parse_args(argv).orden
    rutas = rutas_por_defecto()
    ahora = datetime.now(UTC)
    if orden == "espejo":
        bucket = os.environ.get("LATAM_BUCKET")
        if not bucket:
            print("Falta LATAM_BUCKET (nombre del bucket del organizador).", file=sys.stderr)
            return 2
        print(sincronizar_espejo(rutas, crear_cliente(), bucket, ahora))
        return 0
    res, hallazgos = correr_bronce(rutas, ahora)
    avisos = sum(1 for h in hallazgos if h.resultado in ("aviso", "cuarentena"))
    print(
        f"lotes aplicados {len(res.aplicados)}, ignorados {len(res.ignorados)}, "
        f"bloqueados {len(res.bloqueados)}, avisos {avisos}"
    )
    return 1 if res.bloqueados else 0


if __name__ == "__main__":
    raise SystemExit(main())
