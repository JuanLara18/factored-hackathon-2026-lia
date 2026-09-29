"""Huella de los papeles de Auditoría (R-AUD-01, R-AUD-04).

La huella es SHA-256 del texto con saltos de línea normalizados a LF, para que sea la misma en
Windows y en Linux.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Sequence
from pathlib import Path


def huella(ruta: Path) -> str:
    contenido = ruta.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(contenido).hexdigest()


def huella_texto(ruta: Path) -> str:
    return ruta.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def huella_bloque(ruta: Path) -> str:
    """Huella del texto entre `inicio-sellado` y `fin-sellado` de un informe."""
    texto = huella_texto(ruta)
    m = re.search(r"<!-- inicio-sellado -->\n(.*?)<!-- fin-sellado -->", texto, re.DOTALL)
    if m is None:
        raise ValueError(f"{ruta}: faltan las marcas de sellado")
    return hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    """Imprime `huella  ruta` por cada archivo; con `--bloque`, la del bloque sellado."""
    args = list(sys.argv[1:] if argv is None else argv)
    bloque = "--bloque" in args
    for arg in (a for a in args if a != "--bloque"):
        print(f"{(huella_bloque if bloque else huella)(Path(arg))}  {arg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
