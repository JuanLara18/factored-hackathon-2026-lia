# ruff: noqa: E501
# pyright: basic, reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false, reportReturnType=false, reportMissingTypeStubs=false, reportIndexIssue=false, reportOperatorIssue=false
# (script de experimento: pandas y scikit-learn sin tipos; el módulo de inferencia sí va en estricto)
"""Experimento IA-10: riesgo de incumplir el plazo (SLA) de una disputa al radicarla.

Uso: `uv run python -m latam_ia.experimentos.riesgo_plazo [--fecha AAAA-MM-DD] [--sin-cache] [--reps 1000]`

Consulta BigQuery (`latam_bank`, ADC), parte por fecha de creación, entrena con rasgos conocidos al radicar,
calibra (Platt) y fija umbrales en validación, evalúa una sola vez en prueba y escribe el reporte y la ficha en
`ia/evaluacion/reportes/`. Compara dos etiquetas (SLA incumplido y escalamiento). Artefactos en `ia/artefactos/`.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any

import db_dtypes  # noqa: F401  (registra dbdate para leer la caché parquet)
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from latam_ia.comprension.riesgo_plazo import CAT, NUM, ModeloCalibradoRiesgo, columnas
from latam_ia.experimentos.metricas import bootstrap_clusters

PROYECTO = "latam-bank-hackaton-2026"
SEMILLA = 202616737
T1 = dt.datetime(2025, 3, 1)  # entrenamiento: creación < T1
T2 = dt.datetime(2025, 10, 1)  # validación: T1 <= creación < T2; prueba: >= T2
RAIZ = Path(__file__).resolve().parents[3]
REPORTES = RAIZ / "evaluacion" / "reportes"
ARTEFACTOS = RAIZ / "artefactos"
LIFT_OBJETIVO = (
    1.5  # precisión objetivo = 1,5 veces la prevalencia de validación (fijada antes de mirar prueba)
)
KS = (0.05, 0.10, 0.20)
ETIQUETAS = {"sla": "SLA incumplido", "escalado": "Escalada"}
GB = "árboles calibrados"

SQL = """
with q as (
  select c.complaint_id, c.creation_date, c.customer_id, c.case_type, c.category, c.subcategory,
    c.reception_channel, c.affected_product_id, c.claimed_amount, c.currency, c.priority, c.status,
    c.sla_breached, c.first_response_date, c.resolution_date, c.resolution_days, c.is_repeat_complainer,
    count(*) over (partition by c.customer_id order by c.creation_date, c.complaint_id
                   rows between unbounded preceding and 1 preceding) quejas_previas
  from latam_bank.plata_complaints c
)
select q.*, u.segment, u.country, u.registration_date, p.product_type,
  (select count(*) from latam_bank.plata_transactions t where t.customer_id = q.customer_id
     and t.transaction_date < q.creation_date and t.transaction_date >= datetime_sub(q.creation_date, interval 30 day)) n_tx_30d,
  (select sum(t.amount_usd) from latam_bank.plata_transactions t where t.customer_id = q.customer_id
     and t.transaction_date < q.creation_date and t.transaction_date >= datetime_sub(q.creation_date, interval 30 day)) monto_tx_30d_usd
from q left join latam_bank.plata_customers u using (customer_id)
left join latam_bank.plata_products p on p.product_id = q.affected_product_id
"""


def cargar(sin_cache: bool) -> pd.DataFrame:
    ARTEFACTOS.mkdir(exist_ok=True)
    cache = ARTEFACTOS / "quejas_riesgo.parquet"
    if cache.exists() and not sin_cache:
        return pd.read_parquet(cache)
    from google.cloud import bigquery

    df = bigquery.Client(project=PROYECTO).query(SQL).to_dataframe()
    df.to_parquet(cache)
    return df


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Rasgos de radicación. Estado, fechas de respuesta o cierre, prioridad y reincidente no son rasgos."""
    cre = pd.to_datetime(df["creation_date"])
    d = pd.DataFrame(
        {
            "id": df["complaint_id"],
            "cliente": df["customer_id"],
            "fecha": cre,
            "categoria": df["category"],
            "subcategoria": df["subcategory"].fillna("sin subcategoría"),
            "tipo_caso": df["case_type"],
            "canal": df["reception_channel"],
            "pais": df["country"],
            "segmento": df["segment"],
            "tipo_producto": df["product_type"],
            "moneda": df["currency"],
            "antiguedad_dias": (cre.dt.normalize() - pd.to_datetime(df["registration_date"]))
            .dt.days.clip(lower=0)
            .astype(float),
            "quejas_previas": df["quejas_previas"].astype(float),
            "hora": cre.dt.hour.astype(float),
            "dia_semana": cre.dt.dayofweek.astype(float),
            "n_tx_30d": df["n_tx_30d"].astype(float),
            "monto_tx_30d_usd": df["monto_tx_30d_usd"].astype(float),
            "monto_reclamado": df["claimed_amount"].astype(float),
            # Etiquetas (resultados posteriores a la radicación)
            "y_sla": df["sla_breached"].astype(int),
            "y_escalado": (df["status"] == "Escalated").astype(int),
            # Solo para auditar (nunca rasgos)
            "_horas_resp": (pd.to_datetime(df["first_response_date"]) - cre).dt.total_seconds() / 3600,
            "_dias_res": df["resolution_days"].astype(float),
            "_estado": df["status"],
            "_prioridad": df["priority"],
            "_reincidente": df["is_repeat_complainer"].astype(float),
        }
    )
    d["disputa"] = d["subcategoria"] == "Cargo no reconocido"
    return d


def particionar(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    f = d["fecha"]
    return d[f < T1].copy(), d[(f >= T1) & (f < T2)].copy(), d[f >= T2].copy()


# ------------------------------------------------------------------------------------------ modelos


def _prepro() -> ColumnTransformer:
    num = Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)), ("esc", StandardScaler())])
    return ColumnTransformer(
        [
            ("num", num, list(NUM)),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), list(CAT)),
        ]
    )


def construir(nombre: str, max_depth: int = 3, iters: int = 150) -> Pipeline:
    if nombre == "logistica":
        modelo: Any = LogisticRegression(C=0.1, max_iter=500, random_state=SEMILLA)
    else:
        modelo = HistGradientBoostingClassifier(
            max_depth=max_depth,
            learning_rate=0.05,
            max_iter=iters,
            l2_regularization=1.0,
            min_samples_leaf=200,
            random_state=SEMILLA,
        )
    return Pipeline([("pre", _prepro()), ("clf", modelo)])


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def ajustar_platt(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    lr = LogisticRegression(C=1e6, max_iter=500).fit(_logit(p).reshape(-1, 1), y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def aplicar_platt(p: np.ndarray, ab: tuple[float, float]) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-(ab[0] * _logit(p) + ab[1])))


def _deciles(p: np.ndarray, bins: int = 10) -> np.ndarray:
    cortes = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)[1:-1]))
    return np.digitize(p, cortes)


def ece_binario(p: np.ndarray, y: np.ndarray) -> float:
    c = _deciles(p)
    return float(sum((c == b).mean() * abs(y[c == b].mean() - p[c == b].mean()) for b in np.unique(c)))


def tabla_calibracion(p: np.ndarray, y: np.ndarray) -> list[tuple[float, float, int]]:
    c = _deciles(p)
    return [(float(p[c == b].mean()), float(y[c == b].mean()), int((c == b).sum())) for b in np.unique(c)]


def umbral_precision(p: np.ndarray, y: np.ndarray, objetivo: float) -> float | None:
    """Menor umbral con precisión >= objetivo y al menos 50 casos señalados (validación)."""
    orden = np.argsort(-p, kind="stable")
    n = np.arange(1, len(p) + 1)
    prec = np.cumsum(y[orden]) / n
    ok = np.where((prec >= objetivo) & (n >= 50))[0]
    return float(p[orden][ok.max()]) if len(ok) else None


def recall_precision(
    p: np.ndarray, y: np.ndarray, umbral: float | None, w: np.ndarray
) -> tuple[float, float]:
    if umbral is None:
        return 0.0, float("nan")
    s = p >= umbral
    tp, marcados = (w * s * y).sum(), (w * s).sum()
    return float(tp / (w * y).sum()), float(tp / marcados) if marcados else float("nan")


def captura_topk(p: np.ndarray, y: np.ndarray, k: float, w: np.ndarray) -> float:
    """Fracción de los incumplimientos que caen en el k% de mayor riesgo (simulación de priorización)."""
    top = np.argsort(-p, kind="stable")[: max(1, int(round(k * len(p))))]
    marca = np.zeros(len(p), dtype=bool)
    marca[top] = True
    return float((w * marca * y).sum() / (w * y).sum())


# ----------------------------------------------------------------------------------------- auditoría


def _auc(x: pd.Series, y: pd.Series) -> float:
    m = x.notna()
    return float(roc_auc_score(y[m], x[m])) if m.sum() > 100 and y[m].nunique() == 2 else float("nan")


def auditar(d: pd.DataFrame) -> dict[str, Any]:
    """Validez de las etiquetas: ¿el SLA incumplido se relaciona con lo que debería medirlo?"""
    por_estado = d.groupby("_estado").agg(
        n=("y_sla", "size"), sla=("y_sla", "mean"), sin_resp=("_horas_resp", lambda s: s.isna().mean())
    )
    prio = d["_prioridad"].map({"Low": 0, "Medium": 1, "High": 2, "Critical": 3})
    return {
        "n": len(d),
        "prev_sla": float(d["y_sla"].mean()),
        "prev_esc": float(d["y_escalado"].mean()),
        "auc_horas_resp": _auc(d["_horas_resp"], d["y_sla"]),
        "auc_dias_res": _auc(d["_dias_res"], d["y_sla"]),
        "horas_resp_incumple": float(d.loc[d["y_sla"] == 1, "_horas_resp"].median()),
        "horas_resp_cumple": float(d.loc[d["y_sla"] == 0, "_horas_resp"].median()),
        "sla_en_abiertos": float(d.loc[d["_estado"] == "Open", "y_sla"].mean()),
        "n_abiertos": int((d["_estado"] == "Open").sum()),
        "por_estado": por_estado.round(4).reset_index().to_dict("records"),
        "auc_prioridad": _auc(prio, d["y_sla"]),
        "auc_reincidente": _auc(d["_reincidente"], d["y_sla"]),
        "esc_sin_resp": float(d.loc[d["y_escalado"] == 1, "_horas_resp"].isna().mean()),
        "sd_mensual": float(d.groupby(d["fecha"].dt.to_period("M"))["y_sla"].mean().std()),
        "monto_nulo": float(d["monto_reclamado"].isna().mean()),
        "ids_duplicados": int(d["id"].duplicated().sum()),
    }


# ------------------------------------------------------------------------------------------ ejecución


def evaluar_etiqueta(
    et: str, tr: pd.DataFrame, va: pd.DataFrame, te: pd.DataFrame, reps: int
) -> dict[str, Any]:
    cols = columnas()
    ytr, yv, yt = tr[f"y_{et}"].to_numpy(), va[f"y_{et}"].to_numpy(), te[f"y_{et}"].to_numpy()
    prev_tr = float(ytr.mean())

    tasa = tr.groupby("subcategoria")[f"y_{et}"].mean()
    log = construir("logistica").fit(tr[cols], ytr)
    mejor: Any = None
    mejor_ap, cfg = -1.0, (3, 150)
    for md in (2, 3, 4):
        for it in (60, 150, 300):
            m = construir("arboles", md, it).fit(tr[cols], ytr)
            ap = average_precision_score(yv, m.predict_proba(va[cols])[:, 1])
            if ap > mejor_ap:
                mejor, mejor_ap, cfg = m, ap, (md, it)
    crudo_v, crudo_t = mejor.predict_proba(va[cols])[:, 1], mejor.predict_proba(te[cols])[:, 1]
    ab = ajustar_platt(crudo_v, yv)
    p_gb_v, p_gb_t = aplicar_platt(crudo_v, ab), aplicar_platt(crudo_t, ab)

    perm = construir("arboles", *cfg).fit(tr[cols], np.random.default_rng(SEMILLA).permutation(ytr))
    ap_perm = float(average_precision_score(yt, perm.predict_proba(te[cols])[:, 1]))

    sistemas = {
        "mayoritaria": (np.full(len(va), prev_tr), np.full(len(te), prev_tr)),
        "regla por subcategoría": tuple(
            d["subcategoria"].map(tasa).fillna(prev_tr).to_numpy() for d in (va, te)
        ),
        "regresión logística": (log.predict_proba(va[cols])[:, 1], log.predict_proba(te[cols])[:, 1]),
        GB: (p_gb_v, p_gb_t),
    }
    objetivo = LIFT_OBJETIVO * float(yv.mean())
    umbrales = {n: umbral_precision(pv, yv, objetivo) for n, (pv, _) in sistemas.items()}
    nombres = list(sistemas)
    # desempate determinista de la mayoritaria y de la regla (empates) para AUC-PR
    ruido = 1e-9 * np.random.default_rng(SEMILLA).random(len(te))

    def estad(w: np.ndarray) -> dict[str, float]:
        out: dict[str, float] = {}
        for n in nombres:
            pt = sistemas[n][1]
            out[f"ap:{n}"] = float(average_precision_score(yt, pt + ruido, sample_weight=w))
            out[f"auc:{n}"] = float(roc_auc_score(yt, pt + ruido, sample_weight=w))
            out[f"recall:{n}"], out[f"prec:{n}"] = recall_precision(pt, yt, umbrales[n], w)
            for k in KS:
                out[f"top{int(k * 100)}:{n}"] = captura_topk(pt + ruido, yt, k, w)
        out["dap:gb-prev"] = out[f"ap:{GB}"] - float((w * yt).sum() / w.sum())
        out["dap:gb-regla"] = out[f"ap:{GB}"] - out["ap:regla por subcategoría"]
        out["dap:gb-log"] = out[f"ap:{GB}"] - out["ap:regresión logística"]
        out["dauc:gb-azar"] = out[f"auc:{GB}"] - 0.5
        return out

    puntual = estad(np.ones(len(te)))
    ic = bootstrap_clusters(te["cliente"].to_numpy(), estad, reps, SEMILLA)

    m_d = te["disputa"].to_numpy()
    sub = {
        "n": int(m_d.sum()),
        "prev": float(yt[m_d].mean()),
        "ap": float(average_precision_score(yt[m_d], p_gb_t[m_d])),
        "auc": float(roc_auc_score(yt[m_d], p_gb_t[m_d])),
    }
    from sklearn.inspection import permutation_importance

    idx = np.random.default_rng(SEMILLA).choice(len(va), min(8000, len(va)), replace=False)
    imp_r = permutation_importance(
        mejor, va[cols].iloc[idx], yv[idx], scoring="average_precision", n_repeats=5, random_state=SEMILLA
    )
    imp = dict(sorted(zip(cols, imp_r.importances_mean.round(5), strict=True), key=lambda kv: -kv[1])[:5])
    return {
        "prev": {"tr": prev_tr, "va": float(yv.mean()), "te": float(yt.mean())},
        "cfg": cfg,
        "platt": ab,
        "puntual": puntual,
        "ic": ic,
        "umbrales": umbrales,
        "objetivo": objetivo,
        "sistemas": nombres,
        "ap_permutado": ap_perm,
        "sub": sub,
        "imp": imp,
        "ece": {
            "val": ece_binario(p_gb_v, yv),
            "te": ece_binario(p_gb_t, yt),
            "crudo_te": ece_binario(crudo_t, yt),
        },
        "brier": {
            "gb": float(((p_gb_t - yt) ** 2).mean()),
            "prev": float(((prev_tr - yt) ** 2).mean()),
        },
        "cal_test": tabla_calibracion(p_gb_t, yt),
        "region": (float(np.quantile(p_gb_v, 0.01)), float(np.quantile(p_gb_v, 0.99))),
        "modelo": mejor,
    }


def hay_senal(r: dict[str, Any]) -> bool:
    """Señal solo si los IC 95% de AUC-PR menos prevalencia, menos regla y de AUC menos 0,5 excluyen 0."""
    ic = r["ic"]
    return ic["dap:gb-prev"][0] > 0 and ic["dap:gb-regla"][0] > 0 and ic["dauc:gb-azar"][0] > 0


def pct(v: float) -> str:
    return "n/a" if v != v else f"{v:.1%}"


def ic3(par: tuple[float, float]) -> str:
    return f"[{par[0]:.3f}, {par[1]:.3f}]"


def miles(x: int | float) -> str:
    return f"{int(x):,}".replace(",", ".")


def ejecutar(fecha: str, sin_cache: bool, reps: int) -> dict[str, Any]:
    d = preparar(cargar(sin_cache))
    tr, va, te = particionar(d)
    aud = auditar(d)
    aud["solape_clientes"] = len(set(te["cliente"]) & set(tr["cliente"])) / te["cliente"].nunique()
    res = {et: evaluar_etiqueta(et, tr, va, te, reps) for et in ETIQUETAS}
    return {
        "fecha": fecha,
        "aud": aud,
        "res": res,
        "n": {"tr": len(tr), "va": len(va), "te": len(te)},
        "rangos": {k: (x["fecha"].min(), x["fecha"].max()) for k, x in (("tr", tr), ("va", va), ("te", te))},
        "reps": reps,
    }


def seccion_resultados(r: dict[str, Any], nom: str, num: int) -> list[str]:
    p, ic = r["puntual"], r["ic"]
    L = [f"## {num}. Resultados en prueba: {nom}\n"]
    L.append(
        f"Precisión objetivo para el recall a precisión fija: {r['objetivo']:.3f} (1,5 veces la prevalencia de validación, fijada antes de mirar prueba); el umbral de cada sistema se elige en validación.\n"
    )
    L.append(
        "| Sistema | AUC-PR | IC 95% | AUC | Recall a precisión objetivo | Precisión lograda |\n|---|---|---|---|---|---|"
    )
    for nm in r["sistemas"]:
        ok = r["umbrales"][nm] is not None
        rec = f"{p['recall:' + nm]:.3f}" if ok else "no alcanzable"
        pr = f"{p['prec:' + nm]:.3f}" if ok else "n/a"
        L.append(
            f"| {nm} | {p['ap:' + nm]:.3f} | {ic3(ic['ap:' + nm])} | {p['auc:' + nm]:.3f} | {rec} | {pr} |"
        )
    L.append(
        f"\nDiferencias con IC: AUC-PR del modelo menos la prevalencia {ic3(ic['dap:gb-prev'])}, menos la regla {ic3(ic['dap:gb-regla'])}, menos la logística {ic3(ic['dap:gb-log'])}; AUC menos 0,5 {ic3(ic['dauc:gb-azar'])}. Control con etiqueta permutada: AUC-PR {r['ap_permutado']:.3f}.\n"
    )
    L.append(
        f"**Calibración (prueba).** ECE {r['ece']['te']:.4f} (validación {r['ece']['val']:.4f}; sin calibrar {r['ece']['crudo_te']:.4f}); Brier {r['brier']['gb']:.4f} contra {r['brier']['prev']:.4f} de la prevalencia. Por deciles de probabilidad:\n"
    )
    L.append("| Decil | Probabilidad media | Frecuencia observada | Casos |\n|---|---|---|---|")
    for i, (pm, fo, nn) in enumerate(r["cal_test"], 1):
        L.append(f"| {i} | {pm:.3f} | {fo:.3f} | {miles(nn)} |")
    L.append(
        "\n**Análisis de decisión (simulación fuera de línea, sin humanos reales).** Si el k% de mayor riesgo se prioriza a la cola humana, esta es la fracción de los incumplimientos (o escaladas) que se anticipa. Un orden al azar captura k%.\n"
    )
    L.append("| k | Modelo | IC 95% | Regla por subcategoría | Azar |\n|---|---|---|---|---|")
    for k in KS:
        kk = f"top{int(k * 100)}"
        L.append(
            f"| {int(k * 100)}% | {pct(p[kk + ':' + GB])} | {ic3(ic[kk + ':' + GB])} | {pct(p[kk + ':regla por subcategoría'])} | {pct(k)} |"
        )
    sb = r["sub"]
    L.append(
        f"\nSubgrupo cargos no reconocidos en prueba (n = {miles(sb['n'])}, prevalencia {pct(sb['prev'])}): AUC-PR {sb['ap']:.3f}, AUC {sb['auc']:.3f}. "
        f"Importancia por permutación en validación (caída de AUC-PR), mayores: {', '.join(f'{k} {v:.4f}' for k, v in r['imp'].items())}.\n"
    )
    L.append(
        f"Señal sobre las líneas base: **{'sí' if hay_senal(r) else 'no'}** (se exige que los tres IC excluyan 0).\n"
    )
    return L


def redactar(s: dict[str, Any]) -> str:
    a, n = s["aud"], s["n"]
    rs, re_ = s["res"]["sla"], s["res"]["escalado"]
    L = [f"# Riesgo de incumplir el plazo de una disputa, reporte {s['fecha']}\n"]
    L.append(
        "Segundo componente aprendido, atado al flujo de disputas: al radicar, ¿se puede anticipar que el caso incumplirá el SLA (o será escalado)? "
        f"Reproducible con `uv run python -m latam_ia.experimentos.riesgo_plazo`. Datos: `latam_bank.plata_complaints` ({miles(a['n'])} quejas, sin texto libre), unida a clientes, productos y transacciones previas a la radicación. Todo lo de decisión es una simulación fuera de línea.\n"
    )
    L.append("## Resumen\n")
    for r, nom in ((rs, "SLA incumplido"), (re_, "Escalada")):
        p, ic = r["puntual"], r["ic"]
        L.append(
            f"- **{nom}** (prevalencia en prueba {pct(r['prev']['te'])}): AUC-PR de los árboles calibrados {p['ap:' + GB]:.3f} {ic3(ic['ap:' + GB])} contra {p['ap:mayoritaria']:.3f} de la mayoritaria, {p['ap:regla por subcategoría']:.3f} de la regla por subcategoría y {p['ap:regresión logística']:.3f} de la logística; "
            f"AUC {p['auc:' + GB]:.3f} {ic3(ic['auc:' + GB])}. Señal sobre las líneas base: **{'sí' if hay_senal(r) else 'no'}**."
        )
    L.append(
        f"- Auditoría: el SLA incumplido no guarda relación con lo que debería medirlo. Mediana de horas a la primera respuesta {a['horas_resp_incumple']:.1f} h en incumplidos y {a['horas_resp_cumple']:.1f} h en cumplidos (AUC {a['auc_horas_resp']:.3f}); AUC con los días a la resolución {a['auc_dias_res']:.3f}; "
        f"{pct(a['sla_en_abiertos'])} de los {miles(a['n_abiertos'])} casos aún abiertos ya figuran como incumplidos (contra {pct(a['prev_sla'])} en total)."
    )
    cierre = (
        "Se entrega la pista con abstención calibrada."
        if hay_senal(rs) or hay_senal(re_)
        else "No hay señal verificable más allá de las líneas base. La pista se entrega como infraestructura que se abstiene siempre, y no se afirma ninguna ganancia."
    )
    L.append(f"- Conclusión: {cierre}\n")

    L.append("## 1. Elección de la etiqueta y auditoría\n")
    L.append(
        f"Se comparan dos etiquetas, ambas resultados posteriores a la radicación. **SLA incumplido** (`sla_breached`) es la métrica de la línea base del problema (20,4% en cargos no reconocidos). **Escalada** es `status = Escalated` ({pct(a['prev_esc'])}).\n"
    )
    L.append(
        f"- `sla_breached` no se deriva de los tiempos registrados: la primera respuesta tarda lo mismo en incumplidos y cumplidos (AUC {a['auc_horas_resp']:.3f}; 0,5 es azar) y no hay relación con `resolution_days` (AUC {a['auc_dias_res']:.3f}). Tampoco con la prioridad (AUC {a['auc_prioridad']:.3f}) ni con el reincidente (AUC {a['auc_reincidente']:.3f}). La tasa mensual es plana (desviación estándar entre meses {a['sd_mensual']:.3f}).\n"
        "- Por estado (SLA incumplido y casos sin primera respuesta):\n"
    )
    L.append("| Estado | Casos | SLA incumplido | Sin primera respuesta |\n|---|---|---|---|")
    for f in a["por_estado"]:
        L.append(f"| {f['_estado']} | {miles(f['n'])} | {pct(f['sla'])} | {pct(f['sin_resp'])} |")
    L.append(
        f"\n- `Escalated` es un estado final observado: {pct(a['esc_sin_resp'])} de las escaladas no tiene primera respuesta registrada. Los casos recientes pueden escalar después del corte (censura por la derecha), de modo que la etiqueta subestima los últimos meses.\n"
        f"- Calidad: {miles(a['ids_duplicados'])} identificadores duplicados; monto reclamado vacío en {pct(a['monto_nulo'])}.\n"
    )
    L.append(
        "Veredicto: el SLA incumplido es la etiqueta de interés operativo, pero su validez es dudosa en estos datos (no responde a nada medible); la escalada es un estado real pero censurado. Se evalúan ambas con el mismo procedimiento y se reportan las dos sin escoger la que salga mejor.\n"
    )
    L.append("## 2. Rasgos y fuga\n")
    L.append(
        "Solo lo conocido al radicar: categoría, subcategoría, tipo de caso, canal de recepción, país y segmento del cliente, tipo del producto afectado, moneda, monto reclamado (con indicador de faltante), antigüedad del cliente, número de quejas previas del cliente (estrictamente anteriores a la creación), hora y día de la semana, y número y monto de transacciones del cliente en los 30 días previos (las quejas no se enlazan a una transacción).\n\n"
        "**Excluidos por ser posteriores o derivados:** `status`, `assignment_date`, `first_response_date`, `resolution_date`, `closing_date`, `resolution_days`, `compensation_granted`, `resolution_satisfaction`, `assigned_agent_id`. También `priority` (no se sabe si la fija el cliente o el triaje) e `is_repeat_complainer` (no consta cuándo se calcula); ambos tienen AUC cercano a 0,5 con la etiqueta, así que excluirlos no cuesta señal. Los identificadores no son rasgos.\n"
    )
    L.append("## 3. Partición\n")
    L.append(
        "| Parte | Rango de creación | Casos | Prevalencia SLA | Prevalencia escalada |\n|---|---|---|---|---|"
    )
    for k, nom in (("tr", "Entrenamiento"), ("va", "Validación"), ("te", "Prueba")):
        rg = s["rangos"][k]
        L.append(
            f"| {nom} | {rg[0]:%Y-%m-%d} a {rg[1]:%Y-%m-%d} | {miles(n[k])} | {pct(rs['prev'][k])} | {pct(re_['prev'][k])} |"
        )
    L.append(
        f"\nPartición temporal: calibración y umbrales solo con validación; la prueba se evalúa una vez. {pct(a['solape_clientes'])} de los clientes de prueba tienen quejas en entrenamiento; los IC son bootstrap por cliente (pesos Poisson, {s['reps']} réplicas, semilla {SEMILLA}).\n"
    )
    L.append("## 4. Modelos\n")
    L.append(
        "- **Mayoritaria**: la prevalencia de entrenamiento para todos.\n"
        "- **Regla por subcategoría**: tasa de entrenamiento de la subcategoría.\n"
        "- **Regresión logística** (C = 0,1) sobre todos los rasgos.\n"
        f"- **Árboles de gradiente** (HistGradientBoosting; profundidad e iteraciones elegidas por AUC-PR en validación: SLA {rs['cfg']}, escalada {re_['cfg']}) con escalado de Platt ajustado en validación. "
        f"Control de azar: el mismo modelo con la etiqueta permutada rinde AUC-PR {rs['ap_permutado']:.3f} (SLA) y {re_['ap_permutado']:.3f} (escalada) en prueba, contra prevalencias {pct(rs['prev']['te'])} y {pct(re_['prev']['te'])}.\n"
    )
    L += seccion_resultados(rs, "SLA incumplido", 5)
    L += seccion_resultados(re_, "Escalada", 6)
    L.append("## 7. Errores y límites\n")
    L.append(
        "- Con una etiqueta sin relación con ningún rasgo medible, lo esperable es un AUC cercano a 0,5 y una captura por k% igual a k%; los resultados se leen contra ese techo.\n"
        "- Las tasas por subcategoría, canal y país están todas entre 19% y 22%: las diferencias caen dentro del ruido de muestreo de cada celda.\n"
        "- Las transacciones no se enlazan a la queja, así que ese rasgo describe al cliente y no a la disputa.\n"
        "- Datos sintéticos: la ausencia de señal aquí no prueba que no exista en un banco real; solo que este experimento no sostiene una afirmación de mejora.\n"
    )
    L.append("## 8. Integración\n")
    L.append(
        "`riesgo_plazo(caso, modelo) -> PistaRiesgo` (probabilidad, banda, abstención) en `latam_ia.comprension.riesgo_plazo`. Devuelve probabilidad solo si el experimento halló señal y dentro de la región de validación (percentiles 1 a 99). "
        '`construir_paquete` la usa únicamente para subir un nivel la prioridad del traspaso (hasta P2) y agregar el plazo "En riesgo de plazo"; nunca para negar, decidir o ejecutar. Sin señal verificada no cambia nada.\n'
    )
    return "\n".join(L)


def ficha(s: dict[str, Any]) -> str:
    rs, re_ = s["res"]["sla"], s["res"]["escalado"]
    p, ic, pe, ice = rs["puntual"], rs["ic"], re_["puntual"], re_["ic"]
    senal = hay_senal(rs) or hay_senal(re_)
    return f"""# Ficha del modelo: riesgo de plazo de una disputa, {s["fecha"]}

Versión `riesgo-plazo-{s["fecha"]}`. Pista de prioridad al radicar una disputa: no actúa, no niega, no decide.

**Uso previsto.** Subir un nivel la prioridad del traspaso a una persona y mostrar "en riesgo de plazo" cuando la banda es alta y la calibración está verificada. **Fuera de alcance:** denegar, retrasar o decidir sobre un caso, evaluar agentes o clientes, y cualquier uso con efecto en el cliente.

**Datos.** `latam_bank.plata_complaints` con clientes, productos y transacciones previas; 2023-06-17 a 2026-06-18; sintéticos. Partición temporal: entrenamiento antes de 2025-03-01, validación antes de 2025-10-01, prueba posterior. Sin campos posteriores a la radicación.

**Modelo.** Árboles de gradiente con escalado de Platt (validación); semilla {SEMILLA}. Etiquetas: SLA incumplido y escalada.

**Desempeño en prueba (IC 95% por cliente).** SLA incumplido: AUC-PR {p["ap:" + GB]:.3f} {ic3(ic["ap:" + GB])} con prevalencia {pct(rs["prev"]["te"])}; AUC {p["auc:" + GB]:.3f} {ic3(ic["auc:" + GB])}. Escalada: AUC-PR {pe["ap:" + GB]:.3f} {ic3(ice["ap:" + GB])} con prevalencia {pct(re_["prev"]["te"])}. Señal sobre las líneas base: **{"sí" if senal else "no"}**. ECE (SLA) {rs["ece"]["te"]:.4f}.

**Limitaciones.** Etiqueta de SLA sin relación con los tiempos registrados; escalada censurada por la derecha; datos sintéticos; las quejas no se enlazan a una transacción; sin texto del cliente. {"La pista se abstiene siempre porque no hubo señal." if not senal else "La probabilidad solo es válida en la región calibrada."}

**Gobierno.** Pista sin acción permitida; los umbrales son un parámetro de política y se reentrenan con un nuevo reporte, no a mano. Reporte completo: `riesgo_plazo_{s["fecha"]}.md`.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    ap.add_argument("--sin-cache", action="store_true", help="vuelve a consultar BigQuery")
    ap.add_argument("--reps", type=int, default=1000)
    a = ap.parse_args()
    s = ejecutar(a.fecha, a.sin_cache, a.reps)
    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / f"riesgo_plazo_{a.fecha}.md").write_text(redactar(s), encoding="utf-8")
    (REPORTES / f"modelcard_riesgo_plazo_{a.fecha}.md").write_text(ficha(s), encoding="utf-8")
    r = s["res"]["sla"]
    umb = r["umbrales"][GB]
    modelo = ModeloCalibradoRiesgo(
        r["modelo"],
        r["platt"],
        umb if umb is not None else 1.0,
        r["prev"]["va"],
        r["region"],
        hay_senal(r),  # el SLA es la etiqueta que la pista usaría
        f"riesgo-plazo-{a.fecha}",
    )
    joblib.dump(modelo, ARTEFACTOS / "riesgo_plazo.joblib")
    print(f"listo: {REPORTES / f'riesgo_plazo_{a.fecha}.md'}")


if __name__ == "__main__":
    main()
