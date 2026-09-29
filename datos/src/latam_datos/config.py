"""Configuración de la ingesta desde el entorno (Cloud Run Job). Nada de credenciales: las da la identidad
del servicio (D-30)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

PREFIJO_AUTORIZADO = "data/"
PREFIJO_RESPALDO = "data_backup_20260831/"
PREFIJO_STAGING = "_staging/"
GENERACION_ACTUAL = "data"
GENERACION_RESPALDO = "respaldo"

BRONCE = "latam_bronce"
PLATINO = "latam_platino"
LOTES = f"{BRONCE}._lotes"
CUARENTENA = f"{BRONCE}._cuarentena"
INVENTARIO = f"{PLATINO}.inventario_bucket"
REPORTE = f"{PLATINO}.reporte_calidad_corrida"


@dataclass(frozen=True)
class Configuracion:
    proyecto: str
    bucket: str
    ubicacion: str = "us-central1"

    @classmethod
    def desde_entorno(cls, env: Mapping[str, str] | None = None) -> Configuracion:
        e = os.environ if env is None else env
        faltan = [v for v in ("LATAM_GCP_PROJECT", "LATAM_GCS_ESPEJO") if not e.get(v)]
        if faltan:
            raise ValueError(f"Faltan variables de entorno: {', '.join(faltan)}")
        return cls(e["LATAM_GCP_PROJECT"], e["LATAM_GCS_ESPEJO"], e.get("LATAM_GCP_LOCATION", "us-central1"))
