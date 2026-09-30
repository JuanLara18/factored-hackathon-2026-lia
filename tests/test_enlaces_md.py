"""Todo enlace relativo de un Markdown versionado apunta a un archivo o carpeta que existe."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

RAIZ = Path(__file__).resolve().parents[1]
ENLACE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BLOQUE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def _markdowns() -> list[Path]:
    salida = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=RAIZ, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    return [RAIZ / linea for linea in salida.splitlines() if (RAIZ / linea).is_file()]


def _rotos(md: Path) -> list[str]:
    texto = BLOQUE.sub("", md.read_text(encoding="utf-8"))
    rotos: list[str] = []
    for destino in ENLACE.findall(texto):
        if re.match(r"^([a-z]+:|#|//)", destino):
            continue
        ruta = unquote(destino.split("#", 1)[0])
        if ruta and not (md.parent / ruta).exists():
            rotos.append(destino)
    return rotos


def test_enlaces_relativos_existen() -> None:
    rotos = {str(md.relative_to(RAIZ)): r for md in _markdowns() if (r := _rotos(md))}
    assert not rotos, rotos
