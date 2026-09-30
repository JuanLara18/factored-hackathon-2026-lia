# Hallazgos de backend (QA web, 30 sep 2026)

Para el agente que tiene `tecnologia/src`. Probado contra https://latam-chat-47808508188.us-central1.run.app.

## 1. `POST /api/banca/tarjetas/{producto_ref}/bloqueo` responde 400 `no_es_tarjeta` para toda tarjeta real

- Repro: `ingresar` con `{"indice":0}`, `GET /api/banca/resumen`, y `POST .../tarjetas/prod_6257d555d85a10c6d37b/bloqueo` con `{"confirmo":true}`.
- Esperado: 200 `{estado:"bloqueada", ya_estaba:false}`.
- Actual: 400 `{"error":"no_es_tarjeta"}`. `banca/api.py` compara `"card" not in producto.tipo.lower()`, pero `tipo` llega como texto
  en español (`"Tarjeta Crédito"`, `"Tarjeta Débito"`), no como código (`credit_card`) como dice `API_BANCA.md`.
- Efecto: el botón "Bloquear tarjeta" de la banca no puede funcionar en producción (y la interfaz ni siquiera lo ofrecía, ver QA_2026-09-30.md).
- Propuesta: aceptar `tarjeta` o `card` tras normalizar tildes, o devolver `tipo` como código estable además de `etiqueta`.

## 2. `resumen` devuelve `saldo` y `limite` en `null` para todos los productos de los 6 clientes

- Las tarjetas y cuentas de la banca muestran "Sin saldo para mostrar". El contrato lo permite, pero para la demo se ven vacías.

## 3. `POST /api/agui` a veces termina 200 sin ningún evento de texto, ficha ni interrupción (primer turno de "No la reconozco")

- Visto 1 de 5 corridas de la ficha inicial; además una vez respondió "No pude completar la acción" en el primer turno (llamada malformada de Gemini 2.5, ya conocida).
- El widget ahora muestra el aviso de falla en ese caso, pero conviene que el servidor emita siempre un `RUN_ERROR` o un texto.
