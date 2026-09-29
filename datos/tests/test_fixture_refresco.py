"""El fixture de actualización es del equipo: toda llave lleva el prefijo FX- y hay entre 8 y 10 casos."""

import re
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "refresco.yml"
LLAVES = re.compile(r"\b(?:transaction_id|customer_id|product_id):\s*(\S+?)[,}\s]")


def test_llaves_con_prefijo_fx() -> None:
    llaves = LLAVES.findall(FIXTURE.read_text(encoding="utf-8"))
    assert llaves
    assert all(k.startswith("FX-") for k in llaves), [k for k in llaves if not k.startswith("FX-")]


def test_casos_fx_documentados() -> None:
    casos = set(re.findall(r"\bFX-(\d\d)\b", FIXTURE.read_text(encoding="utf-8")))
    assert 8 <= len(casos) <= 10
