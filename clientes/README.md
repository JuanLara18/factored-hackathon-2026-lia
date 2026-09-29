# VP Clientes: guiones, plantillas y operación humana

| Ruta | Qué es |
|---|---|
| `definicion.md` | definición de la cara (reglas R-CLI) |
| `matriz/matriz.yaml` | CLI-1.1: estados del motor x canal x registro con la intención de cada celda |
| `estilo/` | CLI-1.2: `guia_estilo.md` y `estilo.yaml` (frases prohibidas y obligatorias, vocabulario por país, límites por canal) |
| `src/latam_clientes/linter.py` | CLI-1.6: linter de contenido; `uv run python -m latam_clientes.linter`, y corre en pytest |
| `guiones/` | guiones por estado del motor, ES y PT, chat, WhatsApp y voz |
| `plantillas/es.yaml` | CLI-1.3: plantillas críticas en usted y vos, sin cifras escritas |
| `operacion_humana/` | colas, vista del experto, SLA |
| `demo/` | guion de la demo |
