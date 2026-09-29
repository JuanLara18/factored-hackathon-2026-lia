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
