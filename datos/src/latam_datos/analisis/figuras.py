# pyright: basic
"""Figuras del informe del problema (PNG). Estilo único, paleta de Okabe e Ito (segura para daltonismo)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AZUL, NARANJA, VERDE, ROJO, CELESTE, MORADO, GRIS = (
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#D55E00",
    "#56B4E9",
    "#CC79A7",
    "#6B7280",
)
SERIE = [AZUL, NARANJA, VERDE, CELESTE, MORADO, GRIS]
TINTA = "#1F2937"
NOMBRE_MOTIVO = {
    "Transaccional": "Transaccional",
    "Producto": "Producto",
    "Queja": "Queja",
    "Técnico": "Técnico",
    "Comercial": "Comercial",
    "Retención": "Retención",
}
DIAS = {1: "Dom", 2: "Lun", 3: "Mar", 4: "Mié", 5: "Jue", 6: "Vie", 7: "Sáb"}
CANAL = {
    "Phone": "Teléfono",
    "Email": "Correo",
    "App": "App",
    "WhatsApp": "WhatsApp",
    "Web Chat": "Chat web",
    "Web": "Web",
}
PAIS = {"MX": "México", "CO": "Colombia", "AR": "Argentina"}


def estilo() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.edgecolor": "#9CA3AF",
            "axes.labelcolor": TINTA,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#E5E7EB",
            "grid.linewidth": 0.8,
            "xtick.color": TINTA,
            "ytick.color": TINTA,
            "text.color": TINTA,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.dpi": 160,
            "savefig.bbox": "tight",
        }
    )


def guardar(fig: Any, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta)
    plt.close(fig)


def _fecha(k: str) -> date:
    return date.fromisoformat(k[:10])


def _etiquetas(ax: Any, barras: Any, textos: list[str], dx: float = 0.0) -> None:
    for b, t in zip(barras, textos, strict=True):
        ax.annotate(
            t,
            (b.get_width() + dx, b.get_y() + b.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
        )


def _pct(x: float) -> str:
    return f"{100 * x:.1f}".replace(".", ",") + "%"


def fig_motivos(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1.1, 1, 1.2]})
    total = m["total"]
    motivos = sorted(m["por_motivo"], key=lambda k: m["por_motivo"][k])
    b = ax[0].barh(motivos, [m["por_motivo"][k] / total * 100 for k in motivos], color=AZUL)
    _etiquetas(ax[0], b, [_pct(m["por_motivo"][k] / total) for k in motivos])
    ax[0].set_title("Motivo del contacto")
    ax[0].set_xlabel("% de 686.296 contactos")
    ax[0].set_xlim(0, 45)
    orden = ["Transaccional", "Producto", "Queja", "Técnico", "Comercial", "Retención"]
    for a, (clave, nombres, titulo) in zip(
        ax[1:],
        [
            ("motivo_x_pais", PAIS, "Mezcla por país del cliente"),
            ("motivo_x_canal", CANAL, "Mezcla por canal"),
        ],
        strict=True,
    ):
        datos = m[clave]
        filas = sorted(datos, key=lambda k: -sum(datos[k].values()))
        izq = [0.0] * len(filas)
        for i, mo in enumerate(orden):
            vals = [datos[f].get(mo, 0) / sum(datos[f].values()) * 100 for f in filas]
            a.barh([nombres[f] for f in filas], vals, left=izq, color=SERIE[i], label=mo)
            izq = [x + v for x, v in zip(izq, vals, strict=True)]
        a.invert_yaxis()
        a.set_title(titulo)
        a.set_xlabel("% de los contactos del grupo")
        a.set_xlim(0, 100)
    ax[2].legend(ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
    fig.suptitle(
        "Contactos al centro de atención por motivo, país y canal (2023 a 2026)",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_tendencia(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    meses = sorted(m["mes_total"])
    xs = [_fecha(k) for k in meses]
    ax[0].plot(xs, [m["mes_total"][k] for k in meses], color=AZUL, lw=2, label="Todos los motivos")
    ax[0].plot(
        xs,
        [m["mes_motivo"]["Transaccional"].get(k, 0) for k in meses],
        color=NARANJA,
        lw=1.8,
        label="Transaccional",
    )
    ax[0].set_ylim(0, None)
    ax[0].set_title("Contactos por mes")
    ax[0].legend(frameon=False)
    mq = sorted(m["disputa_mes"])
    ax[1].plot(
        [_fecha(k) for k in mq],
        [m["disputa_mes"][k] for k in mq],
        color=ROJO,
        lw=2,
        label="Cargo no reconocido",
    )
    ax[1].plot(
        [_fecha(k) for k in mq],
        [m["quejas_mes"][k] / 5 for k in mq],
        color=GRIS,
        lw=1.5,
        ls="--",
        label="Quejas totales dividido 5",
    )
    ax[1].set_ylim(0, None)
    ax[1].set_title("Quejas por mes")
    ax[1].legend(frameon=False)
    for a in ax:
        a.tick_params(axis="x", rotation=0)
    fig.suptitle("Tendencia mensual, meses completos de la ventana", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    guardar(fig, ruta)


def fig_estacionalidad(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4))
    dias = list(range(2, 8)) + [1]
    ax[0].bar(
        [DIAS[d] for d in dias], [m["por_dia"][d] / 1000 for d in dias], color=[AZUL] * 5 + [CELESTE] * 2
    )
    ax[0].set_ylabel("Miles de contactos")
    ax[0].set_title("Por día de la semana")
    horas = list(range(24))
    ax[1].bar(horas, [m["por_hora"][h] / 1000 for h in horas], color=AZUL)
    ax[1].set_xticks(range(0, 24, 3))
    ax[1].set_xlabel("Hora del día (hora de la marca de tiempo, sin zona declarada)")
    ax[1].set_ylabel("Miles de contactos")
    ax[1].set_ylim(0, max(m["por_hora"].values()) / 1000 * 1.25)
    ax[1].set_title("Por hora del día")
    fig.suptitle(
        "Estacionalidad de la demanda: cae a la mitad el fin de semana y no varía por hora",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_capacidad(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    bloques = ["Night", "Morning", "Afternoon"]
    nombres = ["00:00 a 07:59", "08:00 a 15:59", "16:00 a 23:59"]
    dem, cap = m["demanda_bloque"], m["capacidad_bloque"]
    td, tc = sum(dem.values()), sum(cap.values())
    x = range(3)
    ax[0].bar([i - 0.2 for i in x], [dem[b] / td * 100 for b in bloques], 0.4, color=AZUL, label="Demanda")
    ax[0].bar(
        [i + 0.2 for i in x],
        [cap[b] / tc * 100 for b in bloques],
        0.4,
        color=NARANJA,
        label="Agentes activos",
    )
    ax[0].set_xticks(list(x), nombres)
    ax[0].set_ylabel("% del total")
    ax[0].set_title("Demanda frente a agentes por franja")
    ax[0].legend(frameon=False)
    idx = m["indice_carga"]
    barras = ax[1].bar(nombres, [idx[b] for b in bloques], color=[ROJO, GRIS, GRIS])
    ax[1].axhline(1, color=TINTA, lw=1)
    for b, v in zip(barras, [idx[k] for k in bloques], strict=True):
        ax[1].annotate(
            f"{v:.2f}".replace(".", ","),
            (b.get_x() + b.get_width() / 2, v),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
        )
    ax[1].set_ylabel("Participación en demanda / participación en agentes")
    ax[1].set_title("Índice de carga (1 es equilibrio)")
    fig.suptitle(
        "La madrugada concentra un tercio de la demanda con un quinto de los agentes",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_resultados(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    orden = sorted(m["por_motivo_res"], key=lambda k: m["por_motivo_res"][k]["resuelto"])
    p = m["por_motivo_res"]
    series = [
        ("resuelto", "Resuelto en el contacto (%)", AZUL),
        ("seguimiento", "Requiere seguimiento (%)", NARANJA),
        ("dur_media", "Duración media (minutos)", VERDE),
    ]
    for a, (k, titulo, color) in zip(ax, series, strict=True):
        vals = [p[o][k] * (1 if k == "dur_media" else 100) / (60 if k == "dur_media" else 1) for o in orden]
        b = a.barh(orden, vals, color=color)
        _etiquetas(a, b, [f"{v:.1f}".replace(".", ",") for v in vals])
        a.set_title(titulo)
        a.set_xlim(0, max(vals) * 1.18)
    fig.suptitle(
        "Resultado del contacto por motivo (escalamiento cercano a 10% en todos)",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_csat(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    cm = m["csat_motivo"]
    orden = sorted(cm, key=lambda k: cm[k]["altos"])
    b = ax[0].barh(orden, [cm[k]["altos"] * 100 for k in orden], color=AZUL)
    _etiquetas(ax[0], b, [f"{_pct(cm[k]['altos'])}  (n={cm[k]['n']:,})".replace(",", ".") for k in orden])
    ax[0].set_xlim(0, 120)
    ax[0].set_title("CSAT de 3 o 4 sobre 4, por motivo")
    cc = m["csat_canal"]
    oc = sorted(cc, key=lambda k: cc[k]["altos"])
    b = ax[1].barh([CANAL.get(k, k) for k in oc], [cc[k]["altos"] * 100 for k in oc], color=CELESTE)
    _etiquetas(ax[1], b, [f"{_pct(cc[k]['altos'])}  (n={cc[k]['n']:,})".replace(",", ".") for k in oc])
    ax[1].set_xlim(0, 120)
    ax[1].set_title("CSAT de 3 o 4 sobre 4, por canal")
    fig.suptitle(
        "Satisfacción posterior al contacto: las quejas son el motivo peor valorado",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_quejas(m: dict[str, Any], ruta: Path) -> None:
    q = m["quejas"]
    orden = sorted(q, key=lambda k: (k != "Cargo no reconocido", k))
    colores = [ROJO if k == "Cargo no reconocido" else GRIS for k in orden]
    campos = [
        ("h_resp_p50", "Horas a la primera respuesta (mediana)", 1.0),
        ("sla", "SLA incumplido (%)", 100.0),
        ("cierre", "Cerradas o resueltas (%)", 100.0),
        ("dias_res_p50", "Días a la resolución (mediana)", 1.0),
    ]
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.4), sharey=True)
    for a, (k, titulo, esc) in zip(ax, campos, strict=True):
        if k == "sla":
            vals = [q[o]["sla_incumplido"] / q[o]["n"] * esc for o in orden]
        elif k == "cierre":
            vals = [q[o]["cerradas"] / q[o]["n"] * esc for o in orden]
        else:
            vals = [q[o][k] * esc for o in orden]
        b = a.barh(orden, vals, color=colores)
        _etiquetas(a, b, [f"{v:.1f}".replace(".", ",") for v in vals])
        a.set_title(titulo, fontsize=10)
        a.set_xlim(0, max(vals) * 1.2)
        a.invert_yaxis()
    fig.suptitle(
        "Línea base de quejas: el cargo no reconocido se atiende como las demás, y todas tardan",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_fraude(m: dict[str, Any], ruta: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    meses = sorted(m["fraude_mes"])
    tasa = [m["fraude_mes"][k] / m["tx_mes"][k] * 10000 for k in meses]
    ax[0].plot([_fecha(k) for k in meses], tasa, color=ROJO, lw=2)
    ax[0].set_ylim(0, max(tasa) * 1.3)
    ax[0].set_title("Transacciones con is_fraud por cada 10.000")
    est = m["fraude_estado"]
    nombres = {
        "Approved": "Aprobada",
        "Declined": "Rechazada",
        "Pending": "Pendiente",
        "Reversed": "Revertida",
    }
    ks = list(est)
    vals = [est[k][1] / est[k][0] * 10000 for k in ks]
    b = ax[1].bar([nombres.get(k, k) for k in ks], vals, color=GRIS)
    for rect, v in zip(b, vals, strict=True):
        ax[1].annotate(
            f"{v:.1f}".replace(".", ","),
            (rect.get_x() + rect.get_width() / 2, v),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
        )
    ax[1].set_ylim(0, max(vals) * 1.25)
    ax[1].set_title("Por estado de la transacción, por cada 10.000")
    fig.suptitle(
        "Prevalencia de fraude marcado: baja y sin estructura por mes ni por estado",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    guardar(fig, ruta)


def fig_calidad(m: dict[str, Any], ruta: Path) -> None:
    c = m["cal"]

    def fr(control: str, valor: str, otro: str) -> float:
        a, b = c.get((control, valor), 0), c.get((control, otro), 0)
        return a / (a + b)

    usd = (
        c[("transactions.amount_usd_origen", "igual_monto")]
        + c[("transactions.amount_usd_origen", "recalculado_tasa")]
    )
    tot = usd + c[("transactions.amount_usd_origen", "fuente")]
    items = [
        ("Interacciones sin transcripción", fr("interactions.con_transcripcion", "false", "true")),
        ("Quejas sin interacción de origen", fr("complaints.interaccion_origen_vacia", "true", "false")),
        ("Quejas sin resolución registrada", fr("complaints.sin_resolucion", "true", "false")),
        ("Disputas sin monto reclamado", fr("complaints.disputa_monto_vacio", "true", "false")),
        ("Quejas sin primera respuesta", fr("complaints.sin_primera_respuesta", "true", "false")),
        ("Eventos digitales sin cliente", m["dig_sin_cliente"] / m["dig_total"]),
        ("Quejas sin producto afectado", fr("complaints.producto_afectado_vacio", "true", "false")),
        (
            "Contactos sin duración (chat, WhatsApp, correo)",
            fr("interactions.duracion_vacia", "true", "false"),
        ),
        ("amount_usd vacío en la fuente", usd / tot),
        ("Quejas sin subcategoría", fr("complaints.subcategoria_vacia", "true", "false")),
    ]
    items.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    b = ax.barh([t[0] for t in items], [t[1] * 100 for t in items], color=NARANJA)
    _etiquetas(ax, b, [_pct(t[1]) for t in items])
    ax.set_xlim(0, 115)
    ax.set_xlabel("% de las filas de la tabla")
    ax.set_title("Vacíos y ausencias que afectan al flujo de disputas")
    guardar(fig, ruta)


def fig_priorizacion(m: dict[str, Any], ruta: Path) -> None:
    cand = m["candidatos"]
    puntos = m["puntos"]
    orden = sorted(puntos, key=lambda k: puntos[k])
    criterios = [
        ("volumen", "Volumen", AZUL),
        ("margen", "Margen de mejora", NARANJA),
        ("riesgo", "Riesgo para el cliente", ROJO),
        ("datos", "Datos y herramientas", VERDE),
    ]
    fig, ax = plt.subplots(figsize=(10, 4))
    izq = [0.0] * len(orden)
    for k, nombre, color in criterios:
        vals = [cand[o][k] * 0.25 for o in orden]
        ax.barh(orden, vals, left=izq, color=color, label=nombre)
        izq = [a + b for a, b in zip(izq, vals, strict=True)]
    for i, o in enumerate(orden):
        ax.annotate(
            f"{puntos[o]:.2f}".replace(".", ","),
            (puntos[o], i),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
        )
    ax.set_xlim(0, 5)
    ax.set_xlabel("Puntaje ponderado (1 a 5, pesos iguales)")
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    ax.set_title("Priorización de flujos candidatos")
    guardar(fig, ruta)


FIGURAS: dict[str, Callable[[dict[str, Any], Path], None]] = {
    "01_motivos.png": fig_motivos,
    "02_tendencia.png": fig_tendencia,
    "03_estacionalidad.png": fig_estacionalidad,
    "04_capacidad.png": fig_capacidad,
    "05_resultados.png": fig_resultados,
    "06_csat.png": fig_csat,
    "07_quejas.png": fig_quejas,
    "08_fraude.png": fig_fraude,
    "09_calidad.png": fig_calidad,
    "10_priorizacion.png": fig_priorizacion,
}


def generar(m: dict[str, Any], carpeta: Path) -> list[str]:
    estilo()
    for nombre, f in FIGURAS.items():
        f(m, carpeta / nombre)
    return list(FIGURAS)
