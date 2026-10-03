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
_PROHIBIDAS = re.compile(
    r"\b(radicad[oa]|bloquead[oa]|reembols\w+|abonad[oa]|estorn\w+|creditad[oa])\b", re.IGNORECASE
)
# Afirmaciones que valen solo si en el turno se ejecutó la acción verificada (aprobada por el cliente). Las de
# movimiento de dinero no se habilitan nunca: el banco no mueve dinero en este flujo.
ACCIONES_VERIFICABLES = frozenset({"radicad", "bloquead"})
_NEGACION = re.compile(r"\b(no|não|nao|nunca|sin|sem|ni|nem)\b(?:\W+\w+){0,3}\W*$", re.IGNORECASE)

# Lo que el cliente ve cuando el filtro bloquea una frase o el turno falla, en el idioma de su registro.
RESPALDO = {
    "es": "Voy a revisar esto con un asesor para darte una respuesta correcta.",
    "pt": "Vou analisar isso com uma pessoa da equipe para dar uma resposta correta.",
}
FALLA = {
    "es": (
        "No pude continuar en este momento. Intenta de nuevo en unos minutos o pide una persona del equipo."
    ),
    "pt": (
        "Não consegui continuar neste momento. Tente de novo em alguns minutos ou peça uma pessoa da equipe."
    ),
}


def _idioma(registro: str) -> str:
    return "pt" if registro == "voce" else "es"


def respaldo_de(registro: str) -> str:
    return RESPALDO[_idioma(registro)]


def falla_de(registro: str) -> str:
    return FALLA[_idioma(registro)]


# Identificadores internos (defensa en profundidad, además del prompt): el de producto pasa a "terminada en
# NNNN" y el de transacción se quita.
_PRODUCTO = re.compile(
    r"(?P<pre>\btarjeta\s+)?\b(?:PRD|tarjeta)-(?P<id>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", re.IGNORECASE
)
_TRANSACCION = re.compile(
    r"[ \t]*[(\[]?(?:\b(?:el |al |del )?ids? (?:de (?:la )?transacci[oó]n )?)?"
    r"\b(?:TXN?|transaction)[-_][A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*\b[)\]]?",
    re.IGNORECASE,
)


def _final(identificador: str) -> str:
    return re.sub(r"\D", "", identificador).rjust(4, "0")[-4:]


def enmascarar_identificadores(frase: str) -> str:
    """`PRD-R7AEZL80P060` pasa a `terminada en 0060`; `TX-1001` se elimina."""
    sin_producto = _PRODUCTO.sub(
        lambda m: f"{m.group('pre') or 'tarjeta '}terminada en {_final(m.group('id'))}", frase
    )
    sin_transaccion = _TRANSACCION.sub("", sin_producto)
    return re.sub(r"\s+([,.;:?])", r"\1", re.sub(r" {2,}", " ", sin_transaccion)).strip()


def filtrar_frase(frase: str, permitidas: frozenset[str] = frozenset()) -> ResultadoFiltro:
    """Enmascara tarjetas e ids internos y bloquea afirmaciones de acción sin `AccionVerificada`.

    `permitidas` trae las raíces de `ACCIONES_VERIFICABLES` cuya acción se ejecutó en el turno; una negación
    ("no fue bloqueada", "não foi bloqueado") no afirma nada y pasa.
    """
    enmascarada = enmascarar_identificadores(_TARJETA.sub(lambda m: f"**** {m.group(1)}", frase))
    for m in _PROHIBIDAS.finditer(enmascarada):
        palabra = m.group(1).lower()
        if palabra[:-1] in permitidas or _NEGACION.search(enmascarada[: m.start()]):
            continue
        return ResultadoFiltro(enmascarada, bloqueada=True, motivo=f"afirmacion_prohibida:{palabra}")
    return ResultadoFiltro(enmascarada)
