"""Referencias opacas: la interfaz nunca ve un identificador interno (D-33)."""

from __future__ import annotations

import hashlib
import hmac
import os

_SECRETO_DEFECTO = "latam-demo-refs"


def _secreto() -> bytes:
    return os.environ.get("LATAM_REF_SECRETO", _SECRETO_DEFECTO).encode()


def ref(clase: str, cliente_id: str, identificador: str) -> str:
    """Determinista por cliente (mismo valor en todas las instancias); sin la clave no se invierte."""
    base = "\x1f".join((clase, cliente_id, identificador)).encode()
    return f"{clase}_{hmac.new(_secreto(), base, hashlib.sha256).hexdigest()[:20]}"


def hash_corto(*partes: str) -> str:
    return hashlib.sha256("\x1f".join(partes).encode()).hexdigest()[:20]
