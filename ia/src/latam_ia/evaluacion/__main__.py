"""`python -m latam_ia.evaluacion [--k 3] [--filtro N0] [--salida ruta]`: corre el arnés y el reporte."""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path
from typing import cast

from latam_tecnologia.canales.geap import VARIABLE_PROVEEDOR

from latam_ia.evaluacion.esquema import DIR_EVALUACION, cargar_escenarios, cargar_retenidos
from latam_ia.evaluacion.reporte import (
    K_POR_DEFECTO,
    a_dict,
    a_markdown,
    ejecutar_suite,
    escribir,
    escribir_trazas,
    etiqueta_agente,
)
from latam_ia.evaluacion.retenido import (
    K_RETENIDO,
    SISTEMAS,
    cargar_crudos,
    correr_sistema,
    escribir_casos_equidad,
    escribir_crudo,
    tablas_markdown,
    validar_etiquetas,
)


def _retenido(args: argparse.Namespace) -> int:
    """Corre un sistema sobre el conjunto retenido y guarda el JSON crudo (fuera de git)."""
    cast(io.TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")
    salida: Path = args.salida
    if args.tablas:
        crudos = cargar_crudos(salida)
        print(tablas_markdown(crudos) if crudos else "no hay JSON crudos de retenido en " + str(salida))
        for datos in crudos.values():
            escribir_casos_equidad(datos, cargar_retenidos(), salida)
        return 0 if crudos else 2
    ids = {i for i in args.ids.split(",") if i}
    escenarios = [e for e in cargar_retenidos() if e.id.startswith(args.filtro) and (not ids or e.id in ids)]
    problemas = validar_etiquetas(cargar_retenidos())
    if problemas:
        print(chr(10).join(problemas))
        return 2
    geap = os.environ.get(VARIABLE_PROVEEDOR, "").lower() == "geap"
    sistema = args.sistema or ("propuesto" if geap else "referencia")
    simulador = args.simulador or ("llm" if geap else "guionado")
    if (sistema != "referencia" or simulador == "llm") and not geap:
        print("sin GEAP (LATAM_MODELO_PROVEEDOR=geap) solo corre la referencia con simulador guionado")
        return 2
    k = args.k if args.k != K_POR_DEFECTO else K_RETENIDO
    cola = sorted(escenarios, key=lambda e: e.id)
    cats = sorted({e.categoria for e in cola})
    por_cat = {c: [e for e in cola if e.categoria == c] for c in cats}
    orden = [
        por_cat[c][i] for i in range(max(map(len, por_cat.values()))) for c in cats if i < len(por_cat[c])
    ]
    datos = correr_sistema(
        sistema, orden, k, simulador=simulador, max_llamadas=args.max_llamadas, avisar=print
    )
    ruta = escribir_crudo(datos, salida)
    print(f"Escrito: {ruta} y {escribir_casos_equidad(datos, escenarios, salida)}")
    print(tablas_markdown({sistema: datos}))
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="latam_ia.evaluacion")
    p.add_argument("--k", type=int, default=K_POR_DEFECTO, help="corridas por escenario (R-GOB-58: 3)")
    p.add_argument("--filtro", default="", help="solo escenarios cuyo id empiece por este texto")
    p.add_argument("--salida", type=Path, default=DIR_EVALUACION / "reportes")
    p.add_argument("--ids", default="", help="ids de escenario separados por coma (además del filtro)")
    p.add_argument(
        "--intercalar", action="store_true", help="alterna categorías para que un tope reparta el recorte"
    )
    p.add_argument("--max-llamadas", type=int, default=None, help="tope de llamadas al modelo (GEAP)")
    p.add_argument(
        "--trazas", type=Path, default=None, help="escribe las trazas completas (JSON, sin subir a git)"
    )
    p.add_argument("--etiqueta", default="ultimo", help="nombre base de los archivos del reporte")
    p.add_argument(
        "--retenido", action="store_true", help="evaluación final sobre el conjunto retenido (IA-5.4)"
    )
    p.add_argument(
        "--sistema",
        choices=SISTEMAS,
        default=None,
        help="con --retenido: propuesto, referencia o sin_herramientas",
    )
    p.add_argument(
        "--simulador", choices=("llm", "guionado"), default=None, help="con --retenido: cliente simulado"
    )
    p.add_argument(
        "--tablas", action="store_true", help="con --retenido: imprime las tablas desde los JSON crudos"
    )
    args = p.parse_args(argv)
    if args.retenido:
        return _retenido(args)
    cast(io.TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")
    ids = {i for i in args.ids.split(",") if i}
    escenarios = [e for e in cargar_escenarios() if e.id.startswith(args.filtro) and (not ids or e.id in ids)]
    if args.intercalar:
        cats = sorted({e.categoria for e in escenarios})
        cola = {c: [e for e in escenarios if e.categoria == c] for c in cats}
        escenarios = [
            cola[c][i] for i in range(max(map(len, cola.values()))) for c in cats if i < len(cola[c])
        ]
    if not escenarios:
        print("ningún escenario coincide con el filtro")
        return 2
    resultados = ejecutar_suite(escenarios, args.k, max_llamadas=args.max_llamadas)
    datos = a_dict(resultados, args.k, etiqueta_agente(escenarios))
    ruta_json, ruta_md = escribir(datos, args.salida, args.etiqueta)
    if args.trazas:
        escribir_trazas(resultados, args.trazas)
    print(a_markdown(datos))
    print(f"Escrito: {ruta_json} y {ruta_md}")
    a = datos["agregado"]
    if len(resultados) < len(escenarios):
        print(f"Tope de llamadas: corrieron {len(resultados)} de {len(escenarios)} escenarios")
    return 0 if a["escenarios_que_pasan"] + a["fallas_conocidas"] == a["escenarios"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
