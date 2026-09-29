from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
ESTADOS = {"verificada", "verificada_con_precision", "pendiente", "en_conflicto", "secundaria"}


def _fuentes() -> list[dict[str, object]]:
    datos = yaml.safe_load((RAIZ / "auditoria" / "fuentes" / "fuentes.yaml").read_text(encoding="utf-8"))
    return datos["fuentes"]


def test_ids_unicos() -> None:
    ids = [f["id"] for f in _fuentes()]
    assert len(ids) == len(set(ids))


def test_campos_y_estados() -> None:
    for f in _fuentes():
        assert {"id", "titulo", "url", "estado", "sostiene", "citada_en"} <= f.keys()
        assert f["estado"] in ESTADOS
        assert str(f["url"]).startswith("https://")
        citas = f["citada_en"]
        assert isinstance(citas, list) and citas
        for c in citas:
            assert (RAIZ / str(c)).is_file(), c


def test_referencias_arxiv_de_2026() -> None:
    de_2026 = [f for f in _fuentes() if str(f["id"]).startswith("arxiv:26")]
    assert len(de_2026) >= 28


def test_informe_de_prueba_sellado() -> None:
    from latam_gobierno.sello import huella, huella_bloque

    sesion = RAIZ / "auditoria" / "sesiones" / "2026-09-28_prueba_plantilla"
    paquete = yaml.safe_load((sesion / "paquete.yaml").read_text(encoding="utf-8"))
    assert paquete["informe"]["sha256_hallazgos"] == huella_bloque(sesion / "informe.md")
    assert paquete["definicion_del_agente"]["sha256"] == huella(RAIZ / ".claude" / "agents" / "auditoria.md")
