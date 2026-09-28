# Investigación 9: grafos, GNN y GraphRAG

**Pregunta:** ¿dónde aportan de verdad los grafos en este problema? Hay tres usos distintos que
suelen mezclarse: **modelos de aprendizaje sobre grafos** (GNN) para fraude, **GraphRAG** para
recuperar conocimiento, y **agentes que consultan un grafo** como herramienta. ¿Qué dice la
evidencia de cada uno y qué encaje tiene con el dataset?

**Hallazgo central:** los grafos **no son una mejora universal**; ganan cuando la pregunta es
**relacional o de varios saltos**, y empatan o pierden en consultas simples. La buena noticia:
**el dataset ya es un grafo** (13 tablas unidas por llaves foráneas), y en fraude y disputas las
preguntas **sí son relacionales**: ¿cuántos clientes disputan el mismo comercio? ¿esta cuenta
receptora recibe de muchas víctimas? Ahí los grafos tienen un argumento real, no decorativo.

> **Nota del 26 de septiembre de 2026, tras la [auditoría del dataset](13_Auditoria_del_dataset.md):** las aristas interacción, reclamo y producto del grafo de la sección 1 no son reales (`origin_interaction_id` vacío; el producto de la queja pertenece a otro cliente). El punto común de compromiso solo puede salir de `transactions` (comercio presente en el 23% de las filas, fraude 0,1%), y las transferencias no traen contraparte, así que las mulas no son modelables con estos datos.

---

## 1. El dataset como grafo heterogéneo

Las llaves foráneas del diccionario definen un **grafo heterogéneo** (varios tipos de nodos y de
aristas):

```
                 ┌──── Sucursal ────┐
                 │                  │
Agente ── Interacción ── Cliente ── Producto ── Transacción ── Comercio
   │          │            │                        │
   └── Transcripción   Reclamo ─────────────────────┘
               │            │
            Encuesta    Campaña
```

Nodos: cliente, producto, transacción, **comercio** (derivado de `merchant_name`), interacción,
transcripción, reclamo, agente, sucursal, campaña. Aristas: posee, realizó, en comercio, atendido
por, originó reclamo, afecta producto.

## 2. GNN para fraude: cuándo ganan y cuándo no

La literatura de GNN para fraude financiero es grande
([revisión, arXiv 2411.05815](https://arxiv.org/pdf/2411.05815)): GraphSAGE, GAT, grafos
heterogéneos con metacaminos, grafos dinámicos. Pero el benchmark más reciente pone un matiz
importante:

**[FinFraudBench](https://arxiv.org/pdf/2608.15177) (agosto de 2026)**, grafos heterogéneos de
cuentas, transacciones y comercios:
- **gradient boosting sobre características tabulares queda competitivo o mejor** que las GNN en
  marcar transacciones individuales;
- los grafos **ganan en patrones relacionales**: anillos, transacciones circulares, redes;
- ninguna familia domina; los híbridos prometen.

**Traducción práctica:** para "¿esta transacción es fraude?" el `fraud_score` y un modelo tabular
bastan. Para "¿esta cuenta es parte de una red de mulas?" o "¿este comercio es un punto de
compromiso?" el grafo es la herramienta correcta. Y **no hace falta una GNN** para empezar:
**características de grafo** (grado, vecinos en común, componentes conexas, PageRank) metidas en un
modelo tabular capturan buena parte de la señal con mucho menos costo. Es la línea base honesta
contra la cual una GNN tendría que justificarse.

### Modelos fundacionales relacionales

Una línea nueva: **modelos que aprenden directamente de la base relacional** sin ingeniería de
características. **KumoRFM** (Stanford y Kumo, 2025; Leskovec, Fey) hace predicción **en contexto**
sobre bases multitabla, y **KumoRFM-2** obtiene el mejor AUROC promedio (79,6) en las 12 tareas de
clasificación de **RelBench**, casi 4 puntos sobre el mejor modelo tabular
([KumoRFM-2](https://arxiv.org/html/2604.12596v1), [NVIDIA](https://docs.nvidia.com/sdgm/research/kumorfm-paper)).
Encaje: predecir **escalamiento, recontacto o riesgo de disputa** directamente desde las 13
tablas. Es innovador, pero depende de acceso al modelo; como mínimo, es una referencia para
justificar el enfoque relacional.

## 3. Tres usos de grafo con encaje directo en el reto

### A. Punto común de compromiso

Cuando muchas tarjetas se comprometen en el mismo comercio (un *skimmer*, una filtración), las
disputas por fraude de clientes distintos **convergen** en él. Es un patrón clásico de los equipos
de fraude.

- **En el grafo:** clientes → transacciones disputadas → comercio. Un comercio con muchas
  disputas de fraude de clientes sin otra relación entre sí, en una ventana corta, es sospechoso.
- **En la conversación:** cuando un cliente dice "no reconozco este cargo" en un comercio que ya
  es punto de compromiso, el agente **ya tiene evidencia**: puede priorizar el bloqueo y la
  reexpedición y escalar con contexto. Cuando el comercio es legítimo y el cliente tiene historial
  de compras ahí, es señal de **"no la recuerda"** o de **fraude de primera parte** (investigación 6).
- **Medible con el dataset:** `transactions.merchant_name`, `is_fraud`, `complaints`.

### B. Mulas y anillos en transferencias

Cuentas receptoras que reciben de muchas víctimas y reenvían rápido. Es lo que MED 2.0 de Pix
rastrea a través de **cadenas de cuentas** (investigación 6) y lo que FraudBench encontró más
difícil para los agentes (1 o 2 de 9). Si el dataset tiene transferencias entre clientes, el grafo
de transferencias es el lugar natural; si no, se documenta como limitación.

### C. Contexto del cliente para el agente (el "cliente 360")

La consulta que el agente necesita no es texto libre, es **navegación de relaciones**: "los
productos de este cliente, sus últimas transacciones en este comercio, sus reclamos abiertos, sus
disputas previas, con qué agente habló la última vez". Tres maneras de dársela:

| Enfoque | Cómo | Riesgo |
|---|---|---|
| **Text2Cypher** | el LLM escribe la consulta al grafo | exactitud imperfecta aun con agentes que corrigen ([guía de Neo4j](https://neo4j.com/blog/genai/text2cypher-guide/)); y **es un vector de inyección y de acceso a datos de otros clientes** |
| **Consultas parametrizadas como herramientas tipadas** | el equipo escribe las consultas; el modelo solo elige cuál y con qué parámetros | seguro y verificable |
| **Subgrafo precargado** | al autenticar, se trae el vecindario del cliente | simple, sin consultas del modelo |

**Recomendación:** la segunda o la tercera. El texto a consulta libre sobre una base con datos de
**todos** los clientes contradice lo aprendido en las investigaciones 2, 3 y 8. Las herramientas
reciben la `SesionAutenticada` y **solo pueden recorrer el vecindario de ese cliente**. Hay trabajo
reciente sobre generar consultas a grafos con privacidad ([*Ask Safely*](https://arxiv.org/pdf/2512.04852)),
que confirma que el problema existe.

## 4. GraphRAG: cuándo sí

**GraphRAG** (Microsoft) construye un grafo de entidades a partir de documentos con un LLM,
detecta comunidades y las resume; variantes más baratas: **LightRAG**, **HippoRAG 2**.

**La evidencia de 2025 y 2026 es consistente:**

| Tipo de pregunta | Ganador | Números |
|---|---|---|
| **Un salto, dato puntual** | **RAG vectorial** o empate | F1 64,8 frente a 63,0 (RAG gana); 60,9 frente a 60,1 (empate) |
| **Varios saltos** | **GraphRAG** | 70,3 frente a 67,0; 53,4 frente a 42,9 |
| Resumen contextual amplio | GraphRAG | +13 puntos |
| Recall@5 | GraphRAG | 73,4% a 87,8% |

([RAG vs. GraphRAG, arXiv 2502.11371](https://arxiv.org/html/2502.11371v3),
[*When to use Graphs in RAG*](https://arxiv.org/pdf/2506.05690),
[GraphRAG-Bench, ICLR 2026](https://arxiv.org/pdf/2506.02404),
[*Do We Still Need GraphRAG?*](https://arxiv.org/pdf/2604.09666),
[VentureBeat](https://venturebeat.com/orchestration/stop-graphing-everything-when-graphrag-actually-beats-vector-rag))

**Costos:** construir el grafo con un LLM cuesta, e indexar con GraphRAG o LightRAG es lento
(LightRAG más de 700 s en un corpus mediano; HippoRAG 2 mucho más eficiente). Además, **muchas
victorias reportadas usan jueces LLM** con sesgos de posición y longitud (investigación 4).
Consenso: **enrutar cada pregunta al método adecuado** o fusionar ambos.

**Encaje en el reto:** el corpus de políticas va a ser **pequeño** (plazos por país, requisitos por
motivo, reglas de confirmación). Para eso **un GraphRAG completo es sobreingeniería**. Lo que sí
encaja es un **grafo de conocimiento curado a mano**, una ontología pequeña:

```
Motivo de disputa ──requiere──► Evidencia
      │                            
      ├──categoría VCR──► 10.x / 12.x / 13.x
      │
País ──plazo──► (motivo, días, tipo de día) ──fuente──► Norma (Ley 1328, LTOSF, ...)
```

Se consulta con herramientas tipadas, no con texto libre, y cada respuesta trae su **fuente
normativa**. Es "GraphRAG" en el sentido útil: **respuestas de política con varios saltos**
(motivo → categoría → plazo en el país del cliente → norma) **con procedencia**, sin el costo ni la
opacidad de construir el grafo con un LLM.

## 5. Tecnología

| Necesidad | Opciones |
|---|---|
| Grafo en proceso para análisis y características | **NetworkX** (pequeño), **igraph** o **rustworkx** (rápido), consultas de grafo sobre **DuckDB** con SQL recursivo o la extensión **DuckPGQ** |
| Base de grafos | **Neo4j** (Cypher), **Kùzu** (embebido, como DuckDB para grafos), **Spanner Graph** o BigQuery en Google Cloud |
| GNN | **PyTorch Geometric**, DGL |
| Lenguaje estándar | **GQL**, norma ISO/IEC 39075 de 2024, que adoptan Neo4j y Spanner Graph |

Para una hackatón, **DuckDB para todo lo tabular y un grafo embebido (Kùzu o NetworkX) para las
características y el contexto** es reproducible sin servidores.

## 6. Qué se lleva el diseño

1. **Punto común de compromiso** como señal de grafo en el flujo de disputas: explica, prioriza y
   da evidencia al traspaso. Es el uso más fuerte y el más demostrable con el dataset.
2. **Características de grafo en un modelo tabular** como línea base; una GNN solo si le gana.
3. **Contexto del cliente con consultas de grafo tipadas**, limitadas a la sesión; **nunca** texto a
   consulta libre.
4. **Ontología pequeña de políticas** con procedencia en vez de GraphRAG sobre un corpus que no
   existe.
5. **Mulas** como caso de escalamiento documentado, si los datos lo permiten.

## Fuentes principales

- [FinFraudBench](https://arxiv.org/pdf/2608.15177)
- [GNN para fraude financiero, revisión](https://arxiv.org/pdf/2411.05815)
- [KumoRFM-2](https://arxiv.org/html/2604.12596v1)
- [RAG vs. GraphRAG](https://arxiv.org/html/2502.11371v3), [GraphRAG-Bench](https://arxiv.org/pdf/2506.02404), [Do We Still Need GraphRAG?](https://arxiv.org/pdf/2604.09666)
- [Text2Cypher, Neo4j](https://neo4j.com/blog/genai/text2cypher-guide/) y [Ask Safely](https://arxiv.org/pdf/2512.04852)
