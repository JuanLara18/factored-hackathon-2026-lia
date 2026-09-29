"""Puente al Gen AI evaluation service de GEAP (D-32, fase 3): trazas del arnés a un dataset de evaluación.

Cada corrida se exporta como un caso con la conversación (`prompt`), las respuestas del agente (`response`) y
la trayectoria de herramientas con efecto, prevista y observada. Las métricas de trayectoria (exactitud y
orden) las calcula el servicio; una métrica de rúbrica con un juez de Gemini valora el tono y la claridad en
español. El JSON crudo queda fuera de git; el resumen sin datos personales va al reporte `geap_<fecha>.md`.

Usa el SDK `vertexai.preview.evaluation` porque el cliente nuevo (`vertexai.Client().evals`) todavía no trae
las métricas de trayectoria (v1.148: "Add trajectory metrics once they are supported").
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from latam_ia.evaluacion.traza import EFECTOS

RUBRICA_TONO = (
    "Valora si la respuesta del asistente bancario es clara y usa un tono cordial y sobrio en español: "
    "frases cortas, sin jerga, sin promesas, sin exclamaciones ni emojis, con el trato (usted o vos) que usa "
    "el cliente, y con un cierre que diga qué se hizo, qué no y qué sigue cuando corresponde."
)
ESCALA_TONO = {
    "5": "Claro, sobrio y cordial, con el trato correcto.",
    "4": "Claro y cordial, con un detalle menor de tono o de trato.",
    "3": "Se entiende, pero es seco, largo o mezcla el trato.",
    "2": "Confuso o con un tono inadecuado.",
    "1": "Ininteligible, en otro idioma o con un tono inaceptable.",
}


def casos_desde_trazas(trazas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Una fila por corrida: conversación, respuestas y trayectorias (herramientas con efecto)."""
    filas: list[dict[str, Any]] = []
    for esc in trazas:
        referencia: list[dict[str, Any]] = [
            {"tool_name": n, "tool_input": {}} for n in esc["esperado_herramientas"]
        ]
        for i, c in enumerate(esc["corridas"]):
            turnos = c["turnos"]
            conversacion = "\n".join(f"{t['rol']}: {t['texto']}" for t in turnos)
            respuestas = [t["texto"] for t in turnos if t["rol"] == "agente"]
            predicha: list[dict[str, Any]] = [
                {"tool_name": h["nombre"], "tool_input": {}}
                for h in c["herramientas"]
                if h["nombre"] in EFECTOS
            ]
            filas.append(
                {
                    "escenario": esc["escenario"],
                    "categoria": esc["categoria"],
                    "corrida": i,
                    "prompt": conversacion,
                    "response": "\n".join(respuestas) or "(sin respuesta)",
                    "predicted_trajectory": predicha,
                    "reference_trajectory": referencia,
                    "estado_arnes": c["estado"],
                }
            )
    return filas


def evaluar(filas: list[dict[str, Any]], proyecto: str, ubicacion: str, juez: str | None) -> dict[str, Any]:
    import pandas as pd  # pyright: ignore[reportMissingTypeStubs]
    import vertexai
    from vertexai.preview.evaluation import (
        EvalTask,
        PointwiseMetric,
        PointwiseMetricPromptTemplate,
    )

    vertexai.init(project=proyecto, location=ubicacion)
    df = pd.DataFrame(
        {
            "prompt": [f["prompt"] for f in filas],
            "response": [f["response"] for f in filas],
            "predicted_trajectory": [f["predicted_trajectory"] for f in filas],
            "reference_trajectory": [f["reference_trajectory"] for f in filas],
        }
    )
    tono = PointwiseMetric(
        metric="tono_y_claridad_es",
        metric_prompt_template=PointwiseMetricPromptTemplate(
            criteria={"tono_y_claridad": RUBRICA_TONO},
            rating_rubric=ESCALA_TONO,
            input_variables=["prompt", "response"],
        ),
    )
    metricas: list[Any] = ["trajectory_exact_match", "trajectory_in_order_match", tono]
    tarea = EvalTask(dataset=df, metrics=metricas)
    kwargs: dict[str, Any] = {}
    if juez:
        from vertexai.preview.evaluation import AutoraterConfig

        kwargs["autorater_config"] = AutoraterConfig(autorater_model=juez)
    r = tarea.evaluate(**kwargs)
    tabla = cast(Any, r.metrics_table)
    return {"resumen": {k: float(v) for k, v in r.summary_metrics.items()}, "filas": tabla.to_dict("records")}


def _nombres(trayectoria: list[dict[str, Any]]) -> list[str]:
    return [str(t["tool_name"]) for t in trayectoria]


def puntaje_local(predicha: list[dict[str, Any]], referencia: list[dict[str, Any]]) -> tuple[float, float]:
    """Exacta y en orden como define el servicio, para trayectorias vacías (que el servicio rechaza)."""
    p, r = _nombres(predicha), _nombres(referencia)
    it = iter(p)
    return float(p == r), float(all(n in it for n in r))


def puntajes(f: dict[str, Any], fila: dict[str, Any]) -> tuple[float, float, bool]:
    """(exacta, en orden, es_local): del servicio si lo dio; si no, el cálculo local."""
    e, o = fila.get("trajectory_exact_match/score"), fila.get("trajectory_in_order_match/score")
    if e is not None and o is not None and e == e and o == o:
        return float(e), float(o), False
    le, lo = puntaje_local(f["predicted_trajectory"], f["reference_trajectory"])
    return le, lo, True


def _tono(fila: dict[str, Any]) -> str:
    valor = fila.get("tono_y_claridad_es/score")
    return "n/d" if valor is None or valor != valor else f"{float(valor):.0f}"


def resumen_markdown(filas: list[dict[str, Any]], resultado: dict[str, Any], fecha: str, extra: str) -> str:
    lineas = [
        f"# Evaluación en GEAP ({fecha})",
        "",
        extra,
        "",
        "Gen AI evaluation service sobre las trazas de la última corrida: trayectoria de herramientas",
        "con efecto (solo nombres, en orden) contra la esperada, y una rúbrica de tono y claridad.",
        "",
        "## Métricas del servicio",
        "",
        "| Métrica | Media |",
        "|---|---|",
        *[
            f"| {k} | {v:.3f} |"
            for k, v in sorted(resultado["resumen"].items())
            if not k.endswith("/std") and k != "row_count"
        ],
        "",
        "## Por escenario",
        "",
        "| Escenario | Arnés | Exacta | En orden | Tono (1 a 5) |",
        "|---|---|---|---|---|",
    ]
    todos = [puntajes(f, r) for f, r in zip(filas, resultado["filas"], strict=False)]
    for f, r, (e, o, local) in zip(filas, resultado["filas"], todos, strict=False):
        marca = "*" if local else ""
        lineas.append(
            f"| {f['escenario']} | {f['estado_arnes']} | {e:.0f}{marca} | {o:.0f}{marca} | {_tono(r)} |"
        )
    n = len(todos)
    lineas += [
        "",
        f"Sobre las {n} corridas: trayectoria exacta {sum(t[0] for t in todos) / n:.1%}, en orden "
        f"{sum(t[1] for t in todos) / n:.1%}. El servicio rechaza las trayectorias vacías (campo "
        f"requerido): en {sum(t[2] for t in todos)} corridas (con *) el puntaje es local, con la misma "
        "definición.",
    ]
    return "\n".join(lineas) + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="latam_ia.evaluacion.servicio_evaluacion")
    p.add_argument("--trazas", type=Path, required=True)
    p.add_argument("--dataset", type=Path, required=True, help="dataset exportado (JSON, fuera de git)")
    p.add_argument(
        "--crudo", type=Path, required=True, help="resultado crudo del servicio (JSON, fuera de git)"
    )
    p.add_argument("--reporte", type=Path, required=True)
    p.add_argument("--fecha", required=True)
    p.add_argument("--nota", default="")
    p.add_argument("--ubicacion", default="us-central1")
    p.add_argument("--juez", default=None)
    p.add_argument("--reusar", action="store_true", help="no llama al servicio: rehace el reporte del crudo")
    args = p.parse_args(argv)
    trazas = cast(list[dict[str, Any]], json.loads(args.trazas.read_text(encoding="utf-8")))
    filas = casos_desde_trazas(trazas)
    args.dataset.write_text(json.dumps(filas, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    try:
        if args.reusar:
            resultado = cast(dict[str, Any], json.loads(args.crudo.read_text(encoding="utf-8")))
        else:
            resultado = evaluar(filas, os.environ["LATAM_GCP_PROJECT"], args.ubicacion, args.juez)
    except Exception as error:
        print(f"El servicio falló: {type(error).__name__}: {error}")
        return 1
    args.crudo.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False, default=str), encoding="utf-8", newline="\n"
    )
    args.reporte.write_text(
        resumen_markdown(filas, resultado, args.fecha, args.nota), encoding="utf-8", newline="\n"
    )
    print(json.dumps(resultado["resumen"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
