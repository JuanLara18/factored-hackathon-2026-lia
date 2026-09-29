from __future__ import annotations

import re
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from latam_gobierno.politica import RUTA_V1, PoliticaInvalida, PoliticaV1, cargar, huella_conjunto, sellar

RAIZ = Path(__file__).resolve().parents[2]
D = Decimal


@pytest.fixture(scope="module")
def pol() -> PoliticaV1:
    return cargar()


def _copia(tmp_path: Path) -> Path:
    destino = tmp_path / "v1"
    shutil.copytree(RUTA_V1, destino)
    return destino


def _reemplazar(ruta: Path, a: str, b: str) -> None:
    texto = ruta.read_text(encoding="utf-8")
    assert a in texto
    ruta.write_text(texto.replace(a, b), encoding="utf-8", newline="\n")


# Cargador y huella


def test_carga_y_referencia(pol: PoliticaV1) -> None:
    assert pol.manifiesto.sintetica is True
    assert pol.referencia == f"policy/v1@{huella_conjunto(RUTA_V1)}"


def test_huella_estable_y_sensible_al_contenido(tmp_path: Path) -> None:
    assert huella_conjunto(RUTA_V1) == huella_conjunto(RUTA_V1)
    d = _copia(tmp_path)
    assert huella_conjunto(d) == huella_conjunto(RUTA_V1)
    _reemplazar(d / "riesgo.yaml", "alto_sobre: 30", "alto_sobre: 31")
    assert huella_conjunto(d) != huella_conjunto(RUTA_V1)


def test_huella_igual_con_saltos_de_linea_crlf(tmp_path: Path) -> None:
    d = _copia(tmp_path)
    for f in d.glob("*.yaml"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert huella_conjunto(d) == huella_conjunto(RUTA_V1)
    assert cargar(d).huella == cargar().huella


def test_politica_alterada_no_carga_hasta_sellarla(tmp_path: Path) -> None:
    d = _copia(tmp_path)
    _reemplazar(d / "riesgo.yaml", "alto_sobre: 30", "alto_sobre: 99")
    with pytest.raises(PoliticaInvalida, match="huella"):
        cargar(d)
    sellar(d)
    assert cargar(d).riesgo.alto_sobre == 99


def test_esquema_estricto(tmp_path: Path) -> None:
    d = _copia(tmp_path)
    _reemplazar(d / "riesgo.yaml", "alto_sobre: 30", "alto_sobre: 30\nsobrante: 1")
    sellar(d)
    with pytest.raises(PoliticaInvalida):
        cargar(d)


def test_regla_incoherente_o_sin_razon_no_carga(tmp_path: Path) -> None:
    d = _copia(tmp_path)
    ruta = d / "escalamiento.yaml"
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    datos["reglas"][0]["estados"] = ["x"]
    ruta.write_text(yaml.safe_dump(datos), encoding="utf-8")
    sellar(d)
    with pytest.raises(PoliticaInvalida):
        cargar(d)
    del datos["reglas"][0]["estados"]
    datos["reglas"][0]["razon"] = ""
    ruta.write_text(yaml.safe_dump(datos), encoding="utf-8")
    sellar(d)
    with pytest.raises(PoliticaInvalida):
        cargar(d)


def test_falta_un_archivo(tmp_path: Path) -> None:
    d = _copia(tmp_path)
    (d / "traspaso.yaml").unlink()
    with pytest.raises(PoliticaInvalida, match="traspaso"):
        cargar(d)


def test_cada_regla_cita_una_regla_de_la_definicion(pol: PoliticaV1) -> None:
    definicion = (RAIZ / "gobierno" / "definicion.md").read_text(encoding="utf-8")
    citas = [r.fundamento for r in pol.escalamiento.reglas]
    citas += [pol.credito_provisional.por_defecto.fundamento, pol.riesgo.fundamento]
    citas += [t.fundamento for t in pol.credito_provisional.por_moneda.values()]
    citas += [r.fundamento for r in pol.autonomia.acciones.values()]
    citas += [d.fundamento for d in pol.traspaso.disparadores]
    for c in set(citas):
        patron = rf"\*\*{re.escape(c)}\." if c.startswith("R-GOB") else rf"\| {re.escape(c)} \|"
        assert re.search(patron, definicion), f"{c} no está en la definición"


# Tablas de decisión


@pytest.mark.parametrize(
    ("urgente", "estado", "producto", "esperado"),
    [
        (True, "completed", True, "urgente"),
        (True, "declined", False, "urgente"),
        (False, "declined", True, "transaccion_no_disputable"),
        (False, "FAILED", True, "transaccion_no_disputable"),
        (False, "Reversed", False, "transaccion_no_disputable"),
        (False, "completed", False, "producto_no_encontrado"),
        (False, None, False, "producto_no_encontrado"),
        (False, "completed", True, None),
        (False, None, True, None),
        (False, "pending", True, None),
    ],
)
def test_tabla_de_escalamiento(
    pol: PoliticaV1, urgente: bool, estado: str | None, producto: bool, esperado: str | None
) -> None:
    d = pol.escalar(urgente=urgente, estado_transaccion=estado, producto_conocido=producto)
    assert (d.motivo if d else None) == esperado


@pytest.mark.parametrize(
    ("moneda", "usd", "esperado"),
    [
        ("COP", "200", True),
        ("COP", "200.01", False),
        ("MXN", "0", True),
        ("ARS", "900", False),
        ("USD", "50", True),
        ("BRL", "201", False),
        ("COP", None, False),
    ],
)
def test_tabla_de_credito_provisional(pol: PoliticaV1, moneda: str, usd: str | None, esperado: bool) -> None:
    assert pol.credito_provisional_aplica(moneda, D(usd) if usd is not None else None) is esperado


@pytest.mark.parametrize(
    ("score", "banda"),
    [
        (None, "zona_gris"),
        (D("0"), "sin_evidencia"),
        (D("24.99"), "sin_evidencia"),
        (D("25"), "zona_gris"),
        (D("30"), "zona_gris"),
        (D("30.01"), "alto"),
        (D("99"), "alto"),
    ],
)
def test_tabla_de_bandas_de_riesgo(pol: PoliticaV1, score: Decimal | None, banda: str) -> None:
    assert pol.banda_riesgo(score) == banda


def test_bajar_el_puntaje_nunca_sube_la_banda(pol: PoliticaV1) -> None:
    orden = {"sin_evidencia": 0, "zona_gris": 1, "alto": 2}
    previo = 2
    for s in range(100, -1, -1):
        actual = orden[pol.banda_riesgo(D(s))]
        assert actual <= previo
        previo = actual


@pytest.mark.parametrize(
    ("accion", "acr"),
    [
        ("transacciones_recientes", "acr1"),
        ("transaccion", "acr1"),
        ("estado_productos", "acr1"),
        ("ficha_transaccion", "acr1"),
        ("casos_abiertos", "acr1"),
        ("bloquear_tarjeta", "acr1"),
        ("abrir_disputa", "acr2"),
        ("escalar", "acr1"),
    ],
)
def test_tabla_de_acr_por_accion(pol: PoliticaV1, accion: str, acr: str) -> None:
    assert pol.acr_requerido(accion) == acr


def test_accion_sin_regla_falla_cerrado(pol: PoliticaV1) -> None:
    with pytest.raises(PoliticaInvalida):
        pol.acr_requerido("mover_dinero")


def test_disparadores_de_traspaso(pol: PoliticaV1) -> None:
    por_evento = {d.evento: d for d in pol.traspaso.disparadores}
    assert por_evento["transferencia_inmediata_no_reconocida"].prioridad == "maxima"
    assert por_evento["aclaraciones_fallidas"].umbral == 2
    assert len({d.id for d in pol.traspaso.disparadores}) == len(pol.traspaso.disparadores)
    motivos = {r.motivo for r in pol.escalamiento.reglas}
    activos = {d.evento for d in pol.traspaso.disparadores if d.en_motor}
    assert motivos - {"urgente"} <= activos


def test_dbt_duplica_los_umbrales_de_riesgo(pol: PoliticaV1) -> None:
    dbt = yaml.safe_load((RAIZ / "datos" / "dbt" / "dbt_project.yml").read_text(encoding="utf-8"))
    v = dbt["vars"]
    assert D(str(v["riesgo_alto_sobre"])) == pol.riesgo.alto_sobre
    assert D(str(v["riesgo_zona_gris_desde"])) == pol.riesgo.zona_gris_desde


def test_monto_sobre_el_umbral_radica_y_escala(pol: PoliticaV1) -> None:
    d = pol.escalar_tras_radicar("COP", D(1500))
    assert d is not None and d.id == "ESC-04" and d.motivo == "monto_sobre_umbral"
    assert pol.escalar_tras_radicar("COP", D(1000)) is None
    assert pol.escalar_tras_radicar("COP", None) is None
