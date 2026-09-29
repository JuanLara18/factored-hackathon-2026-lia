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
