# ADR 0002: Sin MCP en el camino crítico

- **Estado:** firme
- **Decisión de origen:** D-12 (`presidencia/decisiones.md`)
- **Principio que la guía:** P4, P9

## Contexto

Los trabajadores de lenguaje no tienen herramientas (P4) y MCP suma un salto de red y riesgos de envenenamiento de herramientas (investigación 17).

## Opciones consideradas

Exponer las herramientas por MCP desde el inicio; llamadas directas del motor a los servicios.

## Decisión

Los servicios se llaman directamente desde el motor. MCP queda en la ruta a producción para exponer servicios a otros agentes del banco.

## Consecuencias

Menos latencia y menos superficie de ataque en el prototipo. Exponer los servicios por MCP en producción exigirá una capa adicional, ya identificada.
