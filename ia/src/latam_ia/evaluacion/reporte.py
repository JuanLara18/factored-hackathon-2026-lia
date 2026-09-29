"""Suite, métricas agregadas y reporte en JSON y markdown (R-IA-72: nada se excluye en silencio)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from latam_tecnologia.canales.geap import MEDIDOR
from pydantic_ai.models import Model

from latam_ia.evaluacion.ejecutor import Corrida, ejecutar_corrida, elegir_modelo_agente
from latam_ia.evaluacion.esquema import DIR_ESCENARIOS, RUTA_MUNDO_BASE, Escenario
from latam_ia.evaluacion.metricas import pass_k, regla_del_tres, tasa

K_POR_DEFECTO = 3


@dataclass(frozen=True)
class ResultadoEscenario:
    escenario: Escenario
    corridas: list[Corrida]

    @property
    def n(self) -> int:
        return len(self.corridas)

    @property
    def exitos(self) -> int:
        return sum(c.estado == "pasa" for c in self.corridas)

    @property
    def inseguras(self) -> int:
        return sum(c.inseguro for c in self.corridas)

    @property
    def estado(self) -> str:
        """Un caso que alterna entre seguro e inseguro cuenta como inseguro (R-GOB-58)."""
        if self.exitos == self.n:
            return "falla" if self.escenario.falla_conocida else "pasa"
        if self.escenario.falla_conocida and not any(c.estado == "falla_simulador" for c in self.corridas):
            return "falla_conocida"
        if any(c.estado == "falla_simulador" for c in self.corridas) and not any(
            c.estado == "falla" for c in self.corridas
        ):
            return "falla_simulador"
        return "falla"


def ejecutar_suite(
    escenarios: list[Escenario],
    k: int = K_POR_DEFECTO,
    *,
    entorno: Mapping[str, str] | None = None,
    modelo_agente: Model | None = None,
    modelo_simulador: Model | None = None,
    max_llamadas: int | None = None,
) -> list[ResultadoEscenario]:
    """Corre los escenarios en orden; con `max_llamadas` para antes de un escenario si el medidor de GEAP
    ya llegó al tope (los escenarios que no corrieron se reportan como no ejecutados)."""
    resultados: list[ResultadoEscenario] = []
    for e in escenarios:
        if max_llamadas is not None and MEDIDOR.llamadas >= max_llamadas:
            break
        corridas = [
            ejecutar_corrida(
                e, i, entorno=entorno, modelo_agente=modelo_agente, modelo_simulador=modelo_simulador
            )
            for i in range(k)
        ]
        resultados.append(ResultadoEscenario(e, corridas))
    return resultados


def huella_escenarios(directorio: Path = DIR_ESCENARIOS) -> str:
    h = hashlib.sha256()
    for ruta in sorted([*directorio.glob("*.yaml"), RUTA_MUNDO_BASE]):
        h.update(ruta.name.encode())
        h.update(ruta.read_bytes())
    return h.hexdigest()


def agregar(resultados: list[ResultadoEscenario], k: int) -> dict[str, Any]:
    corridas = [c for r in resultados for c in r.corridas]
    n = len(corridas)
    inseguras = sum(c.inseguro for c in corridas)
    por_categoria: dict[str, dict[str, Any]] = {}
    for cat in sorted({r.escenario.categoria for r in resultados}):
        rs = [r for r in resultados if r.escenario.categoria == cat]
        por_categoria[cat] = {
            "escenarios": len(rs),
            "corridas": tasa(sum(r.exitos for r in rs), sum(r.n for r in rs)),
            "escenarios_que_pasan": sum(r.estado == "pasa" for r in rs),
        }
    fallos = Counter(h.verificador for c in corridas for h in c.hallazgos)
    return {
        "escenarios": len(resultados),
        "corridas": n,
        "k": k,
        "escenarios_que_pasan": sum(r.estado == "pasa" for r in resultados),
        "fallas_conocidas": sum(r.estado == "falla_conocida" for r in resultados),
        "exito_por_corrida": tasa(sum(c.estado == "pasa" for c in corridas), n),
        "pass_k": {
            str(i): sum(pass_k(r.exitos, r.n, i) for r in resultados) / len(resultados) if resultados else 0.0
            for i in range(1, k + 1)
        },
        "resultado_inseguro": {
            **tasa(inseguras, n),
            "cota_regla_del_tres": regla_del_tres(n) if inseguras == 0 else None,
        },
        "escaladas_correctas": _escalamiento(resultados),
        "fallas_simulador": sum(c.estado == "falla_simulador" for c in corridas),
        "reintentos_simulador": sum(c.reintentos_simulador for c in corridas),
        "por_categoria": por_categoria,
        "fallos_por_verificador": dict(sorted(fallos.items())),
    }


def _escalamiento(resultados: list[ResultadoEscenario]) -> dict[str, Any]:
    """Escenarios cuya política manda escalar: cuántas corridas no tuvieron falla de escalamiento."""
    con = [r for r in resultados if r.escenario.esperado.debe_escalar is True]
    corridas = [c for r in con for c in r.corridas]
    ok = sum(all(h.verificador != "escalamiento" for h in c.hallazgos) for c in corridas)
    return tasa(ok, len(corridas))


# Tarifa de lista de Gemini 2.5 Flash-Lite en USD por millón de tokens (entrada, salida).
TARIFA_ENTRADA, TARIFA_SALIDA = 0.10, 0.40


def consumo() -> dict[str, Any]:
    m = MEDIDOR
    return {
        "llamadas": m.llamadas,
        "reintentos": m.reintentos,
        "errores": m.errores,
        "tokens_entrada": m.entrada,
        "tokens_salida": m.salida,
        "latencia_media_s": round(m.segundos / m.llamadas, 2) if m.llamadas else 0.0,
        "costo_estimado_usd": round((m.entrada * TARIFA_ENTRADA + m.salida * TARIFA_SALIDA) / 1e6, 4),
    }


def a_dict(resultados: list[ResultadoEscenario], k: int, agente: str) -> dict[str, Any]:
    modos = sorted({c.modo_simulador for r in resultados for c in r.corridas})
    return {
        "manifiesto": {
            "arnes": "IA-5.1",
            "agente": agente,
            "simulador": modos,
            "k": k,
            "huella_escenarios": huella_escenarios(),
            "consumo": consumo(),
            "aviso": (
                "Con la política de referencia guionada esto mide el arnés, los verificadores y las "
                "herramientas, no la calidad de un modelo."
                if agente == "referencia-guionada"
                else "Agente conducido por un modelo real."
            ),
        },
        "agregado": agregar(resultados, k),
        "escenarios": [
            {
                "id": r.escenario.id,
                "version": r.escenario.version,
                "categoria": r.escenario.categoria,
                "descripcion": r.escenario.descripcion,
                "estado": r.estado,
                "falla_conocida": r.escenario.falla_conocida,
                "corridas": r.n,
                "exitos": r.exitos,
                "inseguras": r.inseguras,
                "hallazgos": [h.como_dict() for c in r.corridas for h in c.hallazgos],
                "fallas_simulador": [f for c in r.corridas for f in c.fallas_simulador],
            }
            for r in resultados
        ],
    }


def a_markdown(datos: dict[str, Any]) -> str:
    m, a = datos["manifiesto"], datos["agregado"]
    e, ins = a["exito_por_corrida"], a["resultado_inseguro"]
    lineas = [
        "# Reporte del arnés de evaluación (IA-5.1)",
        "",
        f"Agente: {m['agente']}. Simulador: {', '.join(m['simulador'])}. k: {m['k']}. "
        f"Huella de escenarios: {m['huella_escenarios'][:16]}.",
        "",
        m["aviso"],
        "",
        *(
            [
                f"Consumo del modelo: {m['consumo']['llamadas']} llamadas "
                f"({m['consumo']['reintentos']} reintentos), "
                f"{m['consumo']['tokens_entrada']} tokens de entrada y {m['consumo']['tokens_salida']} de "
                f"salida, latencia media {m['consumo']['latencia_media_s']} s, costo estimado "
                f"US$ {m['consumo']['costo_estimado_usd']}.",
                "",
            ]
            if m["consumo"]["llamadas"]
            else []
        ),
        "## Métricas agregadas",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Escenarios que pasan | {a['escenarios_que_pasan']} de {a['escenarios']} |",
        f"| Fallas conocidas (hallazgos abiertos) | {a['fallas_conocidas']} |",
        f"| Éxito por corrida | {e['x']} de {e['n']} ({e['tasa']:.1%}, "
        f"IC95 {e['ic95_bajo']:.1%} a {e['ic95_alto']:.1%}) |",
        *[f"| pass^{i} | {v:.3f} |" for i, v in a["pass_k"].items()],
        f"| Resultado inseguro | {ins['x']} de {ins['n']}"
        + (
            f" (cota de la regla del tres {ins['cota_regla_del_tres']:.1%})"
            if ins["cota_regla_del_tres"]
            else ""
        )
        + " |",
        f"| Escalamientos correctos | {a['escaladas_correctas']['x']} de {a['escaladas_correctas']['n']} |",
        f"| Fallas del simulador | {a['fallas_simulador']} (reintentos {a['reintentos_simulador']}) |",
        "",
        "## Por categoría",
        "",
        "| Categoría | Escenarios | Pasan | Corridas exitosas |",
        "|---|---|---|---|",
        *[
            f"| {c} | {v['escenarios']} | {v['escenarios_que_pasan']} | "
            f"{v['corridas']['x']} de {v['corridas']['n']} |"
            for c, v in a["por_categoria"].items()
        ],
        "",
        "## Escenarios",
        "",
        "| Escenario | Categoría | Estado | Exitos | Inseguras |",
        "|---|---|---|---|---|",
        *[
            f"| {s['id']} | {s['categoria']} | {s['estado']} | "
            f"{s['exitos']} de {s['corridas']} | {s['inseguras']} |"
            for s in datos["escenarios"]
        ],
    ]
    fallos = [s for s in datos["escenarios"] if s["hallazgos"] or s["fallas_simulador"]]
    if fallos:
        lineas += ["", "## Hallazgos", ""]
        for s in fallos:
            unicos = sorted(
                {f"{h['verificador']}: {h['detalle']}" for h in s["hallazgos"]} | set(s["fallas_simulador"])
            )
            nota = f" [falla conocida: {s['falla_conocida']}]" if s["falla_conocida"] else ""
            lineas += [f"- {s['id']}: " + "; ".join(unicos) + nota]
    if a["fallos_por_verificador"]:
        lineas += ["", "## Fallos por verificador", ""]
        lineas += [f"- {k}: {v}" for k, v in a["fallos_por_verificador"].items()]
    return "\n".join(lineas) + "\n"


def escribir_trazas(resultados: list[ResultadoEscenario], ruta: Path) -> None:
    """Trazas completas (conversación y herramientas) para el GenAI Evaluation Service; no van a git."""
    datos = [
        {
            "escenario": r.escenario.id,
            "categoria": r.escenario.categoria,
            "idioma": r.escenario.idioma,
            "registro": r.escenario.registro,
            "esperado_herramientas": esperado_herramientas(r.escenario),
            "corridas": [
                {
                    "estado": c.estado,
                    "inseguro": c.inseguro,
                    "hallazgos": [h.como_dict() for h in c.hallazgos],
                    "turnos": [{"rol": t.rol, "texto": t.texto} for t in c.traza.turnos],
                    "herramientas": [
                        {"nombre": h.nombre, "args": h.args, "retorno": h.retorno, "aprobacion": h.aprobacion}
                        for h in c.traza.herramientas
                    ],
                    "errores": c.traza.errores,
                }
                for c in r.corridas
            ],
        }
        for r in resultados
    ]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def esperado_herramientas(e: Escenario) -> list[str]:
    """Secuencia esperada de herramientas con efecto, derivada del estado final esperado del escenario."""
    x = e.esperado
    secuencia: list[str] = []
    if x.bloqueos:
        secuencia.append("bloquear_tarjeta")
    if x.casos and "abrir_disputa" not in x.herramientas_prohibidas:
        nuevos = len(x.casos) - len(e.mundo_extra.casos_previos)
        secuencia += ["abrir_disputa"] * max(nuevos, 0)
    if x.debe_escalar:
        secuencia.append("escalar")
    return secuencia


def escribir(datos: dict[str, Any], salida: Path, etiqueta: str = "ultimo") -> tuple[Path, Path]:
    salida.mkdir(parents=True, exist_ok=True)
    ruta_json, ruta_md = salida / f"{etiqueta}.json", salida / f"{etiqueta}.md"
    ruta_json.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    ruta_md.write_text(a_markdown(datos), encoding="utf-8", newline="\n")
    return ruta_json, ruta_md


def etiqueta_agente(escenarios: list[Escenario], entorno: Mapping[str, str] | None = None) -> str:
    return elegir_modelo_agente(escenarios[0], entorno)[1] if escenarios else "ninguno"
