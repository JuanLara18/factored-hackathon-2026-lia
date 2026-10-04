"""Línea base de equidad del servicio histórico (quejas y contactos) por segmentos autorizados.

`uv run python -m latam_datos.analisis.equidad` ejecuta `datos/analisis/equidad.sql` (solo agregados, 20 casos
por celda como mínimo), compara cada grupo con el mejor de su dimensión con las reglas de R-GOB-48 y
revisa si la brecha persiste al ajustar por mezcla (canal, tipo, categoría, monto, horario).
Con `--desde-cache` no consulta.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from latam_gobierno.equidad import MIN_N, UMBRAL_PP, UMBRAL_RAZON_ALTA, Sentido, comparar, wilson

from latam_datos.analisis import consultas

K_ANONIMATO = 20
UMBRAL_CSAT = 0.25
DIMS = ("pais", "segmento", "canal", "acento", "franja_edad", "banda_edad", "genero")
SQL = consultas.RAIZ / "datos" / "analisis" / "equidad.sql"
CIFRAS = consultas.RAIZ / "presidencia" / "reporte" / "figuras" / "equidad_cifras.json"
RAIZ_FIGURAS = consultas.RAIZ / "presidencia" / "reporte" / "figuras"
Fila = dict[str, Any]

# consulta -> (columna observada, columna esperada, etiqueta, sentido)
BINARIAS: dict[str, list[tuple[str, str, str, Sentido]]] = {
    "equidad_quejas": [
        ("resp", "e_resp", "con primera respuesta", "mayor_mejor"),
        ("sla", "e_sla", "incumple SLA", "menor_mejor"),
        ("res", "e_res", "resuelta", "mayor_mejor"),
        ("esc", "e_esc", "escalada", "menor_mejor"),
    ],
    "equidad_contactos": [
        ("res", "e_res", "resuelto", "mayor_mejor"),
        ("esc", "e_esc", "escalado", "menor_mejor"),
        ("seg", "e_seg", "requiere seguimiento", "menor_mejor"),
    ],
}
# consulta -> (n, mediana, etiqueta) del tiempo
TIEMPOS = {
    "equidad_quejas": ("n_h", "h_p50", "horas a primera respuesta (mediana)"),
    "equidad_contactos": ("n_espera", "espera_p50", "espera en segundos (mediana)"),
}


def ejecutar(proyecto: str, dataset: str, ubicacion: str = "US") -> dict[str, list[Fila]]:
    consultas_sql = consultas.parsear_consultas(SQL.read_text(encoding="utf-8"))
    from google.cloud import bigquery

    cliente = bigquery.Client(project=proyecto, location=ubicacion)
    salida: dict[str, list[Fila]] = {}
    for nombre, sql in consultas_sql.items():
        filas = list(cliente.query(sql.replace("{ds}", f"{proyecto}.{dataset}")).result())
        salida[nombre] = [{k: consultas.a_json(v) for k, v in cast(Any, f).items()} for f in filas]
        print(f"{nombre}: {len(salida[nombre])} filas")
    return salida


def verificar_k(resultados: dict[str, list[Fila]]) -> None:
    """Ninguna celda agregada sale con menos de `K_ANONIMATO` casos."""
    for nombre, filas in resultados.items():
        malas = [f for f in filas if f["n"] < K_ANONIMATO]
        if malas:
            raise ValueError(f"{nombre}: {len(malas)} celdas con n menor que {K_ANONIMATO}")


def _varianza(f: Fila) -> tuple[float, float, int] | None:
    n = f.get("n_csat")
    if not n or n < K_ANONIMATO:
        return None
    media = f["s_csat"] / n
    var = max((f["ss_csat"] - f["s_csat"] ** 2 / n) / (n - 1), 0.0)
    return media, var, int(n)


def _binarias(consulta: str, filas: Sequence[Fila]) -> list[Fila]:
    salida: list[Fila] = []
    for ambito in sorted({f["ambito"] for f in filas}):
        del_ambito = [f for f in filas if f["ambito"] == ambito]
        for col, esp, etiqueta, sentido in BINARIAS[consulta]:
            total_n = sum(f["n"] for f in del_ambito if f["dimension"] == "pais")
            total_k = sum(f[col] for f in del_ambito if f["dimension"] == "pais")
            tasa_global = total_k / total_n
            for dim in DIMS:
                grupos = [f for f in del_ambito if f["dimension"] == dim]
                aptos = [f for f in grupos if f["n"] >= MIN_N]
                if not aptos:
                    continue
                elegir = max if sentido == "mayor_mejor" else min
                ref = elegir(aptos, key=lambda f: f[col] / f["n"])

                def ajustado(f: Fila, tg: float = tasa_global, c: str = col, e: str = esp) -> int:
                    return round(f[c] * tg * f["n"] / f[e]) if f[e] else 0

                ref_aj = ajustado(ref)
                for f in sorted(grupos, key=lambda x: x["grupo"]):
                    k, n = int(f[col]), int(f["n"])
                    lo, hi = wilson(k, n)
                    fila: Fila = {
                        "consulta": consulta,
                        "ambito": ambito,
                        "dimension": dim,
                        "grupo": f["grupo"],
                        "metrica": etiqueta,
                        "sentido": sentido,
                        "k": k,
                        "n": n,
                        "tasa": k / n,
                        "lo": lo,
                        "hi": hi,
                        "referencia": ref["grupo"],
                        "esperada": f[esp] / n,
                        "estado": "referencia",
                    }
                    if f is not ref:
                        if n < MIN_N:
                            fila["estado"] = "muestra_insuficiente"
                        else:
                            c = comparar(k, n, int(ref[col]), int(ref["n"]), sentido)
                            fila.update(dif=c.dif, dif_lo=c.dif_lo, dif_hi=c.dif_hi, razon=c.razon)
                            if dim == "canal":
                                # el canal ya es parte de la mezcla: ajustarlo lo anularía por construcción
                                fila["estado"] = "investigar_sin_ajuste" if c.investigar else "sin_disparidad"
                                if c.investigar:
                                    fila["alerta"] = "brecha_5pp" if abs(c.dif) >= UMBRAL_PP else "solo_razon"
                                salida.append(fila)
                                continue
                            ka = ajustado(f)
                            ca = comparar(ka, n, ref_aj, int(ref["n"]), sentido)
                            fila.update(
                                tasa_aj=ka / n, dif_aj=ca.dif, razon_aj=ca.razon, flag_aj=ca.investigar
                            )
                            if not c.investigar:
                                fila["estado"] = "sin_disparidad"
                            else:
                                fila["estado"] = (
                                    "persiste_tras_ajustar" if ca.investigar else "explicada_por_mezcla"
                                )
                                fila["alerta"] = "brecha_5pp" if abs(c.dif) >= UMBRAL_PP else "solo_razon"
                    salida.append(fila)
    return salida


def _tiempos(consulta: str, filas: Sequence[Fila]) -> list[Fila]:
    ncol, mcol, etiqueta = TIEMPOS[consulta]
    salida: list[Fila] = []
    for ambito in sorted({f["ambito"] for f in filas}):
        for dim in DIMS:
            grupos = [
                f for f in filas if f["ambito"] == ambito and f["dimension"] == dim and f[ncol] >= MIN_N
            ]
            if not grupos:
                continue
            mejor = min(grupos, key=lambda f: f[mcol])
            for f in sorted(grupos, key=lambda x: x["grupo"]):
                razon = f[mcol] / mejor[mcol] if mejor[mcol] else math.nan
                estado = (
                    "referencia"
                    if f is mejor
                    else ("investigar" if razon > UMBRAL_RAZON_ALTA else "sin_disparidad")
                )
                salida.append(
                    {
                        "consulta": consulta,
                        "ambito": ambito,
                        "dimension": dim,
                        "grupo": f["grupo"],
                        "metrica": etiqueta,
                        "n": int(f[ncol]),
                        "valor": f[mcol],
                        "referencia": mejor["grupo"],
                        "razon": razon,
                        "estado": estado,
                    }
                )
    return salida


def _csat(consulta: str, filas: Sequence[Fila]) -> list[Fila]:
    salida: list[Fila] = []
    for ambito in sorted({f["ambito"] for f in filas}):
        for dim in DIMS:
            grupos = [(f, _varianza(f)) for f in filas if f["ambito"] == ambito and f["dimension"] == dim]
            validos = [(f, v) for f, v in grupos if v and v[2] >= MIN_N]
            if len(validos) < 2:
                continue
            fm, vm = max(validos, key=lambda t: t[1][0])
            for f, v in sorted(validos, key=lambda t: t[0]["grupo"]):
                dif = v[0] - vm[0]
                se = math.sqrt(v[1] / v[2] + vm[1] / vm[2])
                if f is fm:
                    estado = "referencia"
                else:
                    estado = "investigar" if dif <= -UMBRAL_CSAT and dif + 1.96 * se < 0 else "sin_disparidad"
                salida.append(
                    {
                        "consulta": consulta,
                        "ambito": ambito,
                        "dimension": dim,
                        "grupo": f["grupo"],
                        "metrica": "CSAT medio",
                        "n": v[2],
                        "valor": v[0],
                        "referencia": fm["grupo"],
                        "dif": dif,
                        "dif_lo": dif - 1.96 * se,
                        "dif_hi": dif + 1.96 * se,
                        "estado": estado,
                    }
                )
    return salida


def calcular(resultados: dict[str, list[Fila]]) -> dict[str, list[Fila]]:
    """`binarias`, `tiempos` y `csat`: una fila por grupo y métrica, con estado frente al mejor grupo."""
    verificar_k(resultados)
    sal: dict[str, list[Fila]] = {"binarias": [], "tiempos": [], "csat": []}
    for consulta, filas in resultados.items():
        sal["binarias"] += _binarias(consulta, filas)
        sal["tiempos"] += _tiempos(consulta, filas)
        sal["csat"] += _csat(consulta, filas)
    return sal


def guardar(resultados: dict[str, list[Fila]], ruta: Path = CIFRAS) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def cargar(ruta: Path = CIFRAS) -> dict[str, list[Fila]]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m latam_datos.analisis.equidad", description=__doc__)
    ap.add_argument("--desde-cache", action="store_true", help="usa figuras/equidad_cifras.json")
    args = ap.parse_args(argv)
    if args.desde_cache:
        resultados = cargar()
    else:
        proyecto = os.environ.get("LATAM_GCP_PROJECT", "latam-bank-hackaton-2026")
        dataset = os.environ.get("LATAM_BQ_DATASET", "latam_bank")
        resultados = ejecutar(proyecto, dataset, os.environ.get("LATAM_GCP_LOCATION", "US"))
        verificar_k(resultados)
        guardar(resultados)
    m = calcular(resultados)
    from latam_datos.analisis import equidad_figuras

    hechas = equidad_figuras.generar(m, RAIZ_FIGURAS)
    (RAIZ_FIGURAS / "equidad_resumen.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(f"{len(hechas)} figuras; filas: " + ", ".join(f"{k}={len(v)}" for k, v in m.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
