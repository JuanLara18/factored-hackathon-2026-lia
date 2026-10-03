"""Métricas puras (numpy) del experimento: F1, calibración, abstención y bootstrap por clúster."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def matriz_confusion(y: np.ndarray, pred: np.ndarray, k: int, w: np.ndarray | None = None) -> np.ndarray:
    idx = y * k + pred
    return np.bincount(idx, weights=w, minlength=k * k).reshape(k, k)


def prf(cm: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tp = np.diag(cm).astype(float)
    p = np.divide(tp, cm.sum(0), out=np.zeros_like(tp), where=cm.sum(0) > 0)
    r = np.divide(tp, cm.sum(1), out=np.zeros_like(tp), where=cm.sum(1) > 0)
    f = np.divide(2 * p * r, p + r, out=np.zeros_like(tp), where=(p + r) > 0)
    return p, r, f


def macro_f1(y: np.ndarray, pred: np.ndarray, k: int, w: np.ndarray | None = None) -> float:
    return float(prf(matriz_confusion(y, pred, k, w))[2].mean())


def ece(prob: np.ndarray, y: np.ndarray, bins: int = 15) -> float:
    """Error de calibración esperado sobre la clase predicha."""
    conf = prob.max(1)
    acierto = (prob.argmax(1) == y).astype(float)
    borde = np.linspace(0.0, 1.0, bins + 1)
    cub = np.clip(np.digitize(conf, borde[1:-1]), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        m = cub == b
        if m.any():
            total += m.mean() * abs(acierto[m].mean() - conf[m].mean())
    return float(total)


def brier(prob: np.ndarray, y: np.ndarray) -> float:
    uno = np.eye(prob.shape[1])[y]
    return float(((prob - uno) ** 2).sum(1).mean())


def log_perdida(prob: np.ndarray, y: np.ndarray) -> float:
    return float(-np.log(np.clip(prob[np.arange(len(y)), y], 1e-12, 1.0)).mean())


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def escalar_temperatura(logits: np.ndarray, y: np.ndarray) -> float:
    """Temperatura T>0 que minimiza la log-pérdida en validación (rejilla fina)."""
    mejor, mejor_t = np.inf, 1.0
    for t in np.exp(np.linspace(-1.6094379124341003, 1.6094379124341003, 121)).tolist():  # T en [0,2; 5]
        v = log_perdida(softmax(logits / t), y)
        if v < mejor:
            mejor, mejor_t = v, float(t)
    return mejor_t


def costo_abstencion(
    prob: np.ndarray, y: np.ndarray, umbral: float, c_error: float, c_revision: float
) -> dict[str, float]:
    """Costo medio por caso: revisar cuesta `c_revision`; automatizar mal cuesta `c_error`."""
    auto = prob.max(1) >= umbral
    acierto = prob.argmax(1) == y
    costo = np.where(auto, np.where(acierto, 0.0, c_error), c_revision).mean()
    return {
        "umbral": float(umbral),
        "cobertura": float(auto.mean()),
        "exactitud_auto": float(acierto[auto].mean()) if auto.any() else float("nan"),
        "costo": float(costo),
    }


def elegir_umbral(
    prob: np.ndarray, y: np.ndarray, c_error: float, c_revision: float, rejilla: np.ndarray | None = None
) -> float:
    grilla = np.round(np.arange(0.30, 1.0, 0.01), 2) if rejilla is None else rejilla
    costos = [costo_abstencion(prob, y, float(t), c_error, c_revision)["costo"] for t in grilla]
    return float(grilla[int(np.argmin(costos))])


def bootstrap_clusters(
    clusters: np.ndarray,
    estadisticos: Callable[[np.ndarray], dict[str, float]],
    reps: int,
    seed: int,
) -> dict[str, tuple[float, float]]:
    """IC 95% percentil con pesos Poisson(1) por clúster (cliente): respeta la correlación intra cliente.

    `estadisticos` recibe el peso por fila y devuelve un diccionario de estadísticos ponderados.
    """
    rng = np.random.default_rng(seed)
    _, inv = np.unique(clusters, return_inverse=True)
    n = int(inv.max()) + 1
    muestras: dict[str, list[float]] = {}
    for _ in range(reps):
        w = rng.poisson(1.0, n).astype(float)[inv]
        for k, v in estadisticos(w).items():
            muestras.setdefault(k, []).append(v)
    return {
        k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) for k, v in muestras.items()
    }
