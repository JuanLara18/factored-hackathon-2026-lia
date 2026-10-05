"""Despliega el agente de disputas en Agent Runtime como agente propio (D-32 fase 2).

Uso:
  uv run python tecnologia/infra/agent_runtime/desplegar.py --dry-run   # arma y valida, sin llamar a la API
  uv run python tecnologia/infra/agent_runtime/desplegar.py             # crea un recurso nuevo (SDK y ADC)
  uv run python tecnologia/infra/agent_runtime/desplegar.py --recurso <recurso>
      # actualiza ese recurso (projects/<p>/locations/<l>/reasoningEngines/<id>); también con
      # LATAM_AGENT_RUNTIME_RECURSO

Empaqueta solo lo que el agente necesita (comun, gobierno con su política y tecnologia, sin pruebas ni
web) en una carpeta `latam_paquete` que viaja como `extra_packages`. El agente corre con la cuenta de servicio
`latam-chat@` (Agent Identity exige que el proyecto esté en una organización) y el registro en Agent Registry
es automático para los agentes desplegados con el SDK. Imprime el recurso.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
NOMBRE_PAQUETE = "latam_paquete"
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "tests", ".pytest_cache")
COPIAS = (
    "comun/src",
    "gobierno/src",
    "gobierno/politica",
    "tecnologia/src",
    "ia/prompts/disputas",
    "clientes/plantillas",
)
PROYECTO = "latam-bank-hackaton-2026"
NOMBRE_VISIBLE = "latam-disputas"
ETIQUETAS = {"proyecto": "latam-bank", "agente": "disputas", "fase": "geap-2"}
# El runtime solo necesita estos paquetes; el canal (FastAPI, AG-UI) vive en Cloud Run.
DISTRIBUCIONES = (
    "pydantic",
    "pydantic-ai-slim",
    "openai",
    "google-genai",
    "httpx",
    "google-auth",
    "google-cloud-bigquery",
    "google-cloud-firestore",
    "opentelemetry-sdk",
    "opentelemetry-exporter-gcp-trace",
    "psycopg",
    "pyyaml",
)
EXTRAS = {"pydantic-ai-slim": "[google,openai]", "psycopg": "[binary]"}
VARIABLE_RECURSO = "LATAM_AGENT_RUNTIME_RECURSO"
RECURSO_VALIDO = re.compile(r"^projects/[^/]+/locations/[^/]+/reasoningEngines/[^/]+$")
CLAVE_VALIDA = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
VALOR_VALIDO = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")


def version_del_registro(trabajador: str = "disputas") -> str:
    ruta = RAIZ / "ia" / "agentes" / "trabajadores" / f"{trabajador}.yaml"
    return str(yaml.safe_load(ruta.read_text(encoding="utf-8"))["version"])


def requisitos() -> list[str]:
    """Versiones fijadas a las del entorno donde se despliega (mismo `uv.lock`), más el SDK del runtime."""
    salida = ["google-cloud-aiplatform[agent_engines]", "cloudpickle"]
    for d in DISTRIBUCIONES:
        try:
            salida.append(f"{d}{EXTRAS.get(d, '')}=={metadata.version(d)}")
        except metadata.PackageNotFoundError:
            salida.append(f"{d}{EXTRAS.get(d, '')}")
    return salida


def empaquetar(salida: Path) -> Path:
    """Crea `<salida>/latam_paquete` con la estructura del workspace (el código resuelve rutas relativas)."""
    destino = salida / NOMBRE_PAQUETE
    if destino.exists():
        shutil.rmtree(destino)
    for parte in COPIAS:
        shutil.copytree(RAIZ / parte, destino / parte, ignore=IGNORAR)
    return destino


def entorno(proyecto: str, version: str) -> dict[str, Any]:
    return {
        "LATAM_GCP_PROJECT": proyecto,
        # Sin la clave el agente no arranca: el paquete de traspaso usa las mismas referencias que la banca.
        "LATAM_ENTORNO": "produccion",
        "LATAM_REF_SECRETO": {"secret": "latam-ref-secreto", "version": "latest"},
        "LATAM_GEAP_LOCATION": "global",
        "LATAM_TRABAJADOR_VERSION": version,
        # Gemini 3 por el endpoint compatible con OpenAI pierde la thought_signature de las herramientas;
        # hasta pasar al proveedor nativo de Google, el agente usa 2.5 Flash-Lite.
        "LATAM_MODELO": os.environ.get("LATAM_MODELO", "gemini-3.1-flash-lite"),
    }


def configuracion(proyecto: str, version: str, paquete: Path, *, bucket: str | None = None) -> dict[str, Any]:
    etiquetas = {**ETIQUETAS, "version": version.replace(".", "-")}
    config: dict[str, Any] = {
        "display_name": NOMBRE_VISIBLE,
        "description": "Agente de disputas del banco (PydanticAI) con aprobación del cliente en el canal.",
        "requirements": requisitos(),
        "extra_packages": [str(paquete)],
        "env_vars": entorno(proyecto, version),
        "min_instances": 0,
        "max_instances": 1,
        "labels": etiquetas,
        # Agent Identity exige que el proyecto esté en una organización (el principal lleva org-<id>);
        # este no está, y con esa identidad el runtime recibía 401. Se usa la cuenta de mínimo privilegio.
        "identity_type": "SERVICE_ACCOUNT",
        "service_account": f"latam-chat@{proyecto}.iam.gserviceaccount.com",
    }
    if bucket:
        config["staging_bucket"] = f"gs://{bucket}"
    return config


def validar(config: dict[str, Any], paquete: Path) -> list[str]:
    """Comprobaciones locales; devuelve los problemas (vacío si todo está bien)."""
    problemas: list[str] = []
    for clave, valor in config["labels"].items():
        if not CLAVE_VALIDA.match(clave) or not VALOR_VALIDO.match(valor):
            problemas.append(f"etiqueta inválida {clave}={valor}")
    if not (paquete / "gobierno" / "politica" / "v1" / "autonomia.yaml").is_file():
        problemas.append("falta la política v1 en el paquete")
    if (paquete / "tecnologia" / "src" / "latam_tecnologia" / "web").exists() or any(paquete.rglob("tests")):
        problemas.append("el paquete incluye pruebas o web")
    if config["min_instances"] != 0:
        problemas.append("min_instances debe ser 0")
    # Importa la clase solo desde el paquete y carga la política con su huella, como en el runtime.
    codigo = (
        "import sys, json; raiz = sys.argv[1]\n"
        "for m in ('comun', 'gobierno', 'tecnologia'): sys.path.insert(0, raiz + '/' + m + '/src')\n"
        "import latam_tecnologia, latam_gobierno.politica as p\n"
        "from latam_tecnologia.runtime.agente import AgenteDisputasRuntime\n"
        "p.cargar()\n"
        "assert str(latam_tecnologia.__file__).startswith(raiz), latam_tecnologia.__file__\n"
        "print(json.dumps(AgenteDisputasRuntime('p').register_operations()))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", codigo, str(paquete)], capture_output=True, text=True, cwd=paquete.parent
    )
    if r.returncode != 0:
        detalle = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "sin detalle"
        problemas.append(f"el paquete no importa: {detalle}")
    return problemas


def _cliente(proyecto: str, ubicacion: str) -> tuple[Any, Any]:
    try:
        import agentplatform  # pyright: ignore[reportMissingImports]

        return agentplatform.Client(
            project=proyecto, location=ubicacion, http_options={"api_version": "v1beta1"}
        ), agentplatform
    except ImportError:
        import vertexai

        return vertexai.Client(
            project=proyecto, location=ubicacion, http_options={"api_version": "v1beta1"}
        ), vertexai


def desplegar(config: dict[str, Any], proyecto: str, ubicacion: str, recurso: str | None = None) -> str:
    """Crea el recurso, o actualiza `recurso` si se da (conserva el id y lo que el canal ya apunta)."""
    cliente, sdk = _cliente(proyecto, ubicacion)
    try:
        import cloudpickle  # pyright: ignore[reportMissingImports]
        import latam_tecnologia.runtime.agente as modulo

        cloudpickle.register_pickle_by_value(modulo)  # el runtime no tiene el paquete al deserializar
    except ImportError:
        pass
    from latam_tecnologia.runtime.agente import AgenteDisputasRuntime

    tipos = getattr(sdk, "types", None)
    if tipos is not None and hasattr(tipos, "IdentityType"):
        config = {**config, "identity_type": tipos.IdentityType.SERVICE_ACCOUNT}
    agente = AgenteDisputasRuntime(config["env_vars"]["LATAM_GCP_PROJECT"], "global", "latam_bank")
    api = getattr(cliente, "runtimes", None) or cliente.agent_engines
    if recurso:
        remoto = api.update(name=recurso, agent=agente, config=config)
    else:
        remoto = api.create(agent=agente, config=config)
    return str(remoto.api_resource.name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="arma el paquete y valida sin llamar a la API")
    ap.add_argument("--proyecto", default=PROYECTO)
    ap.add_argument(
        "--ubicacion", default="us-central1", help="región de Agent Runtime (los modelos van a global)"
    )
    ap.add_argument(
        "--recurso",
        default=os.environ.get(VARIABLE_RECURSO),
        help="recurso existente a actualizar (projects/<p>/locations/<l>/reasoningEngines/<id>)",
    )
    ap.add_argument("--bucket", help="bucket de preparación, si el SDK lo pide")
    ap.add_argument("--salida", type=Path, help="carpeta del paquete (por defecto, una temporal)")
    a = ap.parse_args(argv)
    if a.recurso and not RECURSO_VALIDO.match(a.recurso):
        print(
            f"--recurso debe tener la forma projects/<p>/locations/<l>/reasoningEngines/<id>: {a.recurso}",
            file=sys.stderr,
        )
        return 1
    accion = f"actualizar {a.recurso}" if a.recurso else "crear un recurso nuevo"
    version = version_del_registro()
    with tempfile.TemporaryDirectory() as tmp:
        base = a.salida or Path(tmp)
        paquete = empaquetar(base)
        config = configuracion(a.proyecto, version, paquete, bucket=a.bucket)
        problemas = validar(config, paquete)
        resumen = {
            **config,
            "extra_packages": [
                f"{NOMBRE_PAQUETE}/ ({sum(1 for _ in paquete.rglob('*') if _.is_file())} archivos)"
            ],
        }
        print(f"accion: {accion}")
        print(json.dumps(resumen, indent=2, ensure_ascii=False, default=str))
        if problemas:
            print("PROBLEMAS:", *problemas, sep="\n  - ", file=sys.stderr)
            return 1
        if a.dry_run:
            print(f"dry-run correcto ({accion}): paquete y configuración válidos; no se llamó a la API")
            return 0
        # El SDK conserva la ruta dada en el tar: con una ruta absoluta (y en Windows) el paquete no queda en
        # /code/latam_paquete. Se despliega desde la carpeta padre con la ruta relativa.
        anterior = Path.cwd()
        os.chdir(paquete.parent)
        try:
            recurso = desplegar(
                {**config, "extra_packages": [NOMBRE_PAQUETE]}, a.proyecto, a.ubicacion, a.recurso
            )
        finally:
            os.chdir(anterior)
    print(recurso)
    print("Agent Registry: el registro es automático con el SDK; verifíquelo en la consola.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
