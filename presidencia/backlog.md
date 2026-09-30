# Backlog consolidado (v1)

Generado desde la sección 8 de las definiciones `Definiciones/01` a `06`; el detalle (criterio de
aceptación y dependencias) está en cada definición. Rige la [resolución 10](definiciones/10_resolucion.md)
cuando contradiga una historia. El orden de ejecución y el recorte siguen a [07](hoja_de_ruta.md).

**Total:** 285 historias.

## Carga por día

| Día | Historias que empiezan |
|---|---|
| D0 | 25 |
| D1 | 31 |
| D2 | 40 |
| D3 | 50 |
| D4 | 28 |
| D5 | 35 |
| D6 | 20 |
| D7 | 22 |
| D8 | 10 |
| D9 | 16 |
| D10 | 5 |
| sin día | 1 |

## Presidencia y Oficina de Entrega

| ID | Historia | Día |
|---|---|---|
| PRE-3.4 | Definición de "AI-first" para el reporte (H-AUD-19) | D8 |
| PRE-3.5 | Capítulo de trabajo restante para producción, con aportes de cada cara (H-AUD-19) | D9 |

## VP Clientes (36)

| ID | Historia | Día |
|---|---|---|
| CLI-1.1 | Matriz estado × canal × registro con la intención de cada celda (2.2.1) | D2 |
| CLI-1.2 | Guía de estilo: voz de marca, registro y vocabulario por país, frases prohibidas y obligatorias | D2 |
| CLI-1.3 | Plantillas críticas en ES (usted y vos): plazos, montos, confirmaciones y cierre que distingue | D3 |
| CLI-1.4 | Catálogo completo de chat en ES | D4 |
| CLI-1.5 | Catálogo en PT con retrotraducción | D6 |
| CLI-1.6 | Linter de contenido en integración continua (3.4) | D3 |
| CLI-1.7 | Conversaciones de referencia por escenario N, A, E y F para el conjunto de desarrollo | D3 |
| CLI-1.8 | Revisión de `voz-del-cliente` y cierre de hallazgos | D4 |
| CLI-2.1 | Textos y etiquetas de los seis componentes en ES y PT | D3 |
| CLI-2.2 | Degradación a WhatsApp y comportamiento fuera de la ventana | D4 |
| CLI-2.3 | Aviso de IA fijo y botón permanente de persona | D4 |
| CLI-2.4 | Confirmación con vencimiento accesible e historial inerte | D4 |
| CLI-3.1 | Aviso de apertura de voz en ES y PT | D4 |
| CLI-3.2 | Lecturas de vuelta y listas de afirmaciones por idioma | D4 |
| CLI-3.3 | Catálogo de rellenos presintetizados | D4 |
| CLI-3.4 | Silencios, no entendidos, interrupciones y mapa de teclas | D5 |
| CLI-3.5 | Traspaso tibio por voz con mensajes de espera | D5 |
| CLI-4.1 | Supuestos de turnos y costo | D1 |
| CLI-4.2 | Modelo de colas, prioridades, acuerdos y niveles de saturación | D3 |
| CLI-4.3 | Especificación del `PaqueteTraspaso` y su render en ES y PT | D3 |
| CLI-4.4 | Vista del experto: orden, etiquetas de procedencia y roles | D4 |
| CLI-4.5 | Ingreso al mismo hilo y modo asistente | D5 |
| CLI-4.6 | Formulario de corrección y su exportación | D5 |
| CLI-4.7 | Simulación de colas para E7 y E8 con el perfil del dataset | D6 |
| CLI-4.8 | Protocolo del experto (demo, simulado y muestra humana) | D6 |
| CLI-5.1 | Árbol de resultados con la línea base del total | D2 |
| CLI-5.2 | Supuestos de proyección registrados en acta | D2 |
| CLI-5.3 | Control automático de calidad sobre el 100% de las conversaciones | D5 |
| CLI-5.4 | Guion de la demo con semillas de desarrollo | D6 |
| CLI-5.5 | Dos ensayos y respaldos grabados | D9 |
| CLI-5.6 | Sección de servicio del reporte: resultados por idioma y canal, proyección aparte | D9 |
| CLI-6.1 | Plantillas WA-UT-01 a WA-UT-05 y WA-AU-01 en ES (usted y vos) y PT | D4 |
| CLI-6.2 | Texto de consentimiento de la semilla humana de voz | D2 |
| CLI-6.3 | Aviso de privacidad resumido para chat y voz | D3 |
| CLI-6.4 | Reglas de notificaciones: tope y horario silencioso | D5 |
| CLI-6.5 | Revisión de accesibilidad WCAG 2.2 AA del chat y de la vista | D7 |

## VP Inteligencia Artificial (24)

| ID | Historia | Día |
|---|---|---|
| IA-1.1 | Semilla humana de 240 mensajes y su partición ancla y prueba | D1 |
| IA-1.2 | Catálogo de guiones y verbalizador local | D2 |
| IA-1.3 | Generador y verificador con auditoría T1 a T8 | D2 |
| IA-2.1 | Sistema v0: B1 más reglas de entidades y urgencia | D3 |
| IA-2.2 | Candidatos C1 a C5, calibración y umbrales | D4 |
| IA-2.3 | Transferencia a portugués y transcripciones; análisis de errores | D6 |
| IA-2.4 | Entrega a Gobierno para F4 | D6 |
| IA-3.1 | Redacción deslexicalizada y renderizador por locale | D3 |
| IA-3.2 | Léxicos del filtro en ES y PT | D4 |
| IA-4.1 | *Spike* S1 | D0 |
| IA-4.2 | Detección de turno dependiente del estado | D5 |
| IA-5.1 | Arnés con verificadores deterministas y simulador de texto | D2 |
| IA-5.2 | Juez y su validación | D5 |
| IA-5.3 | Líneas base B-reglas, B-LLM y B-humano | D5 |
| IA-5.4 | Modo sellado del retenido | D6 |
| IA-6.1 | Simulador de voz con ruido, G.711 e interrupciones | D7 |
| IA-7.1 | Registro v1 y generación de la configuración del gateway | D3 |
| IA-7.2 | Hojas de vida generadas | D8 |
| IA-8.1 | *Spike* S2 del frontend nativo | D0 |
| IA-8.2 | Experimento nativo contra cascada | D7 |
| IA-9.1 | Biblioteca de prompts con pruebas y trazabilidad | D3 |
| IA-10.1 | Experimento de `fraud_score` preregistrado y reporte | D5 |
| IA-11.1 | Indicadores, deriva y alertas | D7 |
| IA-11.2 | Model Armor medido y simulacro de incidente | D7 |

## VP Datos (51)

| ID | Historia | Día |
|---|---|---|
| DAT-1.1 | Espejo local del bucket con el perfil `latam-organizador`, sincronización por etag y listado completo a `platino.inventario_bucket` | D0 |
| DAT-1.2 | Constructor de bronce: CSV a Parquet todo texto, BOM, metadatos mínimos por fila y `bronce._lotes` | D0 |
| DAT-1.3 | Reglas Q-BRZ-01 a Q-BRZ-11 con reporte en platino | D0 |
| DAT-1.4 | Generación de respaldo en `bronce_respaldo` y prueba real de regeneración | D1 |
| DAT-1.5 | `just vigilar` con clasificación de objetos y programación cada 6 horas | D1 |
| DAT-1.6 | Manifiesto encadenado y `just verificar-cadena` | D1 |
| DAT-2.1 | Veredicto sobre el total de las 24 afirmaciones | D1 |
| DAT-2.2 | Reporte de deriva del diccionario y primera versión de `dominios/` | D1 |
| DAT-2.3 | Bloque A del EDA: demanda | D1 |
| DAT-2.4 | Bloque B: restricciones operativas y `capacidad_humana_franja` | D1 |
| DAT-2.5 | Bloque C: línea base de reclamos con su advertencia | D1 |
| DAT-2.6 | Datos para la auditoría de señal sobre el total (*spike* S5): particiones temporales y tablas | D0 |
| DAT-2.7 | `AS_OF` fijado con su consulta | D1 |
| DAT-2.8 | Rendimiento de la reconstrucción completa medido | D1 |
| DAT-3.1 | Plantilla ODCS, verificador de campos obligatorios y lint en CI | D1 |
| DAT-3.2 | 13 contratos de fuente y 8 de plata, primero `transacciones`, `productos`, `clientes` y `quejas` | D1 |
| DAT-3.3 | Proyecto dbt con dos perfiles y macros despachadas (`conversion_segura`, `coincide_regex`, `hex_md5`, `canon_decimal`, `canon_ts`, `token_hmac`, `huel | D1 |
| DAT-3.4 | Plata incremental por lotes, ventana contra `AS_OF`, ganador determinista y banderas | D2 |
| DAT-3.5 | Evolución de esquema y detector de regeneración | D2 |
| DAT-3.6 | Cuarentena, umbral de sistematicidad y conteos que cuadran | D2 |
| DAT-3.7 | Tokenización con la llave en la zona `seguridad`; `plata_restringida` | D2 |
| DAT-3.8 | *Fixture* de 24 casos con esperados y las propiedades (a) a (c) | D2 |
| DAT-3.9 | Data Contract CLI por corrida a `platino.resultado_contratos` y bloqueo de la publicación | D3 |
| DAT-3.10 | Pruebas de dbt generadas desde los contratos | D2 |
| DAT-4.1 | `transacciones_recientes`, `estado_productos`, `vista_cliente_segura` y `reclamos_cliente` con contrato | D3 |
| DAT-4.2 | `directorio_comercios` del equipo: 24 comercios, descriptores, semilla y versión | D2 |
| DAT-4.3 | `ficha_transaccion` con compras previas anteriores al evento, posibles duplicados, tasa aplicada y clave del estado | D3 |
| DAT-4.4 | `riesgo_transaccion` con acceso exclusivo del diagnóstico de fraude | D3 |
| DAT-4.5 | Publicación de la instantánea con puntero `VIGENTE` y `publicaciones_oro` | D3 |
| DAT-4.6 | Certificación de cada producto de oro operacional | D3 |
| DAT-4.7 | `candidatos_semilla`, `mezcla_rutas_estimada` y materializador de casos con huellas | D2 |
| DAT-4.8 | `features_transaccion` y `particiones_congeladas` sin fuga temporal | D3 |
| DAT-5.1 | Linaje por columna con sqlglot y prueba de caminos de PII | D3 |
| DAT-5.2 | Catálogo M-01 a M-46 en YAML y SQL con pruebas estadísticas | D2 |
| DAT-5.3 | Trazas y costos a platino | D4 |
| DAT-5.4 | Generador de tablas del reporte que exige el trío y separa por naturaleza | D8 |
| DAT-5.5 | Escaneo detectivo con Presidio y testigo positivo | D3 |
| DAT-5.6 | Tabla BCBS 239 y capítulo de datos del reporte | D9 |
| DAT-5.7 | Reconstrucción de la traza al etag | D5 |
| DAT-6.1 | Esquema del inventario y alta de los insumos del organizador y de los documentos | D1 |
| DAT-6.2 | Verificador de cobertura y marca de herencia | D2 |
| DAT-6.3 | Guardas del repositorio | D0 |
| DAT-6.4 | Procedencia de audios y registro de consentimientos, con IA y Auditoría | D5 |
| DAT-6.5 | Plan de retención y acta de borrado al cierre | D10 |
| DAT-7.1 | Proyecto, bucket, datasets por zona, cuentas de servicio, presupuesto, cuota y exportación de facturación, con Tecnología | D3 |
| DAT-7.2 | Carga de bronce y `just data-nube` con dbt-bigquery y contratos contra el servidor `nube` | D4 |
| DAT-7.3 | Taxonomía, reglas de enmascaramiento e IAM, probadas impersonando cada rol | D5 |
| DAT-7.4 | Knowledge Catalog: reglas generadas desde los contratos, perfiles, linaje, aspecto de producto y comparación de linajes | D5 |
| DAT-7.5 | Descubrimiento de Sensitive Data Protection con testigo positivo | D6 |
| DAT-7.6 | Paridad y propiedad (d) del *fixture* | D6 |
| DAT-7.7 | Desmontaje y verificación del borrado | D10 |

## VP Tecnología (96)

| ID | Historia | Día |
|---|---|---|
| TEC-0.1 | repositorio con el esqueleto de 2.5, pre-commit, `justfile` y CI mínimo | D0 |
| TEC-0.2 | ADR de D-11, D-12, D-17, D-18, D-19 y D-20, y de las DP-TEC aprobadas | D0 |
| TEC-0.3 | *spike* S3: texto por frases, un componente y una aprobación por AG-UI a una web mínima | D0 |
| TEC-0.4 | *spike* S4: caso en Postgres retomado de chat a voz sin repetir la acción | D0 |
| TEC-0.5 | *spike* S1 con IA (Voz): Pipecat con proveedores intercambiables, medición de voz a voz y WebSocket en Cloud Run | D0 |
| TEC-0.6 | arranque de Google Cloud: proyecto, facturación, presupuesto con alertas, bucket de estado, WIF | D0 |
| TEC-0.7 | LLM simulado con salidas tipadas y latencia configurable | D1 |
| TEC-1.1 | tipos de 2.6.1 con sus invariantes | D1 |
| TEC-1.2 | constructores privados y contratos de import-linter | D1 |
| TEC-1.3 | JSON Schema de los modelos y tipos TypeScript generados | D1 |
| TEC-1.4 | `Reloj` y reglas `banned-api` | D1 |
| TEC-2.1 | estados, tabla de transiciones y `transicionar()` pura | D3 |
| TEC-2.2 | esquema de 2.6.3 y migraciones con prueba de compatibilidad | D3 |
| TEC-2.3 | cáscara: ciclo de turno, efectos pendientes y bloqueo optimista | D3 |
| TEC-2.4 | idempotencia de turno, efecto y negocio | D3 |
| TEC-2.5 | retoma entre canales | D5 |
| TEC-2.6 | límites por turno y por conversación | D3 |
| TEC-2.7 | cargador de `policy/v1` con esquema y versión en cada decisión | D3 |
| TEC-3.1 | contratos OpenAPI con nombres BIAN confirmados y limitaciones | D3 |
| TEC-3.2 | servicios de lectura sobre el oro con filtro por cliente | D3 |
| TEC-3.3 | servicios de escritura (bloqueo y caso) con `Idempotency-Key` | D1 |
| TEC-3.4 | identidad: sesión de prueba, JWT ES256, `acr`, OTP, reto de RFC 9470, JWKS, reloj | D3 |
| TEC-3.5 | firma con Cloud KMS en la nube | D4 |
| TEC-3.6 | plano de control de inyección de fallas | D3 |
| TEC-3.7 | Schemathesis en CI | D3 |
| TEC-4.1 | catálogo de 2.7.1 con firmas de capacidades | D3 |
| TEC-4.2 | PDP con negación por defecto y registro encadenado | D3 |
| TEC-4.3 | *timeouts*, reintentos e interruptores por herramienta | D3 |
| TEC-4.4 | verificación posterior y efectos inciertos | D3 |
| TEC-4.5 | arnés de propiedades para los invariantes de Gobierno | D4 |
| TEC-5.1 | endpoint AG-UI por SSE con el mapeo de 2.9 | D4 |
| TEC-5.2 | SPA con los seis componentes | D4 |
| TEC-5.3 | confirmación por `nonce` | D4 |
| TEC-5.4 | emisión por frases y filtro de salida | D4 |
| TEC-5.5 | modo WhatsApp simulado con ventana de 24 horas | D5 |
| TEC-5.6 | dispositivo simulado de OTP | D4 |
| TEC-5.7 | N1 a N6 de punta a punta en ES con Playwright | D4 |
| TEC-6.1 | tubería Pipecat con VAD, SmartTurn y los proveedores de S1 | D5 |
| TEC-6.2 | `ProcesadorMotor` con plantillas por frase | D5 |
| TEC-6.3 | registro de lo dicho hasta la interrupción | D5 |
| TEC-6.4 | rellenos presintetizados | D5 |
| TEC-6.5 | DTMF en el navegador | D5 |
| TEC-6.6 | regla de confianza para datos críticos | D5 |
| TEC-6.7 | cliente web de voz: WebRTC en local, WebSocket en la nube | D5 |
| TEC-6.8 | punta a punta con audio sintético | D5 |
| TEC-7.1 | LiteLLM con alias, claves virtuales y presupuestos desde `agentes/registro.yaml` | D3 |
| TEC-7.2 | redacción con Presidio y reconocedores propios | D5 |
| TEC-7.3 | Model Armor en la nube con latencia medida | D6 |
| TEC-7.4 | costo por llamada en los spans | D4 |
| TEC-7.5 | medición del aporte del filtro | D7 |
| TEC-7.6 | salida exclusiva del gateway hacia modelos | D3 |
| TEC-8.1 | OpenTelemetry con convenciones GenAI y atributos `latam.` | D3 |
| TEC-8.2 | Phoenix en local y en la nube detrás de IAP | D3 |
| TEC-8.3 | Cloud Trace y logs correlacionados sin datos personales | D6 |
| TEC-8.4 | paneles y alertas en Terraform | D7 |
| TEC-8.5 | exportación a platino con huella encadenada | D8 |
| TEC-9.1 | escenarios de Locust para chat | D7 |
| TEC-9.2 | generador de carga de voz | D7 |
| TEC-9.3 | perfiles de latencia del LLM simulado ajustados a spans reales | D7 |
| TEC-9.4 | tabla de cuotas llena | D0 |
| TEC-9.5 | reporte de capacidad | D7 |
| TEC-10.1 | perfiles de Compose (`nucleo`, `voz`, `llm-local`, `observabilidad`) | D0 |
| TEC-10.2 | siembra de identidades de prueba, directorio de comercios y plantillas | D3 |
| TEC-10.3 | README de un comando con solución de problemas | D9 |
| TEC-10.4 | prueba en máquina limpia en Linux y Windows | D9 |
| TEC-11.1 | módulos de Terraform de 2.3 | D0 |
| TEC-11.2 | Cloud SQL con autenticación IAM y usuarios por esquema | D3 |
| TEC-11.3 | servicios y jobs de Cloud Run con sondas y límites | D4 |
| TEC-11.4 | IAP para `lb-staff` y `lb-phoenix` | D5 |
| TEC-11.5 | bucket de oro en solo lectura con `origen` | D4 |
| TEC-11.6 | desmontaje verificado | D10 |
| TEC-12.1 | `ci.yml` completo | D1 |
| TEC-12.2 | `cd.yml` con despliegue sin tráfico, humo, promoción y reversión | D4 |
| TEC-12.3 | WIF sin llaves | D0 |
| TEC-12.4 | SBOM, escaneos y zizmor | D2 |
| TEC-12.5 | enfriamiento de dependencias y Dependabot | D1 |
| TEC-13.1 | cuentas de servicio y roles de 4.1 con verificación en CI | D3 |
| TEC-13.2 | inventario de secretos en Secret Manager | D3 |
| TEC-13.3 | seguridad del navegador y límites de tasa | D4 |
| TEC-13.4 | interruptor "todo a humano" | D5 |
| TEC-13.5 | registros de auditoría de acceso a datos | D3 |
| TEC-13.6 | runbooks y simulacro | D7 |
| TEC-13.7 | borde con Cloud Armor (opcional) | D7 |
| TEC-14.1 | `finops/precios.yaml` | D2 |
| TEC-14.2 | consultas de costo por caso y por resolución segura | D6 |
| TEC-14.3 | exportación de facturación y conciliación | D9 |
| TEC-14.4 | sección de costos del reporte con la proyección etiquetada | D9 |
| TEC-15.1 | render del paquete desde el objeto tipado, con hechos, interpretaciones y conflictos separados | D5 |
| TEC-15.2 | cola por idioma, turno y especialidad con espera declarada | D5 |
| TEC-15.3 | vista del experto con roles y registro de acciones | D5 |
| TEC-15.4 | reclasificación del motivo como etiqueta para IA | D6 |
| TEC-16.1 | Gemini Live con una sola herramienta detrás de la bandera | D7 |
| TEC-16.2 | métricas de 5.9 y costo por minuto medido | D8 |
| TEC-17.1 | número de Twilio, Media Streams y serializador | D7 |
| TEC-17.2 | validación de firma de webhooks | D7 |
| TEC-17.3 | prueba con degradación telefónica G.711 | D7 |

## VP Gobierno (47)

| ID | Historia | Día |
|---|---|---|
| GOB-1.1 | Catálogo de normas con nivel de verificación, fecha y texto citado | D1 |
| GOB-1.2 | Reglas por país y producto con casos borde | D2 |
| GOB-1.3 | Matriz de autonomía y niveles `acr` | D2 |
| GOB-1.4 | Regla de riesgo y umbrales con tres puntos de operación | D2 |
| GOB-1.5 | Pruebas de política y detector de U6 | D3 |
| GOB-1.6 | Verificación primaria pendiente (sección 10.2, puntos 1 a 7) |  |
| GOB-2.1 | Mezcla de rutas declarada y tamaños | D2 |
| GOB-2.2 | Casos representativos: generador de otra familia y 25% escrito a mano | D2 |
| GOB-2.3 | Estrés, pares de equidad y detectores de U1 a U13 | D2 |
| GOB-2.4 | Retenido del componente | D2 |
| GOB-2.5 | Segundo anotador frío y κ | D2 |
| GOB-2.6 | Cifrado, huellas, reservas selladas y acta de F2 | D2 |
| GOB-3.1 | Consentimientos y semilla humana de 24 grabaciones o más | D3 |
| GOB-3.2 | Voz derivada del texto por locale, con ruido del dataset y degradación telefónica, con el procedimiento fijado en F2 | D6 |
| GOB-3.3 | Huella del retenido de voz en acta | D6 |
| GOB-4.1 | Tabla MAESTRO con OWASP oficial | D2 |
| GOB-4.2 | Corrección del mapeo de [01](../docs/diseno/01_Interacciones_y_criterios.md) | D2 |
| GOB-4.3 | Catálogo AT-01 a AT-32 automatizado | D2 |
| GOB-5.1 | Especificación de I-01 a I-18 | D3 |
| GOB-5.2 | Máquina de estados de Hypothesis | D4 |
| GOB-5.3 | Corrida de 10.000 secuencias por invariante | D7 |
| GOB-6.1 | Herramientas y guiones de voz listos | D6 |
| GOB-6.2 | Día de equipo rojo | D7 |
| GOB-6.3 | Reprueba y suite de regresión (no el retenido: R-GOB-57) | D8 |
| GOB-7.1 | Validación del componente (D-14) | D6 |
| GOB-7.2 | Validación de la regla de riesgo | D6 |
| GOB-7.3 | Corrida oficial con k = 3 y líneas base | D8 |
| GOB-7.4 | Validación del juez | D8 |
| GOB-7.5 | Reporte de equidad e investigación | D9 |
| GOB-7.6 | Acta de liberación o veto | D9 |
| GOB-8.1 | Ficha GAICF | D2 |
| GOB-8.2 | Registro de riesgos con NIST AI 600-1 | D2 |
| GOB-8.3 | Procedimiento y plantilla de control de cambios | D2 |
| GOB-8.4 | Mapeo con NIST AI RMF e ISO/IEC 42001 para el reporte | D9 |
| GOB-9.1 | Clase y origen en los contratos | D2 |
| GOB-9.2 | EIPD versiones 1 y 2 | D2 |
| GOB-9.3 | Avisos de IA y de voz | D3 |
| GOB-9.4 | Marcadores y prueba de intercepción | D5 |
| GOB-9.5 | Retención y `just purge` con evidencia | D9 |
| GOB-10.1 | Línea base de secretos: gitleaks en *pre-commit*; llave del organizador fuera del repositorio | D0 |
| GOB-10.2 | Cadena de CI de seguridad | D1 |
| GOB-10.3 | Línea base de Google Cloud y Model Armor | D1 |
| GOB-10.4 | Escaneo, SBOM y firma de la versión candidata | D8 |
| GOB-11.1 | Severidades, roles y *playbooks* PB-1 a PB-7 | D3 |
| GOB-11.2 | Simulacro | D7 |
| GOB-12.1 | Cuestionario y evaluación de proveedores | D0 |
| GOB-12.2 | Presupuestos y alertas | D1 |

## Auditoría (29)

| ID | Historia | Día |
|---|---|---|
| AUD-4.1 | escribir `.claude/agents/auditoria.md` con mandato, entradas, salida y permisos | D0 |
| AUD-4.2 | plantilla del paquete de independencia y del informe sellado | D0 |
| AUD-4.3 | declaración de independencia emulada para el reporte | D9 |
| AUD-1.1 | `audit/fuentes.yaml` con las 28 referencias de arXiv de 2026 y las demás que sostienen decisiones | D0 |
| AUD-1.2 | verificación de existencia y fechas en lote con la API de metadatos de arXiv | D1 |
| AUD-1.3 | verificación primaria de las normas de `policy/v1` | D2 |
| AUD-1.4 | verificación de pasajes de las fuentes que sostienen decisiones firmes | D6 |
| AUD-1.5 | notas fechadas en las investigaciones con cifras corregidas o refutadas | D7 |
| AUD-1.6 | cruce de citas del reporte con la tabla | D9 |
| AUD-2.1 | pasar la matriz de 6.3 a `audit/matriz.yaml` con JSON Schema | D1 |
| AUD-2.2 | enlazar cada fila con la regla o historia de la cara dueña | D1 |
| AUD-2.3 | conectar cada fila a su consulta en platino | D8 |
| AUD-2.4 | congelar la matriz con la corrida candidata | D9 |
| AUD-5.1 | primera ronda: pasos 1 a 11 de 2.9 sobre las seis definiciones | D0 |
| AUD-5.2 | ronda de cierre sobre la segunda versión | D0 |
| AUD-5.3 | revisión de esta definición por Gobierno o una invocación fría (R-AUD-07) | D0 |
| AUD-6.1 | script de verificación del retenido | D2 |
| AUD-6.2 | script independiente de verificación de cadenas y raíz | D5 |
| AUD-6.3 | prueba de canarios de PII | D5 |
| AUD-6.4 | script de R-AUD-09 que empareja cifras del reporte con `metricas_reporte` | D8 |
| AUD-7.1 | informe de F2 | D2 |
| AUD-7.2 | informe de F4 | D6 |
| AUD-7.3 | informe de F5, con el artefacto señuelo de R-AUD-56 | D7 |
| AUD-7.4 | informe de F6 | D9 |
| AUD-3.1 | ensayo de máquina limpia en Linux y Windows 11 | D5 |
| AUD-3.2 | prueba completa, pasos 0 a 13 | D10 |
| AUD-3.3 | dictamen y, si hay devolución, reauditoría focalizada | D10 |
| AUD-8.1 | verificar consentimientos contra grabaciones, uno a uno | D5 |
| AUD-8.2 | verificar actas de borrado contra inventario y consentimientos | D9 |
