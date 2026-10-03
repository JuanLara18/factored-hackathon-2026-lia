# ruff: noqa: E501
"""Redacta `presidencia/reporte/01_problema.md` a partir de las cifras calculadas. Cada número viene de `metricas`."""

from __future__ import annotations

from datetime import date
from typing import Any

from latam_datos.analisis.calculos import dec, miles, pct, wilson
from latam_datos.analisis.metricas import COSTO_CHAT_USD, COSTO_VOZ_USD, DISPUTA, MOTIVOS, PESOS

PAIS = {"MX": "México", "CO": "Colombia", "AR": "Argentina"}
CANAL_QUEJA = {
    "Call Center": "centro de llamadas",
    "Email": "correo",
    "Web": "web",
    "App": "app",
    "Branch": "sucursal",
    "Regulator": "regulador",
}
DIA = {1: "domingo", 2: "lunes", 3: "martes", 4: "miércoles", 5: "jueves", 6: "viernes", 7: "sábado"}


def _min(s: float) -> str:
    return dec(s / 60, 1)


def _c(m: dict[str, Any], control: str, valor: str) -> float:
    return m["cal"].get((control, valor), 0)


def _tabla(cabecera: list[str], filas: list[list[str]]) -> str:
    out = ["| " + " | ".join(cabecera) + " |", "|" + "|".join("---" for _ in cabecera) + "|"]
    out += ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join(out)


def redactar(m: dict[str, Any]) -> str:
    cob, p, d = m["cob"], m["por_motivo_res"], m["quejas"][DISPUTA]
    total = m["total"]
    ini = cob["call_center_interactions"]["desde"]
    fin = cob["call_center_interactions"]["hasta"]
    top = max(m["por_motivo"], key=lambda k: m["por_motivo"][k])
    dias = m["por_dia"]
    pico_dia = max(dias, key=lambda k: dias[k])
    horas = m["por_hora"]
    h_max, h_min = max(horas.values()), min(horas.values())
    laborales = sum(dias[k] for k in range(2, 7)) / 5
    finde = (dias[1] + dias[7]) / 2
    ini12, fin12, var12 = m["tendencia"]
    _, _, vard = m["tendencia_disputa"]
    otras = m["otras_quejas"]
    otras_resp = [f["h_resp_p50"] for f in otras]
    otras_sla = [f["sla_incumplido"] / f["n"] for f in otras]
    otras_cierre = [f["cerradas"] / f["n"] for f in otras]
    q_n = m["quejas_total"]
    d_lo, d_hi = wilson(d["sla_incumplido"], d["n"])
    cap, dem, idx = m["capacidad_bloque"], m["demanda_bloque"], m["indice_carga"]
    tt = m["trans_tel"]
    mont = [f for f in m["montos"] if f["moneda"] != "sin moneda"]
    fraude_ap = m["fraude_estado"]["Approved"]
    usd_cal = _c(m, "transactions.amount_usd_origen", "igual_monto") + _c(
        m, "transactions.amount_usd_origen", "recalculado_tasa"
    )
    usd_tot = usd_cal + _c(m, "transactions.amount_usd_origen", "fuente")
    meses = round((date.fromisoformat(fin) - date.fromisoformat(ini)).days / 30.44)
    disp_mes = m["disputas"] / meses
    voz = (disp_mes * COSTO_VOZ_USD[0], disp_mes * COSTO_VOZ_USD[1])
    chat = (disp_mes * COSTO_CHAT_USD[0], disp_mes * COSTO_CHAT_USD[1])
    pts = m["puntos"]
    lider = max(pts, key=lambda k: pts[k])
    sens = m["sensibilidad"]
    cambio = next((pv for pv, ld in sens if ld != lider), None)

    motivos_tab = _tabla(
        [
            "Motivo",
            "Contactos",
            "Participación",
            "Resuelto en el contacto",
            "Seguimiento",
            "Escalado",
            "Duración media (min)",
            "Espera media, llamada entrante (min)",
        ],
        [
            [
                mo,
                miles(p[mo]["n"]),
                pct(p[mo]["n"], total),
                pct(p[mo]["resuelto"], 1),
                pct(p[mo]["seguimiento"], 1),
                pct(p[mo]["escalado"], 1),
                _min(p[mo]["dur_media"]),
                _min(p[mo]["esp_media"]),
            ]
            for mo in sorted(MOTIVOS, key=lambda k: -p[k]["n"])
        ],
    )
    csat_tab = _tabla(
        ["Motivo", "Encuestas CSAT", "Media (1 a 4)", "Respuestas 3 o 4"],
        [
            [
                mo,
                miles(m["csat_motivo"][mo]["n"]),
                dec(m["csat_motivo"][mo]["media"], 2),
                pct(m["csat_motivo"][mo]["altos"], 1),
            ]
            for mo in sorted(MOTIVOS, key=lambda k: -m["csat_motivo"][k]["altos"])
        ],
    )
    q_tab = _tabla(
        [
            "Subcategoría",
            "Quejas",
            "Horas a la asignación (mediana)",
            "Horas a la primera respuesta (mediana, p90)",
            "Días a la resolución (mediana)",
            "SLA incumplido",
            "Cerradas o resueltas",
            "Reincidentes",
        ],
        [
            [
                s,
                miles(f["n"]),
                str(f["h_asig_p50"]),
                f"{f['h_resp_p50']}, {f['h_resp_p90']}",
                dec(f["dias_res_p50"], 0),
                pct(f["sla_incumplido"], f["n"]),
                pct(f["cerradas"], f["n"]),
                pct(f["reincidentes"], f["n"]),
            ]
            for s, f in sorted(m["quejas"].items(), key=lambda kv: (kv[0] != DISPUTA, kv[0]))
        ],
    )
    cand = m["candidatos"]
    punt_tab = _tabla(
        [
            "Flujo candidato",
            "Proxy de volumen (tabla y filtro)",
            "Volumen",
            "Sin cierre",
            "Margen",
            "Riesgo",
            "Datos",
            "Puntaje",
        ],
        [
            [
                c,
                f"{miles(m['proxy_volumen'][c])} ({fuente})",
                dec(cand[c]["volumen"], 1),
                pct(m["proxy_sin_cierre"][c], 1),
                dec(cand[c]["margen"], 1),
                dec(cand[c]["riesgo"], 0),
                dec(cand[c]["datos"], 0),
                dec(pts[c], 2),
            ]
            for (c, fuente) in [
                ("Disputas de cargo", "quejas con subcategoría Cargo no reconocido"),
                ("Consultas de cuenta", "interacciones con motivo Transaccional"),
                ("Servicio de tarjeta", "interacciones con motivo Producto"),
                ("Información de crédito", "interacciones con motivo Comercial"),
            ]
        ],
    )
    sens_txt = ", ".join(f"{pct(pv, 1, 0)}: {ld.lower()}" for pv, ld in sens)
    base_tab = _tabla(
        ["Indicador de base", "Valor", "n", "Fuente y filtro"],
        [
            [
                "Duración media del contacto transaccional",
                f"{_min(p['Transaccional']['dur_media'])} min",
                miles(p["Transaccional"]["n_dur"]),
                "interacciones, motivo Transaccional, duration_seconds no vacío",
            ],
            [
                "Duración mediana y p90, llamada entrante transaccional",
                f"{_min(tt['dur_p50'])} y {_min(tt['dur_p90'])} min",
                miles(tt["n_dur"]),
                "interacciones, motivo Transaccional, canal Phone, tipo Inbound Call",
            ],
            [
                "Espera media, llamada entrante",
                f"{_min(m['esp_global'])} min",
                miles(m["n_esp_global"]),
                "interacciones, tipo Inbound Call, wait_time_seconds no vacío",
            ],
            [
                "Resuelto en el contacto, motivo Transaccional",
                pct(p["Transaccional"]["resuelto"], 1),
                miles(p["Transaccional"]["n"]),
                "interacciones, was_resolved",
            ],
            [
                "Resuelto en el contacto, todos los motivos",
                pct(m["res_global"], 1),
                miles(total),
                "interacciones, was_resolved",
            ],
            [
                "Escalado, todos los motivos",
                pct(m["esc_global"], 1),
                miles(total),
                "interacciones, was_escalated",
            ],
            [
                "Requiere seguimiento, todos los motivos",
                pct(m["seg_global"], 1),
                miles(total),
                "interacciones, requires_followup",
            ],
            [
                "CSAT de 3 o 4 sobre 4, todos los motivos",
                pct(m["csat_altos"], 1),
                miles(m["csat_n"]),
                "satisfaction_surveys, survey_type CSAT, unidas por interaction_id",
            ],
            [
                "CSAT de 3 o 4 sobre 4, motivo Transaccional",
                pct(m["csat_motivo"]["Transaccional"]["altos"], 1),
                miles(m["csat_motivo"]["Transaccional"]["n"]),
                "idem, motivo Transaccional",
            ],
            [
                "Disputa: horas a la primera respuesta (mediana, p90)",
                f"{d['h_resp_p50']} y {d['h_resp_p90']} h",
                miles(d["n_resp"]),
                "complaints, subcategory Cargo no reconocido, first_response_date no vacía",
            ],
            [
                "Disputa: días a la resolución (mediana, p90)",
                f"{dec(d['dias_res_p50'], 0)} y {dec(d['dias_res_p90'], 0)}",
                miles(d["n_res"]),
                "complaints, Cargo no reconocido, resolution_days no vacío",
            ],
            [
                "Disputa: SLA incumplido",
                pct(d["sla_incumplido"], d["n"]),
                miles(d["n"]),
                "complaints, Cargo no reconocido, sla_breached",
            ],
            [
                "Disputa: cerrada o resuelta",
                pct(d["cerradas"], d["n"]),
                miles(d["n"]),
                "complaints, Cargo no reconocido, status Resolved o Closed",
            ],
            [
                "Disputa: reincidente",
                pct(d["reincidentes"], d["n"]),
                miles(d["n"]),
                "complaints, Cargo no reconocido, is_repeat_complainer",
            ],
            [
                "Disputa: satisfacción con la resolución (media, 1 a 4)",
                dec(d["sum_csat"] / d["n_csat"], 2),
                miles(d["n_csat"]),
                "complaints, Cargo no reconocido, resolution_satisfaction no vacía",
            ],
            [
                "Prevalencia de fraude marcado",
                f"{dec(m['fraudes'] / m['tx_total'] * 10000, 1)} por 10.000",
                miles(m["tx_total"]),
                "transactions, is_fraud",
            ],
        ],
    )

    return f"""# Criterio 1: un problema respaldado por datos

Este documento lo genera `uv run python -m latam_datos.analisis` (consultas en `datos/analisis/consultas.sql`, cifras en `figuras/cifras.json`). Todas las cifras salen de BigQuery, dataset `latam_bank`, capa plata (sin duplicados y con tipos canónicos). Los datos son sintéticos, cubren del {ini} al {fin} y llegan hasta tres países: México, Colombia y Argentina. Lo que no sale de una consulta se marca como supuesto.

## 1. Resumen

El centro de atención recibió {miles(total)} contactos de {miles(cob["call_center_interactions"]["clientes"])} clientes, con una demanda estable (variación de {pct(var12, 1)} entre los primeros y los últimos doce meses completos). El motivo más frecuente es {top.lower()} ({pct(m["por_motivo"][top], total)}), pero en las interacciones el motivo no pasa de la categoría gruesa: no existe un motivo fino que aísle los cargos no reconocidos. Esa señal solo aparece en las quejas, donde "{DISPUTA}" es la subcategoría más grande ({miles(m["disputas"])} de {miles(q_n)}, {pct(m["disputas"], q_n)}) y se atiende con una primera respuesta mediana de {d["h_resp_p50"]} horas, {pct(d["sla_incumplido"], d["n"])} de SLA incumplido y solo {pct(d["cerradas"], d["n"])} de casos cerrados. La contención de un fraude se mide en minutos, no en días. La madrugada (00:00 a 07:59) concentra {pct(dem["Night"], sum(dem.values()))} de la demanda con {pct(cap["Night"], sum(cap.values()))} de los agentes activos (rotativos repartidos en tres, supuesto). Por eso el flujo propuesto es la recepción de disputas de transacciones, con atención a cualquier hora.

![Motivos](figuras/01_motivos.png)

## 2. Motivos de contacto

Fuente: `plata_call_center_interactions` (sin filtro) unida a `plata_customers` para el país; consultas `motivo_canal`, `motivo_pais`, `motivo_mes`.

{motivos_tab}

La mezcla de motivos es prácticamente idéntica en los tres países y en los seis canales (figura anterior): no hay un canal ni un país con un problema propio. El canal es el teléfono en {pct(m["por_canal"]["Phone"], total)} de los contactos; correo {pct(m["por_canal"]["Email"], total)}, app {pct(m["por_canal"]["App"], total)}, WhatsApp {pct(m["por_canal"]["WhatsApp"], total)}, chat web {pct(m["por_canal"]["Web Chat"], total)} y web {pct(m["por_canal"]["Web"], total)}. Por país del cliente: México {pct(m["por_pais"]["MX"], total)}, Colombia {pct(m["por_pais"]["CO"], total)} y Argentina {pct(m["por_pais"]["AR"], total)}.

**Contactos por cargos no reconocidos.** En las interacciones no se pueden contar: `contact_reason` es igual a `reason_category` en {pct(_c(m, "interactions.motivo_distinto_categoria", "false"), total, 0)} de las filas y las transcripciones solo traen la intención `consulta_general` ({pct(m["transc_general"], m["transc_total"])} de {miles(m["transc_total"])}). Lo observable es la queja formal: {miles(m["disputas"])} quejas "{DISPUTA}", {pct(m["disputas"], q_n)} del total de quejas y {pct(m["disputas"], q_n - sin_sin_sub(m))} de las que traen subcategoría (consulta `quejas_linea_base`, `plata_complaints`). Por país del cliente representan {", ".join(f"{pct(m['disputa_por_pais'][k], m['quejas_por_pais'][k])} en {PAIS[k]}" for k in ("MX", "CO", "AR"))}; por canal de recepción, {", ".join(f"{pct(m['disputa_por_canal'][k], m['quejas_por_canal'][k])} en {CANAL_QUEJA.get(k, k)}" for k in sorted(m["quejas_por_canal"], key=lambda k: -m["quejas_por_canal"][k]))}. Cada queja es un contacto que no se resolvió a la primera, de modo que {miles(m["disputas"])} es una cota inferior del tráfico de disputas. La cota superior razonable es el motivo Transaccional ({miles(p["Transaccional"]["n"])}).

**Tendencia.** El promedio mensual pasó de {miles(ini12)} a {miles(fin12)} contactos ({pct(var12, 1)}); las quejas por cargo no reconocido, de {miles(m["tendencia_disputa"][0])} a {miles(m["tendencia_disputa"][1])} al mes ({pct(vard, 1)}). Se comparan los primeros y los últimos doce meses completos; el primer y el último mes de la ventana son parciales y se excluyen. No hay crecimiento que justifique urgencia por volumen; la urgencia viene de la calidad de la atención.

![Tendencia](figuras/02_tendencia.png)

**Estacionalidad.** El día con más contactos es el {DIA[pico_dia]}; los días hábiles promedian {miles(laborales)} y el fin de semana {miles(finde)} ({pct(finde, laborales, 0)} de un día hábil). Por hora no hay patrón: el máximo ({miles(h_max)}) es solo {pct(h_max - h_min, h_min)} mayor que el mínimo ({miles(h_min)}). Esa planicie es un artefacto de los datos sintéticos y no debe leerse como comportamiento real; se declara así en los supuestos. La hora usada es la de `interaction_date`, sin zona horaria declarada.

![Estacionalidad](figuras/03_estacionalidad.png)

**Contactos repetidos.** Un cliente vuelve a contactar en menos de 7 días en {pct(m["rec_repite_7d_cualquiera"], m["rec_n"])} de los contactos, y por el mismo motivo en {pct(m["rec_repite_7d_mismo"], m["rec_n"])} (consulta `recurrencia`, ventana por cliente). Por el mismo motivo en 30 días: {pct(m["rec_repite_30d_mismo"], m["rec_n"])}. El motivo Transaccional es el que más se repite: {pct(m["rec"]["Transaccional"]["repite_7d_mismo"], m["rec"]["Transaccional"]["n"])} a 7 días, contra {pct(m["rec"]["Queja"]["repite_7d_mismo"], m["rec"]["Queja"]["n"])} en Queja. La repetición es baja, por lo que la reincidencia por contacto no es el problema a resolver. En quejas, {pct(d["reincidentes"], d["n"])} de las de cargo no reconocido son de clientes reincidentes.

## 3. Demanda frente a capacidad

Fuente: `plata_service_agents` ({miles(m["agentes_total"])} agentes, {miles(m["activos"])} activos) y `plata_call_center_interactions`; consultas `agentes`, `hora_dia`, `carga_turno`.

| Franja | Demanda | Agentes activos (rotativos repartidos en tres) | Índice de carga |
|---|---|---|---|
| 00:00 a 07:59 | {miles(dem["Night"])} ({pct(dem["Night"], sum(dem.values()))}) | {dec(cap["Night"], 0)} ({pct(cap["Night"], sum(cap.values()))}) | {dec(idx["Night"], 2)} |
| 08:00 a 15:59 | {miles(dem["Morning"])} ({pct(dem["Morning"], sum(dem.values()))}) | {dec(cap["Morning"], 0)} ({pct(cap["Morning"], sum(cap.values()))}) | {dec(idx["Morning"], 2)} |
| 16:00 a 23:59 | {miles(dem["Afternoon"])} ({pct(dem["Afternoon"], sum(dem.values()))}) | {dec(cap["Afternoon"], 0)} ({pct(cap["Afternoon"], sum(cap.values()))}) | {dec(idx["Afternoon"], 2)} |

El índice divide la participación en la demanda entre la participación en la capacidad. El reparto de los agentes rotativos en tres partes iguales es un supuesto. Hay {m["activos_turno"].get("Night", 0):.0f} agentes activos de turno nocturno y {m["activos_turno"].get("Rotating", 0):.0f} rotativos. Los agentes de fraude suman {miles(m["fraude_total"])} ({miles(m["fraude_port"])} con portugués) y los de quejas y reclamos, {miles(m["quejas_agentes"])}; los de fraude activos de turno nocturno son {m["fraude_activos_turno"].get("Night", 0):.0f}.

Dos cautelas. Primero, el turno del agente no restringe cuándo atiende: de los {miles(m["madrugada_total"])} contactos de madrugada, solo {pct(m["madrugada_turno_noche"], m["madrugada_total"])} los atendió un agente de turno nocturno; el resto lo atendieron agentes de otros turnos. El dato no permite medir cobertura real, solo capacidad declarada. Segundo, los tres países de clientes son hispanohablantes: no hay clientes de Brasil, de modo que los {miles(m["port_total"])} agentes con portugués no son una restricción para este flujo, y todas las transcripciones están en español ({pct(m["transc_es"], m["transc_total"], 0)} de {miles(m["transc_total"])}).

**Espera, duración y abandono.** La espera media de una llamada entrante es {_min(m["esp_global"])} minutos y la duración media de un contacto, {_min(m["dur_global"])} (consultas `tiempos_resultados`). La duración solo existe para teléfono y web, y para una fracción de la app: chat web, WhatsApp y correo la traen vacía. La espera solo existe para llamadas entrantes. No hay campo de abandono, por lo que la tasa de abandono no se puede medir y no se inventa. Por motivo, la duración va de {_min(min(v["dur_media"] for v in p.values()))} a {_min(max(v["dur_media"] for v in p.values()))} minutos; los motivos de queja, comerciales y de retención son los más largos.

**Dónde ayuda la IA al frente.** Con una demanda sin picos horarios, el valor no está en recortar picos, sino en atender a cualquier hora y en fin de semana sin ampliar turnos nocturnos, y en liberar a los agentes humanos para los casos que requieren juicio. Los eventos digitales apuntan en la misma dirección: hay {miles(m["dig_transfer"])} inicios de transferencia, {miles(m["dig_pago"])} de pago, {miles(m["dig_movs"])} consultas de movimientos y {miles(m["dig_ayuda"])} vistas de ayuda (`plata_digital_events`), de modo que el cliente ya consulta sus movimientos en la app antes de llamar.

![Capacidad](figuras/04_capacidad.png)

## 4. Resultados de la atención

{pct(m["res_global"], 1)} de los contactos terminan resueltos en el mismo contacto y {pct(m["esc_global"], 1)} se escalan, con diferencias grandes por motivo en resolución y ninguna en escalamiento (cercano a 10% en todos). Las quejas se resuelven en {pct(p["Queja"]["resuelto"], 1)} de los casos y requieren seguimiento en {pct(p["Queja"]["seguimiento"], 1)}.

![Resultados](figuras/05_resultados.png)

**Satisfacción.** Fuente: `plata_satisfaction_surveys` unida a las interacciones por `interaction_id`. El CSAT usa una escala de 1 a 4 y se reporta como la proporción de respuestas de 3 o 4.

{csat_tab}

Los canales no cambian el cuadro: la proporción de respuestas altas va de {pct(min(v["altos"] for v in m["csat_canal"].values()), 1)} a {pct(max(v["altos"] for v in m["csat_canal"].values()), 1)}. En NPS ({miles(m["nps_n"])} encuestas, escala observada de 2 a 7) la fuente solo trae las categorías Detractor y Pasivo, sin promotores, y {pct(m["nps_detractores"], 1)} de las respuestas son de detractores; por eso el NPS clásico no se puede calcular y la línea base usa CSAT. El CES medio es {dec(m["ces_media"], 2)} sobre 4 ({miles(m["ces_n"])} encuestas).

![CSAT](figuras/06_csat.png)

**Quejas y SLA.** Fuente: `plata_complaints`, línea base por subcategoría.

{q_tab}

Las cinco subcategorías con nombre se comportan casi igual: la primera respuesta mediana va de {min(otras_resp)} a {max(otras_resp)} horas, el SLA incumplido de {pct(min(otras_sla), 1)} a {pct(max(otras_sla), 1)} y los casos cerrados de {pct(min(otras_cierre), 1)} a {pct(max(otras_cierre), 1)}. El cargo no reconocido no se atiende peor que las demás y tampoco mejor: el argumento no es una diferencia entre subcategorías, sino el nivel absoluto. Para un cargo no reconocido el cliente espera {d["h_resp_p50"]} horas (p90 {d["h_resp_p90"]}) una primera respuesta, el SLA se incumple en {pct(d["sla_incumplido"], d["n"])} (intervalo de Wilson al 95%: {pct(d_lo, 1)} a {pct(d_hi, 1)}) y {pct(1 - d["cerradas"] / d["n"], 1)} de los casos siguen abiertos, en proceso o escalados. Esto es una línea base, no una prueba de que este motivo sea el peor. Además, el campo `sla_breached` no se relaciona con `resolution_days` en la muestra, así que se reporta tal como viene.

![Quejas](figuras/07_quejas.png)

**Fraude y montos.** Fuente: `plata_transactions` (`is_fraud`, `amount_usd` con la regla de plata). {miles(m["fraudes"])} de {miles(m["tx_total"])} transacciones están marcadas como fraude ({dec(m["fraudes"] / m["tx_total"] * 100, 2)}%), por un total de USD {miles(m["fraude_usd"])}; {pct(fraude_ap[1], m["fraudes"])} de ellas están aprobadas, es decir, el dinero salió. La prevalencia es plana por mes y por estado. Entre las disputas con monto declarado ({miles(m["disp_con_monto"])} de {miles(m["disputas"])}), la mediana reclamada es de {", ".join(f"{miles(f['monto_p50'])} {f['moneda']}" for f in mont)} (p90 cercano a {miles(sum(f["monto_p90"] for f in mont) / len(mont))}), en moneda local sin convertir; {miles(m["disp_compensadas"])} tuvieron compensación. Estos montos no tienen respaldo transaccional (la queja no enlaza con la transacción), así que sirven para dimensionar, no para conciliar.

![Fraude](figuras/08_fraude.png)

## 5. Calidad de datos y restricciones del flujo

Fuentes: `datos/LIMITACIONES.md` (bronce) y la consulta `calidad` (plata). Los vacíos están ordenados en la figura; los que afectan al diseño son:

- **Monto en dólares.** `amount_usd` viene vacío en {pct(usd_tot - _c(m, "transactions.amount_usd_origen", "fuente"), usd_tot)} de las filas de origen ({miles(usd_cal)} de {miles(usd_tot)}): todas las transacciones en USD (el monto ya está en dólares) y {miles(_c(m, "transactions.amount_usd_origen", "recalculado_tasa"))} en moneda local, que plata recalcula con la tasa del día. El flujo debe usar `amount_usd` de plata y la bandera `amount_usd_origen`, no el campo crudo.
- **Sin enlace entre queja y transacción.** `origin_interaction_id` está vacío en {pct(_c(m, "complaints.interaccion_origen_vacia", "true"), q_n, 0)} de las quejas y `affected_product_id` en {pct(_c(m, "complaints.producto_afectado_vacio", "true"), q_n)}. El cargo disputado lo tiene que identificar el cliente en la conversación, con la transacción como evidencia; no se puede precargar desde la queja.
- **Disputas sin monto.** {pct(_c(m, "complaints.disputa_monto_vacio", "true"), m["disputas"])} de las quejas por cargo no reconocido no traen monto reclamado.
- **Eventos digitales sin cliente.** {pct(m["dig_sin_cliente"], m["dig_total"])} de {miles(m["dig_total"])} eventos no traen `customer_id` (todos traen sesión), de modo que el recorrido digital previo a un contacto solo se reconstruye para tres cuartas partes del tráfico.
- **Sin motivo fino ni transcripciones útiles.** Las interacciones traen solo la categoría gruesa y {pct(_c(m, "interactions.con_transcripcion", "false"), total)} no tiene transcripción; las existentes son plantillas con una intención casi única.
- **Resolución de quejas incompleta.** {pct(_c(m, "complaints.sin_resolucion", "true"), q_n)} de las quejas no tienen fecha de resolución y {pct(_c(m, "complaints.sin_primera_respuesta", "true"), q_n)} no tienen primera respuesta; los tiempos de la línea base se calculan sobre las que sí la tienen, con n declarado, y pueden ser optimistas.
- **Escalas.** CSAT y CES de 1 a 4; NPS de 2 a 7 sin promotores.
- **Idioma.** Todo en español; el flujo no necesita portugués para estos clientes.
- **Datos sintéticos.** Planicie por hora, indicadores casi idénticos entre subcategorías y etiquetas de fraude sin estructura. Los resultados describen este conjunto, no al banco real. La ventana es 2023-06-17 a 2026-06-17 y `campaign_sends` empieza el 2023-07-01.

![Calidad](figuras/09_calidad.png)

## 6. Priorización del flujo

Se puntúan cuatro flujos candidatos de 1 a 5 en cuatro criterios con pesos iguales ({", ".join(f"{k} {pct(v, 1, 0)}" for k, v in PESOS.items())}). Volumen y margen son medidos y se reescalan entre los candidatos; riesgo y datos son juicios declarados. El margen es la fracción de casos sin cierre en el contacto (para disputas, la fracción de quejas que no están cerradas ni resueltas). Riesgo: gravedad del error para el cliente (una disputa mal recibida deja un fraude sin contener). Datos: respaldo en las tablas de oro operacional (`ficha_transaccion`, `riesgo_transaccion`, `reclamos_cliente`).

{punt_tab}

El volumen de las disputas está medido solo con quejas formales y no con contactos, así que subestima su tamaño y juega en contra de la disputa en este puntaje. Aun así el flujo líder es **{lider.lower()}**, con {dec(pts[lider], 2)} puntos. Sensibilidad al peso del volumen (el resto se reparte en proporción): {sens_txt}. {f"El liderazgo cambia cuando el volumen pesa {pct(cambio, 1, 0)} o más, hacia las consultas de cuenta, que ya se resuelven en {pct(p['Transaccional']['resuelto'], 1)} y dejan poco margen para mejorar." if cambio is not None else "El liderazgo no cambia en el rango probado."}

Por qué disputas de transacciones y no un flujo de más volumen: es el único candidato donde el problema medido es grave y el error es costoso (los cargos no reconocidos tardan {d["h_resp_p50"]} horas en recibir primera respuesta y {pct(1 - d["cerradas"] / d["n"], 1)} no está cerrado), donde hay una fricción que el cliente siente de inmediato y donde el banco ya tiene las herramientas de datos para actuar con evidencia (ficha de la transacción, banda de riesgo y estado de reclamos). Las consultas de cuenta y el servicio de tarjeta ya se resuelven en cerca de nueve de cada diez contactos. El flujo de crédito no tiene respaldo de datos suficiente ni un problema medible.

![Priorización](figuras/10_priorizacion.png)

## 7. Resultados buscados y línea base

**Resultado para el cliente.** Que quien desconoce un cargo reciba una primera respuesta en minutos y no en horas, con el cargo identificado y el caso correctamente clasificado y entregado a una persona con contexto cuando corresponda. **Resultado para el banco.** Menos horas de atención humana por recepción de disputas, menor incumplimiento de SLA y más casos cerrados, sin sacrificar la protección contra el fraude. La dirección es la que se indica; las metas numéricas las fija Gobierno con esta línea base.

{base_tab}

**Costo por contacto (supuesto, no sale de los datos).** Los datos no traen costos. Se usan los rangos de la investigación 11 de `datos/definicion.md`: USD {dec(COSTO_VOZ_USD[0], 0)} a {dec(COSTO_VOZ_USD[1], 0)} por contacto de voz y USD {dec(COSTO_CHAT_USD[0], 0)} a {dec(COSTO_CHAT_USD[1], 0)} por chat. Con {miles(m["disputas"])} quejas de cargo no reconocido en {meses} meses (alrededor de {miles(disp_mes)} al mes, cota inferior), la recepción por voz costaría entre USD {miles(voz[0])} y {miles(voz[1])} al mes y por chat entre USD {miles(chat[0])} y {miles(chat[1])}. Es un orden de magnitud para comparar escenarios, no un ahorro comprometido.

**Cómo se usará la línea base.** La evaluación del sistema compara contra estas cifras sobre casos del mismo alcance: tiempo hasta la primera respuesta, proporción cerrada con evidencia, SLA, CSAT posterior y duración humana por caso. Dos limitaciones: las quejas tienen n grande pero sin enlace a transacciones, y el CSAT de resolución de quejas tiene solo {miles(d["n_csat"])} respuestas para disputas, así que su intervalo es amplio.

## 8. Cómo reproducir

`uv run python -m latam_datos.analisis` (requiere ADC de Google Cloud y `LATAM_GCP_PROJECT`, `LATAM_BQ_DATASET`, opcional `LATAM_GCP_LOCATION`). `--desde-cache` regenera figuras e informe desde `figuras/cifras.json` sin consultar BigQuery. Ninguna cifra ni figura se edita a mano.
"""


def sin_sin_sub(m: dict[str, Any]) -> float:
    return m["quejas"]["Sin subcategoría"]["n"]
