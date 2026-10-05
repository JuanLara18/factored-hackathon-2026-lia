# VP Clientes: guiones, plantillas y operación humana

| Ruta | Qué es |
|---|---|
| `definicion.md` | definición de la cara (reglas R-CLI) |
| `matriz/matriz.yaml` | CLI-1.1: estados del motor x canal x registro (usted, vos y voce, los tres exigidos) con la intención de cada celda |
| `estilo/` | CLI-1.2: `guia_estilo.md` y `estilo.yaml` (frases prohibidas y obligatorias, vocabulario por país, límites por canal) y su perfil `pt` |
| `src/latam_clientes/linter.py` | CLI-1.6: linter de contenido en español y portugués; `uv run python -m latam_clientes.linter`, y corre en pytest |
| `guiones/` | guiones por estado del motor, ES y PT, chat, WhatsApp y voz |
| `plantillas/es.yaml` | CLI-1.3: plantillas críticas en usted y vos, sin cifras escritas |
| `plantillas/pt.yaml` | CLI-1.5: las mismas plantillas en portugués de Brasil (voce), con retrotraducción al español por plantilla |
| `operacion_humana/` | colas, vista del experto, SLA |
| `demo/` | guion de la demo |

## Portugués (CLI-1.5)

Atención en portugués para clientes de la región (cuentas de México, Colombia y Argentina). No hay cuentas ni datos de Brasil: el modo se rotula "atendimento em português para clientes da região" y la limitación está en [`datos/LIMITACIONES.md`](../datos/LIMITACIONES.md).

- **Catálogo.** `plantillas/pt.yaml` calca los 41 ids de `es.yaml` (cada celda de la matriz y cada plantilla crítica) con `textos: {voce: ...}`, `retraduccion` (lo que dice el texto, vuelto a español) y, cuando adapta en lugar de traducir, `notas`. Los marcadores `{monto}`, `{fecha}`, `{norma}` y los demás son los mismos: montos y fechas siguen el formato del país de la cuenta, no el de Brasil, y la norma es la del país de la cuenta.
- **Linter.** Las reglas de siempre (frases prohibidas, caracteres prohibidos, cifras escritas, marcadores declarados y requeridos, longitud por canal, vocabulario por canal y por país, frases obligatorias) corren sobre `pt.yaml` con el perfil `pt` de `estilo.yaml`, más: mismos ids, canales, tipos y marcadores que el español, retrotraducción presente y con los mismos marcadores, registro voce sin tuteo (`tu`, `teu`), sin español colado (`su`, `tarjeta`) y sin trato formal (`o senhor`), pt-BR sin formas de Portugal, y sin Pix, MED, Procon ni Banco Central do Brasil. El límite es de 20 palabras por frase en chat y WhatsApp y 15 en voz, y de 460, 520 y 350 caracteres por canal.
- **Selector.** En las ocho páginas públicas, la banca, el asistente y el chat el cliente elige "Español, usted", "Español, vos" o "Português, você". Viaja como `registro` (`usted`, `vos`, `voce`) en la sesión, el encabezado `X-Registro`, el prompt (`disputas/agente@1.3.0`, variante `pt voce`), las plantillas, los mensajes de aprobación y el paquete de traspaso (`idioma = pt`). La elección (`latam.trato`) y el país (`latam.pais`) son una sola preferencia en todo el sitio. Sin elección explícita, Argentina sugiere `vos` y la banca preselecciona un cliente del país elegido.
- **Revisión.** Sin revisor nativo (S-CLI-14). Quien revise el catálogo parte de `retraduccion` y `notas`.
