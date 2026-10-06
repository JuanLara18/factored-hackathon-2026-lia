"""Evaluación de la recuperación de política (IA-12): `uv run python -m latam_ia.recuperacion`.

Compara, sobre los mismos juicios de relevancia, un recuperador vectorial (componente aprendido, preentrenado)
contra BM25 y contra el azar. La partición es estratificada por artículo con semilla fija: el umbral de
abstención y el margen se eligen en validación y la prueba se evalúa una vez. Con `--escribir` guarda los
vectores de los artículos y la configuración que usa el agente.

Sin red (`--sin-red`) corre solo BM25 y el azar, para CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import yaml
from latam_tecnologia.herramientas.conocimiento import (
    IDIOMAS,
    RUTA_ARTICULOS,
    RUTA_CONFIG,
    RUTA_VECTORES,
    Articulo,
    RecuperadorLexico,
    cargar_articulos,
    coseno,
)

from latam_ia.registro.cargador import RAIZ_IA

SEMILLA = 202616737
RUTA_CONSULTAS = RAIZ_IA / "evaluacion" / "recuperacion" / "consultas.yaml"
DIR_REPORTES = RAIZ_IA / "evaluacion" / "reportes"
MODELO = "gemini-embedding-001"
DIMENSION = 768
COSTO_CITA_FALSA, COSTO_SIN_RESPUESTA = 5.0, 1.0  # citar lo que no es pesa cinco veces abstenerse
MARGENES = (0.0, 0.01, 0.02, 0.03, 0.05)
REPLICAS = 2000

Consulta = dict[str, Any]
Puntajes = dict[str, list[float]]  # pregunta -> puntaje por artículo, en el orden de la base


def cargar_consultas(ruta: Path = RUTA_CONSULTAS) -> list[Consulta]:
    datos = cast(dict[str, Any], yaml.safe_load(ruta.read_text(encoding="utf-8")))
    return cast(list[Consulta], datos["consultas"])


def partir(consultas: Sequence[Consulta], semilla: int = SEMILLA) -> tuple[list[Consulta], list[Consulta]]:
    """Mitad a validación y mitad a prueba dentro de cada artículo (y de las que no tienen artículo)."""
    grupos: dict[str, list[Consulta]] = defaultdict(list)
    for c in consultas:
        grupos[str(c["articulo"])].append(c)
    azar = random.Random(semilla)
    validacion: list[Consulta] = []
    prueba: list[Consulta] = []
    for clave in sorted(grupos):
        grupo = sorted(grupos[clave], key=lambda c: c["q"])
        azar.shuffle(grupo)
        corte = len(grupo) // 2
        validacion += grupo[:corte]
        prueba += grupo[corte:]
    return validacion, prueba


def incrustador(tarea: str) -> Any:
    from google import genai
    from google.genai import types

    cliente = genai.Client(vertexai=True, project=os.environ["LATAM_GCP_PROJECT"], location="global")
    config = types.EmbedContentConfig(task_type=tarea, output_dimensionality=DIMENSION)

    def incrustar(textos: Sequence[str]) -> list[list[float]]:
        salida: list[list[float]] = []
        for i in range(0, len(textos), 20):
            lote = list(textos[i : i + 20])
            for intento in range(3):  # reintentos acotados ante cuota o error transitorio
                try:
                    r = cliente.models.embed_content(model=MODELO, contents=cast(Any, lote), config=config)
                    salida += [list(e.values or []) for e in (r.embeddings or [])]
                    break
                except Exception:
                    if intento == 2:
                        raise
                    time.sleep(5 * (intento + 1))
        return salida

    return incrustar


def ordenar(puntajes: Sequence[float]) -> list[int]:
    return sorted(range(len(puntajes)), key=lambda i: -puntajes[i])


def calidad_del_orden(consultas: Sequence[Consulta], p: Puntajes, ids: Sequence[str]) -> dict[str, float]:
    """Sin umbral, solo preguntas con artículo: ¿qué tan arriba queda el relevante?"""
    r1 = r3 = mrr = 0.0
    con = [c for c in consultas if c["articulo"]]
    for c in con:
        puesto = [ids[i] for i in ordenar(p[c["q"]])].index(c["articulo"]) + 1
        r1 += puesto == 1
        r3 += puesto <= 3
        mrr += 1 / puesto
    n = max(1, len(con))
    return {"n": len(con), "recall_1": r1 / n, "recall_3": r3 / n, "mrr": mrr / n}


def decidir(
    puntajes: Sequence[float], ids: Sequence[str], umbral: float, margen: float, k: int = 2
) -> list[str]:
    orden = ordenar(puntajes)
    if puntajes[orden[0]] < umbral or puntajes[orden[0]] <= 0:
        return []
    mejor = puntajes[orden[0]]
    return [ids[i] for i in orden if puntajes[i] >= umbral and mejor - puntajes[i] <= margen][:k]


def resultado(c: Consulta, citados: Sequence[str]) -> str:
    if not c["articulo"]:
        return "abstencion_correcta" if not citados else "cita_falsa"
    if not citados:
        return "sin_respuesta"
    return "correcta" if c["articulo"] in citados else "cita_equivocada"


def decisiones(
    consultas: Sequence[Consulta], p: Puntajes, ids: Sequence[str], umbral: float, margen: float
) -> dict[str, Any]:
    cuenta: dict[str, int] = defaultdict(int)
    citas = 0
    for c in consultas:
        citados = decidir(p[c["q"]], ids, umbral, margen)
        cuenta[resultado(c, citados)] += 1
        citas += len(citados)
    n = len(consultas)
    malas = cuenta["cita_falsa"] + cuenta["cita_equivocada"]
    return {
        "n": n,
        **{
            k: cuenta[k]
            for k in ("correcta", "abstencion_correcta", "sin_respuesta", "cita_equivocada", "cita_falsa")
        },
        "acierto": (cuenta["correcta"] + cuenta["abstencion_correcta"]) / n,
        "costo_medio": (COSTO_CITA_FALSA * malas + COSTO_SIN_RESPUESTA * cuenta["sin_respuesta"]) / n,
        "articulos_por_respuesta": citas
        / max(1, n - cuenta["sin_respuesta"] - cuenta["abstencion_correcta"]),
    }


def elegir(consultas: Sequence[Consulta], p: Puntajes, ids: Sequence[str]) -> tuple[float, float]:
    """Umbral y margen de menor costo en validación; ante empate, el umbral más alto y el margen menor."""
    valores = sorted({max(v) for v in p.values()})
    candidatos = [0.0] + [(a + b) / 2 for a, b in zip(valores, valores[1:], strict=False)]
    mejor: tuple[float, float, float] | None = None
    for margen in MARGENES:
        for umbral in candidatos:
            costo = decisiones(consultas, p, ids, umbral, margen)["costo_medio"]
            if (
                mejor is None
                or costo < mejor[0] - 1e-12
                or (abs(costo - mejor[0]) <= 1e-12 and umbral > mejor[1] and margen <= mejor[2])
            ):
                mejor = (costo, umbral, margen)
    assert mejor is not None
    return mejor[1], mejor[2]


def intervalo(valores: Sequence[float], semilla: int = SEMILLA) -> tuple[float, float]:
    azar = random.Random(semilla)
    n = len(valores)
    medias = sorted(sum(azar.choices(valores, k=n)) / n for _ in range(REPLICAS))
    return medias[int(0.025 * REPLICAS)], medias[int(0.975 * REPLICAS) - 1]


def aciertos(
    consultas: Sequence[Consulta], p: Puntajes, ids: Sequence[str], umbral: float, margen: float
) -> list[float]:
    return [
        float(resultado(c, decidir(p[c["q"]], ids, umbral, margen)) in ("correcta", "abstencion_correcta"))
        for c in consultas
    ]


def evaluar_sistema(
    nombre: str, p: Puntajes, validacion: Sequence[Consulta], prueba: Sequence[Consulta], ids: Sequence[str]
) -> dict[str, Any]:
    umbral, margen = elegir(validacion, p, ids)
    en_prueba = decisiones(prueba, p, ids, umbral, margen)
    por_idioma = {
        i: decisiones([c for c in prueba if c["idioma"] == i], p, ids, umbral, margen) for i in IDIOMAS
    }
    errores = [
        {"q": c["q"], "esperado": c["articulo"], "citado": decidir(p[c["q"]], ids, umbral, margen)}
        for c in prueba
        if resultado(c, decidir(p[c["q"]], ids, umbral, margen)) not in ("correcta", "abstencion_correcta")
    ]
    return {
        "sistema": nombre,
        "umbral": umbral,
        "margen": margen,
        "validacion": decisiones(validacion, p, ids, umbral, margen),
        "prueba": en_prueba,
        "prueba_ic95_acierto": intervalo(aciertos(prueba, p, ids, umbral, margen)),
        "orden_prueba": calidad_del_orden(prueba, p, ids),
        "por_idioma": por_idioma,
        "errores_prueba": errores,
    }


def puntajes_azar(consultas: Sequence[Consulta], n: int) -> Puntajes:
    azar = random.Random(SEMILLA)
    return {c["q"]: [azar.random() for _ in range(n)] for c in consultas}


def puntajes_lexicos(consultas: Sequence[Consulta], articulos: Sequence[Articulo]) -> Puntajes:
    lexico = RecuperadorLexico(articulos)
    return {c["q"]: lexico.puntajes(c["q"]) for c in consultas}


def tabla(resultados: Sequence[dict[str, Any]]) -> str:
    columnas = [
        "Sistema",
        "Umbral",
        "Acierto en prueba (IC95)",
        "Correctas",
        "Abstención correcta",
        "Sin respuesta",
        "Cita equivocada",
        "Cita falsa",
        "Costo medio",
        "Recall@1",
        "Recall@3",
        "MRR",
    ]
    filas = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    for r in resultados:
        d, o, (lo, hi) = r["prueba"], r["orden_prueba"], r["prueba_ic95_acierto"]
        celdas = [
            r["sistema"],
            f"{r['umbral']:.3f}",
            f"{d['acierto']:.3f} [{lo:.3f}; {hi:.3f}]",
            *(str(d[c]) for c in ("correcta", "abstencion_correcta", "sin_respuesta", "cita_equivocada")),
            str(d["cita_falsa"]),
            f"{d['costo_medio']:.3f}",
            *(f"{o[c]:.3f}" for c in ("recall_1", "recall_3", "mrr")),
        ]
        filas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(filas) + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="latam_ia.recuperacion")
    p.add_argument("--sin-red", action="store_true", help="solo BM25 y azar (sin Vertex)")
    p.add_argument("--escribir", action="store_true", help="guarda vectores.json y recuperacion.yaml")
    p.add_argument("--salida", type=Path, default=DIR_REPORTES)
    args = p.parse_args(argv)
    cast(Any, sys.stdout).reconfigure(encoding="utf-8")

    articulos = cargar_articulos()
    ids = [a.id for a in articulos]
    consultas = cargar_consultas()
    validacion, prueba = partir(consultas)
    todas = validacion + prueba
    resultados = [
        evaluar_sistema("azar", puntajes_azar(todas, len(ids)), validacion, prueba, ids),
        evaluar_sistema("bm25", puntajes_lexicos(todas, articulos), validacion, prueba, ids),
    ]
    vectores: dict[str, dict[str, list[float]]] = {}
    if not args.sin_red:
        doc = incrustador("RETRIEVAL_DOCUMENT")
        planos = doc([a.textos[i] for a in articulos for i in IDIOMAS])
        for n, a in enumerate(articulos):
            vectores[a.id] = {i: planos[n * len(IDIOMAS) + j] for j, i in enumerate(IDIOMAS)}
        vq = incrustador("RETRIEVAL_QUERY")([c["q"] for c in todas])
        pv: Puntajes = {
            c["q"]: [max(coseno(v, vectores[a.id][i]) for i in IDIOMAS) for a in articulos]
            for c, v in zip(todas, vq, strict=True)
        }
        resultados.append(evaluar_sistema(f"vectorial ({MODELO})", pv, validacion, prueba, ids))
    huella = hashlib.sha256(RUTA_ARTICULOS.read_bytes()).hexdigest()
    reporte = {
        "semilla": SEMILLA,
        "articulos": len(ids),
        "huella_articulos": huella,
        "consultas": {"total": len(consultas), "validacion": len(validacion), "prueba": len(prueba)},
        "costos": {"cita_falsa_o_equivocada": COSTO_CITA_FALSA, "sin_respuesta": COSTO_SIN_RESPUESTA},
        "resultados": resultados,
    }
    args.salida.mkdir(parents=True, exist_ok=True)
    nombre = "recuperacion_sin_red.json" if args.sin_red else "recuperacion.json"
    (args.salida / nombre).write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(tabla(resultados))
    if args.escribir and vectores:
        v = resultados[-1]
        manifiesto = {"modelo": MODELO, "dimension": DIMENSION, "huella_articulos": huella}
        compactos = {a: {i: [round(x, 5) for x in v] for i, v in d.items()} for a, d in vectores.items()}
        RUTA_VECTORES.write_text(
            json.dumps({"manifiesto": manifiesto, "vectores": compactos}, separators=(",", ":")),
            encoding="utf-8",
        )
        lex = resultados[1]
        config = {
            "modelo": MODELO,
            "dimension": DIMENSION,
            "umbral": round(v["umbral"], 4),
            "margen": v["margen"],
            "k": 2,
            "respaldo_lexico": {"umbral": round(lex["umbral"], 4)},
            "elegido_en": "validación de ia/evaluacion/recuperacion/consultas.yaml (semilla 202616737)",
            "huella_articulos": huella,
        }
        RUTA_CONFIG.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"Escritos {RUTA_VECTORES.name} y {RUTA_CONFIG.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
