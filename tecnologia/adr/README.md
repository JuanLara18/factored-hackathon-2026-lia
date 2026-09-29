# Decisiones de arquitectura (ADR)

Formato MADR breve (TEC-0.2, R-TEC-41). Cada ADR resume una decisión firme de `presidencia/decisiones.md`; si difieren, manda la decisión.

| ADR | Tema | Origen | Estado |
|---|---|---|---|
| [0001](0001-motor-de-flujo-propio.md) | Motor de flujo propio con PydanticAI para los trabajadores de lenguaje | D-11 | firme |
| [0002](0002-sin-mcp-en-el-camino-critico.md) | Sin MCP en el camino crítico | D-12 | firme |
| [0003](0003-dos-canales-un-nucleo.md) | Dos canales, un núcleo | D-17 | firme |
| [0004](0004-voz-en-cascada-con-pipecat.md) | Voz en cascada con Pipecat y experimento nativo medido | D-18 (precisada por D-22 y D-29) | firme en la arquitectura, provisional en proveedores y marco |
| [0005](0005-chat-con-ag-ui.md) | Chat con AG-UI y componentes tipados que se degradan a WhatsApp | D-19 (modificada por D-29) | firme |
| [0006](0006-plataforma-estado-identidad-gateway-trazas.md) | Plataforma: estado, autorización, identidad, gateway y trazas | D-20 | firme |
| [0007](0007-persistencia-probada-contra-postgres-real.md) | Persistencia probada contra Postgres real | D-23 (DP-TEC-06, enmienda de D-20) | firme |
| [0008](0008-transporte-de-voz-por-perfil.md) | Transporte de voz por perfil | D-22 (DP-TEC-05) | firme, condicionada a S1 |
| [0009](0009-spike-s4-retoma-idempotente.md) | Spike S4: retoma de chat a voz sin repetir la acción | TEC-0.4 | resultado |

Las demás DP-TEC siguen como propuestas hasta que el Comité de Plataforma las apruebe con acta; solo entonces se les abre ADR.
