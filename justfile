# dbt corre aislado del lock del workspace (sus pines de google-cloud-aiplatform chocan con pydantic-ai[google])
dbt := "uvx --from dbt-bigquery==1.12.1 dbt"

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Instala las dependencias de todas las caras
setup:
    uv sync --all-packages --all-groups

# Formato, tipos y pruebas: lo mismo que corre la CI
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest -q

test:
    uv run pytest -q

# Chat web local (TEC-3): http://localhost:8765/ ; con GEMINI_API_KEY usa Gemini, sin ella un guion determinista
chat puerto="8765":
    uv run uvicorn latam_tecnologia.canales.chat_web:crear_app_desde_entorno --factory --port {{puerto}}

# Servicios locales por perfil de Compose (TEC-10.1): nucleo, voz, llm-local, observabilidad
up:
    docker compose --profile nucleo --profile observabilidad up -d

demo-nucleo:
    docker compose --profile nucleo up -d

demo-voz:
    docker compose --profile nucleo --profile voz up -d

demo-llm-local:
    docker compose --profile nucleo --profile llm-local up -d

demo-observabilidad:
    docker compose --profile nucleo --profile observabilidad up -d

down:
    docker compose --profile nucleo --profile voz --profile llm-local --profile observabilidad down

# Datos: valida latam_bank.bronce_* (reglas Q-BRZ) y escribe latam_bank.platino_reporte_calidad_corrida
# Necesita LATAM_GCP_PROJECT y, opcional, LATAM_GCP_LOCATION; la identidad la da gcloud o el servicio
validar:
    uv run python -m latam_datos validar

# Carga supuesta (D-30), una sola vez: espejo local del bucket a latam_bank.bronce_<archivo>
cargar-bronce bucket:
    aws s3 sync s3://{{bucket}}/data/ data/espejo/
    uv run python -m latam_datos.carga_externa

# Datos: manifiesto de carga por tabla (archivos, filas CSV contra BigQuery, huella encadenada)
manifiesto:
    uv run python -m latam_datos.evidencia manifiesto

# Datos: recomputa la cadena de datos/manifiestos/; sale con 1 si un manifiesto viejo fue editado
verificar-cadena:
    uv run python -m latam_datos.evidencia verificar-cadena

# Datos: compara el respaldo del organizador con el espejo (ruta y sha256); solo guarda el resumen
comparar-respaldo:
    uv run python -m latam_datos.evidencia comparar-respaldo

# Datos: inventario de insumos por clase de procedencia, con AS_OF
inventario:
    uv run python -m latam_datos.evidencia inventario

# Datos: crea la llave de seudonimización (una vez), construye plata, oro y platino en BigQuery y corre los tests
dbt-build:
    cd datos/dbt; {{dbt}} run-operation crear_llave; {{dbt}} build

# Datos: solo los casos del fixture de actualización (unit tests de dbt, sin tocar tablas reales)
dbt-test-fixture:
    cd datos/dbt; {{dbt}} test --select "test_type:unit"

# IA: arnés de evaluación del agente de disputas; escribe ia/evaluacion/reportes/ultimo.json y ultimo.md
evaluar *args:
    uv run python -m latam_ia.evaluacion {{args}}

# Chat: arma y sube el backend a un Space de Hugging Face (requiere `hf auth login` con token de escritura)
desplegar-chat space="juanlara/latam-bank-chat":
    uv run python tecnologia/infra/hf_space/preparar.py .hf_space
    uvx --from huggingface_hub hf repo create {{space}} --repo-type space --space-sdk docker --exist-ok
    uvx --from huggingface_hub hf upload {{space}} .hf_space . --repo-type space

# Chat: despliega el backend en Cloud Run (escala a cero, una instancia; presupuesto con alertas en COP 20.000).
# LATAM_TRABAJADOR_VERSION debe coincidir con ia/agentes/trabajadores/disputas.yaml.
desplegar-chat-run:
    uv run python tecnologia/infra/hf_space/preparar.py .hf_space
    gcloud run deploy latam-chat --source .hf_space --project latam-bank-hackaton-2026 --region us-central1 --port 7860 --min-instances 0 --max-instances 1 --cpu 1 --memory 512Mi --concurrency 40 --timeout 300 --allow-unauthenticated --set-env-vars LATAM_GCP_PROJECT=latam-bank-hackaton-2026,LATAM_GCP_LOCATION=US,LATAM_GEAP_LOCATION=global,LATAM_TRABAJADOR_VERSION=0.1.0 --labels proyecto=latam-bank --quiet

# Agente de disputas: arma y valida el paquete de Agent Runtime sin llamar a la API.
probar-agente-runtime:
    uv run python tecnologia/infra/agent_runtime/desplegar.py --dry-run

# Agente de disputas: lo despliega en Agent Runtime (min-instances 0, Agent Identity) e imprime el recurso.
desplegar-agente:
    uv run python tecnologia/infra/agent_runtime/desplegar.py

# Chat con cuenta de servicio mínima (tecnologia/infra/agent_runtime/iam.sh cuenta) que reenvía al agente:
# just desplegar-chat-run-agente projects/<numero>/locations/us-central1/reasoningEngines/<id>
desplegar-chat-run-agente recurso:
    uv run python tecnologia/infra/hf_space/preparar.py .hf_space
    gcloud run deploy latam-chat --source .hf_space --project latam-bank-hackaton-2026 --region us-central1 --port 7860 --min-instances 0 --max-instances 1 --cpu 1 --memory 512Mi --concurrency 40 --timeout 300 --allow-unauthenticated --service-account latam-chat@latam-bank-hackaton-2026.iam.gserviceaccount.com --set-env-vars LATAM_GCP_PROJECT=latam-bank-hackaton-2026,LATAM_GCP_LOCATION=US,LATAM_GEAP_LOCATION=global,LATAM_TRABAJADOR_VERSION=0.1.0,LATAM_AGENT_RUNTIME_RECURSO={{recurso}} --labels proyecto=latam-bank --quiet
