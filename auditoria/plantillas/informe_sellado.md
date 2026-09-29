# INF-AUD-<objeto>-<n>: <título>

Plantilla de AUD-4.2 (R-AUD-01). El informe se guarda textual, se calcula la huella de la sección
`Hallazgos y dictamen` con `python -m latam_gobierno.sello --bloque`, se registra en `paquete.yaml` y se empuja
en un commit **antes** de que la Presidencia lo lea. Después de sellar, esa sección no se edita.

| Campo | Valor |
|---|---|
| Fecha | AAAA-MM-DD |
| Objeto | qué se audita y a qué versión (commit o etiqueta) |
| Paquete | `auditoria/sesiones/<fecha>_<objeto>/paquete.yaml` |
| Estado | borrador o sellado |

## Alcance y método

Qué se revisó, qué no, y con qué pasos de la sección 2 de la definición.

<!-- inicio-sellado -->
## Hallazgos y dictamen

| ID | Dónde | Hallazgo | Severidad | Cambio exigido | Dueño |
|---|---|---|---|---|---|
| H-01 | ruta o sección | qué se encontró | bloqueante, mayor o menor | qué debe cambiar | cara |

**Dictamen:** visto bueno, visto bueno con condiciones o veto. Motivo en dos líneas.
<!-- fin-sellado -->

## Sello

| Campo | Valor |
|---|---|
| Huella (SHA-256 del bloque entre las marcas de sellado, LF) | `<sha256>` |
| Commit empujado | `<hash>` |

## Respuesta de la Presidencia

Sección aparte. No modifica los hallazgos; solo acepta, rechaza con motivo o programa la corrección.
