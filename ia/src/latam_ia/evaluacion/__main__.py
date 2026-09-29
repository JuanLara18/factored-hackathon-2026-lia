"""`python -m latam_ia.evaluacion [--k 3] [--filtro N0] [--salida ruta]`: corre el arnés y el reporte."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import cast

from latam_ia.evaluacion.esquema import DIR_EVALUACION, cargar_escenarios
from latam_ia.evaluacion.reporte import (
    K_POR_DEFECTO,
    a_dict,
    a_markdown,
    ejecutar_suite,
    escribir,
    escribir_trazas,
    etiqueta_agente,
)


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
    args = p.parse_args(argv)
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
