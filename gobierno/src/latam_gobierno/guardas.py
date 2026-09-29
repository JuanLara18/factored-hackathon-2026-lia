"""Guardas del repositorio (GOB-10.1, DAT-6.3, R-DAT-57, R-GOB-70).

Rechaza rutas que nunca deben versionarse: datos del organizador, credenciales, el diccionario del
dataset y audio. Revisa nombres y, en archivos de texto, patrones de llaves de AWS. Nunca imprime el
contenido que coincide: solo la ruta y la regla.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

EXTENSIONES_PROHIBIDAS = frozenset(
    {".csv", ".parquet", ".duckdb", ".pem", ".key", ".wav", ".mp3", ".m4a", ".ogg", ".flac"}
)
# Seeds de dbt hechos por el equipo (dominios canónicos, directorio inventado): sin datos del organizador.
CSV_PERMITIDOS = ("datos/dominios/",)
CARPETAS_PROHIBIDAS = frozenset({"data", "runs", "secretos", "audio", "materializados"})
PATRONES_CONTENIDO: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("llave-de-acceso-aws", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "llave-secreta-aws",
        re.compile(r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}\b", re.IGNORECASE),
    ),
    ("llave-privada", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
)
TAMANO_MAXIMO_LECTURA = 2_000_000


@dataclass(frozen=True)
class Hallazgo:
    ruta: str
    regla: str

    def __str__(self) -> str:
        return f"{self.ruta}: {self.regla}"


def revisar_ruta(ruta: str) -> list[Hallazgo]:
    """Revisa solo el nombre y la ubicación de una ruta relativa al repositorio."""
    p = PurePosixPath(ruta.replace("\\", "/"))
    nombre = p.name.lower()
    hallazgos: list[Hallazgo] = []
    csv_permitido = p.suffix.lower() == ".csv" and str(p).startswith(CSV_PERMITIDOS) and len(p.parts) == 3
    if p.suffix.lower() in EXTENSIONES_PROHIBIDAS and not csv_permitido:
        hallazgos.append(Hallazgo(ruta, f"extension {p.suffix.lower()} prohibida (datos o llaves)"))
    if CARPETAS_PROHIBIDAS & {parte.lower() for parte in p.parts[:-1]}:
        hallazgos.append(Hallazgo(ruta, "carpeta de datos, corridas, audio o secretos"))
    if "diccionario" in nombre:
        hallazgos.append(Hallazgo(ruta, "diccionario del dataset (trae credenciales)"))
    if nombre.startswith(".env") and nombre != ".env.example":
        hallazgos.append(Hallazgo(ruta, "archivo de entorno con secretos"))
    if nombre.startswith("credentials") and p.suffix.lower() == ".json":
        hallazgos.append(Hallazgo(ruta, "archivo de credenciales"))
    if p.parts[:3] == ("gobierno", "retenido", "casos"):
        hallazgos.append(Hallazgo(ruta, "casos del retenido"))
    return hallazgos


def revisar_contenido(ruta: str, raiz: Path) -> list[Hallazgo]:
    """Busca patrones de llaves en un archivo de texto. No devuelve el texto encontrado."""
    archivo = raiz / ruta
    try:
        if not archivo.is_file() or archivo.stat().st_size > TAMANO_MAXIMO_LECTURA:
            return []
        texto = archivo.read_bytes().decode("utf-8", errors="ignore")
    except OSError:
        return []
    return [
        Hallazgo(ruta, f"patron de {nombre}") for nombre, patron in PATRONES_CONTENIDO if patron.search(texto)
    ]


def revisar(rutas: Iterable[str], raiz: Path) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for ruta in rutas:
        hallazgos.extend(revisar_ruta(ruta))
        hallazgos.extend(revisar_contenido(ruta, raiz))
    return hallazgos


def _rutas_versionadas(raiz: Path) -> list[str]:
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=raiz, check=True, capture_output=True, text=True
    ).stdout
    return [r for r in salida.split("\0") if r]


def main(argv: Sequence[str] | None = None) -> int:
    """Sin argumentos revisa todo lo versionado; con argumentos, solo esas rutas."""
    args = list(sys.argv[1:] if argv is None else argv)
    raiz = Path.cwd()
    rutas = args or _rutas_versionadas(raiz)
    # este módulo y sus pruebas contienen los patrones y ejemplos falsos a propósito
    rutas = [r for r in rutas if not r.replace("\\", "/").endswith(("guardas.py", "test_guardas_repo.py"))]
    hallazgos = revisar(rutas, raiz)
    for h in hallazgos:
        print(f"GUARDA: {h}", file=sys.stderr)
    return 1 if hallazgos else 0


if __name__ == "__main__":
    raise SystemExit(main())
