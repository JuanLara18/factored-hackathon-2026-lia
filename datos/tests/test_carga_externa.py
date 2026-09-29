from pathlib import Path

import pytest
from latam_datos.carga_externa import fuentes, unir


def _csv(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def test_fuentes_agrupa_sueltos_y_particiones(tmp_path: Path) -> None:
    _csv(tmp_path / "customers.csv", "id\n1\n")
    _csv(tmp_path / "transactions/year=2026/month=06/day=02/t_20260602.csv", "id\n2\n")
    _csv(tmp_path / "transactions/year=2026/month=06/day=01/t_20260601.csv", "id\n1\n")
    tablas = fuentes(tmp_path)
    assert set(tablas) == {"customers", "transactions"}
    assert [p.name for p in tablas["transactions"]] == ["t_20260601.csv", "t_20260602.csv"]


def test_unir_deja_un_encabezado_y_quita_bom(tmp_path: Path) -> None:
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text('﻿id,nota\n1,"linea\nnueva"\n', encoding="utf-8")
    _csv(b, "id,nota\n2,x\n")
    destino = tmp_path / "u.csv"
    assert unir([a, b], destino) == ["id", "nota"]
    assert destino.read_text(encoding="utf-8").splitlines()[0] == "id,nota"
    assert destino.read_text(encoding="utf-8").count("id,nota") == 1


def test_unir_rechaza_encabezado_distinto(tmp_path: Path) -> None:
    _csv(tmp_path / "a.csv", "id\n1\n")
    _csv(tmp_path / "b.csv", "otro\n2\n")
    with pytest.raises(ValueError):
        unir([tmp_path / "a.csv", tmp_path / "b.csv"], tmp_path / "u.csv")
