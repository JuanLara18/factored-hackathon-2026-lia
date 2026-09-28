# Investigación 14 (VP Clientes): la conversación de disputa, el traspaso y el canal

**Cara:** VP Clientes ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)). **Preguntas:** ¿cómo se
diseña una conversación de "no reconozco este cargo" que resuelva sin crear disputas innecesarias?
¿Qué hace bueno un traspaso? ¿Qué impone el canal (WhatsApp) al diseño? ¿Qué hace el experto humano
en un banco donde la IA atiende primero?

**Hallazgo central:** la mayor parte de los "no reconozco este cargo" **no son fraude sino
confusión**, y la industria ya lo ataca **enriqueciendo la transacción** en el momento de la
consulta, antes de que exista disputa. El camino más barato y más frecuente (R1, explicar) es
también el que más valor tiene, y depende de datos, no de elocuencia del modelo.


> **Nota del 26 de septiembre de 2026, tras la [revisión del enunciado](../Diseno/05_Cobertura_del_enunciado.md):** el dataset solo trae 24 comercios con nombres genéricos y el 1,9% de los pares cliente y comercio se repite, así que la ficha de la transacción necesita un **directorio de comercios del equipo** (razón social, descriptor, marca), declarado como tal, y el escenario de compras previas en el mismo comercio se construye a propósito. Además, solo 7 especialistas en fraude hablan portugués: el traspaso urgente en portugués necesita cola con espera declarada ([05 de diseño](../Diseno/05_Cobertura_del_enunciado.md)).

---

## 1. La confusión es el caso principal

- El 45% de las disputas nace de cargos que el cliente no reconoce en el extracto, y el 76% de los
  clientes acude primero al banco y no al comercio ([Chargeback.io](https://www.chargeback.io/blog/what-is-a-billing-statement-descriptor)).
- El 79% de los consumidores dice haber reportado alguna vez una transacción no reconocida a su banco
  (Ethoca, 2024). El fraude "amistoso" puede ser hasta el 80% del fraude con tarjeta
  ([Chargeback Gurus](https://www.chargebackgurus.com/blog/understanding-ethoca-consumer-clarity)).
- La respuesta de las redes: **Ethoca Consumer Clarity** (Mastercard) y **Visa Order Insight** le
  entregan al emisor, **en el momento de la consulta**, nombre comercial, logo, recibo detallado,
  contacto y estado de reembolso, para que el cliente reconozca la compra antes de disputarla
  ([Ethoca](https://www.ethoca.com/ethoca-consumer-clarity), [Solidgate](https://solidgate.com/blog/ethoca-consumer-clarity-guide/)).
- El descriptor en el extracto tiene 5 a 22 caracteres y muchas veces no coincide con la marca
  ([Wikipedia](https://en.wikipedia.org/wiki/Billing_descriptor)).

**Implicación:** la herramienta más valiosa del flujo no es "radicar disputa" sino **"ficha de la
transacción"**: comercio, categoría, ciudad, canal, fecha y hora del evento, monto y moneda, y
compras previas del cliente en ese comercio. Con el dataset se construye desde `transactions`
(comercio presente en el 23% de las filas, categoría del comercio, ciudad, canal). Es nuestra versión
sintética de Consumer Clarity y se declara como tal.

## 2. Principios de diseño conversacional para este flujo

Reunidos de la industria bancaria ([AIMultiple](https://aimultiple.com/banking-chatbot),
[Gradient Labs](https://gradient-labs.ai/guides/best-ai-chatbots-for-banks)) y de lo ya investigado
(investigaciones 2 y 6):

1. **Primero ubicar la transacción, después clasificar.** Nadie puede decir si es fraude sin saber
   cuál cargo es.
2. **Una pregunta a la vez**, y con opciones cuando hay varias transacciones posibles (enmascaradas).
3. **Enseñar la ficha antes de preguntar "¿la reconoce?"**: es el momento en que se resuelve R1.
4. **No confundir bloquear con disputar.** El cliente no debe salir creyendo que radicó una disputa
   cuando solo se bloqueó la tarjeta ([Gradient Labs](https://gradient-labs.ai/guides/best-ai-chatbots-for-banks)).
   El cierre dice explícitamente qué se hizo y qué no.
5. **Confirmar antes de actuar**, con el monto y la transacción leídos de la base, no del texto.
6. **Plazos reales** de la política del país, con su fuente.
7. **Humano disponible en cualquier turno**, sin resistencia (P7).
8. **Nunca acusar**: si el historial contradice al cliente (compras previas no disputadas en el
   mismo comercio), se registra como evidencia y se escala (E3).

## 3. El traspaso

- Las llamadas transferidas tienen **12% menos CSAT** que las no transferidas (SQM Group, más de 500
  centros); el traspaso "tibio", con contexto, cierra esa brecha, y los agentes que reciben un caso
  con contexto de la IA gestionan en **4,1 minutos menos** que en un traspaso en frío (cifras de
  proveedor, [Fini](https://www.usefini.com/guides/ai-voice-agents-warm-handoff-human-agents),
  [Bluetweak](https://www.bluetweak.com/blog/ai-to-human-handoff)).
- "Tener que repetirme" está entre los primeros motivos para abandonar una marca.
- [*Structured State Reconciliation for Human-AI Task Handover*](https://arxiv.org/abs/2608.28907)
  (2026): convertir registros del sistema y observaciones en un **estado tipado con procedencia**,
  reconciliar hechos y detectar conflictos, conserva tanta utilidad como resumir todo con un LLM de
  punta a punta pero con **mucha menos información falsa**, y renderizar según la tarea es más
  eficiente por token que volcar todo.

**Implicación:** respalda la decisión de tipos (investigación 8): el paquete de traspaso es un
**objeto tipado con procedencia** (hechos verificados, interpretaciones, acciones, conflictos,
preguntas abiertas), y el texto para el humano se **renderiza** desde ese objeto, no lo escribe el LLM
libremente. Campo nuevo que sale de este artículo: **conflictos detectados** (lo que dice el cliente
contra lo que dice la base).

## 4. El canal: WhatsApp impone reglas de diseño

- Al escribir el cliente se abre una **ventana de 24 horas** en la que se responde libremente; fuera
  de ella solo se pueden enviar **plantillas aprobadas** por Meta (aprobación de 24 a 48 horas por
  plantilla) ([Meta](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages),
  [smsmode](https://www.smsmode.com/en/whatsapp-business-api-customer-care-window-ou-templates-comment-les-utiliser/)).
- Existen **plantillas de autenticación** para OTP.
- **Desde el 1 de octubre de 2026** las respuestas dentro de la ventana, gratuitas hasta el 30 de
  septiembre, se cobran por mensaje ([SleekFlow](https://sleekflow.io/en-us/blog/whatsapp-business-price)).

**Implicaciones:**
- La **sesión expirada** del enunciado tiene una forma concreta en LATAM: el cliente vuelve después
  de 24 horas; el sistema retoma con una plantilla y reautentica (escenarios D5 y D6).
- El **costo por caso** debe incluir el costo por mensaje del canal a partir de octubre de 2026 como
  supuesto explícito (investigación 11).
- No construimos WhatsApp real: la demo usa una interfaz de chat que **simula** la ventana y las
  plantillas, documentada como tal.

## 5. El experto humano

En LATAM Bank el humano pasa de contestar a **resolver excepciones y enseñar** (O6). Lo que necesita:

| Necesidad | Cómo se atiende |
|---|---|
| No reinterrogar | paquete tipado con hechos, acciones y preguntas abiertas |
| Saber qué creer | hechos verificados separados de interpretaciones y conflictos |
| Actuar rápido en urgencias | motivo y prioridad del traspaso arriba, con la transacción y la hora |
| Corregir a la IA | su reclasificación del motivo queda registrada como **etiqueta** para el componente aprendido |

## 6. Artefactos de la VP Clientes

1. **Guion conversacional por estado** del motor de flujo (qué pregunta, qué muestra, qué confirma),
   en español y portugués.
2. **Ficha de la transacción** (contrato de datos con Datos: qué campos, de qué tabla de oro).
3. **Paquete de traspaso** tipado, con el campo de conflictos, y su vista para el experto.
4. **Política de servicio**: qué se explica, qué se ofrece, frases de cierre que distinguen bloqueo
   de disputa.
5. **Guion de la demo**: R1 (cargo reconocido al ver la ficha), un ambiguo (A2, tres transacciones
   posibles), R4 (transferencia reciente, urgencia), y el mismo caso en portugués con una compra hecha
   en Brasil.

## 7. Preguntas abiertas

- ¿Cuántas compras previas en el mismo comercio hacen falta para marcar un conflicto (E3)? Lo fija
  Gobierno como umbral de política.
- ¿La vista del experto se evalúa con humanos (muestra) o solo por completitud del esquema?
- ¿Se muestra el logo o la marca del comercio? El dataset solo trae `merchant_name`; cualquier
  enriquecimiento adicional es inventado y se declara.

## Fuentes principales

- [Ethoca Consumer Clarity](https://www.ethoca.com/ethoca-consumer-clarity) y [guía de Solidgate](https://solidgate.com/blog/ethoca-consumer-clarity-guide/)
- [Chargeback.io, descriptores](https://www.chargeback.io/blog/what-is-a-billing-statement-descriptor)
- [Gradient Labs, chatbots bancarios](https://gradient-labs.ai/guides/best-ai-chatbots-for-banks)
- [Structured State Reconciliation for Human-AI Task Handover](https://arxiv.org/abs/2608.28907)
- [Bluetweak, traspaso](https://www.bluetweak.com/blog/ai-to-human-handoff)
- [Meta, mensajes de servicio](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages) y [precios 2026, SleekFlow](https://sleekflow.io/en-us/blog/whatsapp-business-price)
