# ADR 0009: Spike S4, retoma de chat a voz sin repetir la acción

- **Estado:** cerrado con resultado positivo (TEC-0.4); falta el acta del Comité de Plataforma
- **Origen:** D-11, D-17, D-20 y D-23; definición de Tecnología, secciones 2.6.4 y 2.6.5
- **Principio que la guía:** P4, P12

## Pregunta

Un caso persistido en Postgres que empezó en chat y se retoma por voz, ¿ejecuta una acción ya hecha por segunda vez?

## Método

Código en `tecnologia/src/latam_tecnologia/motor/retoma.py` (núcleo puro) y `servicios/almacen.py` (memoria y Postgres), con tipos de `latam_comun.dominio`.

- La llave del efecto es el SHA-256 de conversación, número de transición, tipo de efecto y recurso. No incluye el canal.
- `ejecutar_una_vez` reserva la llave con `INSERT ... ON CONFLICT DO NOTHING`; solo quien la crea ejecuta. Quien pierde la reserva devuelve la `AccionVerificada` guardada, o falla con `EfectoIncierto` si el intento anterior no terminó.
- `retomar` exige una sesión propia del canal nuevo, del mismo cliente, vigente y con `acr2`, y entrega un resumen con las acciones hechas como hechos verificados.

## Guion reproducible

`uv run pytest tecnologia/tests -q` (con Docker para la variante de Postgres, que se omite si no está):

1. Se crea la conversación en chat y se bloquea la tarjeta con confirmación del canal chat: el ejecutor corre una vez.
2. Se retoma por voz de teléfono con una sesión `acr2`: el resumen lista el bloqueo ya hecho.
3. Por voz el motor pide de nuevo el mismo bloqueo: se devuelve la misma `AccionVerificada` y el ejecutor no corre otra vez.

## Resultado

Un solo efecto con la misma llave, en memoria y contra Postgres 16 real (testcontainers). Se rechaza la retoma de otro cliente, con nivel `acr1` o con sesión vencida, y una confirmación de otra acción no ejecuta nada.

## Límites del spike y siguiente paso

- Sin transacción entre el efecto externo y su registro: si el proceso muere entre la reserva y `completar_efecto`, la llave queda `en_curso` y el motor lanza `EfectoIncierto`. Falta la reconsulta con la misma llave y la cabecera `Idempotency-Key` hacia el servicio (R-TEC-51 y R-TEC-53), que llega con TEC-2 y TEC-3.
- No invalida aún las confirmaciones pendientes del canal anterior (2.6.5, punto 4).
- Usa `psycopg` síncrono y un esquema mínimo; la definición prevé SQLAlchemy asíncrono, asyncpg y Alembic.
