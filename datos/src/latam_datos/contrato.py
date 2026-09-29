"""Contrato de las tablas crudas que deja el proceso externo de carga en `latam_bronce` (D-30).

Nombre de tabla igual al del archivo del organizador; todas las columnas STRING. Las columnas listadas son las
que la definición de Datos nombra de forma explícita; el resto se confirma en F1 contra el diccionario del
dataset (que no vive en el repositorio) y se agrega aquí.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

BRONCE = "latam_bronce"
PLATINO = "latam_platino"
REPORTE = f"{PLATINO}.reporte_calidad_corrida"
INICIO_PARTICIONES = date(2023, 6, 17)
FIN_PARTICIONES = date(2026, 6, 17)


@dataclass(frozen=True)
class TablaCruda:
    nombre: str
    llave: str | None
    requeridas: tuple[str, ...]
    fecha: str | None = None  # columna de partición diaria (`process_date`) si la tabla la trae
    de_hechos: bool = False


CONTRATO: tuple[TablaCruda, ...] = (
    TablaCruda("customers", "customer_id", ("customer_id", "document_type")),
    TablaCruda("products", "product_id", ("product_id", "customer_id")),
    TablaCruda(
        "transactions",
        "transaction_id",
        ("transaction_id", "product_id", "customer_id", "process_date"),
        "process_date",
        True,
    ),
    TablaCruda(
        "call_center_interactions",
        "interaction_id",
        ("interaction_id", "customer_id", "process_date"),
        "process_date",
        True,
    ),
    TablaCruda("complaints", "complaint_id", ("complaint_id", "customer_id", "affected_product_id")),
    TablaCruda("satisfaction_surveys", None, ("interaction_id", "survey_date")),
    TablaCruda("service_agents", None, ()),
    TablaCruda("daily_exchange_rates", None, ()),
    TablaCruda("call_transcripts", None, ("interaction_id",)),
    TablaCruda("digital_events", None, ("customer_id", "process_date"), "process_date", True),
    TablaCruda("branches", None, ()),
    TablaCruda("marketing_campaigns", None, ()),
    TablaCruda("campaign_sends", None, ("process_date",), "process_date", True),
)
