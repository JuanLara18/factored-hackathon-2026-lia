"""CLI-1.6: linter de contenido. Corre en pytest (y por línea de comandos) y bloquea la integración continua.

Reglas: frases prohibidas y caracteres prohibidos, frases obligatorias, marcadores declarados y requeridos por
tipo, sin cifras escritas, coherencia de registro, longitud por canal, vocabulario por canal y por país, y
cobertura de la matriz (cada estado del motor x canal x registro exigido tiene plantilla con texto).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from latam_comun.dominio.caso import Estado

from latam_clientes.contenido import (
    MARCADOR,
    Estilo,
    Matriz,
    Plantilla,
    Plantillas,
    cargar_estilo,
    cargar_matriz,
    cargar_plantillas,
    frases_prohibidas,
    renderizar,
)

CIFRAS = re.compile(r"\d|\$|\b(USD|COP|MXN|ARS|BRL)\b")
ORACIONES = re.compile(r"(?<=[.?:;])\s+")


@dataclass(frozen=True)
class Hallazgo:
    regla: str
    plantilla: str
    detalle: str
    registro: str = ""

    def __str__(self) -> str:
        donde = f"{self.plantilla}[{self.registro}]" if self.registro else self.plantilla
        return f"{self.regla}: {donde}: {self.detalle}"


def _estados_de(matriz: Matriz) -> dict[str, set[str]]:
    """Estados de la matriz que usan cada plantilla."""
    por_plantilla: dict[str, set[str]] = {}
    for estado, e in matriz.estados.items():
        for c in e.celdas.values():
            por_plantilla.setdefault(c.plantilla, set()).add(estado)
    return por_plantilla


def _requeridos(estilo: Estilo, p: Plantilla) -> set[str]:
    requeridos: set[str] = set()
    for tipo in p.tipos:
        req = estilo.tipos.get(tipo)
        if req is None:
            continue
        for canal in p.canales:
            requeridos |= set(req.por_canal.get(canal, req.todos))
    return requeridos


def _texto_de_registro(p: Plantilla, registro: str) -> str:
    return p.textos.get(registro, "")


def _verificar_plantilla(p: Plantilla, matriz: Matriz, estilo: Estilo, estados: set[str]) -> list[Hallazgo]:
    h: list[Hallazgo] = []
    prohibidas = frases_prohibidas(estilo, "plantilla")
    reglas = [r for r in estilo.frases_prohibidas if "plantilla" in r.alcance]
    marcas = estilo.marcas_registro

    for tipo in p.tipos:
        if tipo not in estilo.tipos:
            h.append(Hallazgo("tipo", p.id, f"tipo desconocido {tipo!r}"))
    for canal in p.canales:
        if canal not in matriz.canales:
            h.append(Hallazgo("canal", p.id, f"canal desconocido {canal!r}"))
    declarados = set(p.marcadores)
    for m in declarados - set(estilo.marcadores):
        h.append(Hallazgo("marcador", p.id, f"marcador {m!r} fuera del catálogo de la guía de estilo"))
    requeridos = _requeridos(estilo, p)
    if requeridos - declarados:
        h.append(Hallazgo("marcador_requerido", p.id, f"faltan marcadores {sorted(requeridos - declarados)}"))

    for registro in matriz.registros_exigidos():
        texto = _texto_de_registro(p, registro)
        if not texto.strip():
            h.append(Hallazgo("registro_faltante", p.id, "sin texto en este registro", registro))
            continue
        usados = set(MARCADOR.findall(texto))
        if usados != declarados:
            h.append(
                Hallazgo(
                    "marcador",
                    p.id,
                    f"usados {sorted(usados)} y declarados {sorted(declarados)} no coinciden",
                    registro,
                )
            )
        if CIFRAS.search(texto):
            h.append(
                Hallazgo("cifra_escrita", p.id, "cifra, símbolo o código de moneda en el texto", registro)
            )
        for regla, patron in zip(reglas, prohibidas, strict=True):
            if patron.search(texto):
                h.append(Hallazgo("frase_prohibida", p.id, f"{regla.id}: {regla.motivo}", registro))
        for c in estilo.caracteres_prohibidos:
            if re.search(c.patron, texto):
                h.append(Hallazgo("caracter_prohibido", p.id, c.id, registro))
        sin_marcadores = MARCADOR.sub("", texto)
        for t in estilo.terminos_por_pais:
            if re.search(rf"\b{re.escape(t)}\b", sin_marcadores, re.IGNORECASE):
                h.append(Hallazgo("vocabulario_pais", p.id, f"{t!r} escrito; usar el marcador", registro))
        h += _registro(p, registro, texto, marcas.tuteo, marcas.voseo, marcas.usted)
        h += _longitud(p, registro, estilo)
        for o in estilo.frases_obligatorias:
            aplica = bool(set(o.aplica_a.tipos) & set(p.tipos)) or bool(set(o.aplica_a.estados) & estados)
            if aplica and not re.search(o.patron, texto, re.IGNORECASE):
                h.append(Hallazgo("frase_obligatoria", p.id, f"{o.id}: {o.motivo}", registro))
    return h


def _registro(p: Plantilla, registro: str, texto: str, tuteo: str, voseo: str, usted: str) -> list[Hallazgo]:
    ajenos = {"usted": [tuteo, voseo], "vos": [tuteo, usted]}.get(registro, [])
    h: list[Hallazgo] = []
    for patron in ajenos:
        for m in re.finditer(patron, texto, re.IGNORECASE):
            h.append(Hallazgo("registro", p.id, f"marca ajena {m.group(0)!r}", registro))
    return h


def _longitud(p: Plantilla, registro: str, estilo: Estilo) -> list[Hallazgo]:
    usados = set(MARCADOR.findall(p.textos[registro]))
    if usados - set(estilo.marcadores):
        return []  # ya se reportó como marcador fuera del catálogo
    muestras = {m: estilo.marcadores[m] for m in usados}
    texto = renderizar(p, registro, muestras)
    h: list[Hallazgo] = []
    for canal in p.canales:
        lim = estilo.canales.get(canal)
        if lim is None:
            continue
        if len(texto) > lim.max_caracteres:
            h.append(
                Hallazgo(
                    "longitud",
                    p.id,
                    f"{canal}: {len(texto)} caracteres, máximo {lim.max_caracteres}",
                    registro,
                )
            )
        for oracion in ORACIONES.split(texto):
            palabras = len(oracion.split())
            if palabras > lim.max_palabras_frase:
                h.append(
                    Hallazgo(
                        "longitud",
                        p.id,
                        f"{canal}: {palabras} palabras, máximo {lim.max_palabras_frase}: {oracion!r}",
                        registro,
                    )
                )
        for palabra in lim.vocabulario_prohibido:
            if re.search(rf"\b{re.escape(palabra)}\b", texto, re.IGNORECASE):
                h.append(Hallazgo("vocabulario_canal", p.id, f"{canal}: {palabra!r}", registro))
    return h


def _verificar_matriz(
    matriz: Matriz, estilo: Estilo, plantillas: Plantillas, estados_motor: set[str]
) -> list[Hallazgo]:
    h: list[Hallazgo] = []
    por_id = plantillas.por_id()
    if len(por_id) != len(plantillas.plantillas):
        h.append(Hallazgo("plantilla_duplicada", "es.yaml", "ids repetidos"))
    if set(matriz.estados) != estados_motor:
        h.append(
            Hallazgo(
                "matriz_estados",
                "matriz.yaml",
                f"faltan {sorted(estados_motor - set(matriz.estados))}, "
                f"sobran {sorted(set(matriz.estados) - estados_motor)}",
            )
        )
    for estado, e in matriz.estados.items():
        for canal in matriz.canales:
            celda = e.celdas.get(canal)
            if celda is None or not celda.intencion.strip():
                h.append(Hallazgo("celda", f"{estado}.{canal}", "celda o intención ausente"))
                continue
            p = por_id.get(celda.plantilla)
            if p is None:
                h.append(Hallazgo("celda", f"{estado}.{canal}", f"plantilla {celda.plantilla!r} no existe"))
                continue
            if canal not in p.canales:
                h.append(Hallazgo("celda", f"{estado}.{canal}", f"{p.id} no declara el canal {canal}"))
            for registro in matriz.registros_exigidos():
                if not p.textos.get(registro, "").strip():
                    h.append(Hallazgo("celda", f"{estado}.{canal}", "sin texto", registro))
        for canal in set(e.celdas) - set(matriz.canales):
            h.append(Hallazgo("celda", f"{estado}.{canal}", "canal fuera de la matriz"))
    for nombre, pais in {**estilo.paises, "neutro": estilo.pais_neutro}.items():
        if pais.registro not in matriz.registros_exigidos():
            h.append(Hallazgo("pais", nombre, f"registro {pais.registro!r} sin plantillas"))
    return h


def verificar(
    matriz: Matriz | None = None,
    estilo: Estilo | None = None,
    plantillas: Plantillas | None = None,
    estados_motor: set[str] | None = None,
) -> list[Hallazgo]:
    matriz = matriz or cargar_matriz()
    estilo = estilo or cargar_estilo()
    plantillas = plantillas or cargar_plantillas()
    estados_motor = estados_motor if estados_motor is not None else {e.value for e in Estado}
    por_plantilla = _estados_de(matriz)
    hallazgos = _verificar_matriz(matriz, estilo, plantillas, estados_motor)
    for p in plantillas.plantillas:
        hallazgos += _verificar_plantilla(p, matriz, estilo, por_plantilla.get(p.id, set()))
    return hallazgos


def main() -> int:
    hallazgos = verificar()
    for x in hallazgos:
        print(x)
    print(f"{len(hallazgos)} hallazgos")
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main())
