"""Emisión por frases y filtro de salida (definición 2.9, R-TEC-74 y R-TEC-75), versión de *spike*."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

ABREVIATURAS = frozenset({"sr.", "sra.", "no.", "núm.", "aprox."})
MAX_FRASE = 200
_FIN = ".?!;\n"


@dataclass
class SegmentadorFrases:
    """Acumula fragmentos de texto y devuelve solo frases completas.

    Un signo de fin de frase cuenta solo si lo sigue un espacio o un salto de línea, así `1.234,56`
    no se corta. Al terminar, `vaciar` entrega lo que quede.
    """

    _buf: str = field(default="", init=False)

    def alimentar(self, fragmento: str) -> list[str]:
        self._buf += fragmento
        salida: list[str] = []
        while (corte := self._siguiente_corte()) is not None:
            frase, self._buf = self._buf[:corte], self._buf[corte:].lstrip(" ")
            if frase.strip():
                salida.append(frase.strip())
        return salida

    def vaciar(self) -> list[str]:
        resto, self._buf = self._buf.strip(), ""
        return self._partir_largas(resto) if resto else []

    def _siguiente_corte(self) -> int | None:
        b = self._buf
        for i, c in enumerate(b):
            if c not in _FIN:
                continue
            if c != "\n" and (i + 1 >= len(b) or not b[i + 1].isspace()):
                continue
            if c == "." and self._es_abreviatura(b[: i + 1]):
                continue
            return i + 1
        if len(b) > MAX_FRASE:
            espacio = b.rfind(" ", 0, MAX_FRASE)
            return espacio + 1 if espacio > 0 else MAX_FRASE
        return None

    @staticmethod
    def _es_abreviatura(previo: str) -> bool:
        palabras = previo.split()
        return bool(palabras) and palabras[-1].lower() in ABREVIATURAS

    @staticmethod
    def _partir_largas(texto: str) -> list[str]:
        partes: list[str] = []
        while len(texto) > MAX_FRASE:
            corte = texto.rfind(" ", 0, MAX_FRASE)
            corte = corte if corte > 0 else MAX_FRASE
            partes.append(texto[:corte].strip())
            texto = texto[corte:].strip()
        return [*partes, texto] if texto else partes


@dataclass(frozen=True)
class ResultadoFiltro:
    texto: str
    bloqueada: bool = False
    motivo: str | None = None


FiltroFrase = Callable[[str], ResultadoFiltro]

_TARJETA = re.compile(r"\b(?:\d[ -]?){12,18}(\d{4})\b")
_PROHIBIDAS = re.compile(r"\b(radicad[oa]|bloquead[oa]|reembols\w+|abonad[oa]|estorn\w+)\b", re.IGNORECASE)


def filtrar_frase(frase: str) -> ResultadoFiltro:
    """Enmascara tarjetas y bloquea afirmaciones de acción sin `AccionVerificada`."""
    enmascarada = _TARJETA.sub(lambda m: f"**** {m.group(1)}", frase)
    if (m := _PROHIBIDAS.search(enmascarada)) is not None:
        return ResultadoFiltro(
            enmascarada, bloqueada=True, motivo=f"afirmacion_prohibida:{m.group(1).lower()}"
        )
    return ResultadoFiltro(enmascarada)
