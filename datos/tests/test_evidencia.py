from pathlib import Path

from latam_datos.manifiesto import (
    GENESIS,
    Archivo,
    contar_filas,
    encadenar,
    escribir_resumen,
    leer_cadena,
    sha256_de,
    verificar_cadena,
)
from latam_datos.respaldo import comparar


def _csv(ruta: Path, texto: str) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def _cadena(bq: int = 2) -> list[dict]:
    a = Archivo("customers.csv", 10, "ab", 2, "bronce_customers")
    b = Archivo("products.csv", 20, "cd", 3, "bronce_products")
    return encadenar(
        GENESIS, "m1", "2026-09-28T00:00:00+00:00", {"customers": [a], "products": [b]},
        {"customers": bq, "products": 3}, {},
    )  # fmt: skip


def test_contar_filas_con_saltos_dentro_de_comillas(tmp_path: Path) -> None:
    assert contar_filas(_csv(tmp_path / "a.csv", 'id,n\n1,"x\ny"\n2,z\n')) == 2
    assert contar_filas(_csv(tmp_path / "b.csv", "id\n1\n2\n3")) == 3
    assert contar_filas(_csv(tmp_path / "c.csv", "id\n")) == 0


def test_cadena_integra_y_bandera_de_coincidencia() -> None:
    regs = _cadena()
    assert verificar_cadena(regs) == []
    assert regs[0]["huella_previa"] == GENESIS and regs[1]["huella_previa"] == regs[0]["huella_cadena"]
    assert all(r["coincide"] for r in regs)
    assert [r["coincide"] for r in _cadena(bq=1)] == [False, True]
    assert regs[0]["job_id"] is None


def test_editar_un_manifiesto_viejo_se_detecta(tmp_path: Path) -> None:
    regs = _cadena()
    regs[0]["filas_bigquery"] = 99
    assert verificar_cadena(regs)
    regs = _cadena()
    regs[0]["filas_csv"] = 5  # editar y no recalcular rompe el contenido
    assert len(verificar_cadena(regs)) == 1
    regs = _cadena()
    regs[0]["huella_cadena"] = "0" * 64  # editar la huella rompe el eslabón siguiente
    assert len(verificar_cadena(regs)) == 2


def test_resumen_json_ida_y_vuelta(tmp_path: Path) -> None:
    regs = _cadena()
    escribir_resumen(tmp_path, "m1", regs)
    assert leer_cadena(tmp_path) == regs and verificar_cadena(leer_cadena(tmp_path)) == []


def test_comparar_respaldo(tmp_path: Path) -> None:
    e, r = tmp_path / "e", tmp_path / "r"
    _csv(e / "customers.csv", "id\n1\n2\n")
    _csv(r / "customers.csv", "id\n1\n")
    _csv(e / "t/year=2026/day=01/t_1.csv", "id\n1\n")
    _csv(r / "t/year=2026/day=01/t_1.csv", "id\n1\n")
    _csv(e / "t/year=2026/day=02/t_2.csv", "id\n1\n")
    _csv(r / "t/year=2026/day=03/t_3.csv", "id\n1\n")
    res = {f["tabla"]: f for f in comparar(e, r)}
    assert res["customers"]["distintos"] == 1
    assert (res["customers"]["filas_espejo_distintos"], res["customers"]["filas_respaldo_distintos"]) == (
        2,
        1,
    )
    assert (res["t"]["identicos"], res["t"]["solo_espejo"], res["t"]["solo_respaldo"]) == (1, 1, 1)
    assert sha256_de(e / "customers.csv") != sha256_de(r / "customers.csv")
