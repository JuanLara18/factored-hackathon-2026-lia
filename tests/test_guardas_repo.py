from pathlib import Path

import pytest
from latam_gobierno.guardas import main, revisar, revisar_ruta


@pytest.mark.parametrize(
    "ruta",
    [
        "data/bronce/clientes.parquet",
        "datos/fixtures/muestra.parquet",
        "algo/tabla.csv",
        "base.duckdb",
        "runs/2026/manifiesto.json",
        "docs/Dataset_Diccionario_LATAM_Bank.pdf",
        "secretos/llave.txt",
        ".env",
        ".env.local",
        "credentials.json",
        "audio/voluntario.wav",
        "clave.pem",
        "gobierno/retenido/casos/c1.json",
    ],
)
def test_rutas_prohibidas(ruta: str) -> None:
    assert revisar_ruta(ruta)


@pytest.mark.parametrize(
    "ruta", [".env.example", "docs/enunciado/Dataset_Resumen_LATAM_Bank.pdf", "datos/contratos/a.yaml"]
)
def test_rutas_permitidas(ruta: str) -> None:
    assert not revisar_ruta(ruta)


def test_detecta_llave_aws_sin_imprimirla(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    falsa = "AKIA" + "ABCDEFGHIJKLMNOP"
    (tmp_path / "config.txt").write_text(f"clave = {falsa}\n", encoding="utf-8")
    hallazgos = revisar(["config.txt"], tmp_path)
    assert [h.regla for h in hallazgos] == ["patron de llave-de-acceso-aws"]
    assert falsa not in str(hallazgos[0])
    assert main.__name__ == "main"
    capsys.readouterr()


def test_un_parquet_versionado_hace_fallar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.parquet").write_bytes(b"PAR1")
    assert main(["t.parquet"]) == 1
    (tmp_path / "ok.md").write_text("hola", encoding="utf-8")
    assert main(["ok.md"]) == 0


def test_el_repositorio_esta_limpio() -> None:
    raiz = Path(__file__).resolve().parents[1]
    rutas = [r for r in _versionadas(raiz)]
    assert revisar(rutas, raiz) == []


def _versionadas(raiz: Path) -> list[str]:
    from latam_gobierno.guardas import _rutas_versionadas  # pyright: ignore[reportPrivateUsage]

    return [r for r in _rutas_versionadas(raiz) if not r.endswith(("guardas.py", "test_guardas_repo.py"))]


def test_seeds_del_equipo_permitidos_solo_en_dominios() -> None:
    assert revisar_ruta("datos/dominios/dominios_canonicos.csv") == []
    assert revisar_ruta("datos/dominios/sub/otro.csv") != []
    assert revisar_ruta("datos/fixtures/clientes.csv") != []
