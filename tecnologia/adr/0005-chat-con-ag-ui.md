# ADR 0005: Chat con AG-UI y componentes tipados que se degradan a WhatsApp

- **Estado:** firme
- **Decisión de origen:** D-19 (modificada por D-29) (`presidencia/decisiones.md`)
- **Principio que la guía:** P5, P6

## Contexto

La confirmación de una acción debe ser un evento de la superficie, no texto libre (investigación 20).

## Opciones consideradas

Chat de solo texto; WhatsApp real únicamente.

## Decisión

La superficie de chat emite eventos AG-UI desde el motor: texto en streaming filtrado por frases, componentes tipados (ficha de la transacción, opciones enmascaradas, confirmación con el monto de la base, estado del caso, aviso de traspaso) y aprobaciones. Cada componente se degrada a botones (máximo 3) y listas (máximo 10) de WhatsApp. El experto humano entra al mismo hilo con el paquete. Por D-29, WhatsApp funciona con el número de prueba de Meta Cloud API, con hasta 5 destinatarios registrados.

## Consecuencias

Interfaz generativa con confirmación verificable. Cada componente nuevo exige su degradación a WhatsApp.
