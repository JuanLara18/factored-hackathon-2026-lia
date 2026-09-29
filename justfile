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

# Datos (Cloud Run Job): necesitan LATAM_GCP_PROJECT y LATAM_GCS_ESPEJO; la identidad la da gcloud o el servicio
espejo:
    uv run python -m latam_datos espejo

bronce:
    uv run python -m latam_datos bronce

# Espejo, bronce y reglas Q-BRZ en una corrida (lo que ejecuta el Job)
data:
    uv run python -m latam_datos todo
