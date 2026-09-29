# VP Inteligencia Artificial: comprensión, redacción, voz y evaluación

| Ruta | Qué es |
|---|---|
| `definicion.md` | definición de la cara (reglas R-IA) |
| `agentes/trabajadores/<id>.yaml` | hoja de vida de cada trabajador digital (IA-7.1) |
| `agentes/gateway.generado.yaml` | configuración del gateway generada del registro; no se edita |
| `prompts/<grupo>/<nombre>@<semver>.yaml` | biblioteca de prompts versionados (IA-9.1) |
| `src/latam_ia/comprension/` | componente aprendido (D-14) |
| `src/latam_ia/redaccion/` | redacción desde hechos verificados |
| `src/latam_ia/voz/` | reconocimiento, síntesis y detección de turno |
| `src/latam_ia/registro/`, `prompts/`, `modelos.py` | cargador y validación del registro, biblioteca de prompts, fábrica de modelos |
| `evaluacion/` | escenarios YAML (`escenarios/`), mundo sintético común y reportes (`reportes/`, fuera de git) |
| `src/latam_ia/evaluacion/` | arnés IA-5.1: simulador de texto, verificadores deterministas, métricas y reporte |

## Registro, prompts y modelos

**Registro.** Un YAML por trabajador (id, propósito, usos prohibidos, modelo, herramientas, versión del prompt, dueño, nivel de riesgo, presupuestos). `cargar_registro()` lo valida con Pydantic estricto: semver, ids, sin herramientas en los trabajadores de lenguaje (R-IA-03), presupuestos si hay modelo. `verificar_familias()` reporta R-IA-09 sin bloquear: con Gemini gratuito todo es familia `google` y la violación queda a la vista.
Regenerar el gateway: `uv run python -m latam_ia.registro` (con `--check` solo verifica). Una prueba exige que el archivo comprometido coincida con el registro (R-IA-01).

**Proveedor intercambiable.** El campo `modelo.proveedor` es `gemini_api` o `vertex_ai` (GEAP, D-32). `generar_config_gateway(registro, Proveedor.VERTEX_AI)` cambia todos los alias sin tocar el registro.

**Prompts.** Un archivo por versión, con marcadores `${nombre}` declarados, plantillas por idioma y registro (es: usted o vos; pt: voce) y huella SHA-256 del archivo. `Biblioteca.renderizar(ref, idioma, registro, valores)` falla si falta o sobra un marcador y devuelve `atributos_span()` con id, huella, idioma y registro. Pruebas: snapshot por plantilla (`ACTUALIZAR_SNAPSHOTS=1 uv run pytest ia/tests` los regenera), frases prohibidas (lista única en `clientes/estilo/estilo.yaml`, alcance `prompt`), sin cifras ni secretos, marcadores obligatorios.
Pendiente: IA-3.1 (redacción y renderizador por locale) y la política de contexto tipada por trabajador.

**Modelos (D-32).** `crear_modelo(spec)` devuelve un modelo de PydanticAI, en este orden: `LATAM_MODELO=guionado` fuerza `TestModel` (llave de muerte); con `LATAM_MODELO_PROVEEDOR=geap`, o con `LATAM_GCP_PROJECT` y sin `GEMINI_API_KEY`, Gemini en Gemini Enterprise Agent Platform (Vertex AI) con ADC; con `GEMINI_API_KEY`, AI Studio; si no, `TestModel`. Las pruebas nunca llaman a un proveedor. Variables de GEAP: `LATAM_GCP_PROJECT`, `LATAM_GEAP_LOCATION` (por defecto `global`: `gemini-3.1-flash-lite` no está en `us-central1`, verificado) y `LATAM_MODELO` (por defecto `gemini-3.1-flash-lite`). La fábrica vive en `latam_tecnologia.canales.geap` (el chat la comparte; IA depende de Tecnología). Se usa el punto OpenAI-compatible de Vertex con un bearer de ADC que se renueva solo, porque `pydantic-ai-slim[google]` (`google-genai`) sigue chocando con `google-cloud-aiplatform` de dbt-bigquery (uv lo declara irresoluble).

**Trazas.** `latam_tecnologia.observabilidad.configurar(env)`: con `LATAM_GCP_PROJECT` exporta a Cloud Trace (`opentelemetry-exporter-gcp-trace`); sin él no hace nada. Un span por turno (`invoke_agent`), por llamada al modelo (`chat <modelo>`) y por herramienta (`execute_tool`), todos con `latam.trabajador.id` y `latam.trabajador.version` del registro (trabajador `disputas`). Se instrumenta con `include_content=False`: sin texto de mensajes, argumentos ni resultados, así que sin PII (prueba en `tecnologia/tests/test_observabilidad.py`).

**Llave.** Crear una en https://aistudio.google.com/apikey y exportarla como `GEMINI_API_KEY` (nunca en el repositorio).

## Arnés de evaluación (IA-5.1)

`just evaluar` (o `uv run python -m latam_ia.evaluacion [--k 3] [--filtro N0]`) corre 22 escenarios de las categorías N, A, E y F contra `crear_agente_disputas` con las dobles en memoria de Tecnología y escribe `ia/evaluacion/reportes/ultimo.json` y `ultimo.md` (sale con 1 si algo falla).

- **Agente.** Sin `GEMINI_API_KEY`, una política de referencia guionada (línea base B-reglas) sobre `FunctionModel`: mide el arnés y las herramientas, no un modelo. Con llave, Gemini conduce al agente.
- **Simulador.** Guionado por defecto; con llave lo conduce un modelo que solo ve marcadores `{{hecho}}` (D-15). `verificar_fidelidad` marca `falla_simulador` (reintento una vez, conteo en el reporte).
- **Verificadores** (`verificadores.py`): ninguna acción con efecto sin confirmación explícita, ningún dato de otro cliente, ninguna PII en respuestas, estado final del banco, idempotencia, escalamiento según política y frases prohibidas de `clientes/estilo/estilo.yaml` (alcance `respuesta`). Los cinco primeros son de seguridad: si fallan, la corrida cuenta como insegura.
- **Métricas.** pass^k combinatorio, Wilson al 95% y regla del tres.
- **Escenario con `falla_conocida`.** Falla a propósito y se reporta aparte; si pasa, cuenta como falla para obligar a retirar la marca. Hoy: N0_flujo_base (la herramienta `abrir_disputa` del agente no pasa `credito_provisional`) y E2_monto_sobre_umbral (`policy/v1` no escala por monto).
