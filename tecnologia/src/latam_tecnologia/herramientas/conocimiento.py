"""Recuperación de política para el cliente: el asistente responde preguntas de política solo con una fuente.

La base (`clientes/conocimiento/articulos.yaml`) dice en lenguaje llano lo que manda `policy/v1`; cada
artículo nombra sus reglas. Dos recuperadores con la misma interfaz: el léxico (BM25, sin red) y el
vectorial (vectores de los artículos guardados en el repositorio y un solo llamado para la pregunta). El
vectorial decide además si hay fuente: bajo el umbral no devuelve nada y el asistente dice que no tiene
esa información. Si el
servicio de vectores falla, se responde con el léxico y su propio umbral (caída segura, sin reintentos).

El país no se recupera, se filtra: un artículo con `pais` solo vale para clientes de ese país, y el país sale
de la cuenta de la sesión, no de la pregunta.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import yaml

RAIZ_CONOCIMIENTO = Path(__file__).resolve().parents[4] / "clientes" / "conocimiento"
RUTA_ARTICULOS = RAIZ_CONOCIMIENTO / "articulos.yaml"
RUTA_VECTORES = RAIZ_CONOCIMIENTO / "vectores.json"
RUTA_CONFIG = RAIZ_CONOCIMIENTO / "recuperacion.yaml"
IDIOMAS = ("es", "pt")
Incrustar = Callable[[str], Sequence[float]]

# Palabras que no distinguen un artículo de otro; el resto se compara sin tildes y en minúsculas.
_VACIAS = frozenset(
    [
        "a",
        "al",
        "algo",
        "con",
        "de",
        "del",
        "el",
        "en",
        "es",
        "la",
        "las",
        "lo",
        "los",
        "me",
        "mi",
        "mis",
        "no",
        "o",
        "para",
        "por",
        "que",
        "se",
        "si",
        "su",
        "sus",
        "un",
        "una",
        "y",
        "ya",
        "yo",
        "as",
        "com",
        "da",
        "das",
        "do",
        "dos",
        "e",
        "em",
        "eu",
        "meu",
        "minha",
        "na",
        "nas",
        "no",
        "nos",
        "os",
        "ou",
        "para",
        "por",
        "que",
        "se",
        "um",
        "uma",
    ]
)


@dataclass(frozen=True)
class Articulo:
    id: str
    reglas: tuple[str, ...]
    tema: str
    textos: dict[str, str]
    pais: str | None = None
    provisional: bool = False


@dataclass(frozen=True)
class Hallazgo:
    articulo: Articulo
    puntaje: float


@dataclass(frozen=True)
class Busqueda:
    """`hallazgos` vacío significa que no hay fuente; `metodo` dice quién respondió (traza y auditoría)."""

    hallazgos: tuple[Hallazgo, ...]
    metodo: Literal["vectorial", "lexico"]

    def reglas(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(r for h in self.hallazgos for r in h.articulo.reglas))


class Recuperador(Protocol):
    def buscar(self, pregunta: str, pais: str | None = None, k: int = 2) -> Busqueda: ...


def cargar_articulos(ruta: Path = RUTA_ARTICULOS) -> tuple[Articulo, ...]:
    datos = cast(dict[str, Any], yaml.safe_load(ruta.read_text(encoding="utf-8")))
    return tuple(
        Articulo(
            id=a["id"],
            reglas=tuple(a["reglas"]),
            tema=a["tema"],
            textos={i: a[i] for i in IDIOMAS},
            pais=a.get("pais"),
            provisional=bool(a.get("provisional", False)),
        )
        for a in datos["articulos"]
    )


def _elegibles(articulos: Sequence[Articulo], pais: str | None) -> list[Articulo]:
    return [a for a in articulos if a.pais is None or pais is None or a.pais == pais]


def terminos(texto: str) -> list[str]:
    plano = unicodedata.normalize("NFKD", texto.lower())
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", plano) if t not in _VACIAS and len(t) > 1]


class RecuperadorLexico:
    """BM25 sobre el texto de cada artículo en los dos idiomas. Línea base y respaldo del vectorial."""

    def __init__(self, articulos: Sequence[Articulo], umbral: float = 0.0, k1: float = 1.5, b: float = 0.75):
        self._articulos = tuple(articulos)
        self._umbral, self._k1, self._b = umbral, k1, b
        self._docs = [Counter(terminos(" ".join(a.textos.values()))) for a in self._articulos]
        self._largo = [sum(d.values()) for d in self._docs]
        self._medio = sum(self._largo) / max(1, len(self._largo))
        n = len(self._docs)
        presentes = Counter(t for d in self._docs for t in d)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in presentes.items()}

    def puntajes(self, pregunta: str) -> list[float]:
        consulta = terminos(pregunta)
        salida: list[float] = []
        for doc, largo in zip(self._docs, self._largo, strict=True):
            norma = self._k1 * (1 - self._b + self._b * largo / self._medio)
            salida.append(
                sum(
                    self._idf.get(t, 0.0) * doc[t] * (self._k1 + 1) / (doc[t] + norma)
                    for t in consulta
                    if t in doc
                )
            )
        return salida

    def buscar(self, pregunta: str, pais: str | None = None, k: int = 2) -> Busqueda:
        permitidos = {a.id for a in _elegibles(self._articulos, pais)}
        orden = sorted(zip(self._articulos, self.puntajes(pregunta), strict=True), key=lambda x: -x[1])
        hallazgos = tuple(
            Hallazgo(a, p) for a, p in orden if a.id in permitidos and p > 0 and p >= self._umbral
        )[:k]
        return Busqueda(hallazgos, "lexico")


def coseno(u: Sequence[float], v: Sequence[float]) -> float:
    punto = sum(x * y for x, y in zip(u, v, strict=True))
    norma = math.sqrt(sum(x * x for x in u)) * math.sqrt(sum(y * y for y in v))
    return punto / norma if norma else 0.0


class RecuperadorVectorial:
    """Similitud de coseno entre la pregunta y cada artículo (el mayor de sus dos idiomas), con umbral."""

    def __init__(
        self,
        articulos: Sequence[Articulo],
        vectores: Mapping[str, Mapping[str, Sequence[float]]],
        incrustar: Incrustar,
        umbral: float,
        margen: float = 0.0,
        respaldo: Recuperador | None = None,
    ) -> None:
        faltan = [a.id for a in articulos if a.id not in vectores]
        if faltan:
            raise ValueError(f"artículos sin vector (regenerar vectores.json): {faltan}")
        self._articulos = tuple(articulos)
        self._vectores = vectores
        self._incrustar = incrustar
        self._umbral, self._margen = umbral, margen
        self._respaldo = respaldo

    def puntajes(self, vector: Sequence[float]) -> list[float]:
        return [max(coseno(vector, v) for v in self._vectores[a.id].values()) for a in self._articulos]

    def buscar(self, pregunta: str, pais: str | None = None, k: int = 2) -> Busqueda:
        try:
            vector = self._incrustar(pregunta)
        except Exception:
            if self._respaldo is None:
                raise
            return self._respaldo.buscar(pregunta, pais, k)
        permitidos = {a.id for a in _elegibles(self._articulos, pais)}
        orden = sorted(
            (
                (a, p)
                for a, p in zip(self._articulos, self.puntajes(vector), strict=True)
                if a.id in permitidos
            ),
            key=lambda x: -x[1],
        )
        if not orden or orden[0][1] < self._umbral:
            return Busqueda((), "vectorial")
        # además del mejor, solo los que quedan a `margen` de él: no se cita por rellenar
        cerca = [Hallazgo(a, p) for a, p in orden if p >= self._umbral and orden[0][1] - p <= self._margen]
        return Busqueda(tuple(cerca[:k]), "vectorial")


def cargar_vectores(ruta: Path = RUTA_VECTORES) -> tuple[dict[str, Any], dict[str, dict[str, list[float]]]]:
    datos = cast(dict[str, Any], json.loads(ruta.read_text(encoding="utf-8")))
    return datos["manifiesto"], datos["vectores"]


def cargar_config(ruta: Path = RUTA_CONFIG) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(ruta.read_text(encoding="utf-8")))


PAIS_POR_MONEDA = {"MXN": "MX", "COP": "CO", "ARS": "AR", "BRL": "BR"}
VARIABLE_RECUPERADOR = "LATAM_RECUPERADOR"  # `lexico` fuerza BM25 (sin red)


def _incrustar_vertex(proyecto: str, modelo: str, dimension: int) -> Incrustar:
    from google import genai
    from google.genai import types

    cliente = genai.Client(
        vertexai=True, project=proyecto, location="global", http_options=types.HttpOptions(timeout=8000)
    )
    config = types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=dimension)

    def incrustar(texto: str) -> Sequence[float]:
        respuesta = cliente.models.embed_content(model=modelo, contents=texto, config=config)
        return list((respuesta.embeddings or [])[0].values or [])

    return incrustar


def crear_recuperador(entorno: Mapping[str, str]) -> Recuperador:
    """Vectorial si hay proyecto de Google Cloud y vectores al día; si no, léxico. Nunca falla por la red."""
    articulos = cargar_articulos()
    config = cargar_config() if RUTA_CONFIG.exists() else {}
    lexico = RecuperadorLexico(articulos, umbral=float(config.get("respaldo_lexico", {}).get("umbral", 0.0)))
    proyecto = entorno.get("LATAM_GCP_PROJECT")
    if (
        not proyecto
        or entorno.get(VARIABLE_RECUPERADOR, "").lower() == "lexico"
        or not RUTA_VECTORES.exists()
    ):
        return lexico
    manifiesto, vectores = cargar_vectores()
    if manifiesto.get("huella_articulos") != hashlib.sha256(RUTA_ARTICULOS.read_bytes()).hexdigest():
        return (
            lexico  # los artículos cambiaron y los vectores no: mejor el léxico que citar con vectores viejos
        )
    return RecuperadorVectorial(
        articulos,
        vectores,
        _incrustar_vertex(proyecto, str(manifiesto["modelo"]), int(manifiesto["dimension"])),
        umbral=float(config["umbral"]),
        margen=float(config["margen"]),
        respaldo=lexico,
    )
