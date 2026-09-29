set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Instala las dependencias de todas las caras
setup:
    uv sync

# Formato, tipos y pruebas: lo mismo que corre la CI
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest -q

test:
    uv run pytest -q

# Servicios locales: Postgres y Phoenix
up:
    docker compose up -d

down:
    docker compose down

# Datos: valida latam_bank.bronce_* (reglas Q-BRZ) y escribe latam_bank.platino_reporte_calidad_corrida
# Necesita LATAM_GCP_PROJECT y, opcional, LATAM_GCP_LOCATION; la identidad la da gcloud o el servicio
validar:
    uv run python -m latam_datos validar

# Carga supuesta (D-30), una sola vez: espejo local del bucket a latam_bank.bronce_<archivo>
cargar-bronce bucket:
    aws s3 sync s3://{{bucket}}/data/ data/espejo/
    uv run python -m latam_datos.carga_externa

# Datos: crea la llave de seudonimización (una vez), construye plata, oro y platino en BigQuery y corre los tests
dbt-build:
    cd datos/dbt; uv run dbt run-operation crear_llave; uv run dbt build

# Datos: solo los casos del fixture de actualización (unit tests de dbt, sin tocar tablas reales)
dbt-test-fixture:
    cd datos/dbt; uv run dbt test --select "test_type:unit"
