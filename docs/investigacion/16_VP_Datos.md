# Investigación 16 (VP Datos): datos como producto, métricas oficiales y la pila de contratos y linaje

**Cara:** VP Datos ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)). **Preguntas:** ¿qué
significa que cada tabla de oro sea un producto de datos con dueño y contrato? ¿Cómo se definen
métricas oficiales únicas? ¿Qué herramientas concretas dan contratos, pruebas y linaje sobre DuckDB?
¿Qué marco regulatorio le da sentido bancario a todo esto?

**Hallazgo central:** la pila que necesitamos existe y encaja casi sin fricción: **dbt con DuckDB**
para modelos incrementales con contrato, **Data Contract CLI** para validar ODCS contra un archivo de
DuckDB en solo lectura, **OpenLineage** para el linaje (incluso por columna) y **MetricFlow** para
métricas como código. Y hay un marco bancario que ordena el relato: **BCBS 239**, cuyo punto más
débil en la industria es precisamente el linaje.

---

## 1. El relato bancario: BCBS 239 en pequeño

- BCBS 239 son 14 principios del Comité de Basilea (2013) para agregar datos de riesgo con exactitud,
  integridad, completitud, oportunidad y adaptabilidad, con trazabilidad del dato desde el origen
  ([Atlan](https://atlan.com/bcbs-239-guide/), [BIS](https://www.bis.org/publications/implementation-principles-effective-risk-data-aggregation-and-risk-reporting-bcbs-239-principles)).
- Solo el 18% de las instituciones encuestadas lo implementó por completo (BearingPoint 2025), y el
  boletín del Comité de enero de 2026 señala **linaje y trazabilidad** como la brecha principal
  ([Atlan](https://atlan.com/bcbs-239-guide/)).
- Con la IA, los mismos principios pasan a ser prerequisito: calidad, linaje y supervisión humana son
  lo que el AI Act pide y lo que BCBS 239 exige desde 2013
  ([Moody's](https://www.moodys.com/web/en/us/kyc/resources/insights/bcbs-239-in-the-agentic-ai-era-from-compliance-to-command-center-data-lineage-and-governance.html)).

**Uso:** el capítulo de datos se presenta como "BCBS 239 aplicado a los datos que consume un agente":

| Principio (resumido) | Cómo lo cumplimos ([03](../Diseno/03_Datos_por_capas.md)) |
|---|---|
| Gobierno y arquitectura de datos | VP Datos dueña; capas con contrato; manifiesto por corrida |
| Exactitud e integridad | tipado, dominios canónicos, cuarentena, coherencia de dueño |
| Completitud | conteos de entrada, salida, rechazos y duplicados que cuadran |
| Oportunidad | política de frescura contra el reloj simulado |
| Adaptabilidad | evolución de esquema absorbida o en cuarentena, probada con el *fixture* |
| Exactitud del reporte | toda cifra del informe sale de una consulta sobre platino |

## 2. Cada tabla de oro es un producto de datos

- En 2026 el contrato de un producto de datos reúne esquema, reglas de calidad, SLO, políticas de
  acceso, dueño y linaje en un solo artefacto legible por máquina
  ([OvalEdge](https://www.ovaledge.com/blog/data-contract-in-data-mesh),
  [Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/data-strategy/the-state-of-data-mesh-in-2026-from-hype-to-hard-won-maturity)).
- La malla de datos pasó de moda a práctica: lo que quedó es **dato con dueño, contrato y SLO** como
  base de una IA confiable.

**En LATAM Bank:** cada tabla de oro tiene una ficha de producto:

| Producto | Dueño | Consumidores | SLO |
|---|---|---|---|
| `transacciones_recientes` | VP Datos | servicio de cuentas (herramienta del agente) | frescura 1 día; 0 filas con `_owner_ok` falso; 0 PII directa |
| `ficha_transaccion` (investigación 14) | VP Datos, con VP Clientes | herramienta de ficha | idem, más comercio y compras previas |
| `features_transaccion` | VP Datos, con VP IA | puntaje de riesgo | ninguna característica posterior al evento |
| `metricas_reporte` | VP Datos | Presidencia, jurado | cada métrica con su definición versionada |

## 3. La pila concreta

| Pieza | Herramienta | Lo que aporta aquí |
|---|---|---|
| Transformación | **dbt con el adaptador de DuckDB** | estrategias incrementales `merge`, `delete+insert`, `append` y `microbatch`; para *upsert* por llave, `merge` ([dbt-duckdb](https://github.com/duckdb/dbt-duckdb), [dbt](https://docs.getdbt.com/docs/build/incremental-strategy)) |
| Contrato en el modelo | **contratos de dbt** | en modelos incrementales solo con `on_schema_change` en `append_new_columns` o `fail` ([dbt](https://docs.getdbt.com/reference/resource-configs/contract)): es **exactamente** la política del *fixture*: lo aditivo se absorbe, lo que rompe falla |
| Contrato como artefacto | **ODCS** validado con **Data Contract CLI** | la CLI abre un archivo de DuckDB **en solo lectura** y corre pruebas de esquema y calidad (motor Soda) contra el contrato ([Data Contract CLI](https://docs.datacontract.com/testing/duckdb)) |
| Linaje | manifiesto de dbt más **OpenLineage** (`dbt-ol`, un posprocesador) | eventos por corrida; linaje por columna con la faceta `columnLineage` o derivado con sqlglot ([OpenLineage](https://openlineage.io/docs/integrations/dbt/), [ejemplo DuckDB](https://github.com/oluies/duckdb-openmetadata-lineage)); Marquez para verlo, opcional |
| Métricas | **MetricFlow**, con licencia Apache 2.0 desde octubre de 2025 y usable sin dbt Cloud | métricas como código en YAML ([dbt](https://docs.getdbt.com/docs/build/about-metricflow), [Datus](https://datus.ai/blog/dbt-semantic-layer-metricflow/)); verificar en F0 su adaptador para DuckDB |

**Argumento que vale oro ante el jurado:** con linaje por columna se puede **demostrar** que ninguna
columna marcada como PII en el contrato llega a oro operacional (la que ve el agente). Es privacidad
probada con el grafo, no afirmada.

## 4. Métricas oficiales

Las métricas del reporte (resolución automática segura, contención, calidad de escalamiento,
resultados inseguros, latencia, costo, equidad) se definen **una vez** como código sobre platino,
con versión. Dos opciones:

| Opción | Pro | Contra |
|---|---|---|
| MetricFlow | estándar, exportable (especificación OSI) | una dependencia más y su curva |
| YAML propio más vistas SQL en platino | simple, sin dependencias | menos reconocible |

Recomendación: **vistas SQL con definición en YAML** y MetricFlow solo si el adaptador funciona sin
fricción en F0 (P9). En ambos casos, la definición cita el texto del enunciado que implementa.

## 5. Artefactos de la VP Datos

1. Contratos ODCS de las tablas de plata y de los productos de oro, con PII y SLO.
2. Proyecto dbt con modelos incrementales `merge`, contratos y pruebas.
3. Validación con Data Contract CLI en cada corrida; reporte en platino.
4. Linaje por corrida (manifiesto y OpenLineage) y la prueba de "PII no llega a oro operacional".
5. Definiciones versionadas de las métricas oficiales.
6. Tabla BCBS 239 de la sección 1 como parte del reporte.

## 6. Preguntas abiertas

- ¿Emitir OpenLineage o basta el manifiesto de dbt más el grafo? Depende del tiempo en F3.
- ¿La ficha de la transacción calcula "compras previas en el comercio" en oro (precalculado) o en la
  herramienta (consulta en línea)? Afecta latencia y frescura.

## Fuentes principales

- [BCBS 239, guía de Atlan](https://atlan.com/bcbs-239-guide/) y [BIS](https://www.bis.org/publications/implementation-principles-effective-risk-data-aggregation-and-risk-reporting-bcbs-239-principles)
- [Moody's, BCBS 239 en la era agéntica](https://www.moodys.com/web/en/us/kyc/resources/insights/bcbs-239-in-the-agentic-ai-era-from-compliance-to-command-center-data-lineage-and-governance.html)
- [dbt-duckdb](https://github.com/duckdb/dbt-duckdb) y [contratos de dbt](https://docs.getdbt.com/reference/resource-configs/contract)
- [Data Contract CLI con DuckDB](https://docs.datacontract.com/testing/duckdb)
- [OpenLineage para dbt](https://openlineage.io/docs/integrations/dbt/)
- [MetricFlow](https://docs.getdbt.com/docs/build/about-metricflow)
- [Estado de la malla de datos en 2026, Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/data-strategy/the-state-of-data-mesh-in-2026-from-hype-to-hard-won-maturity)
