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
| `evaluacion/` | arnés y simuladores de texto y voz |

## Registro, prompts y modelos

**Registro.** Un YAML por trabajador (id, propósito, usos prohibidos, modelo, herramientas, versión del prompt, dueño, nivel de riesgo, presupuestos). `cargar_registro()` lo valida con Pydantic estricto: semver, ids, sin herramientas en los trabajadores de lenguaje (R-IA-03), presupuestos si hay modelo. `verificar_familias()` reporta R-IA-09 sin bloquear: con Gemini gratuito todo es familia `google` y la violación queda a la vista.
Regenerar el gateway: `uv run python -m latam_ia.registro` (con `--check` solo verifica). Una prueba exige que el archivo comprometido coincida con el registro (R-IA-01).

**Proveedor intercambiable.** El campo `modelo.proveedor` es `gemini_api` (hoy) o `vertex_ai` (cuando se reabra la facturación, D-29). `generar_config_gateway(registro, Proveedor.VERTEX_AI)` cambia todos los alias sin tocar el registro.

**Prompts.** Un archivo por versión, con marcadores `${nombre}` declarados, plantillas por idioma y registro (es: usted o vos; pt: voce) y huella SHA-256 del archivo. `Biblioteca.renderizar(ref, idioma, registro, valores)` falla si falta o sobra un marcador y devuelve `atributos_span()` con id, huella, idioma y registro. Pruebas: snapshot por plantilla (`ACTUALIZAR_SNAPSHOTS=1 uv run pytest ia/tests` los regenera), frases prohibidas de 2.5.5, sin cifras ni secretos, marcadores obligatorios.
Pendiente: IA-3.1 (redacción y renderizador por locale) y la política de contexto tipada por trabajador.

**Modelos.** `crear_modelo(spec)` devuelve un modelo de PydanticAI: Gemini si `GEMINI_API_KEY` está en el entorno; si no, `TestModel`. Las pruebas nunca llaman a un proveedor. Gemini se consulta por su punto de compatibilidad con OpenAI (`generativelanguage.googleapis.com/v1beta/openai/`), porque `google-genai`, que exige el proveedor `google-gla:`, choca con `google-cloud-aiplatform` de dbt-bigquery.

**Llave.** Crear una en https://aistudio.google.com/apikey y exportarla como `GEMINI_API_KEY` (nunca en el repositorio).
