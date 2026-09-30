# Investigación de contexto (26 de septiembre de 2026)

Veintiuna investigaciones: once de contexto con búsqueda en la web, una sobre la organización del
banco, una auditoría empírica del dataset, seis especializadas (una por cada cara de LATAM Bank) y dos
sobre los canales y la organización agéntica. Cada investigación conserva lo que se sabía cuando se escribió;
si algo posterior la corrige, lleva una **nota fechada** al inicio en vez de reescribirse.

## Primera ronda: el problema desde la IA

| # | Documento | Pregunta | Lo que más pesa para decidir |
|---|---|---|---|
| 1 | [Industria y casos](01_Industria_y_casos.md) | ¿quién ya lo hizo, qué midió, qué salió mal? | **las transacciones no reconocidas son la primera queja en Colombia (39,8%), México y Brasil**; Nubank publicó exactamente el método que pide el enunciado; Klarna y CBA muestran que la contención sola engaña |
| 2 | [Arquitectura y control](02_Arquitectura_y_control.md) | ¿qué decide el LLM y qué decide el código? | **el LLM entiende y redacta, el código decide y actúa**; los LLM caen 39% en varios turnos y los *frameworks* no autorizan por llamada |
| 3 | [Seguridad, privacidad y regulación](03_Seguridad_privacidad_regulacion.md) | ¿qué amenazas y qué exige la norma? | la inyección se contiene **por diseño** (CaMeL, seis patrones); plazos de disputa por país como **política determinista**; equidad por variante del español |
| 4 | [Evaluación](04_Evaluacion.md) | ¿cómo se demuestra con números defendibles? | **pass^k**, jueces validados con κ, política versionada antes de etiquetar; FraudBench como plantilla de casos adversariales |
| 5 | [Datos, ML y operación](05_Datos_ML_y_operacion.md) | ¿cómo se ve el rigor de datos y ML? | **auditar el dataset sintético antes de todo**; contratos ODCS; clasificador pequeño frente a LLM; trazas OpenTelemetry |

## Segunda ronda: el banco, el dominio y la tecnología que encaja

| # | Documento | Pregunta | Lo que más pesa para decidir |
|---|---|---|---|
| 6 | [El banco por dentro](06_El_banco_por_dentro.md) | ¿qué pasa dentro del banco con una disputa y con el fraude? | "no reconozco un cargo" son **cuatro casos distintos** (fraude 10.x, error 12.x, comercial 13.x, no lo recuerda); en transferencias inmediatas **el tiempo es todo**; los cambios de datos de contacto preceden a la toma de cuenta |
| 7 | [Atención al cliente como dominio](07_Atencion_al_cliente_como_dominio.md) | ¿cómo opera y qué mide un contact center? | **40 a 60% de la demanda es por falla** del propio banco; la evidencia causal más fuerte de IA generativa es **asistir al agente** (+14%, +34% en novatos); en LATAM el canal es WhatsApp, asíncrono |
| 8 | [IA con tipos seguros](08_IA_con_tipos_seguros.md) | ¿qué es *type-safe AI* y cómo se vuelve innovador? | **autorización como tipo**: la herramienta no se puede llamar sin `SesionAutenticada`; **hecho verificado e interpretación como tipos distintos**; invariantes probados con propiedades |
| 9 | [Grafos](09_Grafos.md) | ¿dónde aportan GNN, GraphRAG y agentes sobre grafos? | los grafos ganan en preguntas **relacionales y de varios saltos**, no en las simples; **punto común de compromiso** como señal en disputas; nunca texto a consulta libre sobre datos de todos los clientes |
| 10 | [Gobernanza y gateway](10_Gobernanza_y_gateway.md) | ¿qué aporta Apigee con Model Armor? | el gateway **gobierna** (cuotas, costo, enrutamiento, redacción, auditoría) pero **no garantiza**: los detectores de inyección se evaden hasta 100%; caché semántica **solo** para contenido genérico |
| 11 | [Latencia y costo](11_Latencia_y_costo.md) | ¿de dónde viene la latencia y cuánto cuesta un caso? | el p95 se **amplifica** con cada paso; la mejor palanca es **hacer menos llamadas al LLM**; el costo que importa es **por resolución segura**, sumando el humano de los traspasos |

## Tercera ronda: la organización y los datos reales

| # | Documento | Pregunta | Lo que más pesa para decidir |
|---|---|---|---|
| 12 | [Organización de un banco](12_Organizacion_de_un_banco.md) | ¿qué caras tiene un banco regulado frente a la IA y cómo se reparten la responsabilidad? | el banco ya existe (**LATAM Bank**); las caras salen de las **funciones obligatorias por país**, las **tres líneas de defensa** y los criterios del enunciado; la evaluación es **segunda línea**; un rol sin artefacto ni veto es decorativo |
| 13 | [Auditoría del dataset](13_Auditoria_del_dataset.md) | ¿el bucket trae lo que dice el diccionario y qué tiene señal? | transacciones, productos y clientes son **coherentes**; motivos, transcripciones y quejas son **plantilla o sorteo**; en la segunda pasada, `is_fraud` **no tiene señal** fuera de `fraud_score`, que es una fuga de la etiqueta; invalida supuestos de 1, 4, 5, 7, 9 y 15 |

## Cuarta ronda: una investigación por cara de LATAM Bank

| # | Cara | Documento | Lo que más pesa para decidir |
|---|---|---|---|
| 14 | VP Clientes | [Conversación, traspaso y canal](14_VP_Clientes.md) | la mayoría de los "no reconozco" es **confusión**: la herramienta clave es la **ficha de la transacción** (nuestro Consumer Clarity sintético); traspaso como estado tipado con procedencia y **conflictos**; la ventana de 24 horas de WhatsApp es la sesión expirada real |
| 15 | VP Inteligencia Artificial | [Agentes, riesgo y datos de conversación](15_VP_Inteligencia_Artificial.md) | **registro de agentes** con hoja de vida; el puntaje de riesgo con ablación contra `fraud_score` (superado: sin señal fuera del puntaje, D-14); conversaciones del equipo con **semilla humana** y generador, sistema y juez de familias distintas |
| 16 | VP Datos | [Productos de datos, métricas y pila](16_VP_Datos.md) | dbt con DuckDB (contratos que absorben lo aditivo y fallan con lo que rompe), Data Contract CLI, OpenLineage por columna para **probar** que la PII no llega al agente; relato **BCBS 239** |
| 17 | VP Tecnología | [Marco, durabilidad, identidad, BIAN](17_VP_Tecnologia.md) | **motor propio** más PydanticAI tipado; estado persistido con idempotencia (DBOS opcional); identidad simulada con `acr` (RFC 9470) y **reloj inyectable**; **sin MCP** en el camino crítico |
| 18 | VP Gobierno | [Validación, política, amenazas, plazos](18_VP_Gobierno.md) | marco **GAICF** compatible con SR 26-2 que el diseño ya cumple; política de negocio en tabla versionada y autorización con tipos (Cedar opcional); **MAESTRO**; plazos de México **en conflicto** y dos regímenes en Argentina: la política exige texto primario |
| 19 | Auditoría | [Evidencia y fuentes](19_Auditoria.md) | se audita la **cadena de evidencia**; trazas completas, huellas encadenadas, actas; matriz con consulta por fila; primera verificación de fuentes (Nubank, FraudBench, *Capability Gates*, SR 26-2 verificadas) |

## Quinta ronda: los canales y la organización agéntica

| # | Documento | Pregunta | Lo que más pesa para decidir |
|---|---|---|---|
| 20 | [Voz y chat en estado del arte](20_Canales_voz_y_chat.md) | ¿qué es estado del arte en cada canal en 2026 y cómo se hace sin romper los principios? | en voz regulada se separa un **frontend conversacional** de un **backend que decide**; la cascada da control y auditoría y el frontend nativo avanza rápido (la voz ya conserva cerca del 79% de la capacidad de texto): se construye la cascada y se **mide** contra el nativo; chat con **AG-UI** y componentes que se degradan a WhatsApp; la voz no autentica |
| 21 | [Lo que faltaba de la organización](21_Organizacion_agentica.md) | ¿qué le falta a la organización v1? | equipos **orientados a un resultado** con personas por encima del circuito; faltaban la operación humana de fraude, la voz, la ingeniería de evaluación, la operación de agentes, el equipo rojo y la oficina que ordena la entrega |

## Lo que se desprende

1. **Flujo candidato: recepción de disputas por transacciones no reconocidas** (18% de las quejas del
   dataset), entendida como el banco la entiende: clasificar entre fraude, error, disputa comercial y "no lo recuerda";
   contener (bloquear) cuando es fraude; radicar con evidencia; escalar con urgencia las
   transferencias inmediatas. Falta confirmar la cifra sobre el total del dataset.
2. **Arquitectura:** gateway que gobierna, comprensión con modelo pequeño más LLM donde haga falta,
   motor de flujo determinista, herramientas con **autorización por tipos**, redacción solo desde
   hechos verificados, traspaso que es también **asistencia al agente humano**.
3. **Diferenciadores con respaldo:** seguridad por construcción con tipos; señal de grafo (punto
   común de compromiso) en la conversación; análisis de demanda por falla; defensa en profundidad
   **medida** (qué detecta el filtro y qué contiene la arquitectura).
4. **La evaluación es el producto:** casos retenidos, usuario simulado, adversariales, pass^k,
   métricas separadas, costo por resolución segura, equidad por variante y segmento.
5. **Primer paso técnico:** el análisis exploratorio de la sección 5 de la investigación 5
   (adelantado sobre una muestra en la investigación 13).
6. **Lo que la auditoría cambió:** el motivo se respalda con `complaints.subcategory`, no con
   `contact_reason`; los casos se anclan en transacciones y productos; el componente aprendido
   principal es el riesgo de la transacción disputada (D-09); las mulas quedan fuera por falta de
   contraparte en las transferencias.
7. **La organización:** LATAM Bank como banco nuevo con cinco vicepresidencias y Auditoría; la
   evaluación es de la segunda línea (Gobierno) ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)).
8. **Lo que dijo la cuarta ronda:** el camino más valioso es **explicar** (R1) con una ficha de la
   transacción construida desde los datos; la política por país necesita **texto primario** antes de
   F2; y el sistema ya cumple por diseño las condiciones de frontera de un marco de validación
   compatible con SR 26-2, lo que da a Gobierno un lenguaje para defenderlo.
9. **Lo que dijo la quinta ronda:** chat y voz son dos superficies del mismo motor; la voz principal va
   en cascada y se compara con un frontend nativo; la organización se ordena por la misión "cargo no
   reconocido" con una Oficina de Entrega ([06](../Diseno/06_Arquitectura.md), [07](../../presidencia/hoja_de_ruta.md)).
