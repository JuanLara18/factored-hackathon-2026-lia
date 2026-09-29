# ADR 0004: Voz en cascada con Pipecat y experimento nativo medido

- **Estado:** firme en la arquitectura, provisional en proveedores y marco
- **Decisión de origen:** D-18 (precisada por D-22 y D-29) (`presidencia/decisiones.md`)
- **Principio que la guía:** P4, P5, P13

## Contexto

La cascada da control y auditoría por etapa, recomendada para banca; el frontend nativo de audio es donde avanza el estado del arte y comparar ambos con datos es la evidencia más fuerte (investigación 20).

## Opciones consideradas

Solo nativo de audio; solo cascada; LiveKit Agents como marco.

## Decisión

Camino principal: cascada en streaming con Pipecat (VAD, reconocimiento, el mismo motor, síntesis), interrupciones registradas y plantillas deterministas para montos, plazos y confirmaciones. Experimento: frontend nativo delegando en el motor con una sola herramienta. La voz no autentica: el OTP es el factor para acciones, con lectura de vuelta y confirmación explícita o DTMF. El audio crudo no se guarda por defecto. Pipecat corre en proceso con el motor; LiveKit queda como alternativa de producción. Por D-22, WebRTC en local y en la nube WebSocket a Cloud Run solo si S1 mide la latencia dentro del presupuesto. Por D-29, se suma la línea telefónica real con Twilio.

## Consecuencias

Auditoría por etapa y plantillas para lo numérico. Los proveedores y el transporte en la nube quedan sujetos a la medición del spike S1.
