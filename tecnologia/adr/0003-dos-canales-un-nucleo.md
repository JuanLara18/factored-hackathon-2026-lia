# ADR 0003: Dos canales, un núcleo

- **Estado:** firme
- **Decisión de origen:** D-17 (`presidencia/decisiones.md`)
- **Principio que la guía:** P4, P12

## Contexto

El 84,8% de los contactos del dataset es telefónico y los canales digitales son el 15% (revisión 05). La presidencia decidió atender por chat y por voz.

## Opciones consideradas

Solo chat; solo voz.

## Decisión

LATAM Bank atiende por chat y por voz como dos superficies del mismo motor. Ninguna superficie decide, el estado del caso viaja entre canales y un caso empezado en chat se retoma por voz sin repetir preguntas ni acciones.

## Consecuencias

Las mismas decisiones en ambos canales. Obliga a que el estado y las llaves de idempotencia sean independientes del canal, que es lo que prueba el spike S4 (ADR 0009).
