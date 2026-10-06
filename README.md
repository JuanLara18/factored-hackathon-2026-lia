# LATAM Bank: atención AI-first para cargos no reconocidos

Solución para la **Factored AI & Data Hackathon 2026**: un banco inventado, LATAM Bank, con datos sintéticos de México, Colombia y Argentina. Un agente (Gemini 3.1 Flash-Lite en Agent Runtime de GEAP) recibe disputas por cargos no reconocidos en **español (usted y vos) y portugués (você)**; el código decide (política `policy/v1`, autenticación por acción, aprobación en pantalla) y el modelo entiende y redacta. Si el caso lo requiere, pasa a una persona con un paquete de traspaso de 19 campos.

## For the judges (English)

**LATAM Bank** is a fictional bank built on the hackathon's synthetic dataset. One focused workflow: **AI-first intake of unrecognized card charges**, in Spanish (usted and vos) and Portuguese (você). The model understands and writes; code decides: policy, permissions and approvals live outside the prompt, and a human expert is always one click away.

| What | Where |
|---|---|
| Live solution | https://latam-bank-hackaton-2026.web.app (online banking demo at `/banca/`, human expert console at `/operador/`; the console access code is in the submission email) |
| Slides (6) | [`presidencia/entrega/LATAM_Bank_Factored_Hackathon_2026.pdf`](presidencia/entrega/LATAM_Bank_Factored_Hackathon_2026.pdf) |
| Final report, in Spanish | [`presidencia/reporte/00_reporte_final.md`](presidencia/reporte/00_reporte_final.md): problem, solution, data and ML, evaluation, fairness, production |
| Held-out evaluation | [`presidencia/reporte/04_evaluacion.md`](presidencia/reporte/04_evaluacion.md) |
| Learned component in the workflow | [`ia/evaluacion/reportes/recuperacion_2026-10-05.md`](ia/evaluacion/reportes/recuperacion_2026-10-05.md): policy retrieval with citation, 0.897 vs 0.515 for BM25 |

| Dimension | Evidence |
|---|---|
| Data analytics | Contact reasons, demand, baseline and workflow prioritization with regenerable figures: [`01_problema.md`](presidencia/reporte/01_problema.md) |
| Data engineering | Bronze to platinum layers in BigQuery with dbt (56 tests), ODCS contracts, quality rules, chained manifest, freshness policy and update fixture: [`datos/`](datos/README.md) |
| Machine learning | Three learned components against baselines with leakage controls, one of them a reported negative result: [`03_datos_y_ml.md`](presidencia/reporte/03_datos_y_ml.md) |
| AI engineering | Agent on Gemini with 8 typed tools, policy as code, one-time approvals, output filter, 19-field human handoff, expert copilot: [`02_solucion.md`](presidencia/reporte/02_solucion.md), [`tecnologia/`](tecnologia/README.md) |
| Technical judgment | Where AI and where deterministic logic, trade-offs, failures found and fixed, and what is still missing before operation: [`00_reporte_final.md`](presidencia/reporte/00_reporte_final.md) section 3, [`06_produccion.md`](presidencia/reporte/06_produccion.md) |

**Honest scope.** Every figure is an offline measurement on synthetic data; there is no production traffic. On the first held-out set a rules baseline follows policy as well as the agent (91% vs 80%, overlapping intervals); the agent adds language, conversation and policy answers with sources. The data has no Brazilian accounts and the Portuguese was not reviewed by a native speaker. Voice and WhatsApp are designed, not deployed. No dataset rows or credentials are in this repository.

Run locally without credentials (deterministic scripted model): `uv sync --all-packages --all-groups`, then `uv run pytest -q` and `uv run uvicorn latam_tecnologia.canales.chat_web:crear_app_desde_entorno --factory --port 8765`.

## Para el jurado

| Qué | Dónde |
|---|---|
| Reporte final (resumen, mapa de criterios, AI-first) | [`presidencia/reporte/00_reporte_final.md`](presidencia/reporte/00_reporte_final.md) |
| Capítulos | [problema](presidencia/reporte/01_problema.md), [solución](presidencia/reporte/02_solucion.md), [datos y ML](presidencia/reporte/03_datos_y_ml.md), [evaluación](presidencia/reporte/04_evaluacion.md), [equidad](presidencia/reporte/05_equidad.md), [producción](presidencia/reporte/06_produccion.md) |
| Guion de la demostración | [`presidencia/reporte/demo/guion.md`](presidencia/reporte/demo/guion.md) |
| Sitio en vivo | https://latam-bank-hackaton-2026.web.app |
| Banca en línea de demostración | https://latam-bank-hackaton-2026.web.app/banca/ |
| Consola del experto humano (pide un código de demostración) | https://latam-bank-hackaton-2026.web.app/operador/ |
| Dictamen preliminar de Auditoría | [`auditoria/reportes/dictamen_borrador.md`](auditoria/reportes/dictamen_borrador.md) |

**Alcance honesto.** Todo es evaluación fuera de línea sobre datos sintéticos; no hay medición de producción. En producción corre el chat web; WhatsApp y voz son diseño. El portugués es atención a clientes de la región (no hay cuentas de Brasil) y no lo ha revisado un hablante nativo. Los límites y las fallas halladas están en el reporte final y en [producción](presidencia/reporte/06_produccion.md).

## Correr en local (5 comandos)

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) y [just](https://github.com/casey/just). Sin credenciales corre con un modelo de guion determinista (sin llamadas a Gemini ni a Google Cloud).

```bash
git clone https://github.com/JuanLara18/factored-hackathon-2026-lia.git
cd factored-hackathon-2026-lia
uv sync --all-packages --all-groups
just check          # formato, tipos y pruebas
just chat           # chat web local en http://localhost:8765
```

Con `GEMINI_API_KEY` el chat usa Gemini; con `LATAM_GCP_PROJECT` y credenciales de Google Cloud usa GEAP. La evaluación: `uv run python -m latam_ia.evaluacion --retenido` (la línea base de reglas corre sin red).

**¿Sesión nueva?** Empieza por [`presidencia/ESTADO.md`](presidencia/ESTADO.md): dónde estamos y qué sigue.

## El repositorio es el organigrama

Cada carpeta de primer nivel es una cara de LATAM Bank y su dueña está en `.github/CODEOWNERS`.

| Carpeta | Cara | Qué vive ahí |
|---|---|---|
| [`presidencia/`](presidencia/README.md) | Presidencia y Oficina de Entrega | modelo operativo, decisiones, backlog, hoja de ruta, bitácora, reporte final |
| [`comun/`](comun/README.md) | Comité de Plataforma | contratos compartidos: los tipos del dominio que conectan a todas las caras |
| [`clientes/`](clientes/README.md) | VP Clientes | guiones, plantillas, operación humana, demo |
| [`ia/`](ia/README.md) | VP Inteligencia Artificial | comprensión, redacción, voz, registro de agentes, arnés de evaluación |
| [`datos/`](datos/README.md) | VP Datos | ingesta, capas bronce a platino, contratos de datos, *fixture* |
| [`tecnologia/`](tecnologia/README.md) | VP Tecnología | motor, herramientas, servicios, canales, gateway, sitio web, infraestructura, ADR |
| [`gobierno/`](gobierno/README.md) | VP Gobierno | política como código, amenazas, adversariales, privacidad, equidad, actas |
| [`auditoria/`](auditoria/README.md) | Auditoría | matriz de trazabilidad, fuentes, dictamen |
| [`docs/`](docs/README.md) | todas | investigación, diseño y enunciado |
| `.claude/agents/` | Gobierno y Auditoría | subagentes revisores en frío |

## Empezar

```bash
uv sync --all-packages --all-groups   # dependencias de todas las caras
just check         # formato, tipos y pruebas
```

Las reglas de trabajo (ramas, commits, revisiones y compuertas) están en [CONTRIBUTING.md](CONTRIBUTING.md).
