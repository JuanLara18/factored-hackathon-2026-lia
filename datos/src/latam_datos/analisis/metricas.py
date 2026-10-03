"""De las filas de las consultas a las cifras del informe. Todo sale de `Resultados`."""

from __future__ import annotations

from typing import Any

from latam_datos.analisis.calculos import (
    agrupar,
    agrupar2,
    bloque_horario,
    cambio_doce_meses,
    capacidad_por_bloque,
    escala_1_5,
    indice_carga,
    meses_completos,
    puntuar,
    sensibilidad_volumen,
    suma,
)
from latam_datos.analisis.consultas import Resultados

DISPUTA = "Cargo no reconocido"
MOTIVOS = ["Transaccional", "Producto", "Queja", "Técnico", "Comercial", "Retención"]
# Supuestos externos (investigación 11 de definicion.md, bloque B4): no salen de los datos.
COSTO_VOZ_USD = (7.0, 14.0)
COSTO_CHAT_USD = (3.0, 7.0)
PESOS = {"volumen": 0.25, "margen": 0.25, "riesgo": 0.25, "datos": 0.25}
# Juicios declarados (1 a 5), no medidos: gravedad del error y respaldo en las tablas de oro operacional.
JUICIO_RIESGO = {
    "Disputas de cargo": 5.0,
    "Servicio de tarjeta": 3.0,
    "Consultas de cuenta": 2.0,
    "Información de crédito": 2.0,
}
JUICIO_DATOS = {
    "Disputas de cargo": 5.0,
    "Servicio de tarjeta": 3.0,
    "Consultas de cuenta": 4.0,
    "Información de crédito": 2.0,
}


def _dur_media(filas: list[dict[str, Any]], **f: Any) -> float:
    return suma(filas, "sum_dur", **f) / suma(filas, "n_dur", **f)


def calcular(r: Resultados) -> dict[str, Any]:
    m: dict[str, Any] = {}
    m["cob"] = {f["tabla"]: f for f in r["cobertura"]}
    # Motivos, canal y país
    mc, mp = r["motivo_canal"], r["motivo_pais"]
    m["total"] = suma(mc)
    m["por_motivo"] = agrupar(mc, "motivo")
    m["por_canal"] = agrupar(mc, "canal")
    m["por_pais"] = agrupar(mp, "pais")
    m["motivo_x_canal"] = agrupar2(mc, "canal", "motivo")
    m["motivo_x_pais"] = agrupar2(mp, "pais", "motivo")
    # Quejas y disputas
    q = r["quejas_linea_base"]
    m["quejas"] = {f["subcategoria"]: f for f in q}
    m["quejas_total"] = suma(q)
    m["disputas"] = suma(q, subcategoria=DISPUTA)
    m["otras_quejas"] = [f for f in q if f["subcategoria"] != DISPUTA]
    qm = r["quejas_mes_pais_canal"]
    disputas_qm = [f for f in qm if f["es_disputa"]]
    m["disputa_por_pais"] = agrupar(disputas_qm, "pais")
    m["quejas_por_pais"] = agrupar(qm, "pais")
    m["disputa_por_canal"] = agrupar(disputas_qm, "canal")
    m["quejas_por_canal"] = agrupar(qm, "canal")
    m["disputa_mes"] = meses_completos(agrupar(disputas_qm, "mes"))
    m["quejas_mes"] = meses_completos(agrupar(qm, "mes"))
    m["tendencia_disputa"] = cambio_doce_meses(m["disputa_mes"])
    # Tendencia
    m["mes_total"] = meses_completos(agrupar(r["motivo_mes"], "mes"))
    m["tendencia"] = cambio_doce_meses(m["mes_total"])
    m["mes_motivo"] = agrupar2(r["motivo_mes"], "motivo", "mes")
    # Estacionalidad
    hd = r["hora_dia"]
    m["por_dia"] = agrupar(hd, "dia")
    m["por_hora"] = agrupar(hd, "hora")
    # Recurrencia
    rec = r["recurrencia"]
    m["rec"] = {f["motivo"]: f for f in rec}
    for k in ("n", "repite_7d_cualquiera", "repite_7d_mismo", "repite_30d_mismo"):
        m[f"rec_{k}"] = suma(rec, k)
    # Capacidad
    ag = r["agentes"]
    activos = agrupar([f for f in ag if f["estado"] == "Active"], "turno", "agentes")
    m["activos_turno"] = activos
    m["activos"] = sum(activos.values())
    m["agentes_total"] = suma(ag, "agentes")
    m["port_total"] = suma(ag, "agentes", portugues=True)
    m["fraude_total"] = suma(ag, "agentes", especialidad="Fraudes")
    m["fraude_port"] = suma(ag, "agentes", especialidad="Fraudes", portugues=True)
    m["fraude_activos_turno"] = agrupar(
        [f for f in ag if f["estado"] == "Active" and f["especialidad"] == "Fraudes"], "turno", "agentes"
    )
    m["quejas_agentes"] = suma(ag, "agentes", especialidad="Quejas y Reclamos")
    dem: dict[str, float] = {"Night": 0, "Morning": 0, "Afternoon": 0}
    for f in hd:
        dem[bloque_horario(int(f["hora"]))] += f["n"]
    m["demanda_bloque"] = dem
    m["capacidad_bloque"] = capacidad_por_bloque(activos)
    m["indice_carga"] = indice_carga(dem, m["capacidad_bloque"])
    ct = r["carga_turno"]
    m["madrugada_total"] = sum(f["n"] for f in ct if f["hora"] < 8)
    m["madrugada_turno_noche"] = sum(f["n"] for f in ct if f["hora"] < 8 and f["turno"] == "Night")
    m["inter_con_agente"] = suma(ct)
    # Tiempos y resultados
    tr = r["tiempos_resultados"]
    por: dict[str, dict[str, float]] = {}
    for mo in MOTIVOS:
        n = suma(tr, motivo=mo)
        entrantes = [f for f in tr if f["motivo"] == mo and f["tipo"] == "Inbound Call"]
        por[mo] = {
            "n": n,
            "resuelto": suma(tr, "resueltos", motivo=mo) / n,
            "escalado": suma(tr, "escalados", motivo=mo) / n,
            "seguimiento": suma(tr, "seguimiento", motivo=mo) / n,
            "dur_media": _dur_media(tr, motivo=mo),
            "n_dur": suma(tr, "n_dur", motivo=mo),
            "negativo": suma(tr, "sent_negativo", motivo=mo) / suma(tr, "n_sent", motivo=mo),
            "esp_media": suma(entrantes, "sum_esp") / suma(entrantes, "n_esp"),
            "n_esp": suma(entrantes, "n_esp"),
        }
    m["por_motivo_res"] = por
    n = m["total"]
    m["res_global"] = suma(tr, "resueltos") / n
    m["esc_global"] = suma(tr, "escalados") / n
    m["seg_global"] = suma(tr, "seguimiento") / n
    m["dur_global"] = _dur_media(tr)
    m["n_dur_global"] = suma(tr, "n_dur")
    entrantes = [f for f in tr if f["tipo"] == "Inbound Call"]
    m["esp_global"] = suma(entrantes, "sum_esp") / suma(entrantes, "n_esp")
    m["n_esp_global"] = suma(entrantes, "n_esp")
    m["dur_canal"] = {
        c: _dur_media(tr, canal=c)
        for c in ("Phone", "Web Chat", "WhatsApp", "App", "Email", "Web")
        if suma(tr, "n_dur", canal=c)
    }
    trans_tel = [
        f
        for f in tr
        if f["motivo"] == "Transaccional" and f["canal"] == "Phone" and f["tipo"] == "Inbound Call"
    ]
    m["trans_tel"] = trans_tel[0] if trans_tel else {}
    # Encuestas
    en = r["encuestas"]
    csat = [f for f in en if f["tipo"] == "CSAT"]
    m["csat_n"] = suma(csat)
    m["csat_media"] = suma(csat, "sum_score") / suma(csat)
    m["csat_altos"] = suma(csat, "altos") / suma(csat)
    m["csat_motivo"] = {
        mo: {
            "n": suma(csat, motivo=mo),
            "media": suma(csat, "sum_score", motivo=mo) / suma(csat, motivo=mo),
            "altos": suma(csat, "altos", motivo=mo) / suma(csat, motivo=mo),
        }
        for mo in MOTIVOS
    }
    m["csat_canal"] = {
        c: {"n": suma(csat, canal=c), "altos": suma(csat, "altos", canal=c) / suma(csat, canal=c)}
        for c in sorted({f["canal"] for f in csat})
    }
    nps = [f for f in en if f["tipo"] == "NPS"]
    m["nps_n"] = suma(nps)
    m["nps_detractores"] = suma(nps, "detractores") / suma(nps)
    m["nps_media"] = suma(nps, "sum_score") / suma(nps)
    ces = [f for f in en if f["tipo"] == "CES"]
    m["ces_n"] = suma(ces)
    m["ces_media"] = suma(ces, "sum_score") / suma(ces)
    # Fraude
    fr = r["fraude"]
    m["tx_total"] = suma(fr)
    m["fraudes"] = suma(fr, "fraudes")
    m["fraude_usd"] = suma(fr, "usd_fraude")
    m["fraude_sin_score"] = suma(fr, "fraude_sin_score")
    m["fraude_mes"] = meses_completos(agrupar(fr, "mes", "fraudes"))
    m["tx_mes"] = meses_completos(agrupar(fr, "mes"))
    m["fraude_estado"] = {
        e: (suma(fr, "n", estado=e), suma(fr, "fraudes", estado=e)) for e in sorted({f["estado"] for f in fr})
    }
    m["fraude_pais"] = {
        p: (suma(fr, "n", pais=p), suma(fr, "fraudes", pais=p)) for p in sorted({f["pais"] for f in fr})
    }
    m["montos"] = r["montos_disputa"]
    m["disp_con_monto"] = suma(r["montos_disputa"], "con_monto")
    m["disp_compensadas"] = suma(r["montos_disputa"], "con_compensacion")
    # Calidad
    m["cal"] = {(f["control"], f["valor"]): f["n"] for f in r["calidad"]}
    dg = r["digital"]
    m["dig_total"] = suma(dg)
    m["dig_sin_cliente"] = suma(dg, "sin_cliente")
    m["dig_sin_sesion"] = suma(dg, "sin_sesion")
    m["dig_ayuda"] = suma(dg, accion="view_help")
    m["dig_transfer"] = suma(dg, accion="initiate_transfer")
    m["dig_pago"] = suma(dg, accion="initiate_payment")
    m["dig_movs"] = suma(dg, accion="view_transactions")
    tc = r["transcripciones"]
    m["transc_total"] = suma(tc)
    m["transc_es"] = suma(tc, idioma="es")
    m["transc_general"] = suma(tc, intencion="consulta_general")
    # Priorización
    m["candidatos"], m["puntos"], m["sensibilidad"] = priorizar(m)
    return m


def priorizar(
    m: dict[str, Any],
) -> tuple[dict[str, dict[str, float]], dict[str, float], list[tuple[float, str]]]:
    por = m["por_motivo_res"]
    vol = {
        "Disputas de cargo": m["disputas"],
        "Servicio de tarjeta": por["Producto"]["n"],
        "Consultas de cuenta": por["Transaccional"]["n"],
        "Información de crédito": por["Comercial"]["n"],
    }
    d = m["quejas"][DISPUTA]
    sin_cierre = {
        "Disputas de cargo": 1 - d["cerradas"] / d["n"],
        "Servicio de tarjeta": 1 - por["Producto"]["resuelto"],
        "Consultas de cuenta": 1 - por["Transaccional"]["resuelto"],
        "Información de crédito": 1 - por["Comercial"]["resuelto"],
    }
    m["proxy_volumen"] = vol
    m["proxy_sin_cierre"] = sin_cierre
    v, g = escala_1_5(vol), escala_1_5(sin_cierre)
    cand = {
        c: {"volumen": v[c], "margen": g[c], "riesgo": JUICIO_RIESGO[c], "datos": JUICIO_DATOS[c]}
        for c in vol
    }
    return cand, puntuar(cand, PESOS), sensibilidad_volumen(cand, PESOS, [0.1, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8])
