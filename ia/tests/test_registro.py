from pathlib import Path

import pytest
import yaml
from latam_ia.modelos import crear_modelo
from latam_ia.prompts import cargar_biblioteca
from latam_ia.registro import (
    Proveedor,
    Registro,
    Trabajador,
    a_yaml,
    cargar_registro,
    generar_config_gateway,
    verificar_familias,
    verificar_prompts,
)
from latam_ia.registro.cargador import DIR_TRABAJADORES, RAIZ_IA, ErrorRegistro

BASE: dict[str, object] = {
    "id": "x",
    "version": "1.0.0",
    "estado": "en_desarrollo",
    "tipo": "lenguaje_preentrenado",
    "proposito": "Un propósito suficientemente largo.",
    "usos_prohibidos": ["nada"],
    "supervisor": {"cara": "VP IA"},
    "duenio_tecnico": {"cara": "VP IA"},
    "riesgo": "moderado",
    "modelo": {"proveedor": "gemini_api", "familia": "google", "id": "m", "max_salida": 100},
    "presupuestos": {"max_entrada": 10, "max_salida": 100, "llamadas_por_conversacion": 1, "usd_diario": 0},
}


def test_registro_real_valido_y_prompts_existen() -> None:
    registro = cargar_registro()
    assert {"comprension", "redaccion"} <= set(registro.ids)
    assert verificar_prompts(registro, cargar_biblioteca().referencias) == []


def test_gateway_generado_esta_al_dia() -> None:
    """R-IA-01: el archivo comprometido es el que sale del registro."""
    esperado = a_yaml(generar_config_gateway(cargar_registro()))
    assert (RAIZ_IA / "agentes" / "gateway.generado.yaml").read_text(encoding="utf-8") == esperado


def test_una_clave_por_trabajador_y_entorno_sin_compartir() -> None:
    config = generar_config_gateway(cargar_registro())
    alias = [k["key_alias"] for k in config["claves_virtuales"]]
    assert len(alias) == len(set(alias))
    assert all(len(k["models"]) == 1 for k in config["claves_virtuales"])


def test_proveedor_intercambiable() -> None:
    config = generar_config_gateway(cargar_registro(), Proveedor.VERTEX_AI)
    assert all(m["litellm_params"]["model"].startswith("vertex_ai/") for m in config["model_list"])
    assert "api_key" not in config["model_list"][0]["litellm_params"]


def test_no_hay_llaves_en_el_repo() -> None:
    texto = (RAIZ_IA / "agentes" / "gateway.generado.yaml").read_text(encoding="utf-8")
    assert "AIza" not in texto
    assert "os.environ/GEMINI_API_KEY" in texto


@pytest.mark.parametrize(
    "cambio",
    [
        {"version": "1.0"},
        {"id": "Mal Id"},
        {"prompt": "sin-version"},
        {"herramientas": ["buscar"]},
        {"usos_prohibidos": []},
        {"presupuestos": None},
        {"riesgo": "extremo"},
        {"campo_extra": 1},
    ],
)
def test_esquema_rechaza(cambio: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Trabajador.model_validate({**BASE, **cambio})


def test_estado_retirado_no_entra_al_gateway() -> None:
    t = Trabajador.model_validate({**BASE, "estado": "retirado"})
    assert generar_config_gateway(Registro(trabajadores={"x": t}))["model_list"] == []


def test_familias_repetidas_entre_roles_se_reportan() -> None:
    a = Trabajador.model_validate({**BASE, "id": "a", "rol": "sistema"})
    b = Trabajador.model_validate({**BASE, "id": "b", "rol": "juez"})
    assert len(verificar_familias(Registro(trabajadores={"a": a, "b": b}))) == 1
    assert verificar_familias(Registro(trabajadores={"a": a})) == []


def test_archivo_con_id_distinto_falla(tmp_path: Path) -> None:
    (tmp_path / "otro.yaml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
    with pytest.raises(ErrorRegistro):
        cargar_registro(tmp_path)


def test_todos_los_archivos_se_cargan() -> None:
    assert len(cargar_registro().ids) == len(list(DIR_TRABAJADORES.glob("*.yaml")))


def test_modelo_sin_llave_es_de_prueba_y_con_llave_es_gemini() -> None:
    spec = cargar_registro().trabajadores["comprension"].modelo
    assert spec is not None
    assert type(crear_modelo(spec, {})).__name__ == "TestModel"
    real = crear_modelo(spec, {"GEMINI_API_KEY": "llave-falsa-de-prueba"})
    assert type(real).__name__ == "OpenAIChatModel"
    assert real.model_name == spec.id
