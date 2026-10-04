# pyright: basic
"""Figuras de equidad (PNG, `presidencia/reporte/figuras/equidad_*`). Mismo estilo que `figuras.py`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from latam_datos.analisis.figuras import AZUL, GRIS, NARANJA, ROJO, estilo, guardar

Fila = dict[str, Any]
ORDEN = ("pais", "segmento", "canal", "acento", "franja_edad", "genero")
ROTULO = {
    "pais": "País", "segmento": "Segmento", "canal": "Canal", "acento": "Acento",
    "franja_edad": "Edad", "genero": "Género",
}  # fmt: skip


def _puntos(filas: list[Fila], ambito: str, metrica: str) -> list[Fila]:
    sel = [f for f in filas if f["ambito"] == ambito and f["metrica"] == metrica and f["dimension"] in ORDEN]
    return sorted(sel, key=lambda f: (ORDEN.index(f["dimension"]), f["grupo"]), reverse=True)


def _puntos_ic(m: dict[str, list[Fila]], ambito: str, metricas: list[str], ruta: Path, titulo: str) -> None:
    fig, ejes = plt.subplots(1, len(metricas), figsize=(4.2 * len(metricas), 7.2), sharey=True)
    for ax, metrica in zip(ejes, metricas, strict=True):
        pts = _puntos(m["binarias"], ambito, metrica)
        y = list(range(len(pts)))
        global_ = [f["tasa"] for f in pts if f["dimension"] == "pais"]
        for yi, f in zip(y, pts, strict=True):
            marcada = f["estado"] == "persiste_tras_ajustar" and f.get("alerta") == "brecha_5pp"
            color = ROJO if marcada else AZUL
            ax.plot([f["lo"], f["hi"]], [yi, yi], color=color, lw=2, alpha=0.8)
            ax.plot(f["tasa"], yi, "o", color=color, ms=5)
        if global_:
            ax.axvline(sum(global_) / len(global_), color=GRIS, lw=1, ls="--")
        ax.set_title(metrica)
        ax.set_xlabel("proporción, IC 95% de Wilson")
        ax.xaxis.set_major_formatter(lambda v, _: f"{100 * v:.0f}%")
        if ax is ejes[0]:
            ax.set_yticks(y, [f"{ROTULO[f['dimension']]}: {f['grupo']}" for f in pts], fontsize=8)
    fig.suptitle(titulo, x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout()
    guardar(fig, ruta)


def _brechas(m: dict[str, list[Fila]], ruta: Path) -> None:
    filas = [f for f in m["binarias"] if f["ambito"] == "disputa" and "dif_aj" in f]
    fig, ax = plt.subplots(figsize=(6.4, 6.2))
    for f in filas:
        marcada = f["estado"] != "sin_disparidad"
        ax.plot(
            100 * f["dif"], 100 * f["dif_aj"], "o", ms=5 if marcada else 4,
            color=ROJO if marcada else AZUL, alpha=0.9 if marcada else 0.45,
        )  # fmt: skip
    lim = max(8.0, 100 * max(abs(f["dif"]) for f in filas) + 1) if filas else 8.0
    ax.plot([-lim, lim], [-lim, lim], color=GRIS, lw=1)
    for v in (-5, 5):
        ax.axvline(v, color=NARANJA, lw=1, ls="--")
        ax.axhline(v, color=NARANJA, lw=1, ls="--")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("brecha frente al mejor grupo (puntos porcentuales)")
    ax.set_ylabel("brecha ajustada por mezcla (puntos porcentuales)")
    ax.set_title("Disputas: el ajuste por mezcla casi no mueve las brechas")
    ax.text(
        0.02, 0.97, "naranja: umbral de 5 puntos; rojo: marcada", transform=ax.transAxes, va="top", fontsize=8
    )
    fig.tight_layout()
    guardar(fig, ruta)


def generar(m: dict[str, list[Fila]], destino: Path) -> list[Path]:
    estilo()
    hechas = [
        destino / "equidad_01_disputas.png",
        destino / "equidad_02_brechas_ajuste.png",
        destino / "equidad_03_contactos.png",
    ]
    _puntos_ic(
        m, "disputa",
        ["con primera respuesta", "incumple SLA", "resuelta", "escalada"],
        hechas[0], "Quejas por cargo no reconocido: resultados por segmento autorizado",
    )  # fmt: skip
    _brechas(m, hechas[1])
    _puntos_ic(
        m, "transaccional", ["resuelto", "escalado", "requiere seguimiento"], hechas[2],
        "Contactos transaccionales: resultados por segmento autorizado",
    )  # fmt: skip
    return hechas
