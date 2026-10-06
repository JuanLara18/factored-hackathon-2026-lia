"""Arma la carpeta del Space de Hugging Face con lo que el backend del chat necesita del repositorio.

Conserva la estructura del workspace porque el código resuelve plantillas, política y web por rutas relativas.
Uso: `uv run python tecnologia/infra/hf_space/preparar.py <salida>`; luego se sube con `hf upload`.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
MIEMBROS = ("comun", "clientes", "ia", "datos", "tecnologia", "gobierno")
# Solo estos paquetes se instalan en el Space; de los demás basta el pyproject para que el workspace resuelva.
CON_CODIGO = ("comun", "gobierno", "tecnologia")
EXTRA = (
    "tecnologia/web/chat",
    "gobierno/politica",
    "clientes/plantillas",
    "clientes/conocimiento",
    "ia/prompts/disputas",
)
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "tests", ".pytest_cache")


def preparar(salida: Path) -> Path:
    if salida.exists():
        shutil.rmtree(salida)
    salida.mkdir(parents=True)
    for nombre in ("pyproject.toml", "uv.lock"):
        shutil.copy2(RAIZ / nombre, salida / nombre)
    for miembro in MIEMBROS:
        (salida / miembro).mkdir()
        shutil.copy2(RAIZ / miembro / "pyproject.toml", salida / miembro / "pyproject.toml")
        for opcional in ("README.md",):
            if (RAIZ / miembro / opcional).is_file():
                shutil.copy2(RAIZ / miembro / opcional, salida / miembro / opcional)
        if miembro in CON_CODIGO:
            shutil.copytree(RAIZ / miembro / "src", salida / miembro / "src", ignore=IGNORAR)
    for ruta in EXTRA:
        if (RAIZ / ruta).exists():
            shutil.copytree(RAIZ / ruta, salida / ruta, ignore=IGNORAR, dirs_exist_ok=True)
    shutil.copy2(AQUI / "Dockerfile", salida / "Dockerfile")
    shutil.copy2(AQUI / "README.space.md", salida / "README.md")
    return salida


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / ".hf_space"
    print(preparar(destino))
