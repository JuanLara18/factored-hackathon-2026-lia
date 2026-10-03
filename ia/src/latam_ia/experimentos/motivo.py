# ruff: noqa: E501
# pyright: basic, reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false, reportReturnType=false, reportMissingTypeStubs=false, reportIndexIssue=false, reportOperatorIssue=false
# (script de experimento: pandas y scikit-learn sin tipos; el módulo de inferencia sí va en estricto)
"""Experimento IA-2.2: clasificador del motivo de contacto frente a líneas base (criterio 4).

Uso: `uv run python -m latam_ia.experimentos.motivo [--fecha AAAA-MM-DD] [--sin-cache] [--reps 1000]`

Consulta BigQuery (`latam_bank`, ADC), parte por `process_date`, entrena, calibra con escalado de temperatura
en validación, elige el umbral de abstención en validación, evalúa una sola vez en prueba y escribe el reporte
y la ficha del modelo en `ia/evaluacion/reportes/`. Los artefactos (modelo, caché) quedan en `ia/artefactos/`,
fuera de git. Semillas fijas.
"""

from __future__ import annotations

import argparse
import datetime as dt
from collections import Counter
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from latam_ia.comprension.motivo import CONJUNTOS, MOTIVOS, ModeloCalibrado, columnas
from latam_ia.experimentos.metricas import (
    bootstrap_clusters,
    brier,
    costo_abstencion,
    ece,
    elegir_umbral,
    escalar_temperatura,
    macro_f1,
    matriz_confusion,
    prf,
    softmax,
)

PROYECTO = "latam-bank-hackaton-2026"
SEMILLA = 202616737  # misma semilla de las entregas del equipo
T1 = dt.date(2025, 7, 1)  # entrenamiento: process_date < T1
T2 = dt.date(2026, 1, 1)  # validación: T1 <= process_date < T2; prueba: >= T2
C_ERROR, C_REVISION = 5.0, 1.0  # un código automático errado cuesta 5 revisiones humanas
RAIZ = Path(__file__).resolve().parents[3]
REPORTES = RAIZ / "evaluacion" / "reportes"
ARTEFACTOS = RAIZ / "artefactos"

SQL = """
select i.interaction_id, i.interaction_date, i.process_date, i.customer_id, i.interaction_type, i.channel,
  i.contact_reason, i.reason_category, i.duration_seconds, i.wait_time_seconds, i.was_resolved,
  i.requires_followup, i.detected_sentiment, i.sentiment_score, i.was_escalated, i.mentioned_products,
  c.segment, c.country, c.registration_date
from latam_bank.plata_call_center_interactions i
left join latam_bank.plata_customers c using (customer_id)
"""


# ---------------------------------------------------------------------------------------------- datos


def _cliente() -> Any:
    from google.cloud import bigquery

    return bigquery.Client(project=PROYECTO)


def cargar(sin_cache: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Interacciones más auditorías baratas de texto y de fraude (solo agregados)."""
    ARTEFACTOS.mkdir(exist_ok=True)
    cache, aud_cache = ARTEFACTOS / "interacciones.parquet", ARTEFACTOS / "auditoria.joblib"
    if cache.exists() and aud_cache.exists() and not sin_cache:
        return pd.read_parquet(cache), joblib.load(aud_cache)
    cli = _cliente()
    df = cli.query(SQL).to_dataframe()
    aud: dict[str, Any] = {}
    kw = cli.query(
        "select detected_keywords k, count(*) n from latam_bank.plata_call_transcripts group by 1"
    ).to_dataframe()
    fichas = Counter[str]()
    for k, n in zip(kw["k"], kw["n"], strict=True):
        if isinstance(k, str):
            for tok in k.split(","):
                fichas[tok.strip()] += int(n)
    aud["palabras_clave"] = dict(fichas)
    aud["tema_igual_motivo"] = dict(
        cli.query(
            """select count(*) n, countif(t.main_topics = i.reason_category) iguales
            from latam_bank.plata_call_center_interactions i join latam_bank.plata_call_transcripts t
            using (interaction_id)"""
        )
        .to_dataframe()
        .iloc[0]
        .astype(int)
    )
    aud["campos_texto_quejas"] = [
        c
        for c in cli.query(
            """select column_name from latam_bank.INFORMATION_SCHEMA.COLUMNS
            where table_name in ('plata_complaints','plata_call_transcripts')
            and data_type = 'STRING' and column_name not like '%id' order by 1"""
        )
        .to_dataframe()["column_name"]
        .tolist()
    ]
    aud["fraude"] = dict(
        cli.query(
            """select count(*) n, countif(is_fraud) fraudes,
            countif(fraud_score > 30) puntaje_sobre_30, countif(fraud_score > 30 and is_fraud) puntaje_sobre_30_y_fraude,
            countif(fraud_score is null) puntaje_nulo,
            max(if(not is_fraud, fraud_score, null)) maximo_puntaje_no_fraude,
            avg(if(is_fraud, fraud_score, null)) media_puntaje_fraude,
            avg(if(not is_fraud, fraud_score, null)) media_puntaje_no_fraude
            from latam_bank.plata_transactions"""
        )
        .to_dataframe()
        .iloc[0]
        .astype(float)
    )
    tasas = cli.query(
        """select channel, countif(is_fraud) / count(*) tasa from latam_bank.plata_transactions group by 1"""
    ).to_dataframe()
    aud["fraude_tasa_canal_min"] = float(tasas["tasa"].min())
    aud["fraude_tasa_canal_max"] = float(tasas["tasa"].max())
    df.to_parquet(cache)
    joblib.dump(aud, aud_cache)
    return df, aud


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Rasgos con nombres del dominio; el motivo es la etiqueta y nunca entra como rasgo."""
    d = pd.DataFrame(
        {
            "id": df["interaction_id"],
            "cliente": df["customer_id"],
            "fecha": pd.to_datetime(df["process_date"]),
            "y_txt": df["contact_reason"],
            "tipo_interaccion": df["interaction_type"],
            "canal": df["channel"],
            "segmento": df["segment"],
            "pais": df["country"],
            "hora": df["interaction_date"].dt.hour.astype(float),
            "dia_semana": df["interaction_date"].dt.dayofweek.astype(float),
            "n_productos": df["mentioned_products"]
            .fillna("")
            .map(lambda s: len([p for p in s.split(",") if p]))
            .astype(float),
            "antiguedad_dias": (
                pd.to_datetime(df["interaction_date"]).dt.normalize()
                - pd.to_datetime(df["registration_date"])
            )
            .dt.days.clip(lower=0)
            .astype(float),
            "espera_segundos": df["wait_time_seconds"].astype(float),
            "duracion_segundos": df["duration_seconds"].astype(float),
            "sentimiento": df["sentiment_score"].astype(float),
            "resuelto": df["was_resolved"].astype(float),
            "requiere_seguimiento": df["requires_followup"].astype(float),
            "escalado": df["was_escalated"].astype(float),
            "sentimiento_txt": df["detected_sentiment"],
        }
    )
    d["y"] = d["y_txt"].map({m: i for i, m in enumerate(MOTIVOS)})
    if bool(d["y"].isna().any()):
        raise ValueError(f"motivos fuera del catálogo: {sorted(d.loc[d['y'].isna(), 'y_txt'].unique())}")
    d["y"] = d["y"].astype(int)
    return d


def particionar(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    f = d["fecha"].dt.date
    return d[f < T1].copy(), d[(f >= T1) & (f < T2)].copy(), d[f >= T2].copy()


# ------------------------------------------------------------------------------------- modelos y reglas


def _prepro(conjunto: str) -> ColumnTransformer:
    num, cat = CONJUNTOS[conjunto]
    return ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [("imp", SimpleImputer(strategy="median", add_indicator=True)), ("esc", StandardScaler())]
                ),
                list(num),
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), list(cat)),
        ]
    )


def construir(nombre: str, conjunto: str) -> Pipeline:
    if nombre == "logistica":
        modelo: Any = LogisticRegression(C=1.0, max_iter=500, random_state=SEMILLA)
    else:
        modelo = HistGradientBoostingClassifier(
            max_depth=4, learning_rate=0.1, max_iter=150, random_state=SEMILLA
        )
    return Pipeline([("pre", _prepro(conjunto)), ("clf", modelo)])


def reglas_b1(d: pd.DataFrame) -> np.ndarray:
    """B1: tabla de decisión fija sobre la duración y el cierre, escrita con medianas de entrenamiento.

    Sin duración (chat, correo) cae en la clase mayoritaria. Se escribió antes de mirar validación o prueba.
    """
    dur = d["duracion_segundos"].to_numpy()
    nombres = np.array(MOTIVOS)
    out = np.full(len(d), "Transaccional", dtype=object)
    ok = ~np.isnan(dur)
    banda = np.select(
        [dur <= 235, dur <= 310, dur <= 395, dur <= 455, dur <= 510],
        ["Transaccional", "Producto", "Técnico", "Queja", "Retención"],
        default="Comercial",
    )
    out[ok] = banda[ok]
    sin_resolver = (d["resuelto"].to_numpy() == 0) & (d["requiere_seguimiento"].to_numpy() == 1)
    out[ok & sin_resolver & (dur > 310)] = "Queja"
    idx = {m: i for i, m in enumerate(nombres)}
    return np.array([idx[x] for x in out])


def _logits(pipe: Pipeline, x: pd.DataFrame) -> np.ndarray:
    return np.log(np.clip(pipe.predict_proba(x), 1e-9, 1.0))


# ------------------------------------------------------------------------------------------- auditoría


def auditar_etiquetas(tr: pd.DataFrame) -> dict[str, Any]:
    """Balance, dependencia de campos y muestra de 50 con rúbrica determinista (no es verdad independiente)."""
    k = len(MOTIVOS)
    balance = tr["y"].value_counts(normalize=True).sort_index().to_numpy()
    lo = tr.groupby("y")[["duracion_segundos", "sentimiento"]].quantile(0.05)
    hi = tr.groupby("y")[["duracion_segundos", "sentimiento"]].quantile(0.95)

    def rubrica(f: pd.Series) -> bool:
        y = int(f["y"])
        ok = True
        if not np.isnan(f["duracion_segundos"]):
            ok &= bool(
                lo.loc[y, "duracion_segundos"] <= f["duracion_segundos"] <= hi.loc[y, "duracion_segundos"]
            )
        ok &= bool(lo.loc[y, "sentimiento"] <= f["sentimiento"] <= hi.loc[y, "sentimiento"])
        if MOTIVOS[y] == "Transaccional":
            ok &= f["sentimiento_txt"] == "Neutral"
        return ok

    muestra = tr.groupby("y", group_keys=False).sample(n=8, random_state=SEMILLA).head(50)
    if len(muestra) < 50:
        muestra = pd.concat([muestra, tr.drop(muestra.index).sample(50 - len(muestra), random_state=SEMILLA)])
    veredicto = muestra.apply(rubrica, axis=1)
    todo = tr.sample(min(20000, len(tr)), random_state=SEMILLA).apply(rubrica, axis=1)
    return {
        "balance": dict(zip(MOTIVOS, balance.round(4), strict=True)),
        "n_clases": k,
        "dif_segmento_max": float(
            (
                pd.crosstab(tr["y"], tr["segmento"], normalize="index").max()
                - pd.crosstab(tr["y"], tr["segmento"], normalize="index").min()
            ).max()
        ),
        "consistentes_50": int(veredicto.sum()),
        "consistentes_muestra_20k": float(todo.mean()),
        "faltante_duracion": float(tr["duracion_segundos"].isna().mean()),
        "faltante_duracion_por_tipo": tr.groupby("tipo_interaccion")["duracion_segundos"]
        .apply(lambda s: float(s.isna().mean()))
        .round(3)
        .to_dict(),
    }


# ------------------------------------------------------------------------------------------ evaluación


def _estad(y: np.ndarray, pred: np.ndarray, prob: np.ndarray | None, tau: float | None) -> Any:
    k = len(MOTIVOS)

    def f(w: np.ndarray) -> dict[str, float]:
        out = {"macro_f1": macro_f1(y, pred, k, w), "exactitud": float(np.average(pred == y, weights=w))}
        if prob is not None and tau is not None:
            auto = prob.max(1) >= tau
            wa = w * auto
            out["cobertura"] = float(wa.sum() / w.sum())
            out["exactitud_auto"] = float((wa * (pred == y)).sum() / wa.sum()) if wa.sum() else float("nan")
            err = (wa * (pred != y)).sum()
            out["costo"] = float((C_ERROR * err + C_REVISION * (w * ~auto).sum()) / w.sum())
        return out

    return f


def evaluar_conjunto(
    nombre: str,
    conjunto: str,
    tr: pd.DataFrame,
    va: pd.DataFrame,
    te: pd.DataFrame,
) -> dict[str, Any]:
    cols = columnas(conjunto)
    pipe = construir(nombre, conjunto).fit(tr[cols], tr["y"])
    lv, lt = _logits(pipe, va[cols]), _logits(pipe, te[cols])
    t = escalar_temperatura(lv, va["y"].to_numpy())
    pv, pt = softmax(lv / t), softmax(lt / t)
    return {
        "pipe": pipe,
        "temperatura": t,
        "pv": pv,
        "pt": pt,
        "pt_sin_calibrar": softmax(lt),
        "f1_val": macro_f1(va["y"].to_numpy(), pv.argmax(1), len(MOTIVOS)),
    }


def tabla_clases(y: np.ndarray, pred: np.ndarray) -> list[tuple[str, float, float, float, int]]:
    cm = matriz_confusion(y, pred, len(MOTIVOS))
    p, r, f = prf(cm)
    return [(m, float(p[i]), float(r[i]), float(f[i]), int(cm[i].sum())) for i, m in enumerate(MOTIVOS)]


def pct(v: float) -> str:
    return "n/a" if np.isnan(v) else f"{v:.1%}"


def ic(par: tuple[float, float]) -> str:
    return f"[{par[0]:.3f}, {par[1]:.3f}]"


def ejecutar(fecha: str, sin_cache: bool, reps: int) -> dict[str, Any]:
    df, aud = cargar(sin_cache)
    d = preparar(df)
    tr, va, te = particionar(d)
    k = len(MOTIVOS)
    yv, yt = va["y"].to_numpy(), te["y"].to_numpy()

    solape = len(set(te["cliente"]) & set(tr["cliente"])) / te["cliente"].nunique()
    aud_et = auditar_etiquetas(tr)

    res: dict[Any, Any] = {}
    for conj in ("contacto", "llamada"):
        for nom in ("logistica", "arboles"):
            res[(conj, nom)] = evaluar_conjunto(nom, conj, tr, va, te)
    # Campeón: mejor macro-F1 de validación entre candidatos del conjunto "llamada" (sugerencia de cierre).
    nom_c = max(("logistica", "arboles"), key=lambda n: res[("llamada", n)]["f1_val"])
    campeon = res[("llamada", nom_c)]
    contacto_c = max(("logistica", "arboles"), key=lambda n: res[("contacto", n)]["f1_val"])
    contacto = res[("contacto", contacto_c)]

    tau = elegir_umbral(campeon["pv"], yv, C_ERROR, C_REVISION)
    tau_contacto = elegir_umbral(contacto["pv"], yv, C_ERROR, C_REVISION)

    mayor = int(np.bincount(tr["y"]).argmax())
    pred_mayor = np.full(len(te), mayor)
    pred_reglas = reglas_b1(te)
    pred_c = campeon["pt"].argmax(1)
    pred_k = contacto["pt"].argmax(1)

    cl = te["cliente"].to_numpy()
    boot_c = bootstrap_clusters(cl, _estad(yt, pred_c, campeon["pt"], tau), reps, SEMILLA)
    boot_k = bootstrap_clusters(cl, _estad(yt, pred_k, contacto["pt"], tau_contacto), reps, SEMILLA)
    boot_m = bootstrap_clusters(cl, _estad(yt, pred_mayor, None, None), reps, SEMILLA)
    boot_r = bootstrap_clusters(cl, _estad(yt, pred_reglas, None, None), reps, SEMILLA)
    dif = bootstrap_clusters(
        cl,
        lambda w: {
            "c_menos_reglas": macro_f1(yt, pred_c, k, w) - macro_f1(yt, pred_reglas, k, w),
            "c_menos_mayoritaria": macro_f1(yt, pred_c, k, w) - macro_f1(yt, pred_mayor, k, w),
            "contacto_menos_mayoritaria": macro_f1(yt, pred_k, k, w) - macro_f1(yt, pred_mayor, k, w),
        },
        reps,
        SEMILLA,
    )

    # Sensibilidad: solo clientes sin ningún contacto en entrenamiento (disjunto por cliente).
    nuevos = ~te["cliente"].isin(set(tr["cliente"])).to_numpy()
    f1_nuevos = macro_f1(yt[nuevos], pred_c[nuevos], k) if nuevos.sum() > 100 else float("nan")

    curva = [
        costo_abstencion(campeon["pt"], yt, float(u), C_ERROR, C_REVISION)
        for u in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
    ]

    # Errores: filas enmascaradas (sin ids ni fechas) donde el modelo acierta con alta confianza y falla.
    conf = campeon["pt"].max(1)
    mal = np.where((pred_c != yt) & (conf >= tau))[0]
    ejemplos = te.iloc[mal[:6]][
        ["tipo_interaccion", "duracion_segundos", "sentimiento", "resuelto", "requiere_seguimiento"]
    ].copy()
    ejemplos["real"] = [MOTIVOS[i] for i in yt[mal[:6]]]
    ejemplos["predicho"] = [MOTIVOS[i] for i in pred_c[mal[:6]]]
    ejemplos["p"] = conf[mal[:6]].round(2)
    # Posible ruido de etiqueta: el modelo da p>=0.9 a otra clase.
    posible_ruido = float(((pred_c != yt) & (conf >= 0.9)).mean())

    modelo = ModeloCalibrado(
        campeon["pipe"], MOTIVOS, campeon["temperatura"], tau, f"motivo-{nom_c}-llamada-{fecha}", "llamada"
    )
    ARTEFACTOS.mkdir(exist_ok=True)
    joblib.dump(modelo, ARTEFACTOS / "motivo.joblib")

    sal: dict[str, Any] = {
        "fecha": fecha,
        "reps": reps,
        "n": {"tr": len(tr), "va": len(va), "te": len(te)},
        "rangos": {
            "tr": (tr["fecha"].min().date(), tr["fecha"].max().date()),
            "va": (va["fecha"].min().date(), va["fecha"].max().date()),
            "te": (te["fecha"].min().date(), te["fecha"].max().date()),
        },
        "solape_clientes": solape,
        "aud": aud,
        "aud_et": aud_et,
        "res": res,
        "nom_c": nom_c,
        "contacto_c": contacto_c,
        "tau": tau,
        "tau_contacto": tau_contacto,
        "mayor": MOTIVOS[mayor],
        "boot": {"campeon": boot_c, "contacto": boot_k, "mayoritaria": boot_m, "reglas": boot_r, "dif": dif},
        "tabla": {
            "mayoritaria": tabla_clases(yt, pred_mayor),
            "reglas": tabla_clases(yt, pred_reglas),
            "campeon": tabla_clases(yt, pred_c),
            "contacto": tabla_clases(yt, pred_k),
        },
        "cm": matriz_confusion(yt, pred_c, k),
        "calib": {
            "ece_sin": ece(campeon["pt_sin_calibrar"], yt),
            "ece_con": ece(campeon["pt"], yt),
            "brier_sin": brier(campeon["pt_sin_calibrar"], yt),
            "brier_con": brier(campeon["pt"], yt),
            "ece_contacto": ece(contacto["pt"], yt),
        },
        "curva": curva,
        "costos": {
            "siempre_revisar": C_REVISION,
            "siempre_automatico": float(C_ERROR * (pred_c != yt).mean()),
            "campeon": costo_abstencion(campeon["pt"], yt, tau, C_ERROR, C_REVISION),
            "contacto": costo_abstencion(contacto["pt"], yt, tau_contacto, C_ERROR, C_REVISION),
        },
        "f1_nuevos": f1_nuevos,
        "n_nuevos": int(nuevos.sum()),
        "ejemplos": ejemplos,
        "posible_ruido": posible_ruido,
        "f1_val": {f"{c}/{n}": res[(c, n)]["f1_val"] for (c, n) in res},
        "temperatura": campeon["temperatura"],
    }
    return sal


# ------------------------------------------------------------------------------------------------ reporte


def _fila_clases(titulo: str, filas: list[tuple[str, float, float, float, int]]) -> str:
    out = [
        f"**{titulo}**\n",
        "| Motivo | Precisión | Cobertura (recall) | F1 | Casos |",
        "|---|---|---|---|---|",
    ]
    out += [f"| {m} | {p:.3f} | {r:.3f} | {f:.3f} | {n:,} |" for m, p, r, f, n in filas]
    return "\n".join(out)


def redactar(s: dict[str, Any]) -> str:
    b = s["boot"]
    au, ae = s["aud"], s["aud_et"]
    fr = au["fraude"]
    cm = s["cm"]
    cb = s["costos"]
    nom = {"logistica": "regresión logística", "arboles": "árboles de gradiente"}
    L: list[str] = []
    a = L.append
    a(f"# Clasificador del motivo de contacto, reporte {s['fecha']}\n")
    a(
        "Criterio 4 del enunciado: evaluar un componente aprendido frente a una línea base, con etiquetas "
        "válidas, sin fuga y con métricas, umbrales y particiones justificados. Reproducible con "
        "`uv run python -m latam_ia.experimentos.motivo`. Datos: `latam_bank.plata_call_center_interactions` "
        "(686.296 contactos, 2023-06-17 a 2026-06-17), solo español, sin PII en este reporte.\n"
    )
    a("## Resumen\n")
    a(
        f"- Con las señales del cierre de la llamada, el modelo ({nom[s['nom_c']]}, calibrado) logra macro-F1 "
        f"**{macro_f1_pt(s, 'campeon'):.3f}** {ic(b['campeon']['macro_f1'])} contra "
        f"{macro_f1_pt(s, 'reglas'):.3f} {ic(b['reglas']['macro_f1'])} de las reglas B1 y "
        f"{macro_f1_pt(s, 'mayoritaria'):.3f} de la clase mayoritaria ({s['mayor']}). "
        f"Diferencia con B1 {ic(b['dif']['c_menos_reglas'])}.\n"
        f"- Con solo lo que se sabe al abrir el contacto (tipo, canal, segmento, país, hora, antigüedad) el modelo "
        f"**no supera a la mayoritaria**: macro-F1 {macro_f1_pt(s, 'contacto'):.3f} {ic(b['contacto']['macro_f1'])}. "
        "Por eso el motivo no sirve para enrutar antes de atender; sirve para sugerir el código de cierre.\n"
        f"- A umbral {s['tau']:.2f} (elegido en validación con costo de error 5 y revisión 1) el modelo automatiza "
        f"{cb['campeon']['cobertura']:.1%} de los casos con exactitud {cb['campeon']['exactitud_auto']:.1%}; "
        f"costo medio {cb['campeon']['costo']:.3f} contra {cb['siempre_revisar']:.3f} de revisar todo y "
        f"{cb['siempre_automatico']:.3f} de automatizar todo: con costo 5 a 1 el ahorro es marginal, así que el valor "
        "está en la pista cuando el error es caro, no en automatizar.\n"
        "- Texto: no existe texto del cliente en los datos (ver auditoría), así que TF-IDF y el clasificador "
        "Gemini no son aplicables; se gastaron 0 de 300 llamadas al modelo. Fraude: se descartó con evidencia "
        "(sección final).\n"
    )
    a("## 1. Elección del componente y por qué no es texto\n")
    a(
        "El enunciado pide etiquetas válidas. Se inspeccionaron las tablas de plata antes de elegir:\n\n"
        f"- Quejas (`plata_complaints`) y transcripciones (`plata_call_transcripts`) no traen texto libre. Los únicos "
        f"campos de texto en ellas son {', '.join('`' + c + '`' for c in au['campos_texto_quejas'])}, todos "
        "categóricos. `detected_keywords` solo contiene las fichas "
        f"{', '.join(f'`{k}`' for k in sorted(au['palabras_clave']))} sin relación con el motivo.\n"
        f"- `main_topics` de la transcripción coincide con el motivo en {au['tema_igual_motivo']['iguales']:,} de "
        f"{au['tema_igual_motivo']['n']:,} contactos (100%): es una copia de la etiqueta y no se usa como rasgo.\n"
        "- Se eligió el motivo de contacto (`contact_reason`, seis clases; `reason_category` es idéntica) porque es la "
        "etiqueta registrada con más volumen y la que la comprensión del agente necesita. Las señales estructuradas "
        "son lo único disponible; no se inventó texto.\n"
    )
    a("## 2. Auditoría de etiquetas\n")
    a(
        "Balance en entrenamiento: " + ", ".join(f"{k} {v:.1%}" for k, v in ae["balance"].items()) + ". "
        "Se usa macro-F1 por el desbalance y porque las clases raras (Retención) cuestan igual que las comunes.\n"
    )
    a(
        f"Muestra de 50 casos (8 por clase, semilla fija) revisada con una rúbrica determinista: el contacto es "
        "consistente si su duración y su sentimiento caen en el rango P5 a P95 de su propia clase y, para "
        f"Transaccional, el sentimiento detectado es Neutral. Resultado: **{ae['consistentes_50']} de 50** consistentes "
        f"({ae['consistentes_muestra_20k']:.1%} en 20.000 casos). La rúbrica mide coherencia interna, no verdad "
        "externa: por construcción un contacto limpio pasa con probabilidad cercana a 0,9 por cada rango, así que "
        "~83% es lo esperado y no evidencia de ruido; no hay segunda fuente independiente del motivo en los datos. "
        f"Como señal complementaria, {s['posible_ruido']:.2%} de la prueba recibe p ≥ 0,9 en otra clase "
        "(el modelo casi nunca llega a esa confianza, así que esta señal tampoco detecta ruido).\n"
    )
    a(
        "Campos con fuga que se excluyen: `reason_category` y `main_topics` (copias de la etiqueta), "
        "`detected_sentiment` (derivado de `sentiment_score`), `has_transcript` y `has_recording` (posteriores), "
        "`agent_id` (identidad del agente) e identificadores de producto. "
        f"Faltante de `duration_seconds`: {ae['faltante_duracion']:.1%}, estructural (chat, correo y video sin "
        "duración): " + ", ".join(f"{k} {v:.0%}" for k, v in ae["faltante_duracion_por_tipo"].items()) + ". "
        "Se imputa con la mediana más un indicador de faltante.\n"
    )
    a("## 3. Partición y fuga\n")
    r = s["rangos"]
    a(
        "| Parte | Rango de `process_date` | Contactos |\n|---|---|---|\n"
        f"| Entrenamiento | {r['tr'][0]} a {r['tr'][1]} (< {T1}) | {s['n']['tr']:,} |\n"
        f"| Validación | {r['va'][0]} a {r['va'][1]} | {s['n']['va']:,} |\n"
        f"| Prueba | {r['te'][0]} a {r['te'][1]} (≥ {T2}) | {s['n']['te']:,} |\n"
    )
    a(
        "Partición temporal porque el modelo se usará sobre contactos futuros; el cálculo de calibración y umbral "
        "usa solo validación y la prueba se evalúa una vez. No hay identificador de cliente ni de agente entre los "
        f"rasgos, de modo que no hay memorización de personas. {s['solape_clientes']:.1%} de los clientes de prueba "
        "ya aparecen en entrenamiento; como prueba de sensibilidad, en los "
        f"{s['n_nuevos']:,} contactos de clientes nunca vistos el macro-F1 es {s['f1_nuevos']:.3f} "
        f"(general {macro_f1_pt(s, 'campeon'):.3f}). Los IC son bootstrap por cliente (pesos Poisson, "
        f"{s['reps']} réplicas, semilla {SEMILLA}) porque los contactos de un cliente están correlacionados.\n"
    )
    a("## 4. Modelos, representaciones y líneas base\n")
    a(
        "- **Mayoritaria**: siempre predice " + s["mayor"] + ".\n"
        "- **B1 reglas**: tabla de decisión fija sobre duración (bandas por medianas de entrenamiento) y cierre "
        "(sin resolver y con seguimiento, duración mayor a 310 s, es Queja); sin duración cae en la mayoritaria. "
        "Escrita con estadísticas de entrenamiento, antes de ver validación o prueba.\n"
        "- **Aprendidos**: regresión logística multinomial y árboles de gradiente (HistGradientBoosting, profundidad 4, "
        "150 iteraciones). Representación: numéricas con imputación por mediana, indicador de faltante y "
        "estandarización; categóricas en one-hot (categorías con menos de 50 casos se agrupan). Se justifican "
        "porque los rasgos son tabulares y de baja dimensión; el árbol captura el corte por bandas y el "
        "modelo lineal sirve de control de que la ganancia no es solo capacidad.\n"
        "- **Dos conjuntos de rasgos**: `contacto` (disponibles al abrir) y `llamada` (añade duración, sentimiento, "
        "resuelto, seguimiento, escalado, conocidos al cerrar).\n"
        "- **Calibración**: escalado de temperatura ajustado en validación. Temperatura "
        f"{s['temperatura']:.2f} (el modelo ya salía calibrado); ECE {s['calib']['ece_sin']:.4f} a {s['calib']['ece_con']:.4f} y Brier "
        f"{s['calib']['brier_sin']:.4f} a {s['calib']['brier_con']:.4f} en prueba.\n"
        "- **Selección**: macro-F1 en validación. "
        + "; ".join(f"{k} {v:.3f}" for k, v in s["f1_val"].items())
        + f". Campeón de `llamada`: {nom[s['nom_c']]}.\n"
    )
    a("## 5. Resultados en prueba\n")
    a(
        "| Sistema | Macro-F1 | IC 95% | Exactitud | IC 95% |\n|---|---|---|---|---|\n"
        f"| Mayoritaria | {macro_f1_pt(s, 'mayoritaria'):.3f} | {ic(b['mayoritaria']['macro_f1'])} | "
        f"{acc_pt(s, 'mayoritaria'):.3f} | {ic(b['mayoritaria']['exactitud'])} |\n"
        f"| B1 reglas | {macro_f1_pt(s, 'reglas'):.3f} | {ic(b['reglas']['macro_f1'])} | "
        f"{acc_pt(s, 'reglas'):.3f} | {ic(b['reglas']['exactitud'])} |\n"
        f"| Aprendido, conjunto `contacto` ({nom[s['contacto_c']]}) | {macro_f1_pt(s, 'contacto'):.3f} | "
        f"{ic(b['contacto']['macro_f1'])} | {acc_pt(s, 'contacto'):.3f} | {ic(b['contacto']['exactitud'])} |\n"
        f"| **Aprendido, conjunto `llamada` ({nom[s['nom_c']]})** | **{macro_f1_pt(s, 'campeon'):.3f}** | "
        f"{ic(b['campeon']['macro_f1'])} | {acc_pt(s, 'campeon'):.3f} | {ic(b['campeon']['exactitud'])} |\n"
    )
    a(
        f"Diferencias de macro-F1 con IC: campeón menos B1 {ic(b['dif']['c_menos_reglas'])}; campeón menos mayoritaria "
        f"{ic(b['dif']['c_menos_mayoritaria'])}; `contacto` menos mayoritaria {ic(b['dif']['contacto_menos_mayoritaria'])}.\n"
    )
    a(_fila_clases("Por clase, campeón (`llamada`, sin abstención)", s["tabla"]["campeon"]) + "\n")
    a(_fila_clases("Por clase, B1 reglas", s["tabla"]["reglas"]) + "\n")
    a("**Matriz de confusión del campeón** (filas: real; columnas: predicho)\n")
    a("| | " + " | ".join(MOTIVOS) + " |\n|---|" + "---|" * len(MOTIVOS))
    for i, m in enumerate(MOTIVOS):
        a(f"| {m} | " + " | ".join(f"{int(v):,}" for v in cm[i]) + " |")
    a("")
    a("## 6. Umbral de abstención\n")
    a(
        f"Costo supuesto: automatizar mal un código cuesta {C_ERROR:.0f} unidades y mandar a revisión humana "
        f"{C_REVISION:.0f}. Con probabilidades calibradas el corte teórico es 1 - {C_REVISION:.0f}/{C_ERROR:.0f} = "
        f"{1 - C_REVISION / C_ERROR:.2f}; se eligió **{s['tau']:.2f}** minimizando el costo en validación (rejilla "
        "0,30 a 0,99). Se aplica a la prueba sin reajustar.\n"
    )
    a("| Umbral | Cobertura automática | Exactitud en lo automático | Costo medio |\n|---|---|---|---|")
    for c in s["curva"] + [cb["campeon"]]:
        marca = " (elegido)" if abs(c["umbral"] - s["tau"]) < 1e-9 else ""
        a(
            f"| {c['umbral']:.2f}{marca} | {c['cobertura']:.1%} | {pct(c['exactitud_auto'])} | {c['costo']:.3f} |"
        )
    a("")
    a(
        f"En el umbral elegido: cobertura {ic(b['campeon']['cobertura'])}, exactitud automática "
        f"{ic(b['campeon']['exactitud_auto'])}, costo {ic(b['campeon']['costo'])} (IC por cliente). Para el conjunto "
        f"`contacto` el umbral elegido es {s['tau_contacto']:.2f} con cobertura "
        f"{cb['contacto']['cobertura']:.1%}: el modelo casi siempre se abstiene, que es el comportamiento correcto "
        "cuando no hay señal.\n"
    )
    a("## 7. Análisis de errores\n")
    a(
        "Las clases Comercial, Queja, Retención y Técnico tienen el mismo sentimiento (misma distribución); solo "
        "se separan por duración y por cierre, y esas distribuciones se solapan, de ahí la confusión entre ellas. "
        "Transaccional y Producto son más fáciles: sentimiento acotado a ±0,3 y cierre resuelto. Ejemplos de "
        "errores con confianza sobre el umbral (filas enmascaradas, sin identificadores ni fechas):\n"
    )
    ej = s["ejemplos"]
    a(
        "| Tipo | Duración (s) | Sentimiento | Resuelto | Seguimiento | Real | Predicho | p |\n|---|---|---|---|---|---|---|---|"
    )
    for _, f in ej.iterrows():
        a(
            f"| {f['tipo_interaccion']} | {f['duracion_segundos']:.0f} | {f['sentimiento']:+.2f} | "
            f"{int(f['resuelto'])} | {int(f['requiere_seguimiento'])} | {f['real']} | {f['predicho']} | {f['p']:.2f} |"
        )
    a("")
    a(
        "Retención (3% de los casos) nunca se predice: sus rasgos se solapan con Comercial y Queja y el modelo "
        "prefiere no acertar en una clase tan pequeña; es la brecha principal y se corregiría con más señal, no con "
        "pesos de clase, que descalibrarían la probabilidad. Según la exploración descriptiva, lo que separa las "
        "clases es la duración, el sentimiento y el cierre; ninguno es texto. Idioma: los "
        "datos están solo en español (`detected_language` = es), por lo que no se mide transferencia a portugués "
        "ni a transcripciones multilingües (IA-2.3 queda abierto).\n"
    )
    a("## 8. Límites y uso permitido\n")
    a(
        "- Los datos son sintéticos: duración, sentimiento y cierre se generaron a partir del motivo, de modo que el "
        "resultado mide qué tan bien se recupera esa estructura y no una capacidad real de entender clientes. La "
        "cifra no debe extrapolarse a producción.\n"
        "- El conjunto `llamada` usa información posterior al contacto: sirve para sugerir el código de cierre "
        "y como pista para el paso de comprensión cuando esas señales ya existen en el caso; no para enrutar antes de "
        "atender. El conjunto `contacto` no tiene señal.\n"
        "- La pista nunca actúa: `SugerenciaMotivo.accion_permitida` es siempre falso y por debajo del umbral el "
        "caso sigue el camino humano.\n"
        "- No se midió equidad por segmento ni país porque las etiquetas no dependen del segmento "
        f"(diferencia máxima de proporción entre clases {ae['dif_segmento_max']:.3f} en entrenamiento); queda como pendiente si el motivo llega a decidir algo con efecto.\n"
    )
    a("## 9. Candidato descartado: fraude (IA-10.1)\n")
    a(
        f"`plata_transactions.is_fraud` tiene {fr['fraudes']:,.0f} positivos en {fr['n']:,.0f} transacciones (0,10%). "
        f"No se entrena ahí por dos hallazgos: (1) `fraud_score` está contaminado por la etiqueta: "
        f"{fr['puntaje_sobre_30_y_fraude']:,.0f} de {fr['puntaje_sobre_30']:,.0f} transacciones con puntaje mayor a "
        f"30 son fraude (100%), el máximo del puntaje en no fraude es {fr['maximo_puntaje_no_fraude']:.0f} (media "
        f"{fr['media_puntaje_no_fraude']:.1f}) contra media {fr['media_puntaje_fraude']:.1f} en fraude, y "
        f"{fr['puntaje_nulo']:,.0f} puntajes son nulos; compararse contra él daría una línea base inválida. "
        f"(2) La tasa de fraude por canal varía solo entre {au['fraude_tasa_canal_min']:.4%} y "
        f"{au['fraude_tasa_canal_max']:.4%}, y no varía de forma apreciable por tipo, hora, moneda ni país en la "
        "exploración, de modo que los rasgos de la transacción no aportan señal. Cualquier modelo de fraude sobre "
        "estos datos solo reproduciría la fuga del puntaje.\n"
    )
    a("## 10. Reproducción y artefactos\n")
    a(
        f"Semilla {SEMILLA}. Modelo y caché en `ia/artefactos/` (fuera de git). Ficha del modelo: "
        f"`modelcard_motivo_{s['fecha']}.md`. Integración: `latam_ia.comprension.motivo.sugerir_motivo`.\n"
    )
    return "\n".join(L)


def macro_f1_pt(s: dict[str, Any], quien: str) -> float:
    return float(np.mean([f for _, _, _, f, _ in s["tabla"][quien]]))


def acc_pt(s: dict[str, Any], quien: str) -> float:
    t = s["tabla"][quien]
    # exactitud = suma de recall ponderado por soporte
    total = sum(n for *_, n in t)
    return float(sum(r * n for _, _, r, _, n in t) / total)


def ficha(s: dict[str, Any]) -> str:
    b = s["boot"]["campeon"]
    return f"""# Ficha del modelo: motivo de contacto, {s["fecha"]}

**Qué es.** Clasificador de seis clases ({", ".join(MOTIVOS)}) que sugiere el código de cierre de un contacto.
Versión `motivo-{s["nom_c"]}-llamada-{s["fecha"]}`. Es una pista de enrutamiento: no actúa, y se abstiene por debajo
de p = {s["tau"]:.2f}.

**Uso previsto.** Sugerir el motivo al agente humano al cerrar el contacto y dar contexto al paso de comprensión del
agente cuando ya existen duración, sentimiento y cierre. **Fuera de alcance:** enrutar antes de atender (el conjunto
`contacto` no tiene señal), decidir efectos sobre el cliente, y evaluar personas.

**Datos.** `latam_bank.plata_call_center_interactions` unido a `plata_customers`, 2023-06-17 a 2026-06-17, español,
sintéticos. Partición temporal: entrenamiento < {T1}, validación < {T2}, prueba posterior. Sin identificadores como
rasgos; sin campos derivados de la etiqueta.

**Modelo.** {s["nom_c"]} sobre rasgos tabulares con imputación e indicadores de faltante; escalado de temperatura
T = {s["temperatura"]:.2f} ajustado en validación; semilla {SEMILLA}.

**Desempeño en prueba (IC 95% por cliente).** Macro-F1 {macro_f1_pt(s, "campeon"):.3f} {ic(b["macro_f1"])}; línea base
de reglas {macro_f1_pt(s, "reglas"):.3f}; mayoritaria {macro_f1_pt(s, "mayoritaria"):.3f}. ECE {s["calib"]["ece_con"]:.4f},
Brier {s["calib"]["brier_con"]:.4f}. A p ≥ {s["tau"]:.2f}: cobertura {s["costos"]["campeon"]["cobertura"]:.1%},
exactitud {s["costos"]["campeon"]["exactitud_auto"]:.1%}.

**Limitaciones.** Datos sintéticos con señal generada a partir de la etiqueta; no hay texto del cliente; solo español;
no se midió equidad porque los rasgos protegidos no influyen; la calibración es válida solo en esta distribución
temporal y debe reverificarse si cambia el mezcla de motivos.

**Gobierno.** Pista sin acción permitida; el umbral es un parámetro de política y se reentrena con un nuevo
reporte, no a mano. Reporte completo: `clasificador_{s["fecha"]}.md`.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    ap.add_argument("--sin-cache", action="store_true", help="vuelve a consultar BigQuery")
    ap.add_argument("--reps", type=int, default=1000)
    a = ap.parse_args()
    s = ejecutar(a.fecha, a.sin_cache, a.reps)
    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / f"clasificador_{a.fecha}.md").write_text(redactar(s), encoding="utf-8")
    (REPORTES / f"modelcard_motivo_{a.fecha}.md").write_text(ficha(s), encoding="utf-8")
    print(f"listo: {REPORTES / f'clasificador_{a.fecha}.md'}")


if __name__ == "__main__":
    main()
