# ADR 0006: Plataforma: estado, autorización, identidad, gateway y trazas

- **Estado:** firme
- **Decisión de origen:** D-20 (`presidencia/decisiones.md`)
- **Principio que la guía:** P5, P9, P13

## Contexto

Lo mínimo que cumple el enunciado con garantías verificables y una instalación de un comando (investigaciones 10, 17 y 18).

## Opciones consideradas

Cedar; Keycloak o un servidor OIDC de prueba; Langfuse; Apigee.

## Decisión

Estado durable en Postgres (DuckDB solo en la ruta analítica). Autorización por tipos más un punto de decisión propio que registra cada decisión, sin Cedar. Identidad propia con niveles acr, OTP simulado, expiración y reloj inyectable, con la forma de RFC 9470. Gateway con LiteLLM (cuotas, costo, enrutamiento) y Presidio con reconocedores de CURP, CC y DNI; Model Armor solo si hay Google Cloud. Proveedores de modelos detrás del gateway, con familias distintas para generador, sistema y juez, y modelo abierto local como plan B. Trazas OpenTelemetry con Phoenix local.

## Consecuencias

Instalación reproducible y auditoría de cada decisión. Los proveedores concretos se fijan cuando respondan los organizadores. La enmienda D-23 (ADR 0007) cambia SQLite en pruebas por Postgres real.
