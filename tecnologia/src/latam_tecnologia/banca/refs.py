"""Referencias opacas: la interfaz nunca ve un identificador interno (D-33)."""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Mapping

VARIABLE_SECRETO = "LATAM_REF_SECRETO"
VARIABLE_ENTORNO = "LATAM_ENTORNO"
SECRETO_EN_SECRET_MANAGER = "latam-ref-secreto"
_SECRETO_DEFECTO = "latam-demo-refs"  # solo para correr en local y en pruebas: está en el repositorio


class SecretoAusente(RuntimeError):
    """Un servicio desplegado no firma referencias con la clave pública del repositorio."""


def desplegado(entorno: Mapping[str, str] | None = None) -> bool:
    """Cloud Run pone `K_SERVICE`; el despliegue del agente pone `LATAM_ENTORNO=produccion`."""
    env = os.environ if entorno is None else entorno
    return bool(env.get("K_SERVICE")) or env.get(VARIABLE_ENTORNO) == "produccion"


def secreto(entorno: Mapping[str, str] | None = None) -> bytes:
    env = os.environ if entorno is None else entorno
    valor = env.get(VARIABLE_SECRETO)
    if valor:
        return valor.encode()
    if desplegado(env):
        raise SecretoAusente(
            f"falta {VARIABLE_SECRETO}: se monta desde Secret Manager ({SECRETO_EN_SECRET_MANAGER})"
        )
    return _SECRETO_DEFECTO.encode()


def ref(clase: str, cliente_id: str, identificador: str) -> str:
    """Determinista por cliente (mismo valor en todas las instancias); sin la clave no se invierte."""
    base = "\x1f".join((clase, cliente_id, identificador)).encode()
    return f"{clase}_{hmac.new(secreto(), base, hashlib.sha256).hexdigest()[:20]}"


def hash_corto(*partes: str) -> str:
    return hashlib.sha256("\x1f".join(partes).encode()).hexdigest()[:20]
