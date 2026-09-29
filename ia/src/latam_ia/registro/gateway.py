"""Configuración del gateway derivada del registro (R-IA-01, R-IA-02). Formato tipo LiteLLM.

El proveedor es intercambiable: por defecto sale del registro; `proveedor` lo fuerza para todos.
"""

from __future__ import annotations

from typing import Any

import yaml

from latam_ia.registro.esquema import ESTADOS_SIN_GATEWAY, Proveedor, Registro

PREFIJO_LITELLM = {Proveedor.GEMINI_API: "gemini", Proveedor.VERTEX_AI: "vertex_ai"}

CABECERA = "# Generado desde ia/agentes/trabajadores con `python -m latam_ia.registro`; no editar a mano.\n"


def _parametros(proveedor: Proveedor, modelo_id: str) -> dict[str, Any]:
    p: dict[str, Any] = {"model": f"{PREFIJO_LITELLM[proveedor]}/{modelo_id}"}
    if proveedor is Proveedor.GEMINI_API:
        p["api_key"] = "os.environ/GEMINI_API_KEY"
    else:
        p["vertex_project"] = "os.environ/LATAM_GCP_PROJECT"
        p["vertex_location"] = "os.environ/LATAM_GEAP_LOCATION"
    return p


def generar_config_gateway(registro: Registro, proveedor: Proveedor | None = None) -> dict[str, Any]:
    """Un alias por trabajador con modelo y una clave virtual por trabajador y entorno."""
    modelos: list[dict[str, Any]] = []
    claves: list[dict[str, Any]] = []
    for id_ in registro.ids:
        t = registro.trabajadores[id_]
        if t.modelo is None or t.presupuestos is None or t.estado in ESTADOS_SIN_GATEWAY:
            continue
        prov = proveedor or t.modelo.proveedor
        params = _parametros(prov, t.modelo.id) | {
            "temperature": t.modelo.temperatura,
            "max_tokens": t.modelo.max_salida,
        }
        modelos.append({"model_name": t.id, "litellm_params": params})
        for entorno in t.entornos:
            claves.append(
                {
                    "key_alias": f"lb-{t.id}-{entorno}",
                    "models": [t.id],
                    "max_budget": t.presupuestos.usd_diario,
                    "budget_duration": "1d",
                    "max_tokens_per_request": t.presupuestos.max_entrada + t.presupuestos.max_salida,
                    "metadata": {
                        "latam.trabajador.id": t.id,
                        "latam.trabajador.version": t.version,
                        "entorno": entorno,
                    },
                }
            )
    return {"model_list": modelos, "claves_virtuales": claves}


def a_yaml(config: dict[str, Any]) -> str:
    return CABECERA + yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
