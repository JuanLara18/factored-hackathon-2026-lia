# ADR 0008: Transporte de voz por perfil

- **Estado:** firme, condicionada a S1
- **Decisión de origen:** D-22 (DP-TEC-05) (`presidencia/decisiones.md`)
- **Principio que la guía:** P9, P13

## Contexto

Cloud Run no recibe UDP, y WebRTC entre pares lo necesita (H-AUD-06).

## Opciones consideradas

WebRTC gestionado desde el inicio; WebSocket en todos los entornos.

## Decisión

WebRTC en local. En la nube, WebSocket del navegador a Cloud Run solo si el spike S1 mide la latencia de voz a voz dentro del presupuesto por ese transporte. La latencia se reporta por transporte.

## Consecuencias

Si S1 no cumple, se recurre a WebRTC gestionado o a Compute Engine, con costo y operación adicionales.
