# ADR 0001: Motor de flujo propio con PydanticAI para los trabajadores de lenguaje

- **Estado:** firme
- **Decisión de origen:** D-11 (`presidencia/decisiones.md`)
- **Principio que la guía:** P4, P5, P13

## Contexto

El motor decide rutas, acciones y escalamientos, y debe autorizar cada llamada y dejar traza. El despacho por defecto de los marcos de agentes no autoriza por llamada (investigaciones 2 y 17).

## Opciones consideradas

LangGraph como núcleo; Google ADK; máquina de estados propia con PydanticAI solo para comprensión y redacción.

## Decisión

Máquina de estados propia, tipada y persistida con llaves de idempotencia. PydanticAI actúa solo como cliente tipado de comprensión y redacción. DBOS queda como opción si sobra tiempo para mostrar durabilidad. Respaldo: LangGraph con la capa de herramientas tipada debajo.

## Consecuencias

Control total de autorización y trazas, y decisiones deterministas verificables. El costo es mantener la máquina de estados propia. El spike S4 (ADR 0009) valida la retoma entre chat y voz sobre este motor.
