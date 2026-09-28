# Registro de decisiones

Una entrada por decisión, la más reciente arriba. Formato corto: qué se decidió, alternativas,
por qué (con el principio que la guía) y estado. Una decisión **provisional** se puede cambiar sin
ceremonia; una **firme** solo con una entrada nueva que explique el cambio.

Estados: `propuesta` → `provisional` → `firme` · `reemplazada por D-xx`.

---

## D-29 · Canales reales, todo en Google Cloud y gasto menor a US$20 (28 sep 2026)

- **Decisión:** WhatsApp real con el número de prueba de Meta Cloud API (hasta 5 destinatarios
  registrados) y voz por teléfono real con la cuenta de prueba de Twilio (número de EE. UU., solo números
  verificados), además de chat y voz en el navegador; el sitio de LATAM Bank en Google Cloud (Firebase
  Hosting y Cloud Run, sin dominio propio). Pago real con tope de US$20: el crédito de prueba de Google
  Cloud (US$300) financia modelos, voz y plataforma sin activar la cuenta completa; presupuesto de
  US$250 de crédito con alertas al 50 y 80%. Sin Claude en Vertex (a confirmar si la cuenta de prueba lo
  permite): generador y juez con dos familias abiertas en Ollama local. El repositorio
  `JuanLara18/factored-hackathon-2026` (privado) es la fuente canónica desde hoy, con carpetas por cara,
  `main` como producción y `develop` como integración.
- **Modifica:** D-18, D-19, D-22 (teléfono y WhatsApp reales), D-24 (sin Anthropic), D-25 (tope real de
  US$20) y D-03 (los documentos pasan al repositorio).
- **Límite conocido:** la protección de ramas no está disponible en repositorios privados del plan
  gratuito; las reglas de `CONTRIBUTING.md` se cumplen por disciplina y CI.
- **Estado:** firme (instrucción de la presidencia humana).

## D-28 · Plataforma de dos perfiles y gateway LiteLLM (27 sep 2026)

- **Decisión:** una sola base de código con dos perfiles: el **local** (DuckDB, dbt, Data Contract CLI,
  Postgres en contenedor, Phoenix) es la referencia y el origen de toda cifra oficial; **Google Cloud**
  (us-central1: Cloud Run, Cloud SQL, BigQuery, Knowledge Catalog, policy tags, Vertex AI, KMS, Secret
  Manager, Cloud Trace) es el despliegue gobernado y solo se certifica si sus huellas coinciden con las del
  local. Gateway **LiteLLM** con Presidio siempre y Model Armor en la nube; Apigee queda en la ruta a
  producción (su entorno con políticas de IA cuesta cerca de US$1.460 al mes). Terraform y GitHub Actions
  con identidad federada; identidad propia con llave en KMS.
- **Por qué:** P13 y P9; DP-DAT-01, DP-TEC-01 a 04, 08 y 09.
- **Estado:** firme; la nube se activa cuando la presidencia humana apruebe el gasto (D-25).

## D-27 · Controles y métricas que resuelven la ronda 1 (27 sep 2026)

- **Decisión:** F5 siempre en R5 sin afirmar el vencimiento; bloquear con nivel `consulta` más
  confirmación, OTP solo para radicar; el dataset no se copia a la nube sin autorización de los
  organizadores; hacia modelos externos solo marcadores sin valores; estado civil y educación fuera incluso
  de la auditoría de equidad (género y banda de edad sí, para auditar); ningún proveedor sin ficha de
  términos; M-07 por tipo U1 a U13; retención: registros operativos 30 días, evidencia de evaluación cierre
  más 90 días.
- **Por qué:** hallazgos H-GOB-01 a 04 y choques 7, 8, 10, 11 y 12 ([10](../Definiciones/10_Resolucion_Presidencia.md)).
- **Estado:** firme.

## D-26 · Repeticiones en el retenido de voz (27 sep 2026)

- **Decisión:** k = 3 en V1, V2, V9 y los casos de seguridad; k = 2 en el resto del retenido de voz,
  declarado en el acta de F2 y en el reporte; en texto, k = 3.
- **Por qué:** consistencia donde está el riesgo, costo donde no (choque 6).
- **Estado:** firme.

## D-25 · Gasto de la hackatón (27 sep 2026)

- **Decisión:** techo único de US$600 antes de créditos, con alertas al 50, 80 y 100%; sub presupuestos de
  Datos (US$50), Gobierno (US$30) y Auditoría (US$60); IA en escenario austero salvo acta; tabla única de
  costos de Tecnología; costo humano con cifras de Latinoamérica y WhatsApp [P] en la proyección. Abrir
  facturación es gasto real y lo aprueba la presidencia humana antes de ejecutarlo.
- **Por qué:** H-AUD-03, choques 2, 3 y 9.
- **Estado:** firme en el techo; **pendiente de aprobación humana** para ejecutar el gasto.

## D-24 · Tabla única de familias de modelos (27 sep 2026)

- **Decisión:** sistema, Google (Gemini en Vertex AI); generador de desarrollo, Anthropic (Claude en Vertex
  AI); generador del retenido y simulador, familia abierta A; juez y verificador, familia abierta B. Si no
  hay dos familias abiertas usables en F0, Gobierno decide con acta qué par comparte familia; nunca el juez
  con el generador ni con el sistema. Precisa D-20.
- **Por qué:** H-AUD-04 y H-AUD-05; DP-IA-01.
- **Estado:** firme.

## D-23 · Enmienda de D-20: persistencia probada contra Postgres real (27 sep 2026)

- **Decisión:** las pruebas de persistencia corren contra Postgres real en contenedor; SQLite solo en
  unitarias sin SQL.
- **Por qué:** DP-TEC-06; H-AUD-07.
- **Estado:** firme.

## D-22 · Transporte de voz por perfil (27 sep 2026)

- **Decisión:** WebRTC en local; en la nube, WebSocket a Cloud Run solo si S1 mide la latencia de voz a voz
  dentro del presupuesto por ese transporte; la latencia se reporta por transporte. Precisa D-18.
- **Por qué:** Cloud Run no recibe UDP (DP-TEC-05); H-AUD-06.
- **Estado:** firme, condicionada a S1.

## D-21 · Extras de datos: qué entra y qué no (26 sep 2026)

- **Decisión:** métricas oficiales como definiciones YAML más vistas SQL en platino; linaje con el
  manifiesto por corrida y el grafo de dbt; MetricFlow y OpenLineage solo si sobra tiempo.
- **Alternativas:** MetricFlow y OpenLineage desde el inicio.
- **Por qué:** cumplen lo que pide el enunciado con menos dependencias (P9); investigación 16.
- **Estado:** firme.

## D-20 · Plataforma: estado, autorización, identidad, gateway y trazas (26 sep 2026)

- **Decisión:**
  - **estado durable** en Postgres (SQLite en pruebas); DuckDB solo en la ruta analítica;
  - **autorización** por tipos más un punto de decisión propio que registra cada decisión; **sin
    Cedar** en el prototipo;
  - **identidad** propia con niveles `acr`, OTP simulado, expiración y reloj inyectable, con la forma de
    RFC 9470;
  - **gateway** con LiteLLM (cuotas, costo, enrutamiento) y Presidio con reconocedores de CURP, CC y
    DNI; Model Armor solo si hay Google Cloud;
  - **proveedores de modelos** detrás del gateway, con familias distintas para generador, sistema y
    juez; modelo abierto local como plan B (D-15);
  - **trazas** OpenTelemetry con Phoenix local.
- **Alternativas:** Cedar; Keycloak o un servidor OIDC de prueba; Langfuse; Apigee.
- **Por qué:** lo mínimo que cumple el enunciado con garantías verificables y una instalación de un
  comando (P5, P9, P13); investigaciones 10, 17 y 18.
- **Estado:** firme; los proveedores concretos se fijan cuando respondan los organizadores.

## D-19 · Chat: AG-UI y componentes tipados que se degradan a WhatsApp (26 sep 2026)

- **Decisión:** la superficie de chat emite eventos AG-UI desde el motor: texto en streaming (filtrado
  por frases antes de enviarse), componentes tipados (ficha de la transacción, opciones enmascaradas,
  confirmación con el monto de la base, estado del caso, aviso de traspaso) y aprobaciones. Cada
  componente tiene su degradación a botones (máximo 3) y listas (máximo 10) de WhatsApp; la ventana de
  24 horas y las plantillas se simulan. El experto humano entra al mismo hilo con el paquete.
- **Alternativas:** chat de solo texto; WhatsApp real.
- **Por qué:** es el estado del arte de 2026 (AG-UI, interfaz generativa) y la confirmación pasa a ser un
  evento, no texto libre (P5, P6); investigación 20.
- **Estado:** firme.

## D-18 · Voz: cascada como camino principal y frontend nativo como experimento medido (26 sep 2026)

- **Decisión:**
  - **camino principal:** cascada en streaming con Pipecat (VAD y detección de turno, reconocimiento
    en streaming, el mismo motor, síntesis en streaming), interrupciones registradas, rellenos honestos
    y **plantillas deterministas** para montos, plazos y confirmaciones;
  - **experimento:** frontend nativo de audio (gpt-realtime o Gemini Live) que delega en el motor con
    una sola herramienta, medido contra la cascada en el mismo retenido de voz;
  - **proveedores** de reconocimiento y síntesis elegidos por medición en F0 (error por acento es-MX,
    es-CO, es-AR y pt-BR; tiempo hasta el primer audio), entre los líderes de 2026;
  - **seguridad de voz:** la voz no autentica (OTP para acciones); lectura de vuelta y "sí" explícito o
    DTMF para confirmar; dígitos por DTMF; el audio crudo no se guarda por defecto;
  - **evaluación de voz:** los casos de texto convertidos a voz con personas por acento, ruido con la
    distribución de calidad de audio del dataset, degradación telefónica, interrupciones guionadas y una
    semilla de grabaciones humanas con consentimiento; se reporta la retención de voz frente a texto;
  - **transporte:** navegador (WebRTC); línea telefónica real solo si sobra tiempo.
- **Alternativas:** solo nativo de audio; solo cascada; LiveKit Agents como marco.
- **Por qué:** la cascada da control y auditoría por etapa, que es la recomendación para banca; el
  frontend nativo es donde avanza el estado del arte y compararlos con datos es la evidencia más fuerte;
  la separación entre frontend de voz y backend que decide es la de nuestro motor (investigación 20).
  Pipecat se integra en proceso con un motor en Python; LiveKit queda como alternativa de producción.
- **Estado:** firme en la arquitectura; provisional en proveedores y marco hasta el *spike* de F0.

## D-17 · Dos canales, un núcleo (26 sep 2026)

- **Decisión:** LATAM Bank atiende por **chat y por voz**, ambos en estado del arte, como dos
  superficies del mismo motor: ninguna superficie decide, el estado del caso viaja entre canales y un
  caso empezado en chat se retoma por voz sin repetir preguntas ni acciones.
- **Alternativas:** solo chat (justificado con los datos); solo voz.
- **Por qué:** decisión de la presidencia; el 84,8% de los contactos del dataset es telefónico y el
  dataset está construido alrededor de la voz, mientras los canales digitales son el 15% (revisión 05).
  Un núcleo único garantiza las mismas decisiones en ambos canales (P4, P12).
- **Estado:** firme.

## D-16 · Dos conjuntos retenidos: representativo y de estrés (26 sep 2026)

- **Decisión:** el retenido se divide en una parte **representativa** (mezcla de rutas estimada de la
  demanda, con supuestos declarados) para resolución y eficiencia, y una **de estrés** (fallas,
  ataques, casos borde) para seguridad y caída segura; cada métrica declara su conjunto.
- **Alternativas:** un solo retenido con todo mezclado.
- **Por qué:** la resolución automática segura se reporta sobre todos los casos del alcance y la
  mezcla la determina; un retenido cargado de ataques la vuelve irrelevante (P2; revisión 05).
- **Estado:** firme (26 sep 2026, cierre de decisiones).

## D-15 · Los datos del organizador no salen (26 sep 2026)

- **Decisión:** ninguna fila del dataset en el repositorio ni en el reporte; los casos de evaluación
  guardan llaves y se materializan localmente; al LLM externo solo llegan hechos mínimos y
  enmascarados, y solo si los organizadores lo autorizan; plan B, un modelo abierto local para los
  trabajadores que tocan datos del cliente.
- **Alternativas:** asumir que por ser sintético se puede compartir.
- **Por qué:** el enunciado prohíbe datos restringidos en entregas públicas y en solicitudes a
  modelos externos, y el acceso al dataset está restringido a participantes (P11).
- **Estado:** **firme** para el repositorio y el reporte (ninguna fila del dataset sale); **provisional**
  para el uso de modelos externos, hasta la respuesta de los organizadores (preguntas 3 y 4 de la
  revisión 05).

## D-14 · El componente aprendido es la comprensión de la recepción (26 sep 2026)

- **Decisión:** el componente aprendido principal es el clasificador de la recepción (motivo,
  urgencia, entidades, fuera de alcance) sobre conversaciones del equipo etiquetadas desde una ruta
  conocida, contra palabras clave y TF-IDF, con calibración, curva de riesgo y cobertura, ES → PT y
  análisis de errores. `fraud_score` pasa a la política como regla determinista (> 30, riesgo alto;
  zona gris con revisión humana). El experimento de riesgo se reporta como resultado negativo.
- **Alternativas:** el puntaje de riesgo de D-09; un localizador aprendido de la transacción (casi
  trivial: mediana de 2 transacciones por cliente en dos meses).
- **Por qué:** en la muestra, `is_fraud` no tiene señal fuera de `fraud_score` (AUC 0,504 con
  partición temporal) y `fraud_score > 30` es fraude con precisión 1,0: fuga de la etiqueta. El
  enunciado admite etiquetas de intención para soluciones preentrenadas (P9, P10; revisión 05).
- **Estado:** firme (reemplaza a D-09). Confirmar la ausencia de señal sobre el total es un paso de
  verificación en F1, no una condición: si el total la contradijera, se abre una decisión nueva.

## D-13 · Política por país desde texto primario (26 sep 2026)

- **Decisión:** cada regla de `policy/v1` cita su texto primario (ley, circular o texto ordenado) y su
  fecha de consulta; si dos fuentes chocan, gana el texto primario y el choque va al acta; mientras
  no se resuelva, se usa el plazo más protector para el cliente, declarado. Argentina elige régimen
  por producto (tarjeta de crédito o general del BCRA).
- **Alternativas:** escribir la política desde las investigaciones y notas de prensa.
- **Por qué:** la investigación 18 encontró un plazo de México en conflicto y dos regímenes en
  Argentina; un plazo equivocado es un resultado materialmente incorrecto (P6, Air Canada).
- **Estado:** firme; el Comité de Confianza aprueba el contenido de `policy/v1` en F2.

## D-12 · Sin MCP en el camino crítico (26 sep 2026)

- **Decisión:** los servicios se llaman directamente desde el motor; MCP queda en la ruta a
  producción para exponer servicios a otros agentes del banco.
- **Alternativas:** exponer las herramientas por MCP desde el inicio.
- **Por qué:** los trabajadores de lenguaje no tienen herramientas (P4); MCP suma un salto de red y
  riesgos de envenenamiento de herramientas sin beneficio aquí (investigación 17, P9).
- **Estado:** firme.

## D-11 · Motor de flujo propio con PydanticAI para los trabajadores de lenguaje (26 sep 2026)

- **Decisión:** máquina de estados propia, tipada y persistida con llaves de idempotencia; PydanticAI
  solo como cliente tipado de comprensión y redacción; DBOS si hay tiempo para mostrar durabilidad.
  Alternativa de respaldo: LangGraph con la capa de herramientas tipada debajo.
- **Alternativas:** LangGraph como núcleo; Google ADK.
- **Por qué:** control total de autorización y trazas (P4, P5, P13); el despacho por defecto de los
  marcos no autoriza por llamada (investigaciones 2 y 17).
- **Estado:** firme; se documenta como ADR en el repositorio en F0 y un *spike* valida la integración
  con la voz (Pipecat) y el chat (AG-UI).

## D-10 · Organización de LATAM Bank y modo de trabajo (26 sep 2026)

- **Decisión:** LATAM Bank se diseña como banco nuevo, no calcado de los existentes: VP Clientes
  (por misiones), VP Inteligencia Artificial (agentes como fuerza laboral), VP Datos, VP Tecnología y
  VP Gobierno (segunda línea unificada, con Seguridad dentro), más Auditoría ante la junta. Los roles
  se ejercen en modo mixto: la presidencia y la primera línea con Claude; Gobierno y Auditoría como
  subagentes de solo lectura invocados en frío en cada compuerta.
- **Alternativas:** organigrama de banco tradicional (v0); solo agentes; solo personas.
- **Por qué:** independencia de quien desafía (P1), funciones obligatorias por país con dueño, cada
  cara con artefacto, compuerta y veto. Ver [04_Organizacion_y_roles.md](04_Organizacion_y_roles.md).
- **Estado:** firme en la **v2** ([04](04_Organizacion_y_roles.md)): misión como unidad de entrega,
  Oficina de Entrega, operación humana de fraude y disputas, voz en tres VP, equipo rojo, lista concreta
  de subagentes. Queda abierto solo el tamaño del equipo (pregunta 2 a los organizadores).

## D-09 · Componente aprendido principal: riesgo de la transacción disputada (26 sep 2026)

- **Decisión:** el componente aprendido principal deja de ser el clasificador de intención sobre
  transcripciones y pasa a ser un puntaje de riesgo de la transacción disputada, con `fraud_score`
  como línea base y partición temporal. El clasificador de intención queda como secundario, sobre
  conversaciones del equipo etiquetadas como tales.
- **Alternativas:** clasificador sobre transcripciones; predictor de escalamiento.
- **Por qué:** las transcripciones no tienen señal (dos aperturas, marcadores sin llenar, V de Cramér
  0,011) y `was_escalated` es ruido (AUC 0,51); `fraud_score` sí discrimina (AUC 0,87). Ver
  [03_Datos_por_capas.md](03_Datos_por_capas.md), sección 2.5 (P9, P10).
- **Estado:** reemplazada por D-14.

## D-08 · Datos por capas: bronce, plata, oro y platino (26 sep 2026)

- **Decisión:** bronce inmutable con metadatos y manifiesto; plata tipada, deduplicada, con dominios
  canónicos, PII tokenizada y cuarentena; oro en tres familias (analítica, operacional para el
  agente, aprendizaje); platino como capa de evidencia. DuckDB, Parquet y dbt, con contratos ODCS.
- **Alternativas:** dos capas (cruda y limpia); Spark o un *warehouse* en la nube.
- **Por qué:** cada capa tiene contrato y consumidor distintos; el volumen (5,3 GB) cabe local
  (P9, P11, P13). Ver [03_Datos_por_capas.md](03_Datos_por_capas.md).
- **Estado:** firme.

## D-07 · Umbrales provisionales hasta medir la línea base (26 sep 2026)

- **Decisión:** los umbrales numéricos del borrador de criterios (latencia, turnos para urgencia,
  monto de escalamiento, k) quedan provisionales y se fijan **después** de medir la línea base y
  **antes** de correr el retenido.
- **Principio:** P1.
- **Estado:** firme.

## D-06 · Evaluación por rutas de conversación (26 sep 2026)

- **Decisión:** toda conversación termina en una de ocho rutas (R1 a R8); cada caso lleva su ruta
  esperada y la resolución automática segura se define sobre ellas.
- **Alternativas:** evaluar solo con juez LLM; evaluar por turno.
- **Por qué:** permite verificación determinista del estado final y localizar dónde falla (P1, P2).
- **Estado:** firme.

## D-05 · Autorización por tipos en la capa de herramientas (26 sep 2026)

- **Decisión:** las herramientas exigen `SesionAutenticada` y `Confirmacion` en su firma; el cliente
  sale de la sesión; verificación estática estricta y pruebas de propiedades.
- **Alternativas:** verificación en tiempo de ejecución dentro de cada herramienta; guardarraíl del
  *framework*.
- **Por qué:** P5 y P6; investigaciones 3 y 8.
- **Estado:** firme (el marco quedó definido en D-11).

## D-04 · Arquitectura: el LLM entiende y redacta, el código decide (26 sep 2026)

- **Decisión:** motor de flujo determinista con estado explícito; LLM con salidas tipadas para
  comprensión y para redacción desde hechos verificados.
- **Alternativas:** agente autónomo con herramientas; varios agentes.
- **Por qué:** P4; investigación 2.
- **Estado:** firme; vale igual para chat y voz (D-17).

## D-03 · Código y datos fuera del Drive (26 sep 2026)

- **Decisión:** repositorio en `C:\Users\LaraJ\Projects\factored-hackathon-2026` con remoto en
  GitHub; datos locales fuera de git; documentos y decisiones en el Drive.
- **Por qué:** el Drive corrompe `.git`; 19 millones de filas no se sincronizan (P13).
- **Estado:** firme.

## D-02 · Flujo candidato: recepción de disputas por transacciones no reconocidas (26 sep 2026)

- **Decisión:** trabajar sobre ese flujo, entendido como fraude, error, disputa comercial y "no lo
  recuerda", con contención y escalamiento urgente para transferencias inmediatas.
- **Alternativas:** consultas de cuenta, tarjetas, información de crédito.
- **Por qué:** primera causa de queja en Colombia, México y Brasil; toca autenticación, fraude,
  plazos y traspaso (P8; investigaciones 1 y 6).
- **Estado:** firme: "Cargo no reconocido" es el 18% de las quejas de la muestra y la primera causa de
  queja en los tres países; la cifra se confirma sobre el total en F1.

## D-01 · Principios del proyecto (26 sep 2026)

- **Decisión:** adoptar [00_Principios.md](00_Principios.md) (P1 a P13) como reglas no negociables.
- **Estado:** firme.
