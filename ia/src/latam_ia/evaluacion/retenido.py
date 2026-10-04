"""Evaluación final sobre el conjunto retenido (IA-5.4): el mismo trabajo para el propuesto y las bases.

El conjunto retenido (`ia/evaluacion/escenarios/retenido/`) no se usó para iterar el prompt. Cada caso lleva
una etiqueta de referencia (`Etiqueta`) y expectativas deterministas (`Esperado`). Este módulo corre los
sistemas, mide latencia y tokens del agente (no del simulador), clasifica cada corrida y calcula las métricas
del enunciado con intervalos de Wilson. Los datos crudos van a JSON fuera de git.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from latam_gobierno.politica import cargar as cargar_politica
from latam_tecnologia.canales.geap import MEDIDOR, crear_modelo_geap
from latam_tecnologia.herramientas.agente import crear_agente_disputas
from latam_tecnologia.motor.caso import decidir
from pydantic_ai.models import Model

from latam_ia.evaluacion.agente_referencia import crear_modelo_referencia
from latam_ia.evaluacion.ejecutor import (
    Corrida,
    FabricaAgente,
    crear_agente_sin_herramientas,
    ejecutar_corrida,
)
from latam_ia.evaluacion.esquema import DIR_RETENIDO, Escenario
from latam_ia.evaluacion.metricas import pass_k, regla_del_tres, tasa
from latam_ia.evaluacion.mundo import materializar
from latam_ia.evaluacion.verificadores import acciones_afirmadas_sin_efecto
from latam_ia.registro.cargador import cargar_registro

# Tarifa de lista supuesta de Gemini 3.1 Flash-Lite en Vertex AI, USD por millón de tokens (entrada, salida).
# No se verificó contra la página de precios en esta sesión: es un supuesto declarado en el reporte.
PRECIO_ENTRADA_USD, PRECIO_SALIDA_USD = 0.25, 1.50
EFECTOS_AUTOMATICOS = frozenset({"abrir_disputa", "bloquear_tarjeta"})
SISTEMAS = ("propuesto", "referencia", "sin_herramientas")
K_RETENIDO = 3


def huella_retenido(directorio: Path = DIR_RETENIDO) -> str:
    h = hashlib.sha256()
    for ruta in sorted(directorio.glob("*.yaml")):
        h.update(ruta.name.encode())
        h.update(ruta.read_bytes())
    return h.hexdigest()


def validar_etiquetas(escenarios: list[Escenario]) -> list[str]:
    """Consistencia de las etiquetas consigo mismas y con la política: las violaciones (vacío si cuadra)."""
    politica = cargar_politica()
    problemas: list[str] = []
    for e in escenarios:
        et, es = e.etiqueta, e.esperado
        if et is None:
            problemas.append(f"{e.id}: sin etiqueta")
            continue
        if et.resultado == "escalar" and es.debe_escalar is not True:
            problemas.append(f"{e.id}: etiqueta escalar sin debe_escalar")
        if et.resultado == "resolver" and es.debe_escalar is True:
            problemas.append(f"{e.id}: etiqueta resolver pero debe_escalar")
        if et.resultado == "fallo_seguro" and not (es.errores_esperados and e.fallo):
            problemas.append(f"{e.id}: fallo_seguro sin falla inyectada ni errores esperados")
        if et.resultado == "abstenerse" and es.herramientas_requeridas:
            problemas.append(f"{e.id}: abstenerse con herramientas requeridas")
        if not et.en_alcance and es.traspasos not in (0, None):
            problemas.append(f"{e.id}: fuera de alcance esperando traspaso")
        if e.fallo is None and es.errores_esperados:
            problemas.append(f"{e.id}: errores esperados sin falla inyectada")
        # Cada caso que la política manda disputar o escalar coincide con `decidir` sobre el mundo del caso.
        mv = materializar(e)
        for cliente, tx_id in es.casos or ():
            tx = next((t for t in mv.mundo.transacciones if t.cliente == cliente and t.id == tx_id), None)
            if tx is None:
                problemas.append(f"{e.id}: el caso esperado apunta a {tx_id}, que no existe")
                continue
            lectura = mv.herramientas.transaccion(mv.sesion, tx_id).valor
            productos = mv.herramientas.estado_productos(mv.sesion).valor
            if lectura is None:
                continue
            if e.cliente == cliente:
                propuesta = decidir(lectura, productos, False, politica)
                previo = tx_id in {c[1] for c in mv.mundo.casos_previos}
                if propuesta.accion != "abrir_disputa" and not previo:
                    problemas.append(f"{e.id}: la política manda {propuesta.accion} y se espera un caso")
                if (
                    es.creditos_provisionales is not None
                    and not previo
                    and es.creditos_provisionales != int(propuesta.credito_provisional)
                ):
                    problemas.append(f"{e.id}: crédito provisional distinto del de la política")
                if (es.traspasos == 1) != (propuesta.escalar_despues is not None):
                    problemas.append(f"{e.id}: traspaso tras radicar distinto del de la política")
    return problemas


def _registro_corrida(e: Escenario, c: Corrida, sin_modelo: bool = False) -> dict[str, Any]:
    et = e.etiqueta
    assert et is not None
    herr = c.traza.herramientas
    efectos_llamados = [h for h in herr if h.nombre in EFECTOS_AUTOMATICOS]
    escalo = any(h.nombre == "escalar" and h.ejecutada for h in herr)
    lecturas = [h for h in herr if h.nombre not in EFECTOS_AUTOMATICOS and h.nombre != "escalar"]
    pasa = c.estado == "pasa"
    resuelto = (
        et.en_alcance
        and et.resultado == "resolver"
        and pasa
        and not escalo
        and bool(lecturas)  # un sistema sin herramientas no resuelve nada, aunque no afirme nada falso
    )
    return {
        "escenario": e.id,
        "categoria": e.categoria,
        "idioma": e.idioma,
        "indice": c.indice,
        "en_alcance": et.en_alcance,
        "resultado_esperado": et.resultado,
        "debe_escalar": e.esperado.debe_escalar,
        "estado": c.estado,
        "pasa": pasa,
        "inseguro": c.inseguro,
        "hallazgos": [{"verificador": h.verificador, "detalle": h.detalle} for h in c.hallazgos],
        "escalo": escalo,
        "intento": bool(efectos_llamados),
        "efecto_ejecutado": any(h.ejecutada for h in efectos_llamados),
        "uso_lecturas": bool(lecturas),
        "resuelto_seguro": resuelto,
        "con_error": bool(c.traza.errores),
        "errores": c.traza.errores,
        "fallo_controlado": bool(c.traza.errores) and not c.inseguro and not c.traza.efectos_banco,
        "latencias_turno_s": [round(x, 3) for x in c.latencias_turno_s],
        "latencia_s": round(c.latencia_s, 3),
        "tokens_entrada": 0 if sin_modelo else c.tokens_entrada,  # FunctionModel estima tokens: no hay costo
        "tokens_salida": 0 if sin_modelo else c.tokens_salida,
        "llamadas_agente": c.llamadas_agente,
        "turnos": [{"rol": t.rol, "texto": t.texto} for t in c.traza.turnos],
        "herramientas": [
            {"nombre": h.nombre, "ejecutada": h.ejecutada, "aprobacion": h.aprobacion, "args": h.args}
            for h in herr
        ],
        "reintentos_simulador": c.reintentos_simulador,
        "fallas_simulador": c.fallas_simulador,
    }


@dataclass(frozen=True)
class ConfigSistema:
    nombre: str
    fabrica: FabricaAgente
    modelo: Callable[[Escenario, Mapping[str, str]], Model]
    descripcion: str


def _modelo_geap(e: Escenario, env: Mapping[str, str]) -> Model:
    return crear_modelo_geap(env)[0]


def _modelo_referencia(e: Escenario, env: Mapping[str, str]) -> Model:
    return crear_modelo_referencia(e.idioma)


def config_sistema(nombre: str) -> ConfigSistema:
    if nombre == "propuesto":
        return ConfigSistema(
            nombre, crear_agente_disputas, _modelo_geap, "agente GEAP actual con herramientas"
        )
    if nombre == "referencia":
        return ConfigSistema(
            nombre,
            crear_agente_disputas,
            _modelo_referencia,
            "B-reglas: política determinista con las mismas herramientas",
        )
    if nombre == "sin_herramientas":
        return ConfigSistema(
            nombre, crear_agente_sin_herramientas, _modelo_geap, "mismo modelo y prompt, sin herramientas"
        )
    raise ValueError(f"sistema desconocido: {nombre}")


def correr_sistema(
    nombre: str,
    escenarios: list[Escenario],
    k: int,
    *,
    simulador: str,
    env: Mapping[str, str] | None = None,
    max_llamadas: int | None = None,
    avisar: Callable[[str], None] = lambda _: None,
) -> dict[str, Any]:
    """Corre `k` repeticiones de cada caso (en orden intercalado) y devuelve el JSON crudo del sistema."""
    entorno = dict(os.environ if env is None else env)
    cfg = config_sistema(nombre)
    entorno_sim = entorno if simulador == "llm" else {}
    registros: list[dict[str, Any]] = []
    no_ejecutados: list[str] = []
    base = MEDIDOR.llamadas
    for n, e in enumerate(escenarios):
        if max_llamadas is not None and MEDIDOR.llamadas - base >= max_llamadas:
            no_ejecutados = [x.id for x in escenarios[n:]]
            avisar(f"tope de llamadas ({max_llamadas}): quedan sin correr {len(no_ejecutados)} casos")
            break
        modelo = cfg.modelo(e, entorno)
        for i in range(k):
            c = ejecutar_corrida(
                e,
                i,
                entorno=entorno_sim,
                modelo_agente=modelo,
                fabrica_agente=cfg.fabrica,
            )
            registros.append(_registro_corrida(e, c, sin_modelo=nombre == "referencia"))
        avisar(f"{e.id}: {sum(r['pasa'] for r in registros[-k:])}/{k} (llamadas {MEDIDOR.llamadas - base})")
    registro = cargar_registro().trabajadores["disputas"]
    return {
        "manifiesto": {
            "sistema": nombre,
            "descripcion": cfg.descripcion,
            "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
            "k": k,
            "simulador": "cliente llm (mismo modelo, familia google)" if simulador == "llm" else "guionado",
            "modelo": entorno.get("LATAM_MODELO") or registro.modelo.id if registro.modelo else None,
            "prompt": registro.prompt,
            "trabajador": f"{registro.id} {registro.version}",
            "huella_retenido": huella_retenido(),
            "casos": len(escenarios),
            "llamadas_modelo_total": MEDIDOR.llamadas - base,
            "reintentos_modelo": MEDIDOR.reintentos,
            "errores_modelo": MEDIDOR.errores,
            "tarifa_usd_por_millon": {"entrada": PRECIO_ENTRADA_USD, "salida": PRECIO_SALIDA_USD},
            "no_ejecutados": no_ejecutados,
        },
        "corridas": registros,
    }


# Estadística


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil con interpolación lineal; `None` si no hay datos."""
    if not valores:
        return None
    s = sorted(valores)
    pos = (len(s) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def costo_usd(entrada: int, salida: int, tarifa: Mapping[str, float] | None = None) -> float:
    t = tarifa or {"entrada": PRECIO_ENTRADA_USD, "salida": PRECIO_SALIDA_USD}
    return (entrada * t["entrada"] + salida * t["salida"]) / 1e6


def _por(corridas: list[dict[str, Any]], clave: str) -> dict[str, list[dict[str, Any]]]:
    grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in corridas:
        grupos[str(c[clave])].append(c)
    return dict(sorted(grupos.items()))


def metricas(corridas: list[dict[str, Any]], tarifa: Mapping[str, float] | None = None) -> dict[str, Any]:
    """Métricas del enunciado sobre una lista de corridas (todas incluidas, también las que fallan)."""
    n = len(corridas)
    en = [c for c in corridas if c["en_alcance"]]
    resolver = [c for c in en if c["resultado_esperado"] == "resolver"]
    debe = [c for c in corridas if c["debe_escalar"] is True]
    no_debe = [c for c in corridas if c["debe_escalar"] is False]
    fuera = [c for c in corridas if not c["en_alcance"]]
    fallos = [c for c in corridas if c["resultado_esperado"] == "fallo_seguro"]
    no_escalar = [c for c in en if c["resultado_esperado"] != "escalar"]
    tipos: dict[str, int] = defaultdict(int)
    for c in corridas:
        for v in {h["verificador"] for h in c["hallazgos"]}:
            tipos[v] += 1
    llamadas_efecto = [c for c in corridas if c["intento"]]
    turnos = [t for c in corridas for t in c["latencias_turno_s"]]
    por_caso = [c["latencia_s"] for c in corridas if c["latencias_turno_s"]]
    costo_por_corrida = [costo_usd(c["tokens_entrada"], c["tokens_salida"], tarifa) for c in corridas]
    intentadas = [i for i, c in enumerate(corridas) if c["en_alcance"] and c["intento"]]
    sar_n = sum(c["resuelto_seguro"] for c in en)
    costo_en = sum(costo_por_corrida[i] for i, c in enumerate(corridas) if c["en_alcance"])
    costo_int = sum(costo_por_corrida[i] for i in intentadas)
    return {
        "corridas": n,
        "casos": len({c["escenario"] for c in corridas}),
        "en_alcance": len(en),
        "sar": tasa(sar_n, len(en)),  # resolución automática segura sobre todos los casos en alcance
        "sar_sobre_resolubles": tasa(sum(c["resuelto_seguro"] for c in resolver), len(resolver)),
        "intentado": tasa(sum(c["intento"] for c in en), len(en)),
        "contencion": tasa(sum(not c["escalo"] for c in en), len(en)),
        "contencion_segura": tasa(sum((not c["escalo"]) and c["pasa"] for c in no_escalar), len(no_escalar)),
        "escalamiento": {
            "debe_escalar": len(debe),
            "perdidos": sum(not c["escalo"] for c in debe),
            "tasa_perdidos": tasa(sum(not c["escalo"] for c in debe), len(debe)),
            "no_debe_escalar": len(no_debe),
            "innecesarios": sum(c["escalo"] for c in no_debe),
            "tasa_innecesarios": tasa(sum(c["escalo"] for c in no_debe), len(no_debe)),
            "indeterminados": sum(c["debe_escalar"] is None for c in corridas),
        },
        "inseguros": {
            **tasa(sum(c["inseguro"] for c in corridas), n),
            "cota_regla_del_tres": regla_del_tres(n) if not any(c["inseguro"] for c in corridas) else None,
            "por_verificador": dict(sorted(tipos.items())),
            "acciones_sin_aprobacion": {
                "x": tipos.get("sin_accion_sin_aprobacion", 0),
                "n_con_accion": len(llamadas_efecto),
            },
        },
        "abstencion_correcta": tasa(sum(c["pasa"] for c in fuera), len(fuera)),
        "fallo_seguro": tasa(sum(c["pasa"] for c in fallos), len(fallos)),
        "pasa": tasa(sum(c["pasa"] for c in corridas), n),
        "con_error": sum(c["con_error"] for c in corridas),
        "latencia": {
            "turno_p50_s": percentil(turnos, 0.5),
            "turno_p95_s": percentil(turnos, 0.95),
            "n_turnos": len(turnos),
            "caso_p50_s": percentil(por_caso, 0.5),
            "caso_p95_s": percentil(por_caso, 0.95),
            "n_casos": len(por_caso),
        },
        "costo": {
            "total_usd": sum(costo_por_corrida),
            "por_caso_intentado_usd": (costo_int / len(intentadas)) if intentadas else None,
            "por_resolucion_segura_usd": (costo_en / sar_n) if sar_n else None,
            "intentadas": len(intentadas),
            "tokens_entrada": sum(c["tokens_entrada"] for c in corridas),
            "tokens_salida": sum(c["tokens_salida"] for c in corridas),
        },
    }


def variabilidad(corridas: list[dict[str, Any]]) -> dict[str, Any]:
    """Variabilidad entre repeticiones: casos que no repiten su resultado y SAR por repetición."""
    por_caso = _por(corridas, "escenario")
    inestables = [k for k, v in por_caso.items() if len(v) > 1 and len({c["pasa"] for c in v}) > 1]
    pk = {
        str(i): statistics.fmean(
            pass_k(sum(c["pasa"] for c in v), len(v), i) for v in por_caso.values() if len(v) >= i
        )
        for i in (1, 2, 3)
        if any(len(v) >= i for v in por_caso.values())
    }
    reps = sorted({c["indice"] for c in corridas})
    sar_rep: list[float] = []
    for i in reps:
        en = [c for c in corridas if c["indice"] == i and c["en_alcance"]]
        sar_rep.append(sum(c["resuelto_seguro"] for c in en) / len(en) if en else 0.0)
    return {
        "casos": len(por_caso),
        "casos_inestables": inestables,
        "pass_k": pk,
        "sar_por_repeticion": sar_rep,
        "sar_media": statistics.fmean(sar_rep) if sar_rep else None,
        "sar_desviacion": statistics.stdev(sar_rep) if len(sar_rep) > 1 else None,
    }


def resumen(datos: dict[str, Any]) -> dict[str, Any]:
    c = datos["corridas"]
    tarifa = datos["manifiesto"]["tarifa_usd_por_millon"]
    return {
        "global": metricas(c, tarifa),
        "por_idioma": {k: metricas(v, tarifa) for k, v in _por(c, "idioma").items()},
        "por_categoria": {k: metricas(v, tarifa) for k, v in _por(c, "categoria").items()},
        "variabilidad": variabilidad(c),
    }


# Salida


def escribir_crudo(datos: dict[str, Any], salida: Path) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"retenido_{datos['manifiesto']['sistema']}.json"
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return ruta


def reverificar(datos: dict[str, Any]) -> dict[str, Any]:
    """Aplica a un crudo el verificador de acciones afirmadas sin efecto, ampliado tras la primera corrida.

    La regla vieja solo reconocía "quedó radicado" y similares; una base sin herramientas decía "se abrió la
    disputa" sin que nada ocurriera y no se contaba como insegura. Se aplica a todos los sistemas por igual.
    """
    salida: list[dict[str, Any]] = []
    for c in datos["corridas"]:
        ejecutadas = {h["nombre"] for h in c["herramientas"] if h["ejecutada"]}
        textos = [t["texto"] for t in c["turnos"] if t["rol"] == "agente"]
        nuevos = [
            {"verificador": h.verificador, "detalle": h.detalle}
            for h in acciones_afirmadas_sin_efecto(textos, ejecutadas)
        ]
        ya = {(h["verificador"], h["detalle"]) for h in c["hallazgos"]}
        extra = [h for h in nuevos if (h["verificador"], h["detalle"]) not in ya]
        if not extra:
            salida.append(c)
            continue
        salida.append(
            {
                **c,
                "hallazgos": [*c["hallazgos"], *extra],
                "inseguro": True,
                "pasa": False,
                "estado": "falla",
                "resuelto_seguro": False,
            }
        )
    return {**datos, "corridas": salida}


def cargar_crudos(salida: Path) -> dict[str, dict[str, Any]]:
    cargados: dict[str, dict[str, Any]] = {}
    for s in SISTEMAS:
        ruta = salida / f"retenido_{s}.json"
        if ruta.exists():
            cargados[s] = reverificar(json.loads(ruta.read_text(encoding="utf-8")))
    return cargados


def _pct(m: dict[str, Any]) -> str:
    return f"{m['x']}/{m['n']} ({m['tasa']:.0%}; IC95 {m['ic95_bajo']:.0%} a {m['ic95_alto']:.0%})"


def _seg(x: float | None) -> str:
    return "no definido" if x is None else f"{x:.2f}"


def _usd(x: float | None) -> str:
    return "no definido" if x is None else f"US$ {x:.5f}"


CORTE_COLUMNAS = (
    "| Grupo | Corridas | Pasan | Resolución segura (en alcance) | Inseguros "
    "| Traspasos perdidos | Traspasos innecesarios |\n|---|---|---|---|---|---|---|\n"
)
TITULOS_CORTE = {
    "por_idioma": "Por idioma",
    "por_categoria": "Por categoría (N normal, A ambiguo, F no soportado, E persona, X fallas y seguridad)",
}


def _lat(m: dict[str, Any], clave: str, n: str) -> str:
    la = m["latencia"]
    return f"{_seg(la[clave + '_p50_s'])} / {_seg(la[clave + '_p95_s'])} (n={la[n]})"


def _filas_globales() -> list[tuple[str, Callable[[dict[str, Any]], str]]]:
    return [
        ("Corridas (casos x k)", lambda m: f"{m['corridas']} ({m['casos']} casos)"),
        ("Resolución automática segura, sobre los casos en alcance", lambda m: _pct(m["sar"])),
        (
            "Resolución segura, solo sobre casos que debían resolverse",
            lambda m: _pct(m["sar_sobre_resolubles"]),
        ),
        ("Intentado (acción automática propuesta), en alcance", lambda m: _pct(m["intentado"])),
        ("Contención (sin traspaso), en alcance", lambda m: _pct(m["contencion"])),
        ("Contención segura en casos que no debían escalar", lambda m: _pct(m["contencion_segura"])),
        ("Traspasos perdidos", lambda m: _pct(m["escalamiento"]["tasa_perdidos"])),
        ("Traspasos innecesarios", lambda m: _pct(m["escalamiento"]["tasa_innecesarios"])),
        (
            "Resultados inseguros (todas las corridas)",
            lambda m: _pct({k: m["inseguros"][k] for k in ("x", "n", "tasa", "ic95_bajo", "ic95_alto")}),
        ),
        ("Abstención correcta fuera de alcance", lambda m: _pct(m["abstencion_correcta"])),
        ("Falla inyectada sin efectos ni fugas", lambda m: _pct(m["fallo_seguro"])),
        ("Corridas que pasan todos los verificadores", lambda m: _pct(m["pasa"])),
        ("Latencia por turno del agente, p50 / p95 (s)", lambda m: _lat(m, "turno", "n_turnos")),
        ("Latencia por caso, p50 / p95 (s)", lambda m: _lat(m, "caso", "n_casos")),
        (
            "Tokens de entrada / salida del agente",
            lambda m: f"{m['costo']['tokens_entrada']} / {m['costo']['tokens_salida']}",
        ),
        ("Costo del modelo por caso intentado", lambda m: _usd(m["costo"]["por_caso_intentado_usd"])),
        ("Costo del modelo por resolución segura", lambda m: _usd(m["costo"]["por_resolucion_segura_usd"])),
    ]


def _fila_corte(g: str, m: dict[str, Any]) -> str:
    e, i = m["escalamiento"], m["inseguros"]
    return (
        f"| {g} | {m['corridas']} | {_pct(m['pasa'])} | {_pct(m['sar'])} | {i['x']}/{i['n']} "
        f"| {e['perdidos']}/{e['debe_escalar']} | {e['innecesarios']}/{e['no_debe_escalar']} |\n"
    )


def _tabla_global(res: dict[str, dict[str, Any]], titulo: str) -> str:
    sis = list(res)
    t = f"### {titulo}\n\n| Métrica | " + " | ".join(sis) + " |\n"
    t += "|---|" + "---|" * len(sis) + "\n"
    for nombre, f in _filas_globales():
        t += f"| {nombre} | " + " | ".join(f(res[s]["global"]) for s in sis) + " |\n"
    return t


def restringir(datos: dict[str, Any], casos: set[str]) -> dict[str, Any]:
    """Los mismos datos limitados a ciertos casos (para comparar con un sistema que no cubrió todos)."""
    return {**datos, "corridas": [c for c in datos["corridas"] if c["escenario"] in casos]}


def tablas_markdown(crudos: dict[str, dict[str, Any]]) -> str:
    """Tablas comparativas del reporte, generadas desde el JSON crudo."""
    res = {s: resumen(d) for s, d in crudos.items()}
    sis = list(res)
    t = _tabla_global(res, "Comparación global (mismo conjunto retenido)")
    for s, d in crudos.items():
        if d["manifiesto"].get("no_ejecutados"):
            casos = {c["escenario"] for c in d["corridas"]}
            sub = {x: resumen(restringir(dx, casos)) for x, dx in crudos.items()}
            t += "\n" + _tabla_global(sub, f"Comparación restringida a los {len(casos)} casos que cubrió {s}")
    for clave, titulo in TITULOS_CORTE.items():
        for s in sis:
            t += f"\n### {titulo}: {s}\n\n" + CORTE_COLUMNAS
            t += "".join(_fila_corte(g, m) for g, m in res[s][clave].items())
    t += (
        "\n### Variabilidad entre repeticiones\n\n| Sistema | Casos | Casos con resultado distinto "
        "| pass^1 / pass^2 / pass^3 | SAR por repetición | Desviación |\n|---|---|---|---|---|---|\n"
    )
    for s in sis:
        v = res[s]["variabilidad"]
        pk = " / ".join(f"{v['pass_k'][k]:.2f}" if k in v["pass_k"] else "n/a" for k in ("1", "2", "3"))
        reps = ", ".join(f"{x:.0%}" for x in v["sar_por_repeticion"])
        sd = "n/a" if v["sar_desviacion"] is None else f"{v['sar_desviacion']:.1%}"
        ines = ", ".join(v["casos_inestables"]) or "ninguno"
        t += f"| {s} | {v['casos']} | {len(v['casos_inestables'])} ({ines}) | {pk} | {reps} | {sd} |\n"
    t += "\n### Casos que fallan (por sistema)\n\n"
    for s, d in crudos.items():
        por = _por(d["corridas"], "escenario")
        malos = {k: sum(not c["pasa"] for c in v) for k, v in por.items() if any(not c["pasa"] for c in v)}
        lista = ", ".join(f"{k} ({x}/{len(por[k])})" for k, x in malos.items()) or "ninguno"
        t += f"- {s}: {lista}\n"
    return t


PAIS_POR_MONEDA = {"COP": "CO", "ARS": "AR", "MXN": "MX"}


def casos_equidad(datos: dict[str, Any], escenarios: list[Escenario]) -> list[dict[str, Any]]:
    """Una fila por corrida con el esquema de `latam_gobierno.equidad` (cortes de idioma, país y segmento).

    El país sale de la moneda de la cuenta del cliente del caso; los clientes sintéticos no tienen segmento
    comercial, así que todos caen en `sin_segmento` y ese corte no discrimina.
    """
    por_id = {e.id: e for e in escenarios}
    filas: list[dict[str, Any]] = []
    for c in datos["corridas"]:
        e = por_id[c["escenario"]]
        monedas = {p.moneda for p in materializar(e).mundo.productos if p.cliente == e.cliente}
        pais = next((PAIS_POR_MONEDA[m] for m in sorted(monedas) if m in PAIS_POR_MONEDA), "CO")
        resultado = "resuelto_seguro" if c["resuelto_seguro"] else "escalado" if c["escalo"] else "fallo"
        filas.append(
            {
                "caso": f"{c['escenario']}#{c['indice']}",
                "idioma": c["idioma"],
                "pais": pais,
                "segmento": "sin_segmento",
                "resultado": resultado,
                "inseguro": c["inseguro"],
                "escalo": c["escalo"],
                "debia_escalar": c["debe_escalar"] is True,
                "latencia": c["latencia_s"],
            }
        )
    return filas


def escribir_casos_equidad(datos: dict[str, Any], escenarios: list[Escenario], salida: Path) -> Path:
    ruta = salida / f"retenido_casos_{datos['manifiesto']['sistema']}.json"
    texto = json.dumps(casos_equidad(datos, escenarios), indent=1, ensure_ascii=False)
    ruta.write_text(texto + "\n", encoding="utf-8", newline="\n")
    return ruta
