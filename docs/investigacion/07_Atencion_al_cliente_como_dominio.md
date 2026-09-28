# Investigación 7: la atención al cliente como dominio completo

**Pregunta:** el chatbot es una pieza de algo mucho más grande. ¿Cómo funciona un contact center
bancario como operación, qué mide, dónde se va el costo, y en qué puntos de esa operación la IA
aporta más que "responder chats"?

**Hallazgo central:** el valor más grande no está en contestar más rápido sino en **no generar
el contacto**. Entre el 40% y el 60% de la demanda de un contact center es **demanda por falla**:
el cliente llama porque el banco hizo algo mal o no le avisó. Y donde la IA generativa tiene
evidencia causal sólida no es reemplazando al agente, sino **asistiéndolo** (+14% de
productividad, +34% en los novatos).

> **Nota del 26 de septiembre de 2026, tras la [auditoría del dataset](13_Auditoria_del_dataset.md):** el dataset trae los campos de la sección 1, pero `was_escalated` no tiene señal y el NPS está truncado entre 2 y 7 (no hay promotores); la línea base de negocio se construye con esas advertencias.

---

## 1. Cómo se mide un contact center bancario

| Métrica | Qué es | Referencia en banca |
|---|---|---|
| **FCR** (resolución en primer contacto) | se resolvió sin volver a contactar | meta 70 a 80%; servicios financieros suelen quedar en **65 a 78%**; solo 5% de los centros supera 80% |
| **AHT** (tiempo medio de gestión) | conversación + espera + trabajo posterior | **4 a 6 minutos**, más en fraude |
| **Nivel de servicio** | % de contactos atendidos en X segundos | **80/20** (80% en 20 s), hoy se empuja a 90/15 |
| **Abandono** | cuelga antes de ser atendido | aceptable **2 a 5%** |
| **CSAT, NPS, CES** | satisfacción, recomendación, esfuerzo | CSAT > 80% |
| **Costo por contacto** | por canal | voz **US$7 a 14**, chat **3 a 7**, correo 2 a 5, **bot 0,03 a 0,15** |

([Bluetweak](https://bluetweak.com/blog/call-center-kpi-benchmarks/),
[Plivo](https://www.plivo.com/blog/contact-center-statistics-benchmarks-2025/))

**El dataset trae casi todas:** `was_resolved` (FCR), `duration_seconds` y `wait_time_seconds`,
`was_escalated`, `requires_followup`, sentimiento, y encuestas CSAT, NPS y CES en
`satisfaction_surveys`. Se puede reconstruir **la línea base de negocio** del flujo elegido.

**La diferencia de costo es de dos órdenes de magnitud** (US$10 contra US$0,10), y por eso el
negocio empuja la contención. Klarna y Commonwealth Bank (investigación 1) muestran lo que pasa
cuando se optimiza eso solo.

## 2. Demanda por falla: el concepto que cambia el problema

**John Seddon** acuñó *failure demand* observando **bancos** en los años ochenta: al mover el
trabajo telefónico de las sucursales a los call centers, la demanda explotó. Distingue:

- **demanda de valor**: lo que el cliente quiere hacer (pedir un producto, hacer una consulta
  genuina);
- **demanda por falla**: lo que el cliente pide porque **el banco falló** (no le avisó, le cobró
  mal, la app no funcionó, no le resolvió la primera vez).

En un contact center típico la demanda por falla es **40 a 60%**, y en el sector público llega al
**80%** ([Wikipedia](https://en.wikipedia.org/wiki/Failure_demand),
[Call Centre Helper](https://www.callcentrehelper.com/failure-demand-a-technique-to-reduce-cost-and-improve-the-customer-experience-91527.htm)).

**Implicación para el reto:** automatizar la respuesta a demanda por falla **es automatizar la
disculpa**. El criterio 1 del enunciado pide analizar motivos de contacto y restricciones
operativas: clasificar cada motivo del dataset como **valor o falla** es un análisis poco común y
muy defendible, y apunta a dos palancas distintas:

| Tipo de demanda | Palanca |
|---|---|
| Falla recurrente (cobros duplicados, caídas de la app) | **arreglar la causa** y **avisar proactivamente**; el agente de IA la contiene mientras tanto |
| Falla por falta de información ("¿qué es este cargo?") | **explicar mejor en el origen** (descriptores claros) y responder automáticamente |
| Valor (disputa genuina, fraude) | **resolverla bien** en el primer contacto: ahí la IA vale |

## 3. Lo proactivo: evitar el contacto

Un mensaje oportuno reemplaza un contacto que el cliente iba a hacer de todos modos: aviso de
compra negada con la razón, alerta de cargo grande, confirmación de transferencia, estado de un
reclamo abierto ([Latinia](https://latinia.com/en/resources/reduce-call-volume-banking-call-center)).
Los estudios de proveedores reportan caídas de **40 a 70%** en consultas de estado, cifras que hay
que leer con cuidado pero que apuntan en una dirección clara.

Bank of America envió **13.300 millones de alertas proactivas** en 2025 y atribuye a ellas buena
parte de la reducción de pérdidas por fraude (investigación 1).

**Idea encajable:** el mismo modelo que clasifica el motivo del contacto puede usarse **al revés**:
dado el estado del cliente (compra negada hace 10 minutos, reclamo abierto con SLA a punto de
vencer), **predecir que va a contactar y por qué**, y abrir la conversación con la respuesta.
Con el dataset es medible: ¿las interacciones están precedidas por eventos observables en
`transactions`, `digital_events` o `complaints`?

## 4. Los canales, y por qué en LATAM el canal es WhatsApp

- Más del **90%** de los usuarios de internet en Brasil, México, Colombia y Argentina usan
  WhatsApp; **76 a 80%** interactúa con empresas por ahí (Brasil 80%, México 78%, Colombia 76%)
  ([Aurora Inbox](https://www.aurorainbox.com/en/2026/03/05/whatsapp-business-latam-adoption/)).
- La banca y las fintech son de los sectores que más lo usan; **WhatsApp Pay** ya opera en Brasil
  con Pix y se expande a México y Colombia.
- La confianza en WhatsApp supera a la del correo corporativo
  ([Greenbook](https://www.greenbook.org/insights/focus-on-latam/why-latin-american-consumers-trust-whatsapp-more-than-corporate-emails)),
  lo que es un arma de doble filo: **es también el canal preferido de los estafadores**
  (investigación 6, suplantación de Bre-B y SPEI).

**Implicación:** diseñar para mensajería **asíncrona** (el cliente responde horas después, la
sesión expira, cambia de dispositivo) y no solo para chat en vivo. Es exactamente el caso de
**sesión expirada** que pide el enunciado.

## 5. Dónde entra la IA en la operación (más allá del bot)

| Punto | Qué hace | Evidencia |
|---|---|---|
| **Asistencia al agente** | sugiere respuestas, busca la política, resume | **la más sólida**: +14% de productividad, **+34% en novatos**, mejor sentimiento del cliente, menos rotación ([Brynjolfsson, Li y Raymond, QJE 2025](https://academic.oup.com/qje/article/140/2/889/7990658), 5.179 agentes, diseño cuasiexperimental). EricaAssist de Bank of America: casi un minuto menos por llamada |
| **Resumen y trabajo posterior** | escribe la nota del caso al cerrar | reduce la parte "posterior" del AHT |
| **QA automático** | califica el **100%** de las interacciones contra la rúbrica, en lugar del 1 a 2% que revisa un humano ([Observe.AI](https://www.observe.ai/post-interaction/auto-qa), [MaestroQA](https://www.maestroqa.com/features/auto-qa)) | útil para cumplimiento: ¿se leyó la divulgación? ¿se autenticó? |
| **Enrutamiento** | manda cada contacto a la cola o al agente correcto | reduce transferencias internas |
| **Analítica de motivos** | tópicos y tendencias en transcripciones | detecta **demanda por falla** emergente (una caída, un cobro mal aplicado) |
| **Autoservicio** | el bot | la de mayor riesgo y la que más se publicita |
| **Pronóstico y planificación** (WFM) | cuántos agentes por intervalo | **Erlang C** con la tasa de desvío como parámetro nuevo |

**Sobre WFM:** el dimensionamiento clásico (Erlang C) es no lineal: pasando el ~85% de ocupación
hacen falta desproporcionadamente más agentes para sostener el nivel de servicio
([DEV](https://dev.to/gamlin/workforce-management-for-call-centers-erlang-c-schedule-adherence-and-the-forecasting-math-that-keeps-you-staffed)).
Cuando un bot desvía contactos, **se lleva los fáciles** y deja a los humanos los difíciles: el
AHT humano **sube**. Un análisis honesto de ahorro tiene que modelar eso (el enunciado pide
separar ahorros proyectados de mediciones). Es exactamente lo que Commonwealth Bank no hizo.

## 6. El agente humano como usuario del sistema

El enunciado habla del traspaso, pero el agente humano es **un usuario** del sistema, no un
destino. Tres cosas que la operación real exige:

1. **Que no tenga que repetir preguntas**: la métrica de repetición (investigación 2).
2. **Que pueda confiar en lo que recibe**: hechos verificados separados de interpretación.
3. **Que su corrección vuelva al sistema**: si el humano reclasifica el motivo o corrige el caso,
   eso es una **etiqueta nueva** para el componente aprendido. Es el ciclo de retroalimentación
   que Nubank usa para iterar.

## 7. Qué se lleva el diseño

1. **Analizar el motivo de contacto como valor o falla**, no solo por volumen. Es el criterio 1
   del enunciado hecho con una lente que casi nadie usa.
2. **La línea base de negocio sale del dataset**: FCR, AHT, escalamiento y satisfacción del motivo
   elegido.
3. **El sistema puede tener dos caras**: autoservicio para el cliente y **asistencia al agente**
   con el mismo motor. La segunda tiene la evidencia más fuerte y el menor riesgo; mostrarla
   aunque sea como vista del traspaso suma mucho.
4. **Lo proactivo como extensión**: si el dataset lo permite, predecir el contacto antes de que
   ocurra.
5. **Asíncrono y WhatsApp** como supuesto de canal para LATAM.
6. **Ahorros con el efecto de selección**: si el bot se lleva lo fácil, el AHT humano sube.

## Fuentes principales

- [Brynjolfsson, Li y Raymond, *Generative AI at Work*, QJE 2025](https://academic.oup.com/qje/article/140/2/889/7990658)
- [Failure demand](https://en.wikipedia.org/wiki/Failure_demand)
- [Benchmarks de KPIs, Bluetweak](https://bluetweak.com/blog/call-center-kpi-benchmarks/)
- [WhatsApp Business en LATAM](https://www.aurorainbox.com/en/2026/03/05/whatsapp-business-latam-adoption/)
- [Erlang C y WFM](https://dev.to/gamlin/workforce-management-for-call-centers-erlang-c-schedule-adherence-and-the-forecasting-math-that-keeps-you-staffed)
- [Latinia, reducir llamadas en banca](https://latinia.com/en/resources/reduce-call-volume-banking-call-center)
