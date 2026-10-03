"""Detección de idioma por léxico para el arnés: ¿el texto está en español o en portugués?

No es un clasificador de idioma general: mira solo palabras que existen en un idioma y no en el otro, lo que
basta para decidir si el agente respondió en el idioma del último mensaje del cliente (CLI-1.5).
"""

from __future__ import annotations

import re
import unicodedata

PT = re.compile(
    r"\b(voc[eê]s?|n[aã]o|uma|foi|vou|seu|sua|seus|suas|meu|minha|cart[aã]o|cobran[cç]a|contesta[cç][aã]o|"
    r"tamb[eé]m|ainda|ent[aã]o|pode|posso|estou|sim|ol[aá]|oi|quero|portugu[eê]s|falar|confirme|"
    r"est[aã]o|roubaram|ajudar|mas|obrigad[oa]|equipe|pessoa|conta|prazo|agora)\b",
    re.IGNORECASE,
)
ES = re.compile(
    r"\b(usted|ustedes|una|fue|voy|su|sus|tarjeta|reclamo|cargo|cobro|tambi[eé]n|todav[ií]a|entonces|puede|"
    r"estoy|aqu[ií]|s[ií]|mejor|sigamos|espa[nñ]ol|quiero|perd[oó]n|hablar|conf[ií]rmelo|gracias|hola|"
    r"cuenta|monto|plazo|reconozco|ayudar|pero|equipo|ahora)\b",
    re.IGNORECASE,
)


def detectar_idioma(texto: str) -> str | None:
    """`es`, `pt` o `None` si el texto no trae palabras que decidan (cifras, nombres, saludos sueltos)."""
    t = unicodedata.normalize("NFC", texto)
    pt, es = len(PT.findall(t)), len(ES.findall(t))
    if pt == es:
        return None
    return "pt" if pt > es else "es"
