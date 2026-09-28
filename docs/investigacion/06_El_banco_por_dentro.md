# Investigación 6: el banco por dentro (disputas, fraude y core)

**Pregunta:** ¿qué pasa dentro del banco cuando un cliente dice "yo no hice esta compra"? ¿Qué
sistemas, qué equipos, qué plazos y qué redes intervienen? Y ¿cómo opera el fraude, que es el
contexto de casi todo lo que llega al servicio al cliente?

**Hallazgo central:** la conversación con el cliente es **la punta** de un proceso largo. Una
disputa pasa por la red de tarjetas, el adquirente y el comercio, con plazos que se cuentan en
meses; el fraude se decide en milisegundos en la autorización, y el servicio al cliente recibe
sus errores (falsos positivos) y sus fallas (lo que no se detectó). **Un agente de atención que
entienda este proceso puede hacer la recepción bien hecha, que es lo que más valor tiene
aguas abajo.**

---

## 1. Anatomía de una disputa con tarjeta

### Los actores

```
Tarjetahabiente ─► Banco emisor ─► Red (Visa, Mastercard) ─► Adquirente ─► Comercio
     (cliente)     (nuestro banco)                          (banco del comercio)
```

El emisor es quien atiende al cliente y quien **inicia** la disputa ante la red. Lo que el agente
recoja en la conversación se vuelve la evidencia del emisor.

### Visa Claims Resolution (VCR)

Desde 2018 Visa agrupa los motivos en **cuatro categorías**, y cada una sigue un flujo distinto
([Chargebacks911](https://chargebacks911.com/chargeback-reason-codes/visa/),
[Adyen](https://docs.adyen.com/risk-management/chargeback-guidelines/visa-chargebacks),
[Chargeflow](https://www.chargeflow.io/blog/visa-chargeback-dispute-rules-fees-time-limit)):

| Código | Categoría | Flujo | Ejemplo |
|---|---|---|---|
| **10.x** | **Fraude** | **asignación**: Visa decide automáticamente con sus datos | "no reconozco esta compra" |
| 11.x | Autorización | asignación | cobro sin autorización válida |
| 12.x | Error de procesamiento | **colaboración**: emisor y adquirente presentan su versión | cobro duplicado, monto incorrecto, moneda equivocada |
| **13.x** | **Disputa del consumidor** | colaboración | no recibió el producto, cancelé y me cobraron |

**Plazos de Visa:** el emisor tiene **120 días** desde el procesamiento para abrir una disputa por
fraude (75 por autorización); el comercio responde hasta el día 18 (asignación) o 24
(colaboración); el adquirente tiene 30 días para la **prearbitraje**. De punta a punta, **31 a 100
días**.

**Implicación directa para el agente:** "no reconozco un cargo" **no es una sola intención**. Hay
que distinguir, con preguntas, entre:
- **fraude** (nunca la hice, perdí la tarjeta, me clonaron) → 10.x, y **bloquear la tarjeta ya**;
- **error de procesamiento** (sí compré, pero me cobraron dos veces o de más) → 12.x;
- **disputa comercial** (compré, no llegó o lo devolví) → 13.x, que suele exigir haber
  intentado resolver con el comercio primero;
- **no la recuerda pero es suya** (el nombre del comercio en el extracto no coincide con la
  marca) → no es disputa: se resuelve explicando. **Este es el caso más barato y más frecuente**
  de resolver automáticamente.

La **clasificación correcta del motivo** determina el flujo, los plazos y la evidencia. Es un
lugar natural para el componente aprendido, y es verificable contra el estado final.

### Fraude de primera parte ("friendly fraud")

El propio cliente disputa algo que sí hizo. Visa lo ataca con **Compelling Evidence 3.0** (desde
2023, automatizado en octubre de 2025): el comercio demuestra con **dos transacciones previas no
disputadas** con el mismo dispositivo, IP o dirección que el cliente sí participó
([Chargeflow](https://www.chargeflow.io/blog/visa-compelling-evidence-3-0-explained)). Mastercard
tiene **First-Party Trust**, que comparte esos datos **en el momento de la compra**.

**Implicación:** el historial del cliente (compras previas al mismo comercio, disputas previas,
`is_repeat_complainer` en el dataset) es **evidencia**, y FraudBench mostró que los agentes
fallan justo aquí (2 a 7 de 9 casos). El agente **no acusa**: registra la contradicción y escala
con evidencia.

### Crédito provisional

En EE. UU., la **Regulation E** obliga, si la investigación no termina en **10 días hábiles**, a
abonar provisionalmente el monto y permite extender hasta 45 o 90 días
([Canarie](https://www.canarie.ai/blog/regulation-e-error-resolution-timeframes)). En **México**
hay una regla análoga: **reporte en 48 horas = abono provisional** al segundo día hábil
(investigación 3). Los proveedores de automatización de disputas (Pega Smart Dispute, Quavo,
Finboa) **codifican estos plazos como reglas**, no como texto.

## 2. Pagos inmediatos: la disputa que no se puede revertir

Una transferencia inmediata, a diferencia de la tarjeta, **no tiene contracargo**. El dinero sale
en segundos. Es donde más crece el fraude por **ingeniería social** (el cliente autoriza el pago
engañado: *APP fraud*).

| País | Sistema | Estado y fraude |
|---|---|---|
| **Brasil** | **Pix** | 79.800 millones de transacciones en 2025; **MED 2.0** (Resolución BCB 493 de 2025), obligatorio desde febrero de 2026: **rastrea el dinero a través de cadenas de cuentas**, bloquea la llave Pix del defraudador y tiene **botón de contestación en la app** desde octubre de 2025. La recuperación por MED 1.0 se había estancado en ~9% ([ClearingPost](https://clearingpost.com/insights/bcb-pix-med-2-fraud-recovery-mandatory-2026/), [PagBrasil](https://www.pagbrasil.com/blog/pix/med-2-0/)) |
| **Colombia** | **Bre-B** | operación masiva desde el **6 de octubre de 2025**, 227 entidades, más de 84 millones de llaves; olas de *smishing* que suplantan notificaciones de Bre-B ([Cambio](https://cambiocolombia.com/economia/articulo/2025/10/bre-b-entra-en-operacion-masiva-mas-de-84-millones-de-llaves-ya-estan-activas/), [Infobae](https://www.infobae.com/colombia/2026/08/05/alerta-por-fraude-digital-en-bogota-asi-suplantan-la-plataforma-de-bre-b-a-traves-de-mensajes-de-texto/?outputType=amp-type)) |
| **México** | **SPEI, CoDi, DiMo** | desde octubre de 2025 el **MTU**, límite diario por usuario; CONDUSEF registró **67.651 reclamaciones por posible fraude** en 2025; estafas de "transferencia retenida" ([Infobae](https://www.infobae.com/mexico/2025/09/26/alerta-condusef-este-es-el-fraude-con-transferencias-spei-que-aumenta-en-mexico/)) |
| Reino Unido (referencia) | Faster Payments | reembolso obligatorio del APP fraud desde octubre de 2024, costo **compartido 50/50** entre banco emisor y receptor, tope de £85.000 ([PSR](https://www.psr.org.uk/publications/policy-statements/ps247-faster-payments-app-scams-reimbursement-requirement-confirming-the-maximum-level-of-reimbursement/)) |

**Implicación:** en una transferencia no reconocida **el tiempo es todo**. Lo único que puede
recuperar el dinero es bloquear rápido la cuenta receptora. El flujo de atención debe **detectar
urgencia** (transferencia reciente, cliente que dice "me llamaron del banco") y escalar
**inmediatamente** a fraude, no poner al cliente a llenar un formulario.

## 3. Cómo opera el fraude en el banco

### En la autorización (milisegundos)

La decisión de aprobar o negar una compra se toma dentro de un presupuesto de **~100 ms**, y el
puntaje de fraude en **10 a 50 ms**. Los sistemas más grandes califican **700.000 transacciones
por segundo** con almacenes de características en tiempo real
([Redis](https://redis.io/blog/real-time-fraud-detection/)). La arquitectura típica (FIS, entre
otros) combina tres cosas ([FIS](https://www.fisglobal.com/products/total-issuing)):

1. **Modelos de ML** que dan un puntaje de riesgo (el `fraud_score` del dataset).
2. **Reglas definidas por el banco** (montos, países, comercios de riesgo, velocidad).
3. **Perfiles** del tarjetahabiente (lo normal para él).

Salidas: aprobar, negar, o **aprobar con desafío** (OTP, 3-D Secure en compras en línea).

### En la operación (horas a días)

Lo que el motor marca pasa a **colas de analistas** en un sistema de **gestión de casos**, que
confirman con el cliente (llamada o notificación "¿reconoce esta compra?"), bloquean,
reemiten tarjetas y alimentan de vuelta al modelo con la etiqueta confirmada.

**El servicio al cliente vive en medio de las dos puntas:**
- recibe los **falsos positivos**: "me negaron la compra y sí era yo", "me bloquearon la tarjeta";
- recibe los **falsos negativos**: "hay una compra que no hice";
- y es **vector de ataque**: la ingeniería social contra los agentes humanos.

### El contact center como superficie de ataque

[Pindrop, 2025](https://www.pindrop.com/research/report/voice-intelligence-security-report/)
(más de mil millones de llamadas): los ataques con **voz sintética** a contact centers pasaron de
uno cada dos días en 2023 a **siete por día** en 2024 (+1.300%); en bancos, la voz sintética
creció **149%**; la IA impulsa el **42,5%** de los intentos de fraude. El atacante llama para
**tomar la cuenta**: cambiar el teléfono, el correo o pedir una tarjeta nueva.

**Implicación:** un agente de IA es **otro agente** al que se le puede hacer ingeniería social,
más paciente y más consistente que un humano, pero igual de explotable si su criterio vive en el
prompt. **Los cambios de datos de contacto son la acción más peligrosa del servicio**, porque
preceden a la toma de cuenta: deberían exigir el nivel más alto de autenticación o no estar en el
alcance del agente.

### Mulas de dinero

Cuentas que reciben y mueven el dinero del fraude. [BioCatch](https://www.biocatch.com/blog/the-value-of-precision-in-disrupting-mule-networks):
casi **2 millones** de cuentas mula documentadas en 257 instituciones de 21 países en 2024;
aumento de **168%** en el primer semestre de 2025 en EE. UU.; y en LATAM, **155% más intentos de
estafa**. Se detectan por **redes**: flujos entre cuentas, dispositivos compartidos,
comportamiento. Es el uso natural de los **grafos** (investigación 9). FraudBench midió que los
agentes defienden **1 o 2 de 9** escenarios de mulas: es lo más difícil.

## 4. Dónde vive cada cosa: el core y sus vecinos

Un banco moderno tiene tres capas: **core** (cuentas, saldos, transacciones, intereses),
**middleware y APIs** (integración con fraude, CRM, apps) y **canales** (app, web, cajero, contact
center) ([Vacuumlabs](https://vacuumlabs.com/articles/how-core-banking-system-works/)).

**BIAN** (*Banking Industry Architecture Network*) es el modelo de referencia de la industria:
descompone el banco en **dominios de servicio** independientes, agrupados en áreas como
**Ventas y Servicio** (gestión de clientes, **gestión de casos**), **Operaciones y Ejecución**
(cuentas, pagos) y **Riesgo y Cumplimiento** ([BIAN](https://en.wikipedia.org/wiki/Banking_Industry_Architecture_Network)).
Los dominios relevantes para este reto, con nombres BIAN: *Customer Case Management*, *Card
Case*, *Payment Order*, *Fraud Diagnosis*, *Customer Relationship Management*, *Party
Authentication*.

**Implicación:** nombrar las herramientas del agente **como dominios BIAN** (una API de casos,
una de tarjetas, una de autenticación) muestra que el diseño respeta cómo está hecho un banco y
que el prototipo se conecta a sistemas reales cambiando adaptadores, no la lógica.

## 5. El mapa completo de una disputa por "no reconozco un cargo"

| Paso | Quién | Qué hace | Dónde puede ayudar la IA |
|---|---|---|---|
| 1. Contacto | cliente, agente | describe el problema | entender, **clasificar el motivo** (fraude, error, comercial, no lo recuerda) |
| 2. Autenticación | agente, identidad | verifica que es el titular | **no la IA**: servicio de identidad |
| 3. Identificar la transacción | agente, core | encontrar el cargo entre los movimientos | búsqueda por monto, fecha, comercio; **explicar descriptores confusos** |
| 4. Contención | agente, fraude | si es fraude: **bloquear tarjeta ya**; si es transferencia reciente: escalar urgente | detectar urgencia; confirmar con el cliente |
| 5. Radicación | agente, casos | crear el caso con motivo, monto, evidencia, hora | armar el caso completo y **verificarlo** |
| 6. Crédito provisional | reglas | según país y plazo | **reglas**, no IA |
| 7. Investigación | back office, red | VCR, respuesta del comercio, prearbitraje | resumir evidencia para el analista |
| 8. Resolución | back office | a favor o en contra, reversa o no | explicar la decisión con sus fuentes |
| 9. Comunicación | agente | informar al cliente | redactar, con plazos reales |

**El reto de la hackatón es sobre todo los pasos 1 a 6**, con 7 a 9 como contexto y traspaso. Es
un alcance acotado, con verificación de estado final clara (el caso existe, con el motivo y monto
correctos; la tarjeta está bloqueada) y con casos de escalamiento naturales (fraude en curso,
monto alto, fraude de primera parte, transferencia inmediata).

## Fuentes principales

- [Visa Claims Resolution, Chargeflow](https://www.chargeflow.io/blog/visa-chargeback-dispute-rules-fees-time-limit) y [códigos de motivo](https://chargebacks911.com/chargeback-reason-codes/visa/)
- [Compelling Evidence 3.0](https://www.chargeflow.io/blog/visa-compelling-evidence-3-0-explained)
- [Regulation E, plazos](https://www.canarie.ai/blog/regulation-e-error-resolution-timeframes)
- [Pix MED 2.0](https://clearingpost.com/insights/bcb-pix-med-2-fraud-recovery-mandatory-2026/)
- [UK PSR, APP fraud](https://www.psr.org.uk/publications/policy-statements/ps247-faster-payments-app-scams-reimbursement-requirement-confirming-the-maximum-level-of-reimbursement/)
- [Pindrop 2025](https://www.pindrop.com/research/report/voice-intelligence-security-report/)
- [BioCatch, mulas](https://www.biocatch.com/blog/the-value-of-precision-in-disrupting-mule-networks)
- [Redis, fraude en tiempo real](https://redis.io/blog/real-time-fraud-detection/)
