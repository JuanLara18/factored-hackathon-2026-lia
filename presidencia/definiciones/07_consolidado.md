# Consolidado de solicitudes, decisiones propuestas y reglas

Generado automáticamente desde `Definiciones/01` a `06` para la ronda de revisión. No se edita a mano.

## Reglas por cara

| Cara | Reglas distintas citadas |
|---|---|
| Clientes | 124 |
| IA | 96 |
| Datos | 62 |
| Tecnología | 137 |
| Gobierno | 93 |
| Auditoría | 56 |

## Matriz de solicitudes (quién pide a quién)

| De \ Para | Clientes | IA | Datos | Tecnología | Gobierno | Auditoría | Presidencia |
|---|---|---|---|---|---|---|---|
| Clientes |  | 3 | 2 | 3 | 4 | 1 | 1 |
| IA | 2 |  | 2 | 1 | 4 |  | 1 |
| Datos | 2 | 2 |  | 3 | 2 | 1 | 2 |
| Tecnología | 3 | 3 | 2 |  | 4 | 1 | 1 |
| Gobierno | 3 | 6 | 4 | 10 |  | 1 | 1 |
| Auditoría | 1 | 2 | 3 | 4 | 3 |  | 2 |
| Presidencia |  |  |  |  |  |  |  |

## Solicitudes (90)

| ID | De | Para | Qué | Para cuándo |
|---|---|---|---|---|
| S-CLI-01 | Clientes | VP Gobierno (Cumplimiento y privacidad) | en policy/v1, los datos de los que dependen los textos al cliente: plazos por país con número, unidad | D2 |
| S-CLI-02 | Clientes | VP Gobierno (Protección al consumidor) | aprobación del aviso de IA, del aviso de voz, de las frases prohibidas y obligatorias (2.3.6), de la | D3 |
| S-CLI-03 | Clientes | VP Gobierno (Riesgo y riesgo de modelo) | registrar en el acta previa al retenido los acuerdos de servicio de 2.6.3 y los supuestos de costo | D2 |
| S-CLI-04 | Clientes | VP Gobierno (Seguridad y equipo rojo) | casos adversariales del canal en texto y voz: suplantación del banco ("me llamaron del banco"), | D2 (escritos) y D7 (equipo roj... |
| S-CLI-05 | Clientes | VP Inteligencia Artificial (Voz) | en S1, voces por locale (es-MX, es-CO, es-AR, pt-BR) con prueba de pronunciación de montos, fechas, | D0 (medición) y D4 (presíntesi... |
| S-CLI-06 | Clientes | VP Inteligencia Artificial (Comprensión... | que la redacción reciba registro, país de la cuenta e idioma como parámetros y nunca el acento; que la | D3 |
| S-CLI-07 | Clientes | VP Inteligencia Artificial (Evaluación y... | personas del simulador con país, registro, idioma, paciencia y tendencia a pedir persona; persona en | D5 |
| S-CLI-08 | Clientes | VP Tecnología (Canales) | textos de los componentes con sus límites; botón permanente "Hablar con persona"; línea fija de | D4 |
| S-CLI-09 | Clientes | VP Tecnología (Plataforma del agente) | eventos experto_asignado y experto_unido; modo asistente (la IA no escribe al cliente); campo | D5 |
| S-CLI-10 | Clientes | VP Tecnología (Canales, voz) | temporizadores de silencio y de no entendido configurables; interrupción permitida salvo la primera | D5 |
| S-CLI-11 | Clientes | VP Datos | incorporar al catálogo oficial las métricas propuestas MP-CLI-1 a MP-CLI-10 (sección 6.2), con | D3 |
| S-CLI-12 | Clientes | VP Datos | capacidad_humana_franja con los supuestos de 2.6.7; distribución de duración y espera por categoría | D2 |
| S-CLI-13 | Clientes | Auditoría | aceptar el texto de consentimiento de la semilla humana de voz (2.8.2) y las reglas de la demo | D2 (consentimiento) y D7 (demo... |
| S-CLI-14 | Clientes | Presidencia | decidir DP-CLI-01 a DP-CLI-13; aprobar la compra opcional de una revisión nativa de portugués | D1 |
| S-IA-01 | IA | VP Gobierno (Riesgo y riesgo de modelo) | aprobar la taxonomía de 2.4.2 y la guía de anotación como parte de policy/v1; riesgos objetivo r* | D2 |
| S-IA-02 | IA | VP Gobierno (Riesgo y riesgo de modelo) | que el generador del retenido (R-GOB-54) no sea de la familia Google ni Anthropic, y que el | D2 |
| S-IA-03 | IA | VP Gobierno | decidir k en la parte de voz (propuesta k = 2 por costo) y aceptar la redacción y comprensión | D2 |
| S-IA-04 | IA | VP Gobierno (Seguridad) | configuración de Model Armor de 2.9.5 (inspeccionar en entrada, bloquear en salida) y umbral de | D5 |
| S-IA-05 | IA | VP Gobierno y VP Datos | partición por cliente y por tiempo de los casos de punta a punta: clientes del retenido disjuntos de | D2 |
| S-IA-06 | IA | VP Clientes (Diseño conversacional) | textos finales de las preguntas de desempate, léxico por país (2.5.3), revisión de los léxicos del | D2 (semilla) y D3 (textos) |
| S-IA-07 | IA | VP Clientes (Operaciones de fraude y dis... | que la vista del experto registre la corrección del motivo como etiqueta con procedencia | D5 |
| S-IA-08 | IA | VP Tecnología | gateway con clave virtual por trabajador generada del registro; escaneo canario de valores en los | D3 |
| S-IA-09 | IA | VP Datos | materializador local de casos desde llaves para el arnés; esquema de platino para resultados de | D3 |
| S-IA-10 | IA | Presidencia (Oficina de Entrega) | sumar a las preguntas a los organizadores: uso de corpus públicos de voz con acento (Common Voice, | D0 |
| S-DAT-01 | Datos | Presidencia (Oficina de Entrega) | sumar dos preguntas a las de los organizadores: (11) ¿podemos copiar el dataset a un proyecto | D0 |
| S-DAT-02 | Datos | VP Tecnología | proyecto de Google Cloud con facturación, presupuesto de US$50 con alertas, exportación de | D2 (ADR) y D3 (proyecto) |
| S-DAT-03 | Datos | VP Tecnología | contrato de lectura de oro operacional: columnas que usa cada herramienta; apertura de la | D2 |
| S-DAT-04 | Datos | VP Tecnología | exportación de trazas y costos a platino (EventoTraza con corrida de evaluación, caso, turno, | D3 |
| S-DAT-05 | Datos | VP Gobierno | aprobación de la clasificación y la taxonomía de policy tags (4.1), del uso de atributos | D2 |
| S-DAT-06 | Datos | VP Gobierno | parámetros de política como datos versionados que lee el pipeline: ventana_dias (al menos el | D2 |
| S-DAT-07 | Datos | VP Inteligencia Artificial | alta en el inventario de cada conjunto del equipo (semilla humana, conversaciones generadas | desde D2, en cada alta |
| S-DAT-08 | Datos | VP Inteligencia Artificial | confirmar las necesidades de oro de aprendizaje (features_transaccion y particiones_congeladas | D2 |
| S-DAT-09 | Datos | VP Clientes | validar el directorio de comercios del equipo (razón social, descriptor de 5 a 22 caracteres, | D3 |
| S-DAT-10 | Datos | VP Clientes | supuestos de turnos (horario de cada turno de agentes) y de costo por canal y por minuto | D1 |
| S-DAT-11 | Datos | Auditoría | aceptar como evidencia el trío métrica@versión, corrida_id y huella, el manifiesto encadenado y | D2 |
| S-DAT-12 | Datos | Presidencia | aprobar un tope de gasto de US$50 en Google Cloud para la hackatón, con la opinión de | D0 |
| S-TEC-01 | Tecnología | VP Gobierno (Cumplimiento) | policy/v1 en YAML que valide contra el JSON Schema que entrega Tecnología (acciones, acr por acción, | D2 |
| S-TEC-02 | Tecnología | VP Gobierno (Seguridad y equipo rojo) | matriz de fallas abiertas o cerradas por filtro y nivel de degradación (2.12); umbral de recuperación | D3 |
| S-TEC-03 | Tecnología | VP Gobierno (Cumplimiento y privacidad) | retención por clase de dato (R-TEC-117), ventana de retoma (R-TEC-54), presupuesto por conversación | D2 |
| S-TEC-04 | Tecnología | VP Datos | contrato ODCS y exportación en Parquet del oro operacional (transacciones recientes, estado de | D3 |
| S-TEC-05 | Tecnología | VP Datos y VP Clientes | directorio de comercios del equipo (razón social, descriptor, marca) y contrato de la ficha | D3 |
| S-TEC-06 | Tecnología | VP Datos | esquema de trazas_resumen y de costos en platino, y definición oficial de latencia y costo por caso | D3 |
| S-TEC-07 | Tecnología | VP Inteligencia Artificial | esquema de salida de Interpretacion; modelo con versión por alias; presupuesto de tokens por | D2 |
| S-TEC-08 | Tecnología | VP Inteligencia Artificial (Voz) | resultado de S1: proveedores de reconocimiento y síntesis con error por acento, tiempo al resultado | D0 (F0) |
| S-TEC-09 | Tecnología | VP Clientes (Diseño conversacional) | guiones por estado en ES y PT como plantillas con variables tipadas; catálogo de rellenos; catálogo de | D3 para chat y D4 para voz |
| S-TEC-10 | Tecnología | VP Clientes (Operaciones de fraude y dis... | modelo de colas (idioma, turno, especialidad, capacidad por hora desde el dataset, espera declarada) | D3 |
| S-TEC-11 | Tecnología | Presidencia | aprobar el gasto (cuenta de facturación con medio de pago, techo de DP-TEC-12, opcionales de 7.2) y | D0 |
| S-TEC-12 | Tecnología | Auditoría | criterio de la prueba en máquina limpia (sistemas, tiempo máximo, evidencia) y formato de | D7 |
| S-TEC-13 | Tecnología | VP Gobierno (Riesgo y riesgo de modelo) | protocolo de la corrida del retenido contra el digest congelado (quién la corre, dónde y qué se registra) | D8 |
| S-TEC-14 | Tecnología | VP Inteligencia Artificial (Evaluación y... | perfiles de carga derivados del conjunto de desarrollo (mezcla de rutas, turnos, pausas) y distribución | D5 |
| S-GOB-01 | Gobierno | Tecnología | punto de decisión que carga policy/v1 con validación de esquema y huella, y registra en cada | D3 |
| S-GOB-02 | Gobierno | Tecnología | ContextoDecision sin atributos protegidos, acento ni segmento, más la prueba metamórfica I-10 | D3 |
| S-GOB-03 | Gobierno | Tecnología | modos de operación por canal (normal, solo_informacion, solo_humano, apagado), conmutables sin | D5 |
| S-GOB-04 | Gobierno | Tecnología | identidad con acr0, acr1 y acr2; OTP de un solo uso ligado a sesión y clase de acción, capturado | D3 |
| S-GOB-05 | Gobierno | Tecnología | gateway con Model Armor o sustituto en la entrada, en los campos de texto de herramientas y en la | D5 |
| S-GOB-06 | Gobierno | Tecnología | cadena de CI de la sección 4.5, rama protegida, CODEOWNERS de Gobierno (policy/, prompts, | D1 |
| S-GOB-07 | Gobierno | Tecnología | redacción de datos sensibles antes de persistir las trazas y huella encadenada en las trazas de | D4 |
| S-GOB-08 | Gobierno | Tecnología | lectura de eval/cases/holdout/ denegada en los permisos de las sesiones de primera línea | D2 |
| S-GOB-09 | Gobierno | Tecnología | vista del experto con escape de todo texto, política de contenido estricta, control de acceso por | D5 |
| S-GOB-10 | Gobierno | Tecnología | línea base de Google Cloud de la sección 4.2 (si se usa la nube), con presupuestos y alertas | D1 |
| S-GOB-11 | Gobierno | IA | agentes/registro.yaml con los campos de R-GOB-04, nivel GAICF y versiones fijadas; el gateway | D3 |
| S-GOB-12 | Gobierno | IA | solicitud de cambio con clase de materialidad para todo cambio posterior al congelamiento de F2 | continuo desde D2 |
| S-GOB-13 | Gobierno | IA | modo de corrida oficial en el arnés: lee el retenido solo por el ejecutor de Gobierno, corre k = 3, | D6 |
| S-GOB-14 | Gobierno | IA | juez con rúbrica versionada, de familia distinta del sistema y del generador, y muestra de | D6 |
| S-GOB-15 | Gobierno | IA y Tecnología | evaluación de proveedores de modelos y voz con el cuestionario de la sección 4.10 durante el | D0 y D1 |
| S-GOB-16 | Gobierno | IA | curva de riesgo y cobertura de la comprensión en desarrollo para los tres puntos de operación, y | D6 |
| S-GOB-17 | Gobierno | Datos | clase (C1 a C4) y origen en cada contrato ODCS; columnas protegidas marcadas "solo auditoría" y | D2 |
| S-GOB-18 | Gobierno | Datos | tabla de equidad en platino (resultados por caso unidos a los segmentos autorizados) con tamaño | D8 |
| S-GOB-19 | Gobierno | Datos | percentiles de monto por país y distribución de fraud_score en transacciones legítimas, sobre la | D2 |
| S-GOB-20 | Gobierno | Datos | inventario de insumos con clase y origen y, para cada audio, referencia al consentimiento y | D5 |
| S-GOB-21 | Gobierno | Clientes | plantillas en ES y PT por regla de policy/v1 (con el identificador de la regla), avisos de IA y de | D3 |
| S-GOB-22 | Gobierno | Clientes | capacidad de la cola humana por idioma, turno y especialidad, para el mensaje de espera y PB-7 | D3 |
| S-GOB-23 | Gobierno | Clientes y Tecnología | paquete de traspaso con hechos, interpretaciones y conflictos separados, regla aplicada y plazos | D4 |
| S-GOB-24 | Gobierno | Presidencia | sumar a las preguntas para los organizadores: (a) si pueden salir marcadores y texto del equipo | D0 |
| S-GOB-25 | Gobierno | Auditoría | verificación de consentimientos y actas de borrado, y verificación primaria de las normas que | D9 |
| S-AUD-01 | Auditoría | VP Tecnología | esquema de EventoTraza y de spans con los campos mínimos de 2.3.1 y 2.3.2 (o su tabla de | D2 el esquema; D8 la exportaci... |
| S-AUD-02 | Auditoría | VP Tecnología | ensayo de máquina limpia con la versión del día, en Linux y Windows 11 | D5 |
| S-AUD-03 | Auditoría | VP Tecnología | digests de imágenes y SBOM de la versión candidata, etiqueta firmada, y confirmación de que | D8 |
| S-AUD-04 | Auditoría | VP Datos | completar metricas_reporte con conjunto, alcance, numerador, denominador, intervalo y método, e | D3 el catálogo; D8 los valores |
| S-AUD-05 | Auditoría | VP Datos | reconfirmación sobre el total de las cifras de la muestra (investigación 13; 05, sección 3) con | D1 (spike S5 y DAT-2) |
| S-AUD-06 | Auditoría | VP Datos | inventario de insumos completo con la clase de cada tabla, caso, audio, directorio de comercios | D7 borrador; D9 final |
| S-AUD-07 | Auditoría | VP Gobierno (Riesgo y riesgo de modelo) | huellas del retenido de texto (representativo y estrés) en el acta de F2 y en la etiqueta | D2 |
| S-AUD-08 | Auditoría | VP Gobierno (Cumplimiento y privacidad) | lista de normas de policy/v1 con su nivel de verificación (primaria, secundaria, a confirmar) | D1 |
| S-AUD-09 | Auditoría | VP Gobierno | actas de F2, F4, F5 y F6 con desafíos, decisiones y lista de cambios posteriores a F2; informe | el día de cada compuerta |
| S-AUD-10 | Auditoría | VP Inteligencia Artificial | reporte del componente (justificación de representaciones, métricas, umbrales y particiones; | D6 el componente; D9 las hojas... |
| S-AUD-11 | Auditoría | VP Inteligencia Artificial | rúbrica versionada del juez, muestra etiquetada por humanos o por reglas con κ y precisión para | D8 |
| S-AUD-12 | Auditoría | VP Clientes | guion de la demo con los tres casos obligatorios en español y portugués por canal, un ataque | D8 el guion; D9 la grabación |
| S-AUD-13 | Auditoría | Presidencia y Oficina de Entrega | borrador completo del reporte generado desde platino 24 horas antes de la entrega; bitácora | D0 las preguntas; D9 el borrad... |
| S-AUD-14 | Auditoría | Presidencia | decidir si hay un modelo de otra familia disponible por el gateway para la segunda opinión de | D0 |
| S-AUD-15 | Auditoría | VP Gobierno (con VP Tecnología) | una sola tabla de retención: R-TEC-117 propone 30 días para trazas y logs y Gobierno propone | D2 |

## Decisiones propuestas (82)

| ID | Resumen |
|---|---|
| DP-CLI-01 | El registro sale del país de la cuenta verificada; antes de autenticar, usted neutro o você |
| DP-CLI-02 | Pedir persona inicia el traspaso en el turno siguiente; una contención pendiente se ofrece una sola vez y después de encolar |
| DP-CLI-03 | Sin especialista del idioma, contención verificada primero y oferta de idioma alterno (español ya o portugués al abrir el turno), a elección del cliente |
| DP-CLI-04 | Sin llamadas salientes: la devolución de contacto es un aviso para que el cliente vuelva por un canal oficial |
| DP-CLI-05 | El experto entra al mismo hilo y la IA pasa a modo asistente: no escribe al cliente y sus borradores solo salen si el experto los envía |
| DP-CLI-06 | El segmento no cambia prioridad ni acuerdo y no se muestra en la vista del experto |
| DP-CLI-07 | Tres escenarios nuevos antes de congelar el retenido: **E8** cola saturada (espera P1 mayor que 5 minutos); **D10** ventana de 24 horas vencida con cambio de estado del caso; **L7** cliente en portugués que acepta españo... |
| DP-CLI-08 | La espera se declara en rangos calibrados, nunca como promesa, con su métrica de calibración |
| DP-CLI-09 | Las métricas MP-CLI-1 a MP-CLI-10 entran al catálogo oficial o se mapean a una M existente |
| DP-CLI-10 | Espejo del tuteo en México solo por chat: si el cliente tutea, el sistema tutea; por defecto, usted |
| DP-CLI-11 | Plantillas fuera de ventana sin montos, nombres, tarjetas ni enlaces |
| DP-CLI-12 | Costo del minuto humano con cifras de Latinoamérica (bajo, central, alto) registradas en acta antes del retenido; la cifra de EE. UU. de US$7 a 14 por contacto solo como sensibilidad (discrepa de [04](04_VP_Tecnologia.md... |
| DP-CLI-13 | La proyección de producción incluye el costo por mensaje de WhatsApp desde el 1 de octubre de 2026 (discrepa de [04](04_VP_Tecnologia.md), sección 7.4, "sin costo de mensajes") |
| DP-IA-01 | Cuatro familias: Google para el sistema, Anthropic para el generador, una tercera abierta para el simulador, una cuarta abierta para juez y verificador |
| DP-IA-02 | Redacción deslexicalizada con renderizador por locale; comprensión sobre texto con marcadores; ningún valor del dataset a modelos externos |
| DP-IA-03 | Comprensión en cascada: clasificador local primero, LLM solo como comparado y respaldo si gana; aclaración dirigida por par de motivos |
| DP-IA-04 | Etiqueta = motivo declarado por turno, con seis motivos, urgencia con señales, actos, temas fuera de alcance y frustración |
| DP-IA-05 | Generación por guion con marcadores y verbalizador local; valores sintéticos; semilla partida en ancla y prueba humana |
| DP-IA-06 | Umbrales por riesgo selectivo garantizado con tres r* |
| DP-IA-07 | Live API de Gemini como frontend nativo; gpt-realtime solo si S2 falla |
| DP-IA-08 | Proveedores de voz elegidos por el error crítico en el peor acento |
| DP-IA-09 | Detección de turno dependiente del estado |
| DP-IA-10 | k = 2 en la parte de voz del retenido |
| DP-DAT-01 | **Un código, dos perfiles:** local (DuckDB, Parquet, dbt con DuckDB, Data Contract CLI) como referencia y origen de toda cifra oficial; Google Cloud (Cloud Storage, BigQuery, dbt con BigQuery, Knowledge Catalog, policy t... |
| DP-DAT-02 | dbt Core en ambos perfiles; Dataform descartado porque rompe la paridad |
| DP-DAT-03 | **Linaje por columna obligatorio** con sqlglot y prueba de cero caminos de PII a oro operacional y platino; en nube, linaje de Knowledge Catalog exportado a platino (retención de 30 días) y comparado; OpenLineage y Metri... |
| DP-DAT-04 | Tokenización HMAC-SHA-256 portable con la llave en la zona `seguridad` y vectores del RFC 4231; Sensitive Data Protection como control detectivo, no como tokenizador |
| DP-DAT-05 | Fuente autorizada `data/`; el respaldo solo como generación aparte para auditoría y prueba de regeneración, hasta que los organizadores digan otra cosa |
| DP-DAT-06 | Oro operacional como instantánea publicada de solo lectura con huella; nunca BigQuery en la ruta de una herramienta; como alternativa, carga en un esquema `referencia` de Postgres |
| DP-DAT-07 | La llave de AWS del organizador vive solo en la máquina de ingesta; Storage Transfer Service no se usa en la hackatón y en producción va con identidad federada |
| DP-DAT-08 | Ventana de corrección de 3 días medida contra `AS_OF`, con modo inicial y reproceso manual registrado |
| DP-DAT-09 | Ganador determinista por `last_updated`, `last_modified` del objeto y huella de fila, **sin** `_ingerido_en` |
| DP-DAT-10 | Metadatos mínimos por fila y completos por lote |
| DP-DAT-11 | Umbrales de regeneración (50% de llaves en común) y de sistematicidad (0,5% del lote), revisables tras la auditoría del total |
| DP-DAT-12 | Atributos protegidos solo en `plata_restringida` para auditar equidad; segmentos autorizados: idioma, variante, segmento, canal y país |
| DP-DAT-13 | Región `us-central1` y tope de US$50 para el perfil de nube en la hackatón |
| DP-DAT-14 | Borrado al cierre con destrucción de la llave de tokenización, acta y verificación en nube después de sus ventanas de recuperación |
| DP-TEC-01 | Google Cloud como plataforma de referencia, con entorno `demo` en `us-central1`; el entorno local es la vía reproducible oficial; la región de producción la fija la residencia de datos |
| DP-TEC-02 | LiteLLM como gateway en todos los entornos, con Presidio siempre y Model Armor en la nube; Apigee como ruta a producción con mapeo política por política; evaluación gratuita de Apigee solo como *spike* opcional S7; contr... |
| DP-TEC-03 | Observabilidad dual en la nube: Phoenix más Cloud Trace, Logging y Monitoring |
| DP-TEC-04 | Identidad propia para clientes con llave de firma en Cloud KMS; IAP para superficies internas; Identity Platform descartado para clientes |
| DP-TEC-05 | Transporte de voz: WebRTC entre pares en local; WebSocket del navegador a Cloud Run en la nube; WebRTC gestionado solo si S1 lo exige; telefonía opcional con Twilio y número de EE. UU. para la demo |
| DP-TEC-06 | Pruebas de persistencia contra Postgres real en contenedor; SQLite solo en pruebas unitarias sin SQL |
| DP-TEC-07 | Oro operacional en la nube como Parquet versionado en Cloud Storage, montado en solo lectura en `lb-bian`, solo con autorización registrada; sin ella, datos generados por el equipo |
| DP-TEC-08 | Terraform para la infraestructura y GitHub Actions con WIF para CI/CD; Cloud Build no se usa |
| DP-TEC-09 | Monolito modular con seis servicios y tres trabajos (sección 2.1); el núcleo es una biblioteca |
| DP-TEC-10 | Autorización también en la capa de servicio (JWT con `acr` y dueño), además de tipos y PDP |
| DP-TEC-11 | Frontend React, TypeScript y Vite con `@ag-ui/client`; componentes como herramientas de interfaz; confirmación por `nonce` |
| DP-TEC-12 | Techo de gasto total de US$600 para la hackatón (antes de créditos), con alertas al 50, 80 y 100%; opcionales solo con aprobación |
| DP-TEC-13 | Enfriamiento de 7 días para dependencias y controles de cadena de suministro de R-TEC-133 |
| DP-TEC-14 | Capacidad con Locust y generador propio de voz, en modos plataforma y real, con reporte de punto de quiebre |
| DP-GOB-01 | Plazos de México. Dictamen en 45 días naturales; 180 días naturales en el extranjero; 90 |
| DP-GOB-02 | Argentina, regla compuesta por producto. Tarjeta de crédito: BCRA más Ley 25.065, con el |
| DP-GOB-03 | Colombia, reversión del pago. 15 días hábiles de respuesta, canal del Defensor y la |
| DP-GOB-04 | Nunca "fuera de plazo" automático. El escenario F5 termina siempre en R5. *Alternativa:* |
| DP-GOB-05 | Regla de cómputo protectora de días y horas (R-GOB-14, R-GOB-15). *Alternativa:* |
| DP-GOB-06 | Corrección del mapeo OWASP de [01](../Diseno/01_Interacciones_y_criterios.md): ASI03 |
| DP-GOB-07 | Reserva sellada del retenido y suite adversarial separada; los hallazgos del equipo rojo |
| DP-GOB-08 | Marcadores en la frontera de todo modelo externo, con entidades numéricas extraídas por un |
| DP-GOB-09 | `fraud_score` solo suma protección; zona gris desde un percentil de las legítimas en |
| DP-GOB-10 | Niveles `acr` por acción: bloquear con acr1 y confirmación; radicar con acr2; OTP fuera |
| DP-GOB-11 | Lista cerrada U1 a U13, con el traspaso urgente faltante y el derecho negado incluidos. |
| DP-GOB-12 | Umbrales de disparidad: 5 puntos con intervalo de Newcombe, razón de 0,8, 30 casos por |
| DP-GOB-13 | Clases de materialidad A, B, C y E para el control de cambios. *Por qué:* velocidad sin |
| DP-GOB-14 | La detección del filtro restringe el turno, no bloquea al cliente; configuraciones |
| DP-GOB-15 | Segmento y acento fuera de toda decisión, incluida la prioridad de cola; el idioma solo |
| DP-GOB-16 | Prohibidos los niveles gratuitos de proveedores que entrenen o revisen con nuestros |
| DP-GOB-17 | Toda transferencia inmediata no reconocida es R4. *Alternativa:* un umbral de |
| DP-GOB-18 | Segundo anotador frío para el retenido; el κ humano solo en desarrollo. *Alternativa:* |
| DP-GOB-19 | Estado civil y educación no se usan ni para auditar, salvo acta. *Por qué:* |
| DP-AUD-01 | El dictamen opina sobre veracidad y reproducibilidad, no sobre la calidad del sistema; tres salidas (aprobado, con salvedades, devuelto) con la lista cerrada de bloqueantes de 2.8 |
| DP-AUD-02 | Cadena de custodia con SHA-256 sobre JSON canónico, cadenas por conversación, raíz por corrida y sello externo con etiqueta de git firmada y empujada; sin cadena de bloques |
| DP-AUD-03 | Ninguna cifra a mano: toda cifra del reporte sale de `metricas_reporte` con el trío de Datos, y un script lo verifica |
| DP-AUD-04 | El razonamiento visible se permite, se guarda aparte y etiquetado, y nunca alimenta decisiones, explicaciones, traspasos ni cifras |
| DP-AUD-05 | Reproducibilidad en dos niveles: recálculo exacto y reejecución de una submuestra con tolerancias fijadas antes |
| DP-AUD-06 | Auditoría hace verificaciones en F2, F4, F5 y F6, no solo en F7 |
| DP-AUD-07 | La verificación de una fuente exige el pasaje textual; el resumen de un modelo no es verificación |
| DP-AUD-08 | Retenido cifrado en reposo o fuera del árbol de trabajo de la primera línea (propuesta a Gobierno, dueño del retenido) |
| DP-AUD-09 | Matriz como código en `audit/matriz.yaml`, validada en `just audit`, con ids `M-nn` de Datos y provisionales `Q-AUD-nn` |
| DP-AUD-10 | Segunda revisión fría de todo hallazgo bloqueante y opinión de otra familia de modelos si el gateway la ofrece |
| DP-AUD-11 | La verificación de las normas de `policy/v1` se adelanta a D2, antes del comité de F2 |
| DP-AUD-12 | La matriz de 6.3 reemplaza la tabla de trazabilidad de 01, sección 8 |
