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

# Datos: espejo del bucket (necesita LATAM_BUCKET y el perfil AWS latam-organizador fuera del repo)
espejo:
    uv run python -m latam_datos espejo

# Datos: bronce (Parquet por lote, bronce._lotes) y reglas Q-BRZ con reporte en platino
bronce:
    uv run python -m latam_datos bronce

# Datos: espejo y bronce en una corrida
data: espejo bronce
