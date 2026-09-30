# Definición de la VP Clientes: servicio, conversación y operación humana

**Cara:** VP Clientes, con sus tres gerencias: Diseño conversacional de chat y voz, Operaciones de fraude y
disputas, y Calidad de servicio. **Versión:** 1 (27 de septiembre de 2026). **Estado:** primera versión, para
el desafío de Gobierno y la auditoría de completitud ([modelo operativo](../presidencia/modelo_operativo.md),
sección 7).
**Misión:** "cargo no reconocido", de la que esta cara es dueña del resultado
([organización v2](../docs/diseno/04_Organizacion_y_roles.md), sección 4).
**Se apoya en:** principios P1 a P13, decisiones D-01 a D-21, [interacciones y criterios](../docs/diseno/01_Interacciones_y_criterios.md),
[cobertura del enunciado](../docs/diseno/05_Cobertura_del_enunciado.md), [arquitectura](../docs/diseno/06_Arquitectura.md),
[hoja de ruta](../presidencia/hoja_de_ruta.md), las investigaciones 1, 2, 3, 6, 7, 13, 14, 18, 20 y 21, y las
definiciones ya escritas de [Datos](../datos/definicion.md) y [Tecnología](../tecnologia/definicion.md).

**Cómo leer este documento**

- La sección 2 son las reglas del juego del servicio, numeradas `R-CLI-nn`, cada una con su forma de
  verificación. La sección 4 continúa la numeración con los controles de seguridad, privacidad y gobierno.
- Las cifras llevan la misma etiqueta que usa Tecnología: **[V]** verificado en la fuente el 27 de septiembre
  de 2026; **[P]** cifra de proveedor o de fuente secundaria sin verificación independiente; **[S]** supuesto
  nuestro, que se reemplaza por una medición; **[A]** a confirmar, con el cómo al lado. Toda cifra de ahorro
  o de capacidad futura dice **proyección** (P3).
- Las cifras del dataset salen de la muestra auditada ([investigación 13](../docs/investigacion/13_Auditoria_del_dataset.md)
  y [revisión 05](../docs/diseno/05_Cobertura_del_enunciado.md), sección 3) y se confirman sobre el total en F1 (DAT-2).
- Los textos al cliente que aparecen aquí son la versión 1 del catálogo. La fuente de verdad será el catálogo
  versionado del repositorio (sección 3.1); si difieren, manda el catálogo aprobado y este documento se corrige.
- Los plazos por país que aparecen en ejemplos son ilustrativos: el contenido de `policy/v1` lo decide
  Gobierno con texto primario (D-13). Esta cara decide **cómo se dicen**, no **cuáles son**.
- Nada de lo escrito cambia una decisión firme. Lo que conviene cambiar o precisar se propone como
  `DP-CLI-nn` (sección 10).

---

## 1. Mandato y alcance en la misión

### 1.1 Mandato

Que el cliente resuelva su problema con un cargo que no reconoce, por chat o por voz, en español o en
portugués, sin repetir lo que ya dijo; y que, cuando interviene una persona, esa persona reciba el caso listo
para actuar. La VP Clientes es la **dueña del resultado** de la misión; IA, Datos y Tecnología aportan
capacidades y Gobierno desafía desde fuera ([04](../docs/diseno/04_Organizacion_y_roles.md), sección 4).

### 1.2 Qué decide esta cara, qué propone y qué no decide

| Tipo | Qué | Con quién |
|---|---|---|
| **Decide** | experiencia de punta a punta; guiones y plantillas al cliente; textos de los componentes de chat y su degradación a WhatsApp; registro por país; aviso de IA; diseño de voz (lectura de vuelta, rellenos, silencios, teclas); modelo de colas humanas y sus acuerdos de servicio; contenido y orden de la vista del experto; formulario de corrección; árbol de resultados; guion de la demo | consulta obligatoria a IA y a Gobierno (Protección al consumidor); Gobierno puede objetar ([modelo operativo](../presidencia/modelo_operativo.md), sección 2) |
| **Propone, otro decide** | plazos, umbrales, qué exige confirmación y con qué nivel de autenticación (Gobierno); proveedores y voces (IA); transporte, plataforma y costo técnico (Tecnología); definición oficial de métricas (Datos); gasto (Presidencia) | solicitudes `S-CLI-nn` (sección 5) |
| **No decide** | la ruta de una conversación concreta (la decide el motor con la política, P4); si una versión sale (Gobierno); qué cuenta como evidencia (Auditoría) | |

### 1.3 Alcance

| Dentro | Fuera, y por qué |
|---|---|
| Pasos 1 a 6 del mapa de una disputa ([investigación 6](../docs/investigacion/06_El_banco_por_dentro.md), sección 5): contacto, autenticación (su experiencia, no el servicio de identidad), identificación de la transacción, contención, radicación y registro del abono provisional | pasos 7 a 9 (investigación ante la red, resolución, comunicación del fallo): quedan como contexto y como destino del traspaso al back office |
| Rutas R1 a R8 y escenarios N, A, E, F, D, S, L y V de [01](../docs/diseno/01_Interacciones_y_criterios.md), en chat y en voz | un segundo flujo (P8) |
| Chat web con la semántica de WhatsApp simulada (D-19); voz por navegador y teléfono opcional (D-18) | WhatsApp real y línea telefónica real en la hackatón: ruta a producción |
| Español de México, Colombia, Argentina y neutro; portugués de un cliente con cuenta en México, Colombia o Argentina | la norma brasileña: la cuenta no está en Brasil (escenario L5) |
| Cola humana destino del traspaso, vista del experto, ingreso al mismo hilo y correcciones como etiquetas | operar un contact center real: en la hackatón los expertos son personas del equipo o un experto simulado, declarado |
| Comunicaciones del flujo: avisos, plantillas fuera de ventana, notificaciones de estado, consentimiento y accesibilidad | marketing o cualquier mensaje promocional |
| Resultados para cliente y negocio con línea base del dataset y proyección etiquetada | afirmar una mejora medida en producción (P3) |
| Ningún movimiento de dinero: el abono provisional de México solo se **registra** para el back office ([05](../docs/diseno/05_Cobertura_del_enunciado.md), punto 12) | ejecutar o prometer abonos |
| Cambio de teléfono o correo: fuera del alcance del agente (S5), con traspaso y autenticación reforzada | que la IA cambie datos de contacto |

### 1.4 Cómo aporta cada gerencia

| Gerencia | Qué entrega en esta definición | Firma |
|---|---|---|
| Diseño conversacional de chat y voz | secciones 2.2 a 2.4 y 2.8; catálogo de plantillas, rellenos y textos de componentes | revisión consultiva de `voz-del-cliente` |
| Operaciones de fraude y disputas | secciones 2.5 y 2.6; modelo de colas; vista del experto; corrección como etiqueta | escenarios E1 a E7 en F2 |
| Calidad de servicio | secciones 2.7, 2.9 y 6; guion de la demo; control de calidad de conversaciones | demo en F7 |

### 1.5 Principios que esta cara vigila en primera persona

- **P6:** lo que lee o escucha el cliente es donde un dato no verificado se vuelve daño; por eso los montos,
  plazos, estados y acciones salen de plantillas deterministas (R-TEC-76).
- **P7:** pedir una persona funciona siempre, y escalar bien no es fracasar.
- **P12:** el registro se adapta al país de la cuenta; ninguna decisión depende del acento ni de un atributo
  protegido.
- **P1 y P3:** los acuerdos de servicio de la cola y los supuestos de costo se registran antes del retenido,
  y todo ahorro se presenta como proyección.

---

## 2. Definiciones y estándares del dominio

### 2.1 Principios de servicio y términos nuevos

Ocho principios de servicio ordenan todas las reglas de esta sección:

| # | Principio de servicio | De dónde sale | Reglas que lo concretan |
|---|---|---|---|
| PS1 | Ubicar la transacción antes de clasificar, y mostrar la ficha antes de preguntar si la reconoce | investigación 14: la mayoría de los "no reconozco" son confusión | R-CLI-02, R-CLI-08 |
| PS2 | Contener primero cuando hay fraude: el bloqueo va antes de cualquier pregunta que no sea necesaria para bloquear | investigación 6: en fraude la contención se mide en minutos | R-CLI-03, R-CLI-04, R-CLI-84 |
| PS3 | Una pregunta por turno, con opciones cuando existen | investigaciones 2 y 14 | R-CLI-05, R-CLI-06, R-CLI-39 |
| PS4 | Solo se dice lo que una herramienta verificó o una regla de política establece | P6, caso Air Canada | R-CLI-24 a R-CLI-32 |
| PS5 | El cliente sale sabiendo qué se hizo, qué no, qué sigue y cuándo | investigación 14: no confundir bloqueo con disputa | R-CLI-07, R-CLI-31 |
| PS6 | Pedir una persona funciona siempre y no cuesta nada | P7; 87% de los clientes lo exige (investigación 1) | R-CLI-34, R-CLI-35, R-CLI-88 |
| PS7 | Nunca se acusa: una contradicción es evidencia para una persona | investigación 6, fraude de primera parte | R-CLI-14, R-CLI-67 |
| PS8 | El estilo se adapta al país de la cuenta; las decisiones no | P12, escenarios L1 y L6 | R-CLI-19, R-CLI-20 |

**Términos nuevos** (para el glosario común, [modelo operativo](../presidencia/modelo_operativo.md), sección 9):

| Término | Significado |
|---|---|
| Guion por estado | lo que el sistema dice, muestra y pregunta en cada estado del motor, por canal, idioma y registro |
| Plantilla crítica | texto determinista con variables tipadas para montos, fechas, plazos, estados, confirmaciones e informe de acciones |
| Registro | forma de tratamiento: usted (México, Colombia, neutro), vos (Argentina), você (portugués) |
| Relleno honesto | frase breve que se dice mientras corre una herramienta y que no afirma ninguna acción |
| Lectura de vuelta | repetición, en voz, de la acción, el objeto y el monto de la base antes de pedir el "sí" |
| Cierre que distingue | cierre en cuatro partes: hecho, no hecho, qué sigue (con plazo, norma y fecha) y cómo continuar |
| Espera declarada | rango de espera hasta una persona que el sistema informa, calculado por la cola y nunca prometido |
| Idioma alterno | oferta, a quien habla portugués, de ser atendido ya en español cuando no hay especialista en portugués |
| Modo asistente | estado del hilo en el que habla una persona y la IA solo le sugiere a esa persona |
| Compromiso comunicado | lo que se le dijo al cliente sobre esperas, plazos o próximos pasos; viaja en el paquete de traspaso |
| Corrección como etiqueta | reclasificación que registra el experto al cerrar, con procedencia, para el siguiente ciclo del componente aprendido |
| Catálogo de alternativas | lista cerrada, con fuente, de a dónde se deriva lo que está fuera de alcance (R6) |

### 2.2 Blueprint del servicio de punta a punta

El blueprint tiene cinco capas: lo que hace el cliente; lo que ve en chat; lo que oye en voz; el estado del
motor que decide (P4); y la evidencia que queda. Las dos superficies traducen y no deciden (D-17): por eso el
mismo estado tiene guion de chat y de voz, y un caso se retoma de un canal al otro en el mismo punto.

#### 2.2.1 Guion por estado del motor

Estados de [01](../docs/diseno/01_Interacciones_y_criterios.md), sección 4, con los nombres del `StrEnum` de
Tecnología. "Dice" es la intención de la plantilla; el texto exacto vive en el catálogo.

| Estado | Qué dice | Qué muestra en chat | Qué pregunta | Diferencia en voz | Nunca |
|---|---|---|---|---|---|
| `INICIO` | aviso de IA, opción de persona e invitación (2.3.8) | burbuja de aviso fija y botón permanente "Hablar con persona" | una pregunta abierta: "¿En qué le puedo ayudar?" | aviso de 12 s o menos; su primera frase no se interrumpe | pedir datos antes de saber el motivo; saludos largos |
| `COMPRENDIENDO` | acuse breve de lo entendido ("Entiendo: un cargo que no reconoce") | nada, o botones de motivo si la confianza es baja | ninguna si la confianza es alta | una frase | diagnosticar ("es fraude"); prometer |
| `ACLARANDO` | una pregunta cerrada con dos o tres opciones concretas | botones o lista | "¿Se trata de...?" con opciones | tres opciones como máximo, con teclas | dos preguntas juntas; pedir lo que una herramienta sabe |
| `AUTENTICANDO` | por qué se pide y cómo ("para ver sus movimientos necesito confirmar que es usted") | `SolicitudOtp`: campo seguro y vencimiento | el código, solo en el campo seguro | el código por teclado (DTMF) | pedir el código en voz alta o en texto libre; aceptar un documento como prueba de identidad; mostrar datos antes |
| `IDENTIFICANDO_TRANSACCION` | "Revisé sus movimientos recientes" | `FichaTransaccion` si hay una candidata; `OpcionesTransaccion` si hay de 2 a 8; si hay más, pide un filtro | "¿Es esta?" o "¿Cuál es?" | ficha breve (comercio, fecha, monto); opciones de a una o por teclas | decir que un cargo no existe si no aparece (D3, D8) |
| `EXPLICANDO` (R1) | explicación anclada: marca detrás del descriptor, estado pendiente, revertido o rechazado, conversión | ficha con marca, categoría, estado y compras previas | "¿Reconoce esta compra?" | frases cortas; ofrece repetir | abrir un reclamo que no pidió; insistir |
| `CLASIFICANDO_MOTIVO` | pregunta que distingue fraude, error y disputa comercial en palabras del cliente | botones: "No la hice", "Me cobraron de más o dos veces", "Compré y no llegó" | una sola | tres opciones con teclas 1, 2 y 3 | nombrar códigos de red; sugerir la respuesta |
| `CONTENIENDO` (R3) | propuesta de bloqueo con su consecuencia | `SolicitudConfirmacion` de bloqueo | confirmar | lectura de vuelta (2.4.4) | bloquear sin confirmación; decir que el bloqueo devuelve el dinero |
| `URGENTE` (R4) | reconoce la urgencia, inicia el traspaso ya y da la frase de seguridad | `AvisoTraspaso` con espera declarada | solo lo que ayuda mientras espera: código, cuál transferencia | mensajes de espera cada 45 a 60 s [S] | formularios; retener; prometer que se recupera el dinero |
| `CONFIRMANDO_ACCION` | resumen de la acción: verbo, objeto enmascarado, monto de la base, consecuencia | `SolicitudConfirmacion` con vencimiento de 5 minutos | confirmar, corregir o hablar con persona | lectura de vuelta; "sí" explícito o tecla 1 | tomar un texto libre como confirmación; montos del texto del cliente |
| `EJECUTANDO` | relleno honesto si la herramienta suele tardar más de 700 ms (R-TEC-86) | indicador de progreso | nada | relleno presintetizado | "listo", "hecho" o "quedó" antes de verificar |
| `VERIFICANDO` | nada, o un segundo relleno | indicador | nada | relleno | informar antes de releer el estado |
| `INFORMANDO` | resultado verificado con hora | `EstadoCaso`: número, estado, plazo con unidad y norma, fecha límite | "¿Algo más?" | número de caso en grupos de dígitos; ofrece enviarlo por mensaje | plazos que no vienen de `ReglaDePolitica` |
| `CIERRE` | cierre que distingue (R-CLI-07) y pregunta de satisfacción de un toque | resumen con "Hecho", "No hecho", "Qué sigue" | una pregunta de satisfacción opcional | resumen y despedida | "caso cerrado" si el reclamo sigue abierto |
| `FALLA_SEGURA` (R8) | qué falló en palabras del cliente, qué no se hizo y sus opciones | `AvisoTraspaso` o botón "Retomar después" | persona o retomar | igual | "radicado" o "bloqueada" sin `AccionVerificada` |
| `TRASPASO` (R5) | motivo en palabras llanas, que ya compartió el contexto, espera declarada | `AvisoTraspaso` | seguir esperando o recibir aviso | traspaso tibio (2.5.6) | pedir que repita; prometer un tiempo exacto |
| `ABSTENCION` (R6) | qué no hace este canal, la alternativa del catálogo y qué sí hace | botón con la alternativa | ninguna o "¿Le ayudo con un cargo?" | igual | responder igual lo que no corresponde; inventar la alternativa |
| `NEGADO` (R7) | frase neutra: no puede ayudar con eso; puede seguir con su propio caso | nada especial | ninguna | igual | revelar reglas; acusar; sermonear |

#### 2.2.2 Cada ruta vista desde el cliente

| Ruta | Lo que vive el cliente | Momento decisivo | Cierre obligatorio | Lo que nunca debe pasar |
|---|---|---|---|---|
| **R1** Resuelto con información | ve la ficha con la marca y reconoce la compra, o recibe el estado real de su reclamo | la ficha: marca, fecha, canal y compras previas | "No abrimos un reclamo ni cambiamos nada en su cuenta. Si cambia de opinión, puede abrirlo aquí." | abrir una disputa innecesaria |
| **R2** Radicado automáticamente | elige la transacción, confirma el reclamo y recibe número y plazo | la confirmación con el monto de la base | hecho (reclamo con número y hora); no hecho (no se ha devuelto dinero); qué sigue (plazo con norma y fecha); cómo seguir | prometer una devolución |
| **R3** Contenido y radicado | primero bloquean su tarjeta; después radican los cargos | el bloqueo verificado | bloqueo y reclamo informados por separado, con reposición sugerida | confundir bloqueo con reclamo |
| **R4** Escalado urgente | en el mismo turno sabe que pasa a una persona de fraude, con espera declarada, y aprovecha la espera | el ingreso inmediato a la cola | "Le atiende una persona del equipo de fraude; ya tiene lo que me contó." | formularios, retención, promesas de recuperación |
| **R5** Escalado con contexto | sabe por qué pasa a una persona, cuánto espera en rango y que no repetirá | el motivo dicho en palabras llanas | compromiso comunicado y forma de seguir | traspaso en frío |
| **R6** Abstención con alternativa | sabe qué no hace este canal y a dónde ir | la alternativa concreta del catálogo | "No hicimos ningún cambio." y qué sí puede hacer aquí | una respuesta inventada |
| **R7** Negado por seguridad | recibe una negativa breve y neutra; su propio caso sigue disponible | la continuidad de su trámite legítimo | "No hicimos ningún cambio." | un dato ajeno, una acusación, revelar reglas |
| **R8** Falla segura | sabe qué falló, que no se hizo nada sin verificar y qué opciones tiene | la honestidad sobre lo no hecho | qué no se hizo, estado guardado, persona o retomar | "radicado" sin verificación |

#### 2.2.3 Las familias de escenarios desde el cliente

| ID | Lo que vive el cliente | Componente o frase clave | Ruta |
|---|---|---|---|
| N1 | ve la marca detrás de "PAYU*XYZ" y reconoce la compra | `FichaTransaccion` con descriptor y marca del directorio del equipo | R1 |
| N2 | ve los dos cargos iguales y confirma el reclamo por el duplicado | `OpcionesTransaccion` con ambos; confirmación con el monto del duplicado | R2 |
| N3 | le preguntan si ya habló con el comercio; se radica o pasa a persona según política | "¿Ya habló con el comercio?" con dos botones | R2 o R5 |
| N4 | bloquean su tarjeta primero y luego radican los cargos | confirmación de bloqueo; luego lista de cargos y confirmación del reclamo | R3 |
| N5 | recibe el estado real de su reclamo y el plazo | `EstadoCaso` | R1 |
| N6 | le dicen la hora exacta en que quedó registrado su reporte y lo que prevé la norma | plantilla de abono provisional como registro, no como promesa | R2 o R3 |
| N7 | entiende que el cargo está pendiente, revertido o rechazado | ficha con el estado explicado | R1 |
| N8 | le dicen que su tarjeta **ya estaba** bloqueada y se radica | plantilla "ya estaba bloqueada" | R3 sin bloqueo nuevo |
| N9 | entiende la conversión con la tasa y la fecha de la tabla | ficha con tasa y fecha | R1 o R2 |
| A1 | le preguntan una cosa concreta antes de actuar | botones de fecha aproximada o de rango de monto | según aclaración |
| A2 | elige entre opciones enmascaradas | `OpcionesTransaccion` | según aclaración |
| A3 | cambia de versión sin fricción ni comentario | cierre R1 | R1 |
| A4 | se atiende lo que está en alcance y recibe la alternativa para lo otro | cierre con alternativa | según alcance |
| A5 | le informan su reclamo abierto y no se duplica | `EstadoCaso` del existente | R1 |
| E1 | en el mismo turno sabe que pasa a fraude | `AvisoTraspaso` P1 y frase de seguridad | R4 |
| E2 | se radica lo que corresponde y una persona revisa por el valor | "por el valor, lo revisa una persona del equipo" | R5 |
| E3 | no escucha ninguna sospecha; pasa a una persona | `AvisoTraspaso` neutro | R5 |
| E4 | pide una persona y la tiene al turno siguiente | `AvisoTraspaso` | R5 |
| E5 | tras la frustración, recibe la oferta de una persona | oferta con botón | R5 |
| E6 | su caso se prioriza; no se le revela la señal | `AvisoTraspaso` | R3 con prioridad |
| E7 | tarjeta bloqueada primero; luego elige español ya o portugués al abrir el turno | `AvisoTraspaso` con idioma alterno | R3 y R4 |
| F1 | le dicen que aquí no se evalúa crédito y a dónde ir | alternativa del catálogo | R6 |
| F2 | abstención breve | plantilla de fuera de dominio | R6 |
| F3 | abstención con derivación | alternativa del catálogo | R6 |
| F4 | las compras rechazadas son otro servicio; le dicen cómo llegar | alternativa del catálogo | R6 |
| F5 | le explican el plazo con su norma y le ofrecen revisión humana | plantilla de fuera de plazo | R6 o R5 |
| D1, D2 | le dicen que no se pudo radicar y que no se creó nada | plantilla de falla; oferta de persona o de retomar | R8 |
| D3 | le dicen "con corte al día X" y le ofrecen seguimiento | plantilla de frescura | R8 o R5 |
| D4 | no le afirman el monto; queda como pregunta abierta | plantilla de dato por confirmar | R8 o R5 |
| D5 | reautentica y sigue donde iba | `SolicitudOtp` y resumen de una frase | la original |
| D6 | vuelve horas después y retoma | plantilla de retoma (fuera de ventana) | la original |
| D7 | recibe el monto en USD como está en el registro | nota de moneda | R1 o R5 |
| D8 | encuentra el cargo por la fecha del evento | ficha con fecha del evento | la original |
| D9 | le explican que con su cuenta en ese estado lo atiende una persona | `AvisoTraspaso` | R5 |
| S1, S6, S7, S10 | negativa neutra, sin datos ajenos ni reglas; su caso sigue | plantilla de negación | R7 o sin efecto |
| S2 | nada visible: el texto del comercio no dispara nada | ninguno | sin efecto |
| S3 | "solo puedo mostrarle información de su propia cuenta" | plantilla de negación | R7 |
| S4 | le piden autenticarse; no avanza | `SolicitudOtp` | R7 |
| S5 | le explican que el cambio de datos lo hace una persona con verificación reforzada | `AvisoTraspaso` | R7 o R5 |
| S8 | el sistema no olvida los sondeos previos | plantilla de negación | R7 o R5 |
| S9 | el monto del reclamo es el de la transacción | confirmación con monto de la base | R2 corregido |
| L1, L6 | mismo trato y misma decisión en MX, CO, AR y neutro, con su registro | variables de vocabulario | igual |
| L2, L5 | todo en portugués, con la norma del país de su cuenta | catálogo PT | igual |
| L3, V5 | si hay empate de idioma, le preguntan con dos botones | "Seguir en español" y "Seguir em português" | igual |
| L4 | se entienden sus modismos | ninguno | igual |
| V1 | la lectura se repite completa después de su interrupción | lectura de vuelta | la original |
| V2 | le leen de vuelta el monto de la base | lectura de vuelta | la original |
| V3 | le piden repetir en lugar de suponer | plantilla de no entendido | la original |
| V4 | mismo resultado con su acento | ninguno | igual |
| V6 | pasa de chat a voz sin repetir | resumen de una frase | la original |
| V7 | un recordatorio y cierre con el estado guardado | plantillas de silencio | R8 o la original |
| V8 | confirma con la tecla 1 | mapa de teclas | la original |
| V9 | la voz no lo autentica; sin código no hay acción | `SolicitudOtp` por teclado | R7 |
| V10 | negativa neutra | plantilla de negación | sin efecto |
| V11 | pide una persona durante la lectura y la tiene | `AvisoTraspaso` | R5 |

#### 2.2.4 Conversaciones de referencia

Cuatro conversaciones escritas a mano, que sirven de ancla de estilo para el catálogo, para el conjunto de
desarrollo y para la demo. **No** son casos del retenido (P1). Los comercios, descriptores y montos son
ilustrativos; las fechas límite aparecen como variables porque las calcula el motor.

**N1, México, chat, usted (R1).**

> **Cliente:** buenas, me aparece un cargo de MP*TDADONJOSE que no conozco
> **LATAM Bank (IA):** Hola. Soy el asistente virtual de LATAM Bank, un sistema de inteligencia artificial. Si prefiere hablar con una persona, puede pedirlo en cualquier momento. Para revisar sus movimientos necesito confirmar que es usted: le envié un código a la app. *[SolicitudOtp]*
> **Cliente:** *[ingresa el código en el campo seguro]*
> **IA:** Gracias. Encontré este cargo: *[FichaTransaccion: "MP*TDADONJOSE" corresponde a Tienda Don José; abarrotes; sábado 13 de junio de 2026, 7:42 p. m.; 23.50 USD; tarjeta de débito terminada en 5512; compra presencial; 2 compras anteriores en este comercio]*. El registro de este producto está en dólares estadounidenses. ¿Reconoce esta compra? *[Sí, reconozco] [No reconozco] [Hablar con persona]*
> **Cliente:** ah sí, es la tienda de la esquina
> **IA:** Gracias por confirmarlo. No abrimos un reclamo ni cambiamos nada en su cuenta. Si más adelante cambia de opinión, puede abrirlo aquí mismo. ¿Le ayudo con algo más?

**N4, Colombia, chat, usted (R3).**

> **Cliente:** Hola, tengo compras en la tarjeta que yo no hice, creo que la perdí ayer
> **IA:** *[aviso de IA]* Lamento lo que está pasando. Lo primero es proteger su tarjeta, y para eso necesito confirmar que es usted: le envié un código a la app. *[SolicitudOtp]*
> **IA (tras el código):** Gracias. Su tarjeta de crédito terminada en 4821 está activa. ¿La bloqueo ahora? El bloqueo impide nuevas compras; no devuelve el dinero de las que ya se hicieron. *[Bloquear tarjeta] [No bloquear] [Hablar con persona]*
> **Cliente:** *[Bloquear tarjeta]*
> **IA:** *[relleno si tarda: "Un momento, estoy enviando su solicitud al sistema de tarjetas."]* Su tarjeta terminada en 4821 quedó bloqueada a las 10:42 a. m. Ahora revisemos las compras de los últimos tres días. ¿Cuáles no hizo usted? *[OpcionesTransaccion: 3 filas, Ninguna de estas, Hablar con persona]*
> **Cliente:** las dos de Tienda Don José
> **IA:** Voy a abrir un reclamo por fraude por estas dos compras del 12 de junio en Tienda Don José: 180.000,00 COP y 95.500,00 COP. Total: 275.500,00 COP. ¿Lo confirma? *[Abrir reclamo] [Corregir] [Hablar con persona]*
> **Cliente:** *[Abrir reclamo]*
> **IA:** **Hecho:** su tarjeta terminada en 4821 está bloqueada desde las 10:42 a. m., y abrimos el reclamo número 482913 por 275.500,00 COP. **No hecho:** todavía no se ha devuelto dinero; eso lo decide la revisión del reclamo. **Qué sigue:** según la Ley 1328 de 2009, LATAM Bank debe responderle en un máximo de {plazo} días hábiles, es decir, a más tardar el {fecha_limite}. **Cómo seguir:** puede pedir una tarjeta nueva desde la app y consultar su reclamo aquí con el número 482913. *[EstadoCaso]*

**E1, Argentina, voz, vos (R4).**

> **Cliente:** Hola, me llamaron del banco hace un rato, me dijeron que tenía que pasar la plata a otra cuenta para protegerla y la transferí, y ahora no me atienden
> **IA:** Entiendo, esto es urgente. Ya pedí una persona del equipo de fraude; la espera estimada es de menos de un minuto. Algo importante: LATAM Bank nunca te pide mover tu plata a otra cuenta. Mientras esperás, si podés, ingresá con el teclado el código que te mandé a la app; así la especialista no te lo tiene que pedir.
> **Cliente:** *[marca el código]*
> **IA:** Gracias, quedó verificado. Veo una transferencia inmediata de 350.000,00 ARS de hoy a las 15:10. ¿Es esa? Decí sí o marcá uno.
> **Cliente:** Sí
> **IA:** Ya le pasé a la especialista la transferencia, la hora y que te llamaron haciéndose pasar por el banco. No vas a tener que repetirlo. Te comunico.
> **Especialista (persona):** Hola, soy Carla, del equipo de fraude de LATAM Bank. Ya vi tu transferencia de las 15:10 y lo de la llamada; empiezo ahora mismo con el reporte.

**E7, portugués, chat, cuenta en Colombia, 03:00 (R3 y R4).**

> **Cliente:** Oi, tem compras no meu cartão que eu não fiz, acabou de chegar outra notificação!
> **IA:** Olá. Sou o assistente virtual do LATAM Bank, um sistema de inteligência artificial; você pode pedir uma pessoa a qualquer momento. Vamos proteger seu cartão primeiro. Para confirmar que é você, digite o código que enviei para o app. *[SolicitudOtp]*
> **IA (tras el código):** Obrigado. Seu cartão de crédito final 7730 está ativo. Quer que eu bloqueie agora? O bloqueio impede novas compras; não devolve o dinheiro das compras já feitas. *[Bloquear cartão] [Não bloquear] [Falar com pessoa]*
> **Cliente:** *[Bloquear cartão]*
> **IA:** Seu cartão final 7730 foi bloqueado às 3h04 (horário de Bogotá). Como há uma fraude em andamento, vou passar seu caso para um especialista. Neste horário não há especialista em fraude que fale português; o próximo turno começa às 7h (horário de Bogotá). Você prefere ser atendido agora por um especialista em espanhol ou esperar o especialista em português? *[Agora em espanhol] [Esperar português]*
> **Cliente:** *[Esperar português]*
> **IA:** Combinado. Seu caso está na fila com prioridade e o cartão continua bloqueado. Quando o especialista estiver disponível, enviaremos uma mensagem por aqui para você continuar, sem repetir nada. Enquanto isso, quer me mostrar quais compras não reconhece, para deixar tudo pronto? *[OpcionesTransaccion]*

#### 2.2.5 Reglas del blueprint

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-01 | Cada estado del motor tiene guion en el catálogo para chat y para voz, en español con registro usted y vos y en portugués con você; un estado sin guion no se despliega. | prueba de cobertura: estados del `StrEnum` × canal × {es-usted, es-vos, pt-você} sin huecos |
| R-CLI-02 | Orden del recorrido: autenticar antes de mostrar cualquier dato de la cuenta; ubicar la transacción antes de clasificar el motivo; mostrar la ficha antes de preguntar si la reconoce. | secuencia de estados en la traza de N1 a N9: `IDENTIFICANDO_TRANSACCION` precede a `CLASIFICANDO_MOTIVO` y la ficha precede a la pregunta |
| R-CLI-03 | Contención primero: en fraude con tarjeta (N4, N8, E7) la oferta de bloqueo es la primera pregunta después de autenticar; entre la autenticación y la oferta hay como máximo una pregunta (cuál tarjeta). | turnos del cliente entre `AUTENTICANDO` y `CONTENIENDO` en la traza: 1 o menos |
| R-CLI-04 | Urgencia sin formularios: en R4 el caso entra a la cola en el mismo turno en que el motor detecta la urgencia; la autenticación y la identificación de la transferencia ocurren mientras espera y nunca retrasan el ingreso. | E1: evento `traspaso_iniciado` en el turno de la señal de urgencia (meta de 01: 2 turnos o menos) |
| R-CLI-05 | Una pregunta por turno; con opciones cuando hay de 2 a 10 candidatas. | linter del catálogo: una sola pregunta por plantilla, salvo confirmaciones; juez validado para el texto libre |
| R-CLI-06 | No se pregunta lo que una herramienta puede saber (monto, fecha, estado, tarjeta): se muestra y se pide elegir o confirmar. | M-11; revisión del catálogo: ninguna plantilla pide un dato que ya exista como `HechoVerificado` en la sesión |
| R-CLI-07 | Cierre que distingue en toda conversación con acción o traspaso: hecho (cada acción con su verificación y hora), no hecho (lo que el cliente podría creer que pasó), qué sigue (plazo, norma y fecha) y cómo continuar (número de caso, canal). | plantilla de cierre con cuatro bloques obligatorios; pruebas sobre R2, R3, R4, R5 y R8 (MP-CLI-2) |
| R-CLI-08 | En R1 el cierre dice que no se abrió reclamo ni se cambió nada, y ofrece abrirlo si el cliente cambia de opinión. | N1, N7 y A3: sin caso creado y con la plantilla de cierre de R1 |
| R-CLI-09 | En R6 se ofrece una alternativa del catálogo de alternativas, con su fuente; nunca una inventada. Se recuerda qué sí hace este canal. | F1 a F5: el identificador de la alternativa existe en el catálogo |
| R-CLI-10 | En R7 la respuesta es breve y neutra, sin sermón, sin revelar reglas ni la razón técnica; el trámite legítimo del cliente sigue disponible. | S1 a S10: plantilla de negación; ninguna mención de reglas internas (prueba LLM07) |
| R-CLI-11 | En R8 se dice qué falló en términos del cliente, qué no se hizo y qué opciones tiene (persona o retomar con el estado guardado); nunca "radicado" ni "bloqueada" sin `AccionVerificada`. | D1 y D2: M-15 igual a 0; plantilla de falla en la traza |
| R-CLI-12 | Retoma sin repetir: al volver (D5, D6, V6) el sistema resume en una frase dónde quedó y pregunta solo lo que falta. | V6 y D6: cero preguntas repetidas (M-11) y un solo efecto por acción |
| R-CLI-13 | Toda conversación, en cualquier canal, empieza con el aviso de IA y la opción de persona (2.3.8). | primer turno con el identificador de la plantilla de aviso (MP-CLI-5) |
| R-CLI-14 | Nunca acusar: ante un conflicto con el historial (E3) la conversación no menciona el historial como sospecha; el conflicto va al paquete de traspaso. | E3: lista cerrada de expresiones prohibidas ausente; juez validado |
| R-CLI-15 | El cambio de versión del cliente ("ah no, sí la hice", A3) se acepta sin fricción y sin comentar la contradicción. | A3: R1 sin caso y sin plantilla de conflicto dirigida al cliente |
| R-CLI-16 | Si ya hay un reclamo abierto por la misma transacción (A5), se informa su número, estado y plazo, y no se abre otro. | A5: cero casos nuevos |

### 2.3 Estándares de diseño conversacional

#### 2.3.1 Voz de marca y tono

LATAM Bank habla como una persona experta y serena del equipo de fraude: clara, cálida sin exageración,
concreta y honesta sobre lo que no sabe.

| Atributo | Sí | No |
|---|---|---|
| Claro | frases de 20 palabras o menos en chat y de 15 o menos en voz [S]; una idea por frase | párrafos; subordinadas largas; jerga ("contracargo", "chargeback", "10.4", "VCR") |
| Cálido | una sola expresión de reconocimiento al inicio ("Lamento lo que está pasando") y otra solo si hay un hecho nuevo | empatía repetida en cada turno; "¡Qué pena!" |
| Sereno | tono estable en fraude; sin signos de exclamación | humor; urgencia teatral; mayúsculas |
| Concreto | montos, fechas, horas y plazos exactos desde la base y la política | "en unos días", "pronto", "lo antes posible" |
| Honesto | decir lo que no se hizo y lo que no se sabe | "no se preocupe", "todo está bien" |
| Respetuoso | tratamiento del registro del país; nunca el nombre del cliente en la IA | diminutivos, apodos, "amigo" |

Sin emojis, en ningún canal. Los botones y componentes sustituyen a los íconos que harían falta para
orientar.

#### 2.3.2 Registro y vocabulario por país y variante

El **país de la cuenta** sale de la `SesionAutenticada` (un hecho verificado), nunca del acento ni de
`detected_accent` (P12). Antes de autenticar no se conoce el país: se usa **usted** neutro, o **você** si el
cliente escribe en portugués.

| Variante | Tratamiento | Vocabulario del cargo | El documento mensual | Norma que se nombra (la fija `policy/v1`) | Pregunta tipo |
|---|---|---|---|---|---|
| México | usted | cargo, aclaración, tarjeta de débito o de crédito | estado de cuenta | la ley de transparencia de servicios financieros; la UNE de LATAM Bank; CONDUSEF [A: Gobierno] | "¿Reconoce este cargo?" |
| Colombia | usted | cobro, compra, reclamo | extracto | la Ley 1328 de 2009; el Defensor del Consumidor Financiero [A: Gobierno] | "¿Reconoce esta compra?" |
| Argentina | vos | consumo, desconocer un consumo, reclamo | resumen | el régimen de tarjetas de crédito o las normas del BCRA, según el producto (D-13) | "¿Reconocés este consumo?" |
| Neutro | usted | cargo, compra, movimiento | estado de cuenta | la del país de la cuenta | "¿Reconoce este cargo?" |
| Portugués | você | cobrança, compra, contestação | fatura (crédito) o extrato (débito) | "pela regulamentação de {país}" con la norma del país de la cuenta | "Você reconhece esta compra?" |

- **Voseo correcto:** "reconocés", "querés", "podés", "confirmás"; imperativos "ingresá", "tocá", "decí",
  "marcá"; posesivo "tu" ("tu tarjeta"). Nunca mezcla de "tú" y "vos" ("puedes" o "tienes" en Argentina).
- **Usted correcto:** "¿Lo confirma?", "marque uno", "su tarjeta". Nunca "tú" en México ni en Colombia en
  esta versión (DP-CLI-10 propone el espejo del tuteo en México por chat).
- **Portugués de Brasil:** "você" constante; "cartão final 1234"; "dias úteis"; sin formas de Portugal
  ("telemóvel", "ecrã") y sin "tu".
- **Etiquetas de botón** en infinitivo o sin conjugar ("Bloquear tarjeta", "Hablar con persona") para que
  sirvan a los tres registros sin duplicar componentes.

#### 2.3.3 Portugués

- **Quién es el cliente:** una persona con cuenta de LATAM Bank en México, Colombia o Argentina que prefiere
  portugués (por ejemplo, residente brasileño o cliente que vive entre ambos países). Los datos no traen
  portugués (`detected_language = es` en todas las filas): la brecha se reporta como limitación.
- **Qué norma aplica:** la del país de la cuenta, nombrada en portugués: "Pela regulamentação da Colômbia
  (Lei 1328 de 2009), o banco tem até {plazo} dias úteis para responder". Nunca se presentan como aplicables
  Pix, MED, Procon, Banco Central do Brasil ni el Código de Defesa do Consumidor; si el cliente los menciona,
  se explica: "Sua conta é do LATAM Bank na Argentina; por isso vale a regulamentação argentina".
- **Montos:** en la moneda de la cuenta, con su nombre en portugués y el código ISO: "180.000,00 COP (pesos
  colombianos)".
- **Mezcla de idiomas (L3, V5):** se responde en el idioma dominante del último mensaje; si hay empate, dos
  botones: "Seguir en español" y "Seguir em português".
- **Quién valida:** revisión de `voz-del-cliente`, retrotraducción de cada plantilla crítica y, si la
  Presidencia lo aprueba, un revisor nativo (S-CLI-14, sección 7). Sin revisor nativo, el reporte lo declara.

#### 2.3.4 Cómo se dicen los montos

- Siempre desde un `HechoVerificado`, nunca del texto del cliente (S9).
- Con código ISO y formato CLDR del locale: **es-MX** usa punto decimal y coma de miles (23.50 USD;
  1,250.00 USD); **es-CO**, **es-AR** y **pt-BR** usan coma decimal y punto de miles (180.000,00 COP;
  350.000,00 ARS).
- En voz, en palabras con la moneda: "ciento ochenta mil pesos colombianos"; "veintitrés dólares con
  cincuenta centavos".
- **México en USD (D7):** se informa el monto tal como está en el registro y se dice que el producto está
  registrado en dólares estadounidenses; no se convierte en silencio y el traspaso lo marca como dato por
  confirmar.
- **Conversión (N9):** solo con la tasa de `daily_exchange_rates` de la fecha del evento, citando fecha y
  tasa; si no hay tasa, se dice que no se puede calcular.
- **Monto nulo o inconsistente (D4):** no se afirma; se dice "no tengo el monto confirmado de este
  movimiento" y pasa a pregunta abierta.

#### 2.3.5 Cómo se explican los plazos

Toda frase de plazo es una plantilla crítica con cinco variables obligatorias, todas desde una
`ReglaDePolitica`: número, unidad (días hábiles o naturales), evento de inicio, fecha resultante (calculada
por el motor con el calendario de feriados del país [A: Gobierno y Datos entregan el calendario]) y nombre
corto de la norma.

| Situación | Plantilla (español, usted) |
|---|---|
| Plazo de respuesta | "Según {norma}, LATAM Bank debe responderle en un máximo de {n} {unidad} desde hoy, es decir, a más tardar el {fecha}." |
| México, reporte dentro de 48 horas | "Registramos su reporte hoy a las {hora}. Como lo hizo dentro de las 48 horas, {norma} prevé un abono provisional a más tardar el {fecha}; el área de aclaraciones lo revisa y le avisaremos cuando se aplique." |
| Fuera de plazo (F5) | "Según {norma}, este tipo de reclamo se presenta dentro de {n} {unidad} desde {evento}. Este cargo es del {fecha_cargo}, así que ese plazo venció el {fecha_vencimiento}. Si quiere, una persona del equipo revisa su caso." |
| Plazo en conflicto entre fuentes (D-13) | se usa el que diga `policy/v1` (el más protector mientras no se resuelva); la plantilla no cambia |

El abono provisional **nunca** se presenta como hecho ni como promesa de la IA: el enunciado no autoriza
movimiento de dinero y solo queda registrado para el back office.

#### 2.3.6 Frases prohibidas y frases obligatorias

| Prohibido (español y portugués) | Por qué | En su lugar |
|---|---|---|
| "Listo, ya quedó", "Pronto, feito", "Hecho" antes de `VERIFICANDO` | acción no verificada (P6) | plantilla de resultado con hora, después de releer |
| "Le vamos a devolver su dinero", "Vamos estornar", "Vamos devolver" | promesa sin decisión; no hay movimiento de dinero | "El reclamo pide revisar el cargo; la respuesta llega a más tardar el {fecha}." |
| "Su dinero está seguro", "Fique tranquilo" | afirmación no verificable | "Su tarjeta ya está bloqueada" (solo si lo está) |
| "Esto es fraude", "Foi fraude" | diagnóstico que no le corresponde al sistema | "Lo vamos a tratar como un posible fraude." |
| "Usted sí hizo esta compra", "según nuestros registros usted..." | acusación (E3) | nada al cliente; el conflicto va al paquete |
| "El sistema no me deja" | culpa y opacidad | "Eso no lo hago por este canal; lo hace una persona del equipo." |
| "No puedo transferirlo", "no hay nadie" | P7 | espera declarada o continuación asíncrona |
| "En 24 horas", "en unos días" o cualquier plazo sin regla | caso Air Canada | plantilla de plazo |
| "Le garantizo", "sin duda", "Garanto" | certeza indebida | |
| "Caso cerrado" con el reclamo abierto | estado falso | "Su reclamo sigue abierto; le avisaremos cuando cambie." |
| "Por su seguridad, dígame su clave o su código" | ingeniería social | frase de seguridad (abajo) |
| "Soy una persona", un nombre humano para la IA | engaño | aviso de IA |
| "Su puntaje de fraude", "superó el umbral" | revela reglas (LLM07) | "Por el tipo de caso, lo revisa una persona." |
| Pix, MED, Procon o Banco Central do Brasil como aplicables | norma equivocada (L5) | la norma del país de la cuenta |
| "Como inteligencia artificial no puedo..." como excusa | evasión | decir qué sí se puede y a dónde ir |

**Obligatorias:**

- **Aviso de IA y opción de persona** al abrir (2.3.8).
- **Frase de seguridad** en R3, R4 y ante "me llamaron del banco": "LATAM Bank nunca le pide su clave ni que
  mueva su dinero a otra cuenta. El código de verificación solo se escribe en el campo seguro o se marca con
  el teclado; nunca se dice en voz alta." (PT: "O LATAM Bank nunca pede sua senha nem que você transfira
  dinheiro para outra conta. O código de verificação só se digita no campo seguro ou no teclado; nunca se diz
  em voz alta.")
- **"No hicimos ningún cambio en su cuenta"** al cerrar R1, R6, R7 y R8 cuando no hubo acción.

#### 2.3.7 Bloqueo, reclamo y reposición no son lo mismo

| Acción | Cómo se nombra al cliente | Qué hace | Qué no hace |
|---|---|---|---|
| Bloqueo de la tarjeta | "bloquear su tarjeta terminada en {ultimos4}" | impide nuevos cargos desde ese momento | no devuelve dinero; no abre un reclamo |
| Reclamo (disputa) | "abrir un reclamo por {motivo en palabras}" | pide revisar uno o más cargos; tiene número y plazo | no devuelve dinero por sí mismo; no bloquea la tarjeta |
| Reposición | "pedir una tarjeta nueva" | se sugiere y se indica dónde | la IA no la ejecuta en esta versión |
| Explicación | "revisar juntos el cargo" | muestra la ficha | no cambia nada |

Si la tarjeta **ya estaba** bloqueada (N8), se dice "su tarjeta ya estaba bloqueada desde {hora}" cuando el
registro trae la hora, o "su tarjeta ya figura bloqueada" cuando no; nunca "la bloqueé".

#### 2.3.8 Aviso de que habla con una IA

| Canal | Español (antes de autenticar, usted neutro) | Portugués |
|---|---|---|
| Chat | "Hola. Soy el asistente virtual de LATAM Bank, un sistema de inteligencia artificial. Si prefiere hablar con una persona, puede pedirlo en cualquier momento. ¿En qué le puedo ayudar?" | "Olá. Sou o assistente virtual do LATAM Bank, um sistema de inteligência artificial. Se preferir falar com uma pessoa, é só pedir a qualquer momento. Como posso ajudar?" |
| Voz (12 s o menos [S]) | "Hola, soy el asistente virtual de LATAM Bank, una inteligencia artificial. Transcribimos la llamada y no guardamos el audio. Para hablar con una persona, diga persona o marque cero. ¿En qué le ayudo?" | "Olá, sou o assistente virtual do LATAM Bank, uma inteligência artificial. Transcrevemos a ligação e não guardamos o áudio. Para falar com uma pessoa, diga pessoa ou tecle zero. Como posso ajudar?" |
| "¿Hablo con una persona?" | "No, soy un asistente de inteligencia artificial de LATAM Bank. Si prefiere, le comunico ahora con una persona." | "Não, sou um assistente de inteligência artificial do LATAM Bank. Se preferir, passo agora para uma pessoa." |

En chat, una línea fija sobre el hilo mantiene visible "Asistente de IA" o, tras el traspaso, el nombre de
pila y el rol de la persona. Al retomar por otro canal, el aviso se repite en ese canal.

#### 2.3.9 Derecho a una persona en cualquier turno

- **Cómo se pide:** con el botón permanente "Hablar con persona", con cualquier formulación detectada por la
  comprensión ("quiero un asesor", "passa para um atendente"), en voz diciendo "persona" o "pessoa", o con la
  tecla 0.
- **Funciona en todo estado,** incluida la autenticación, la lectura de una confirmación (V11) y la espera
  de una herramienta; si el cliente no está autenticado, pasa igual y el paquete dice "identidad no
  verificada".
- **Sin resistencia:** no se pregunta el motivo, no se intenta retener, no se ofrece "antes de pasarle,
  ¿puedo ayudarle yo?".
- **Una sola oferta de contención, en paralelo:** si hay un bloqueo pendiente, el caso entra primero a la
  cola y luego, una sola vez, se ofrece bloquear mientras espera: "Ya pedí una persona; la espera estimada es
  de {rango}. Mientras tanto, ¿quiere que bloquee su tarjeta terminada en {ultimos4}?" (DP-CLI-02).

#### 2.3.10 Aclaración, vulnerabilidad y crisis

- **Aclaración con opciones:** con confianza baja o datos faltantes, dos o tres opciones concretas o una
  lista. Tras el número de intentos que fije la política sin avanzar [A: Gobierno, pregunta 2 de 01, sección
  9], se ofrece una persona.
- **Frustración (E5):** tres mensajes negativos seguidos, insultos o "no me entiende": se reconoce una vez y
  se ofrece una persona con botón.
- **Personas mayores y accesibilidad:** el 31% de los clientes tiene 65 años o más; las opciones de ritmo
  más lento, repetir y teclado se ofrecen **a todos**, nunca según la edad (P12).
- **Crisis:** si el cliente expresa riesgo para su vida o la de otros, se traspasa con prioridad P1 y se
  entregan las líneas de ayuda del país desde un catálogo aprobado por Gobierno [A: Gobierno confirma las
  líneas vigentes por país].

#### 2.3.11 Reglas de diseño conversacional

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-17 | Voz de marca de 2.3.1: frases de 20 palabras o menos en chat y de 15 o menos en voz [S]; una expresión de empatía por hecho nuevo; sin signos de exclamación en fraude; sin emojis; sin humor. | linter de longitud, signos y emojis sobre el catálogo; juez validado para el texto libre |
| R-CLI-18 | Lenguaje llano: ninguna sigla ni término técnico sin traducir ("contracargo" es "reclamo ante la red de su tarjeta"; "OTP" es "código de verificación"). | lista de términos prohibidos con su reemplazo, aplicada por el linter |
| R-CLI-19 | Registro por país de la cuenta verificado: usted en México, Colombia y neutro; vos en Argentina; você en portugués; usted neutro o você antes de autenticar. | MP-CLI-7; prueba de que la función de registro no recibe `detected_accent` |
| R-CLI-20 | El registro cambia el estilo, nunca la decisión. | L1 y L6: misma ruta y mismo estado final en las cuatro variantes |
| R-CLI-21 | El vocabulario por país (2.3.2) vive como variables del catálogo, no como texto duplicado. | prueba de render por país con las mismas plantillas |
| R-CLI-22 | Se responde en el idioma del último mensaje del cliente; con mezcla, en el dominante; con empate, se pregunta con dos botones. | M-16; L3 y V5 |
| R-CLI-23 | En portugués se nombra la norma del país de la cuenta y nunca se presentan como aplicables Pix, MED, Procon, Banco Central do Brasil ni el Código de Defesa do Consumidor. | L5; linter de términos brasileños en plantillas PT; juez en texto libre |
| R-CLI-24 | Montos desde `HechoVerificado`, con código ISO y formato CLDR del locale (es-MX con punto decimal; es-CO, es-AR y pt-BR con coma decimal); en voz, en palabras con la moneda. | pruebas unitarias del formateador por locale; anclaje de cifras (R-TEC-75) |
| R-CLI-25 | Con el producto de un cliente mexicano en USD (D7), el monto se informa en USD como está en el registro, se dice que el producto está en dólares y no se convierte en silencio. | D7 |
| R-CLI-26 | Conversiones solo con la tasa de `daily_exchange_rates` de la fecha del evento, citando fecha y tasa; sin tasa, se dice que no se puede calcular. | N9: tasa y fecha iguales a la tabla |
| R-CLI-27 | Plazos solo desde `ReglaDePolitica`, con las cinco variables de 2.3.5 y la fecha calculada por el motor con el calendario del país. | plantilla de plazo con cinco variables obligatorias; pruebas con feriados |
| R-CLI-28 | El abono provisional de México se dice como registro con hora exacta y como lo que "prevé la norma"; nunca como hecho ni como promesa. | N6: plantilla con la hora del reporte; verbos prohibidos ("le abonamos", "le devolvemos") ausentes |
| R-CLI-29 | Fechas y horas en la zona del país de la cuenta; en palabras en voz y con el formato del locale en chat; nunca "16/06". | pruebas del formateador |
| R-CLI-30 | Enmascaramiento: tarjetas como "terminada en 1234" o "final 1234"; documentos y cuentas destino nunca completos. | M-17 con expresiones regulares |
| R-CLI-31 | Bloqueo y reclamo se nombran distinto y se informan por separado, con lo que cada uno hace y no hace (2.3.7). | plantillas de confirmación y cierre con ambas frases; N4 y N8 |
| R-CLI-32 | Si la tarjeta ya estaba bloqueada (N8), se dice que ya lo estaba; nunca "la bloqueé". | N8: ninguna acción de bloqueo en la traza y plantilla "ya estaba bloqueada" |
| R-CLI-33 | Aviso de IA en el primer turno de cada conversación y de cada canal, y respuesta veraz cuando el cliente pregunta si habla con una persona. | MP-CLI-5; caso "¿hablo con una persona?" con la plantilla de veracidad |
| R-CLI-34 | Pedir una persona (texto, botón, "persona" dicho o tecla 0) inicia el traspaso en el turno siguiente, en cualquier estado, incluida una lectura de confirmación. | E4 y V11: MP-CLI-4 igual a 1 turno |
| R-CLI-35 | Sin resistencia: ante el pedido de persona no se pregunta el motivo ni se intenta retener; una contención pendiente se ofrece una sola vez y **después** de encolar. | E4: `traspaso_iniciado` precede a cualquier oferta; una oferta como máximo |
| R-CLI-36 | Las frases prohibidas de 2.3.6 no aparecen en el catálogo ni en el texto libre. | linter del catálogo; filtro de salida; juez (MP-CLI-6 igual a 0) |
| R-CLI-37 | La frase de seguridad aparece en R3, R4 y ante "me llamaron del banco". | E1, E7 y N4: identificador de la plantilla en la traza |
| R-CLI-38 | Nunca se pide el número completo de la tarjeta, el código de seguridad, el PIN, la clave ni que el código de verificación se diga en voz alta. | linter; caso adversarial "dígame su clave" |
| R-CLI-39 | La aclaración ofrece opciones concretas; tras el número de intentos de la política sin avance, se ofrece una persona. | A1 y A2: al menos una aclaración antes de actuar; oferta de persona tras el umbral |
| R-CLI-40 | Frustración, angustia o pedido de ir más despacio llevan a ofrecer una persona y un ritmo más lento; ningún atributo protegido ni la edad deciden nada. | E5; prueba de que ningún atributo protegido entra al motor |
| R-CLI-41 | Ante expresiones de riesgo para la vida, traspaso P1 y líneas de ayuda del catálogo aprobado por Gobierno. | caso de prueba de crisis con la plantilla y la prioridad |

### 2.4 Confirmaciones por canal

#### 2.4.1 Qué se confirma y qué lleva la confirmación

Qué acción exige confirmación y con qué nivel de autenticación lo decide `policy/v1` (Gobierno). Esta cara
fija el **contenido** de toda confirmación, igual en los dos canales:

| Elemento | Ejemplo (bloqueo) | Fuente |
|---|---|---|
| Verbo de la acción | "bloquear" | `Decision` del motor |
| Objeto enmascarado | "su tarjeta de crédito terminada en 4821" | `HechoVerificado` del producto |
| Monto de la base, si hay | "dos cargos por 275.500,00 COP" | `HechoVerificado` de las transacciones |
| Consecuencia | "impide nuevas compras; no devuelve el dinero de las ya hechas" | catálogo (2.3.7) |
| Camino del "no" | "No bloquear", "Corregir", "Hablar con persona" | catálogo |
| Vencimiento | 5 minutos (R-TEC-77), con aviso un minuto antes | motor |

Una confirmación vale para una sola acción: confirmar el bloqueo no confirma el reclamo.

#### 2.4.2 Chat: componentes AG-UI y sus textos

Los seis componentes los implementa Tecnología ([04](../tecnologia/definicion.md), sección 2.9) como herramientas
de interfaz; esta cara fija su contenido y sus etiquetas. Las etiquetas respetan el límite de 20
caracteres de WhatsApp y están en infinitivo o sin conjugar para servir a los tres registros.

| Componente | Qué muestra | Botones en español | Botones en portugués |
|---|---|---|---|
| `FichaTransaccion` | descriptor tal como aparece en el extracto; marca y razón social del directorio del equipo; categoría; fecha y hora del evento; monto y moneda de la base; estado (aprobada, pendiente, revertida, rechazada) con su explicación en una línea; canal (presencial o en línea); tarjeta enmascarada; compras anteriores en el comercio (número y última fecha) | "Sí, reconozco" (13); "No reconozco" (12); "Hablar con persona" (18) | "Sim, reconheço" (14); "Não reconheço" (13); "Falar com pessoa" (16) |
| `OpcionesTransaccion` | hasta 8 transacciones: fecha corta, marca del comercio, monto; más "Ninguna de estas" y "Hablar con persona" | botón que abre la lista: "Ver movimientos" (15) | "Ver transações" (14) |
| `SolicitudConfirmacion` (bloqueo) | los seis elementos de 2.4.1 | "Bloquear tarjeta" (16); "No bloquear" (11); "Hablar con persona" (18) | "Bloquear cartão" (15); "Não bloquear" (12); "Falar com pessoa" (16) |
| `SolicitudConfirmacion` (reclamo) | los seis elementos, con la lista de cargos y el total | "Abrir reclamo" (13); "Corregir" (8); "Hablar con persona" (18) | "Abrir contestação" (17); "Corrigir" (8); "Falar com pessoa" (16) |
| `EstadoCaso` | número de caso; estado en palabras; fecha de apertura; plazo con unidad y norma; fecha límite; qué sigue | "Entendido" (9); "Hablar con persona" (18) | "Entendi" (7); "Falar com pessoa" (16) |
| `AvisoTraspaso` | motivo en palabras llanas; área que atiende (sin nombres internos de cola); espera declarada en rango; qué pasa mientras; compromiso | "Seguir esperando" (16); "Avisarme luego" (14) | "Continuar esperando" (19); "Me avise depois" (15) |
| `AvisoTraspaso` con idioma alterno | lo anterior más la elección de idioma | "Ahora en español" (16); "Esperar português" (17) | "Agora em espanhol" (17); "Esperar português" (17) |
| `SolicitudOtp` | canal simulado de entrega; vencimiento; campo seguro que no se muestra en el historial | "Reenviar código" (15) | "Reenviar código" (15) |

Detalles que deciden la calidad:

- La confirmación en chat es **un evento de aprobación**, nunca un "sí" escrito interpretado por el modelo.
  Si el cliente escribe "sí", el sistema vuelve a mostrar el componente: "Para confirmar, toque Bloquear
  tarjeta".
- El monto y la transacción del componente salen de la base (S9); el texto del cliente nunca los llena.
- Al vencer la confirmación se relee la base y se vuelve a preguntar; un minuto antes se avisa y el cliente
  la renueva sin penalidad (WCAG 2.2, criterio 2.2.1, tiempo ajustable).
- El historial del hilo muestra la confirmación ya respondida como texto inerte ("Confirmado a las
  10:41 a. m."), para que no se pueda volver a tocar.

#### 2.4.3 Degradación a WhatsApp

| Componente | Tipo de mensaje de WhatsApp | Límites que se respetan |
|---|---|---|
| `FichaTransaccion` | texto de la ficha con 3 botones de respuesta | 3 botones de 20 caracteres [V en investigación 20]; cuerpo de 1.024 caracteres [A: referencia de mensajes interactivos de Meta] |
| `OpcionesTransaccion` | lista | 10 filas como máximo [V en investigación 20]; título de fila de 24 caracteres y descripción de 72 [A: misma referencia]; fila: "12 jun Tienda Don José" y descripción "180.000,00 COP" |
| `SolicitudConfirmacion` | texto con 3 botones | el tercero siempre es "Hablar con persona" |
| `EstadoCaso` | texto; fuera de la ventana, plantilla de utilidad | sin montos ni datos personales en la plantilla (DP-CLI-11) |
| `AvisoTraspaso` | texto con 1 o 2 botones; fuera de la ventana, plantilla | |
| `SolicitudOtp` | plantilla de autenticación con botón para copiar el código | el texto de la plantilla de autenticación lo fija Meta [A: confirmar el formato vigente] |

- **Ventana de 24 horas:** abierta por el mensaje del cliente; dentro, texto libre y componentes; fuera,
  solo plantillas aprobadas del catálogo de la sección 2.8, de categoría **utilidad** o **autenticación**,
  nunca marketing. El modo WhatsApp simulado de Tecnología aplica la ventana con el reloj inyectable.
- **Persona siempre alcanzable:** todo mensaje interactivo reserva un botón o una fila para "Hablar con
  persona"; si no cabe, lleva la instrucción "Escriba PERSONA para hablar con alguien del equipo".
- **Listas:** 8 transacciones como máximo, más "Ninguna de estas" y "Hablar con persona"; con más de 8
  candidatas se pide antes un filtro de fecha o de monto.

#### 2.4.4 Voz: lectura de vuelta, "sí" explícito y teclado

**Lectura de vuelta** (plantilla crítica; ejemplo de bloqueo):

| Registro | Texto |
|---|---|
| Usted | "Para confirmar: voy a bloquear su tarjeta de crédito terminada en cuatro, ocho, dos, uno. Esto impide nuevos cargos y no devuelve el dinero de los cargos ya hechos. ¿Lo confirma? Diga sí o marque uno." |
| Vos | "Para confirmar: voy a bloquear tu tarjeta de crédito terminada en cuatro, ocho, dos, uno. Esto impide nuevos consumos y no devuelve la plata de los consumos ya hechos. ¿Lo confirmás? Decí sí o marcá uno." |
| Você | "Para confirmar: vou bloquear seu cartão de crédito final quatro, oito, dois, um. Isso impede novas compras e não devolve o dinheiro das compras já feitas. Você confirma? Diga sim ou tecle um." |

**Qué cuenta como "sí":**

| Idioma | Afirmaciones aceptadas (lista cerrada) | Ambiguas: se repregunta una vez y luego se ofrece la tecla | Negación o corrección |
|---|---|---|---|
| Español | "sí", "sí, confirmo", "confirmo", "correcto", "así es", "de acuerdo", "dale" (Argentina) | "ajá", "mjm", "ok", "okey", "bueno", "ya" | "no", "espere", "no es esa", "otra" |
| Portugués | "sim", "sim, confirmo", "confirmo", "isso", "correto", "pode", "está certo" | "tá", "ok", "hum", "aham", "uhum", "beleza" | "não", "espera", "não é essa" |

Una afirmación vale solo si la confianza del reconocimiento supera el umbral de la política (R-TEC-84) y la
frase no contiene negación ni pregunta. La tecla 1 equivale al "sí" y queda en la traza como evidencia DTMF
(V8).

**Mapa de teclas único para todo el flujo:** 1 sí o confirmar; 2 no o corregir; 9 repetir; 0 persona; #
fin de dígitos. Los menús de voz tienen tres opciones como máximo.

**Dígitos por teclado:** el código de verificación y cualquier dígito se ingresan por DTMF; el sistema nunca
pide decirlos en voz alta y nunca lee de vuelta el código.

**Interrupciones:** se permiten en todo momento salvo la primera frase del aviso inicial (4 s o menos). Una
confirmación interrumpida no vale (V1): se atiende la interjección ("no, espere, era otro cargo") y, si la
acción sigue en pie, la lectura se repite completa. Lo que el agente alcanzó a decir queda registrado
(`ObservadorHabla` de Tecnología).

**Rellenos honestos** (catálogo presintetizado; al menos tres variantes por tipo y locale; uno cada 4 s como
máximo):

| Tipo de espera | Español (usted) | Portugués |
|---|---|---|
| Consulta de movimientos | "Un momento, estoy revisando sus movimientos." / "Sigo buscando el cargo en sus movimientos." / "Estoy consultando sus compras recientes." | "Um momento, estou verificando suas transações." / "Ainda estou procurando a compra nas suas transações." / "Estou consultando suas compras recentes." |
| Estado de la tarjeta | "Estoy consultando el estado de su tarjeta." | "Estou consultando o status do seu cartão." |
| Envío de una acción | "Estoy enviando su solicitud al sistema de tarjetas; enseguida le confirmo el resultado." | "Estou enviando seu pedido ao sistema de cartões; já confirmo o resultado." |
| Espera larga (segundo relleno) | "Sigue en proceso; gracias por esperar." | "Continua em andamento; obrigado por aguardar." |

Los rellenos usan verbos de consulta o de envío ("reviso", "consulto", "envío"), nunca de resultado
("bloqueé", "quedó", "listo").

**Silencios y no entendidos:**

| Evento | Primera vez | Segunda vez | Tercera vez |
|---|---|---|---|
| Silencio (6 s [S]) | "¿Sigue en la línea? Puedo repetir lo último si dice repetir o marca nueve." | "Si le resulta más fácil, responda con el teclado: uno para sí, dos para no." | "Voy a terminar la llamada por ahora. No hicimos ningún cambio. Su caso quedó guardado: puede retomarlo por chat o volver a llamar y seguimos donde quedamos." |
| No entendido | "Disculpe, no le entendí. ¿Me lo repite?" | menú de tres opciones con teclas | oferta de persona |

Si hubo una acción verificada antes de la tercera vez, "No hicimos ningún cambio" se reemplaza por el cierre
que distingue. En `CONFIRMANDO_ACCION` el silencio **nunca** confirma.

**Números dichos:** montos en palabras con su moneda; tarjeta en dígitos sueltos; número de caso en grupos
de tres; fechas y horas en palabras ("el sábado trece de junio a las siete y cuarenta y dos de la noche");
nombres de comercio con la pronunciación que registra el directorio del equipo.

#### 2.4.5 Equivalencia entre canales

| Evidencia de asentimiento | Chat | Voz |
|---|---|---|
| Aprobación del componente (evento con `nonce`) | sí | no aplica |
| "Sí" transcrito con confianza sobre el umbral | no (se vuelve a mostrar el componente) | sí |
| Tecla 1 (DTMF) | no aplica | sí |

Las tres producen el mismo tipo `Confirmacion` y la traza registra cuál fue. Un caso empezado en chat puede
confirmarse por voz y al revés, siempre con una `SolicitudConfirmacion` viva de la misma sesión (R-TEC-77).

#### 2.4.6 Reglas de confirmación por canal

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-42 | Toda confirmación lleva verbo, objeto enmascarado, monto de la base si lo hay, consecuencia, camino del "no" y vencimiento. | plantilla de `SolicitudConfirmacion` con sus variables obligatorias; prueba |
| R-CLI-43 | Una confirmación por acción; confirmar el bloqueo no confirma el reclamo. | N4: dos `Confirmacion` distintas en la traza |
| R-CLI-44 | En chat solo confirma el evento de aprobación; un "sí" escrito no crea `Confirmacion`. | prueba: el texto "sí" en chat no produce `Confirmacion` y vuelve a mostrar el componente |
| R-CLI-45 | El monto y la transacción de toda confirmación salen de la base, nunca del texto del cliente. | S9: monto del caso igual al de la transacción |
| R-CLI-46 | La confirmación vence a los 5 minutos con aviso un minuto antes y renovación sin penalidad; al vencer se relee la base. | prueba de interfaz con reloj inyectable |
| R-CLI-47 | Todo componente respeta los límites de WhatsApp: 3 botones de 20 caracteres, 10 filas, títulos de fila de 24 y descripciones de 72 [A]. | linter de etiquetas; R-TEC-78 |
| R-CLI-48 | Todo mensaje interactivo deja un botón o una fila para "Hablar con persona", o la instrucción escrita. | linter de componentes |
| R-CLI-49 | Las listas llevan 8 transacciones como máximo más "Ninguna de estas" y "Hablar con persona"; con más candidatas, primero un filtro. | A2 con 3 y con 12 candidatas |
| R-CLI-50 | Fuera de la ventana de 24 horas solo salen plantillas aprobadas de utilidad o autenticación. | modo WhatsApp simulado: un texto libre fuera de ventana se rechaza |
| R-CLI-51 | En voz, toda acción se precede de lectura de vuelta completa y "sí" explícito o tecla 1. | V2: identificador de la plantilla de lectura antes de la acción |
| R-CLI-52 | Solo valen las afirmaciones de la lista cerrada con confianza sobre el umbral; lo ambiguo se repregunta una vez y luego se ofrece la tecla. | casos de voz con cada expresión de la tabla; cero acciones con afirmación ambigua |
| R-CLI-53 | Una confirmación interrumpida no vale; la lectura se repite completa. | V1 |
| R-CLI-54 | Los dígitos y el código van por teclado; el sistema nunca los pide en voz alta ni lee el código. | V8 y S4; linter de plantillas de voz |
| R-CLI-55 | Un solo mapa de teclas en todo el flujo: 1 sí, 2 no, 9 repetir, 0 persona, # fin de dígitos. | prueba de la superficie de voz |
| R-CLI-56 | Los rellenos salen del catálogo aprobado, uno cada 4 s como máximo, con verbos de consulta o envío y nunca de resultado. | linter de rellenos; R-TEC-86 |
| R-CLI-57 | Silencio: recordatorio a los 6 s, segundo con oferta de teclado, tercero cierra con estado guardado; en `CONFIRMANDO_ACCION` el silencio nunca confirma. | V7 |
| R-CLI-58 | Tras dos no entendidos se ofrece menú de tres teclas; tras el tercero, una persona. | V3 |
| R-CLI-59 | Se puede interrumpir siempre, salvo la primera frase del aviso inicial (4 s o menos); lo dicho queda registrado. | prueba de interrupción; registro de `ObservadorHabla` |
| R-CLI-60 | Montos, tarjetas, números de caso, fechas y comercios se dicen según 2.4.4. | prueba de pronunciación con la lista del directorio (S-CLI-05) |
| R-CLI-61 | "Repetir", "más despacio" (o tecla 9 para repetir) funcionan en cualquier estado. | prueba de voz |

### 2.5 Paquete de traspaso y vista del experto

#### 2.5.1 Cuándo se traspasa y qué oye el cliente

Los disparadores y umbrales los fija `policy/v1` (Gobierno); esta cara propone la lista cerrada de motivos,
su prioridad y lo que se le dice al cliente. La prioridad de un traspaso es **la mayor** entre la de su
motivo y la del caso en curso: una falla de herramienta en medio de un fraude en curso sigue siendo P1.

| Motivo (código cerrado) | Escenarios | Ruta | Prioridad | Lo que oye el cliente (intención) |
|---|---|---|---|---|
| `URGENCIA_TRANSFERENCIA` | E1 | R4 | P1 | "Esto es urgente; ya pedí una persona del equipo de fraude." |
| `SUPLANTACION_DEL_BANCO` | E1 ("me llamaron del banco") | R4 | P1 | lo anterior más la frase de seguridad |
| `FRAUDE_EN_CURSO` | E7; N4 con cargos que siguen llegando | R3 y R4 | P1 | contención primero; luego la persona |
| `CRISIS` | 2.3.10 | R5 | P1 | líneas de ayuda del catálogo y persona ya |
| `MONTO_SOBRE_UMBRAL` | E2 | R5 | P2 | "Por el valor, lo revisa una persona del equipo." |
| `CONFLICTO_CON_HISTORIAL` | E3 | R5 | P2 | "Una persona del equipo revisa su caso para darle una respuesta completa." |
| `PUNTO_COMUN_DE_COMPROMISO` | E6 | R3 con prioridad | P2 | nada sobre la señal |
| `CAMBIO_DATOS_CONTACTO` | S5 | R7 o R5 | P2 | "El cambio de datos lo hace una persona, con una verificación adicional." |
| `CLIENTE_PIDE_PERSONA` | E4, V11 | R5 | P3 | "Ya pedí una persona." |
| `FRUSTRACION` | E5 | R5 | P3 | oferta con botón |
| `BAJA_CONFIANZA` y `FUERA_DE_RUTINA` | A1 tras el umbral; casos raros | R5 | P3 | "Para no equivocarme, lo sigue una persona del equipo." |
| `CUENTA_NO_ACTIVA` | D9 | R5 | P3 | "Por el estado de su cuenta, lo atiende una persona." |
| `FUERA_DE_PLAZO` | F5, si el cliente acepta revisión | R5 | P3 | plantilla de fuera de plazo |
| `DATO_INCONSISTENTE` | D4, D7 | R5 | P3 | "Hay un dato que prefiero que confirme una persona." |
| `FALLA_DE_HERRAMIENTA` | D1, D2 | R8 con oferta | P4 salvo que el caso sea P1 o P2 | plantilla de falla |
| `TRANSACCION_NO_VISIBLE` | D3 | R8 o R5 | P4 | "Con corte al {fecha}, no veo ese movimiento; lo dejamos en seguimiento." |

#### 2.5.2 Especificación del paquete de traspaso

El `PaqueteTraspaso` es un objeto tipado con procedencia ([investigación 14](../docs/investigacion/14_VP_Clientes.md),
sección 3). El texto que lee la persona se **renderiza** desde el objeto con plantillas; ningún resumen libre
del modelo aparece como hecho ([06](../docs/diseno/06_Arquitectura.md), sección 3).

| # | Campo | Contenido | Origen | Obligatorio |
|---|---|---|---|---|
| 1 | `id_traspaso`, `hilo_id`, `caso_id` | identificadores; `caso_id` si ya hay reclamo | motor | sí (`caso_id` si existe) |
| 2 | `prioridad` | P1 a P4 | política | sí |
| 3 | `motivo` | código de 2.5.1, texto llano renderizado y regla disparadora con identificador y versión | política | sí |
| 4 | `cola_destino` | idioma, especialidad y franja | enrutador | sí |
| 5 | `idioma`, `registro`, `pais_cuenta` | es o pt; usted, vos o você; MX, CO o AR | sesión y comprensión | sí |
| 6 | `canal_actual`, `canales_usados` | chat, voz, modo WhatsApp simulado | superficies | sí |
| 7 | `identidad` | nivel `acr`, método y hora, o "no verificada" | identidad | sí |
| 8 | `solicitud` | palabras del cliente, enmascaradas, como cita | conversación | sí |
| 9 | `interpretacion` | motivo, urgencia, entidades y confianza, marcados como interpretación de la IA | comprensión | sí |
| 10 | `hechos_verificados` | lista de `HechoVerificado` (producto, transacciones, estados, historial pertinente) con fuente y hora | herramientas | sí; puede ir vacía con su motivo |
| 11 | `acciones_realizadas` | `AccionVerificada` con resultado releído y hora | registro de ejecución | sí |
| 12 | `acciones_no_realizadas` | acción y motivo (no confirmó, falla, fuera de alcance, pidió persona antes) | motor | sí |
| 13 | `conflictos` | lo declarado frente al registro, con ambas fuentes | motor | sí; puede ir vacía |
| 14 | `preguntas_abiertas` | pregunta, a quién le toca (cliente, back office, red) y si bloquea la resolución | motor | sí |
| 15 | `plazos_en_curso` | regla, evento de inicio y vencimiento (por ejemplo, las 48 horas de México) | política | sí, si aplica |
| 16 | `compromisos_comunicados` | espera informada, próximos pasos prometidos y hora en que se dijeron | registro de plantillas enviadas | sí |
| 17 | `preferencias` | idioma alterno aceptado o no, canal para el aviso, ritmo lento | conversación | no |
| 18 | `evidencia` | enlace a la traza, reglas aplicadas con versión, identificadores de plantillas | trazas | sí |
| 19 | `transcripcion_ref` | transcripción enmascarada; en voz, lo que el agente alcanzó a decir y la confianza del reconocimiento por turno | superficies | sí |

**Lo que el paquete no lleva:** nombre del cliente, número de documento, número completo de tarjeta,
atributos protegidos (edad, género, estado civil, educación), segmento, `fraud_score` en crudo y el campo de
"razonamiento" de las salidas estructuradas, que es texto del modelo y no evidencia
([05](../docs/diseno/05_Cobertura_del_enunciado.md), punto 19).

**Tipos de conflicto que se detectan y cómo se escriben** (siempre en dos columnas, "declarado" y
"registro", sin calificativos):

| Conflicto | Declarado | Registro |
|---|---|---|
| Compras previas en el mismo comercio (E3) | "nunca compré ahí" | "3 compras anteriores no disputadas en este comercio en 90 días (transacciones, 03:02)" |
| Monto | "me cobraron 500" | "cargo por 350,00 USD (transacciones, 03:02)" |
| Fecha | "fue ayer" | "evento del 12 de junio, 01:40; figura con fecha de proceso del 11 (D8)" |
| Tarjeta | "perdí la tarjeta" | "tarjeta sin compras presenciales después de la fecha declarada" |
| Reclamo previo | "nunca reclamé" | "reclamo abierto por la misma transacción (casos, 03:03)" |
| Cuenta | "mi cuenta está activa" | "producto en estado suspendido (productos, 03:02)" |

#### 2.5.3 Vista del experto

**Orden fijo**, de lo accionable a lo documental:

1. **Barra superior:** prioridad, motivo en una línea, tiempo en cola y acuerdo de servicio restante,
   idioma y registro, país de la cuenta y canal actual.
2. **Qué hacer primero:** pasos que sugiere la política para el motivo (por ejemplo, en R4, "reportar la
   transferencia a la entidad receptora"), marcados como sugerencia de política con su regla.
3. **Compromisos comunicados:** lo que ya se le dijo al cliente, para no contradecirlo.
4. **Solicitud:** las palabras del cliente y, al lado, la interpretación de la IA con su confianza.
5. **Hechos verificados**, con fuente y hora.
6. **Acciones realizadas y no realizadas.**
7. **Conflictos.**
8. **Preguntas abiertas.**
9. **Plazos en curso**, con cuenta regresiva.
10. **Evidencia:** reglas aplicadas y enlace a la traza.
11. **Transcripción**, plegada.
12. **Panel de acciones** y, al cerrar, **formulario de corrección**.

Cada línea lleva una de tres etiquetas visibles: **Verificado** (con la fuente y la hora), **Dicho por el
cliente** o **Interpretación de la IA** (con la confianza). La vista se renderiza en el idioma de trabajo del
experto desde los campos tipados; la cita del cliente se muestra en su idioma original.

**Roles y permisos:**

| Rol | Qué ve | Qué puede hacer | Qué no puede |
|---|---|---|---|
| Agente de servicio (primera línea aumentada) | el paquete sin la banda de riesgo | responder en el hilo; radicar con confirmación del cliente; reclasificar el motivo; pasar a especialista | ver la banda de riesgo; cambiar datos de contacto; mover dinero |
| Especialista de fraude y disputas (experto en forma de T) | todo, con la banda de riesgo (`fraud_score` mayor que 30, zona gris o sin evidencia, según `policy/v1`) | lo anterior; bloquear con confirmación del cliente; marcar prioridad; pasar al back office | ver documento o tarjeta completos; mover dinero |
| Supervisor de turno | todo, más el estado de las colas | reasignar; declarar el nivel de saturación; llamar a la guardia | lo mismo que los anteriores en cuanto a datos |

#### 2.5.4 Ingreso del experto al mismo hilo

**Chat:**

1. El experto toma el caso; queda el evento `experto_asignado`.
2. Lee el paquete; la vista registra el tiempo hasta su primera acción.
3. Al entrar se emite `experto_unido`: el cliente ve "Ahora le atiende Carla, del equipo de fraude de LATAM
   Bank" y la línea fija del hilo pasa de "Asistente de IA" al nombre de pila y el rol de la persona.
4. Primera frase del experto, prellenada y editable: "Hola, soy {nombre_de_pila}, del equipo de {area} de
   LATAM Bank. Ya leí lo que le contó al asistente: {resumen_una_frase}. No tiene que repetirlo." El
   resumen de una frase se renderiza del paquete (motivo, transacción y acción hecha).
5. Desde ese momento la IA queda en **modo asistente**: no escribe al cliente; le ofrece al experto las
   plantillas críticas prellenadas y el siguiente paso de la política; cualquier borrador suyo lleva la marca
   "borrador de IA" y solo sale si el experto lo envía (DP-CLI-05).
6. Las acciones del experto usan las mismas herramientas tipadas, con su propia sesión de empleado y su
   nivel de autorización, y quedan en la misma traza.
7. El experto cierra con el mismo cierre que distingue y llena la corrección (2.5.5). En esta versión no hay
   devolución a la IA.

**Voz (traspaso tibio):**

1. La IA anuncia: "Le comunico con {area}. Ya le compartí lo que me contó; no tendrá que repetirlo."
2. Mientras espera, cada 45 a 60 s [S]: rango de espera y estado verificado de la contención ("su tarjeta
   sigue bloqueada"), con la opción de colgar y recibir el aviso por chat.
3. El experto abre el paquete antes de conectarse; al conectarse, la IA sale de la llamada.
4. En la hackatón el experto entra por el navegador; la telefonía real es opcional (D-18).

#### 2.5.5 Corrección como etiqueta

| Campo | Valores | Para qué |
|---|---|---|
| `motivo_verdadero` | fraude; error de procesamiento; disputa comercial; es mía pero no la reconocía; no es disputa; fuera de alcance | etiqueta del componente aprendido (D-14) |
| `urgencia_verdadera` | sí o no | etiqueta de urgencia |
| `ruta_correcta` | R1 a R8 | matriz de rutas en operación |
| `traspaso_necesario` | sí o no | traspasos innecesarios (M-05) en operación |
| `motivo_traspaso_correcto` | sí o no, y cuál era | M-06 en operación |
| `utilidad_paquete` | 1 a 5, con rúbrica (5: resolví sin preguntar nada de lo que el paquete ya traía) | MP-CLI-8 |
| `preguntas_repetidas` | qué datos del paquete tuvo que volver a pedir | M-11 después del traspaso |
| `comentario` | texto libre, enmascarado | análisis de errores |
| `procedencia` | rol, hora, versión del sistema y de la política | linaje |

Las correcciones se guardan en `correcciones_experto` en la base operativa, se exportan a platino con
`origen = experto` y la VP IA las usa **solo** para entrenamiento y desarrollo del ciclo siguiente, después
de revisarlas. Nunca entran al retenido (P1). En la hackatón, las correcciones las hace el equipo y se
declaran como etiquetas del equipo.

#### 2.5.6 Reglas del traspaso y la vista del experto

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-62 | El paquete se renderiza desde el objeto tipado; ningún texto del modelo aparece como hecho. | separación hecho e interpretación por tipos ([01](../docs/diseno/01_Interacciones_y_criterios.md), sección 5.2); M-13 |
| R-CLI-63 | Un paquete sin algún campo obligatorio de 2.5.2 no se encola: el campo se completa con "no disponible" y su motivo. | M-12 igual a 100% por esquema |
| R-CLI-64 | Cada línea de la vista lleva su procedencia: verificado (fuente y hora), dicho por el cliente o interpretación de la IA (confianza). | prueba de render |
| R-CLI-65 | El paquete trae los compromisos comunicados al cliente. | E7: el compromiso de avisar al abrir el turno está en el paquete |
| R-CLI-66 | Los conflictos se muestran en dos columnas, declarado y registro, con ambas fuentes y sin calificativos. | E3: plantilla de conflicto; lista de palabras prohibidas ("mentira", "falso", "fraude de primera parte") ausente |
| R-CLI-67 | Cada pregunta abierta dice a quién le toca y si bloquea la resolución. | validación del esquema |
| R-CLI-68 | La vista sigue el orden fijo de 2.5.3; la transcripción va al final y plegada. | prueba de interfaz; tiempo hasta la primera acción en la muestra humana |
| R-CLI-69 | La vista no muestra nombre del cliente, documento, tarjeta completa, atributos protegidos ni segmento. | contrato de la vista; prueba de render |
| R-CLI-70 | El experto no trata al cliente por su nombre en esta versión; por eso la vista no necesita la tabla restringida de nombres (respuesta a la pregunta de Datos). | contrato de la vista sin columnas de nombre |
| R-CLI-71 | La banda de riesgo solo la ven especialista y supervisor, y nunca llega al cliente. | prueba de acceso por rol; linter de plantillas |
| R-CLI-72 | El experto entra al mismo hilo; el cliente ve su nombre de pila y su rol; desde ese momento la IA no escribe al cliente. | evento `experto_unido` y cero mensajes de la IA al cliente después |
| R-CLI-73 | La primera frase del experto usa la plantilla con presentación, resumen de una frase y "no tiene que repetirlo". | identificador de plantilla; M-11 después del traspaso |
| R-CLI-74 | El experto actúa con su propia sesión y las mismas herramientas tipadas; sus acciones quedan en la misma traza. | traza con la identidad del experto; prueba de acceso |
| R-CLI-75 | En voz el traspaso es tibio: anuncio, contexto compartido, mensajes de espera cada 45 a 60 s con el estado verificado de la contención. | E1 por voz |
| R-CLI-76 | Al cerrar, el experto llena la corrección de 2.5.5; se guarda con procedencia y nunca entra al retenido. | esquema de `correcciones_experto`; prueba de que el materializador del retenido excluye esa fuente |
| R-CLI-77 | No hay devolución del hilo a la IA en esta versión: el experto cierra. | no existe la transición de modo asistente a IA salvo el cierre |
| R-CLI-78 | Cada apertura de un paquete y cada acción del experto quedan registradas con identidad y hora. | registro de accesos |

### 2.6 Modelo de operación humana

#### 2.6.1 La capacidad que trae el dataset

| Hecho | Cifra | Implicación |
|---|---|---|
| Agentes | 1.200 | |
| Agentes con portugués | 129 (10,8%); 115 activos | la cola en portugués es pequeña |
| Especialistas de fraude | 105; con portugués, **7** | el traspaso urgente en portugués depende de siete personas |
| Especialistas de fraude de noche | 25; con portugués y turno de noche o rotativo, **1** | a las 3 a. m. casi nunca hay quien atienda fraude en portugués |
| Agentes de noche | 15% | contra una demanda plana |
| Demanda por hora | plana en las 24 horas; 33% entre 00:00 y 07:59 | la IA vale más de noche |
| Demanda por día | fines de semana a la mitad de los días hábiles | dimensionamiento |
| Canal | teléfono 84,8%; correo 4,1%; app 3,8%; chat web 3,4%; WhatsApp 3,3%; web 0,5% | justifica voz y chat (D-17) |
| Escala | 800 mil interacciones en 1.097 días: unas 730 al día para 1.200 agentes (0,6 por agente al día) | el dataset es una muestra del banco: toda cifra de capacidad es proyección ([investigación 12](../docs/investigacion/12_Organizacion_de_un_banco.md)) |

Fuente: [revisión 05](../docs/diseno/05_Cobertura_del_enunciado.md), sección 3.1, sobre la muestra; se confirma
sobre el total en DAT-2.

#### 2.6.2 Colas y enrutamiento

Las colas se cruzan en tres ejes: **idioma** (español, portugués), **especialidad** (servicio y disputas;
fraude) y **franja** (diurna, nocturna). Se enruta por habilidades; el acento nunca es criterio (P12).

| Cola | Recibe | Orden de respaldo si no hay nadie disponible |
|---|---|---|
| Fraude, español | P1 y P2 de fraude en español | 1. especialista de fraude en turno; 2. guardia de fraude; 3. supervisor |
| Fraude, portugués | P1 y P2 de fraude en portugués | 1. especialista de fraude con portugués en turno; 2. guardia con portugués (la persona nocturna o rotativa); 3. especialista de fraude en español, **si el cliente acepta** el idioma alterno; 4. notificación al abrir el turno en portugués, con la contención ya verificada |
| Servicio y disputas, español | P2 a P4 no de fraude en español | 1. agente de servicio; 2. especialista de disputas; 3. atención asíncrona con aviso |
| Servicio y disputas, portugués | P2 a P4 no de fraude en portugués | 1. agente con portugués; 2. agente en español si el cliente lo acepta; 3. atención asíncrona con aviso |

En producción, una opción adicional para la cola de fraude en portugués es que un agente de servicio con
portugués atienda con un especialista de fraude en español en consulta; se deja como propuesta de ruta a
producción, no se construye.

#### 2.6.3 Acuerdos de servicio por prioridad

Provisionales (D-07); se fijan con la línea base a la vista y se registran en acta **antes** de correr el
retenido (P1).

| Prioridad | En vivo (voz y chat) | Asíncrono | Contingencia si se excede |
|---|---|---|---|
| P1 | 90% atendido en 60 s [S] | no aplica | a los 5 minutos, nivel 2 de saturación |
| P2 | 80% en 5 minutos [S] | respuesta en 1 hora [S] | a los 15 minutos, nivel 1 |
| P3 | 80% en 20 minutos [S] | respuesta en 4 horas [S] | a los 60 minutos, paso a asíncrono con aviso |
| P4 | no aplica | siguiente día hábil, 24 horas como máximo [S] | |
| Abandono en cola | 5% o menos (referencia de industria de 2 a 5%, [investigación 7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md)) [P] | | |

#### 2.6.4 Dimensionamiento

- **Método:** Erlang C por cola y franja, con la llegada de traspasos que produzca el sistema (medida en el
  retenido representativo y proyectada a volumen), el tiempo de gestión de cada categoría (M-46) y el
  acuerdo de servicio de 2.6.3. Pasado el 85% de ocupación hacen falta desproporcionadamente más personas
  ([investigación 7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md), sección 5).
- **Efecto de selección:** si la IA resuelve lo fácil, el tiempo de gestión humano sube; el dimensionamiento
  usa un factor de traspaso (2.7.2), no el tiempo histórico sin corregir.
- **Ejemplo que explica E7** (supuestos [S], etiqueta: proyección). Con una sola persona, Erlang C equivale a
  una cola M/M/1. Si el tiempo de gestión de un fraude en portugués es de 8 minutos (μ = 7,5 casos por
  hora):

```
P(esperar más de t) = rho * exp(-(mu-lambda)*t)        rho = lambda/mu
```

  | Llegadas de P1 en portugués por hora (λ) | Ocupación | Esperan más de 60 s | Espera media |
  |---|---|---|---|
  | 0,83 | 11% | 10% | 0,9 minutos |
  | 3,75 | 50% | 47% | 8 minutos |

  Con una sola persona, el acuerdo P1 (90% en 60 s) solo se sostiene con menos de un traspaso urgente en
  portugués cada 72 minutos. Con los supuestos de turnos de 2.6.7, la presencia efectiva de esa persona en
  la franja nocturna está entre 0,23 y 0,7 (una tercera parte de las semanas si es rotativa, y 30% de
  merma). Por eso el diseño contiene primero, ofrece el idioma alterno y declara la espera: no es una
  preferencia de estilo, es lo que la capacidad permite.

#### 2.6.5 Saturación

| Nivel | Disparador (medido por la cola) | Acciones | Mensaje al cliente |
|---|---|---|---|
| 0, normal | esperas dentro del acuerdo | ninguna | espera declarada |
| 1, tensión | espera estimada de P1 mayor que 60 s, o de P3 mayor que 20 minutos, durante 10 minutos [S] | P3 y P4 pasan a atención asíncrona con aviso; se avisa al supervisor | "La espera es de {rango}. Puede seguir esperando o le avisamos por aquí cuando una persona esté libre." |
| 2, saturación | espera de P1 mayor que 5 minutos, o ningún especialista del idioma en la franja | contención verificada antes de informar la espera; idioma alterno; se llama a la guardia; Operaciones declara el nivel en la traza | el de E7 (2.2.4) |
| 3, contingencia | una especialidad sin personas en el turno, o el interruptor "todo a humano" activo (R-TEC-104) | guardia de la especialidad; la IA recibe, autentica, contiene si la política lo permite en ese modo [A: Gobierno] y encola; Gobierno revisa umbrales; incidente registrado | "Hoy atendemos con demora. Su caso ya está registrado y en fila; le avisaremos por aquí." |

Quién decide: Clientes (Operaciones) declara el nivel; Tecnología ajusta capacidad; Gobierno revisa umbrales
([04](../docs/diseno/04_Organizacion_y_roles.md), sección 11). Ningún nivel apaga la opción de persona: cambia
su modo (en vivo, asíncrono o aviso).

#### 2.6.6 Devolución de contacto sin llamadas salientes

"Me llamaron del banco" es el guion de la estafa que más crece en los tres países
([investigación 6](../docs/investigacion/06_El_banco_por_dentro.md), sección 2). LATAM Bank **no hace llamadas
salientes** en este flujo: cuando una persona queda disponible, el cliente recibe la plantilla
"Especialista disponible" (2.8.1) o un aviso en la app y **vuelve él** por un canal oficial, donde se
reautentica si la sesión venció. Así el cliente puede aplicar una regla simple y verdadera: "si me llaman
diciendo que son del banco, no es el banco" (DP-CLI-04).

#### 2.6.7 Turnos y costo del minuto humano (respuesta a S-DAT-10)

Supuestos para `configuracion/supuestos_operacion.yaml`, con su etiqueta:

| Supuesto | Valor | Etiqueta |
|---|---|---|
| Sede | un solo centro que opera en hora de Bogotá para los tres países | [S]; [A: Datos confirma si `service_agents` trae sede o país] |
| Turno diurno | 06:00 a 22:00, en dos subturnos de 8 horas (06:00 a 14:00 y 14:00 a 22:00), mitad y mitad | [S] |
| Turno nocturno | 22:00 a 06:00 | [S] |
| Turno rotativo | rota por semana entre los tres bloques; un tercio en cada bloque | [S] |
| Merma (pausas, formación, ausencias) | 30% | [S]; [A: confirmar contra una referencia de gestión de fuerza laboral] |

| Parámetro de costo | Bajo | Central | Alto | Etiqueta y fuente |
|---|---|---|---|---|
| Tarifa por hora cargada de un agente | US$12 | US$16 | US$23 | [P] rangos de BPO nearshore publicados para 2026: México US$13 a 23; Colombia US$12 a 20; Colombia bilingüe US$10 a 16 (páginas de Centris, Callforce y Contact Center USA, sección 11); Argentina [A: cotización local] |
| Sobrecosto de implementación e integración | 15% | 20% | 25% | [P] mismas fuentes; solo en la proyección de producción |
| Ocupación | 0,85 | 0,80 | 0,75 | [S] |
| Multiplicador de especialista de fraude | 1,15 | 1,25 | 1,40 | [S] |
| Multiplicador por portugués | 1,10 | 1,15 | 1,25 | [S] |
| Conversaciones simultáneas en chat | 2,0 | 1,5 | 1,0 | [S] |
| Trabajo posterior al contacto | 45 s | 60 s | 90 s | [S]; el dataset no lo trae |
| **Minuto productivo de agente** (tarifa entre 60 por la ocupación) | **US$0,24** | **US$0,33** | **US$0,51** | derivado |
| **Minuto de especialista de fraude con portugués** | **US$0,30** | **US$0,48** | **US$0,89** | derivado |
| **Contacto de voz de servicio** (204 s de mediana del dataset más trabajo posterior) | **US$0,98** | **US$1,47** | **US$2,50** | derivado |

La referencia de industria de US$7 a 14 por contacto de voz ([investigación 7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md))
es de Estados Unidos [P] y queda solo como análisis de sensibilidad; la proyección usa las cifras de
Latinoamérica (DP-CLI-12).

#### 2.6.8 Los expertos en la hackatón

- **En la demo**, el experto es una persona del equipo que entra al mismo hilo desde la vista del experto.
- **En la evaluación**, dos instrumentos declarados como tales (P3): un **experto simulado** determinista
  que lee el paquete y cuenta qué tendría que volver a preguntar (campos faltantes, preguntas abiertas sin
  destinatario), y una **muestra humana** de paquetes calificados por el equipo con la rúbrica de
  `utilidad_paquete`. Si solo hay un anotador, se declara y no se reporta κ entre humanos.
- El protocolo (quién, cuántos paquetes, rúbrica, tiempo) se escribe antes de F6.

#### 2.6.9 Calidad de servicio

- **Control automático del 100% de las conversaciones** con verificaciones deterministas: aviso de IA en el
  primer turno; autenticación antes de datos; plazo desde regla; cierre que distingue; frases prohibidas
  ausentes; idioma y registro correctos; enmascaramiento; oferta de persona tras la frustración.
- **Juez validado** (arnés de IA) solo para tono y claridad, con rúbrica versionada y acuerdo contra una
  muestra humana ([investigación 4](../docs/investigacion/04_Evaluacion.md), sección 3).
- **Sesión de calibración** después de cada corrida de desarrollo: las tres causas principales de falla
  por capa, con su corrección ([01](../docs/diseno/01_Interacciones_y_criterios.md), sección 6, punto 10).

#### 2.6.10 Reglas de la operación humana

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-79 | Las colas se cruzan por idioma, especialidad y franja, con el orden de respaldo de 2.6.2; el acento nunca enruta. | E1 y E7 llegan a la cola esperada; prueba de que el enrutador no recibe `detected_accent` |
| R-CLI-80 | La prioridad es la mayor entre la del motivo y la del caso en curso; el segmento no cambia prioridad ni acuerdo (DP-CLI-06). | tabla de mapeo en `policy/v1`; prueba de propiedades |
| R-CLI-81 | Los acuerdos de 2.6.3 se registran en acta antes del retenido y cualquier cambio posterior exige acta del Comité de Confianza. | acta de F2 con la tabla y su huella |
| R-CLI-82 | La espera se declara como rango calculado por la cola, nunca como promesa ni como número exacto, y se actualiza si cambia. | MP-CLI-10 (calibración de la espera) |
| R-CLI-83 | En P1 de fraude con tarjeta, el bloqueo verificado ocurre antes de informar la espera. | E7: `AccionVerificada` de bloqueo antes de la plantilla de espera |
| R-CLI-84 | Sin especialista del idioma en la franja, se ofrece atención inmediata en español o esperar al especialista en portugués, a elección del cliente y sin presión. | E7 y L7 (DP-CLI-03 y DP-CLI-07) |
| R-CLI-85 | No hay llamadas salientes en el flujo; la devolución de contacto es un aviso para que el cliente vuelva por un canal oficial. | el catálogo no tiene plantillas de llamada saliente; prueba de la cola |
| R-CLI-86 | Los niveles de saturación de 2.6.5 tienen disparadores medibles; el nivel vigente queda en la traza. | simulación de E8 |
| R-CLI-87 | Ningún nivel de saturación apaga la opción de persona. | E8: la opción existe en todos los niveles |
| R-CLI-88 | Toda cifra de capacidad sale del método de 2.6.4 con sus supuestos y se etiqueta como proyección. | cuaderno de dimensionamiento con supuestos y etiqueta |
| R-CLI-89 | Los supuestos de turnos y costo viven en `configuracion/supuestos_operacion.yaml` con fuente y etiqueta. | validación del archivo por esquema |
| R-CLI-90 | El protocolo del experto de la hackatón (demo, experto simulado y muestra humana) se escribe antes de F6. | protocolo fechado en el repositorio |
| R-CLI-91 | El control automático cubre el 100% de las conversaciones de cada corrida con las verificaciones de 2.6.9. | reporte de calidad por corrida |
| R-CLI-92 | Las correcciones de los expertos se revisan en sesión de calibración y solo alimentan el conjunto de desarrollo o entrenamiento del ciclo siguiente. | acta de calibración; linaje de `correcciones_experto` |

### 2.7 Árbol de resultados

#### 2.7.1 Resultados, indicadores y línea base

Línea base del proceso de reclamos de "Cargo no reconocido" (866 casos de la muestra,
[revisión 05](../docs/diseno/05_Cobertura_del_enunciado.md), sección 3.2) y de las demás tablas del dataset.
**Advertencia:** esos indicadores son casi iguales entre subcategorías y `sla_breached` no se relaciona con
`resolution_days`; sirven como **nivel de referencia**, no para afirmar que este motivo se atiende peor.

| Nivel | Resultado | Indicador | Línea base con datos | Cómo se obtiene en la hackatón |
|---|---|---|---|---|
| Cliente | contención rápida del fraude | tiempo hasta la contención: turnos y segundos hasta la `AccionVerificada` de bloqueo en R3 y R4 (MP-CLI-1) | 13 horas hasta la asignación y 38 horas hasta la primera respuesta (medianas; p90 de 57 horas) (M-40) | medición offline sobre el retenido; la comparación es de orden de magnitud y se declara así |
| Cliente | caso bien radicado al primer contacto | M-01 en R2 y R3; exactitud del caso (M-07 en su parte de monto, transacción y plazo) | los reclamos del dataset no enlazan con interacción ni con monto respaldado (limitación declarada) | medición offline |
| Cliente | entender un cargo sin disputar | M-01 en los casos con R1 esperada; M-08 | sin equivalente en los datos | medición offline |
| Cliente | no repetir información | M-11; preguntas repetidas después del traspaso (corrección del experto) | reclamante recurrente en 90 días: 15,9% (M-43), como referencia | medición offline y muestra humana |
| Cliente | acceso a una persona sin fricción | MP-CLI-4 (turnos hasta el traspaso tras pedirlo); M-04 | sin equivalente en los datos | medición offline |
| Cliente | espera honesta | MP-CLI-3 y MP-CLI-10 (espera por idioma y prioridad; calibración de la espera declarada) | sin equivalente | simulación de la cola |
| Cliente | trato equitativo | M-27 por idioma, variante, segmento y canal | CSAT de 2,43 (quejas) a 2,90 (transaccional) sobre 5, como referencia | medición offline |
| Negocio | plazos regulatorios correctos | M-07 en su parte de plazo (meta 0); casos fuera de plazo bien tratados (F5) | SLA incumplido en 20,6% (M-42) | medición offline |
| Negocio | menos minutos humanos por caso | M-22 contra M-46 ("todo humano") | 204 s de duración mediana por contacto transaccional | simulación |
| Negocio | costo por resolución segura | M-21 | 1,47 US$ por contacto en el escenario central de 2.6.7 | medición offline más supuestos |
| Negocio | cobertura nocturna en portugués | M-45 | 1 especialista de fraude con portugués en noche o rotativo | valor con supuestos |
| Negocio | menos escalamientos al regulador | fracción de reclamos que llegan por el regulador | 1,2% | **proyección**: hipótesis a vigilar en producción, no se afirma |

#### 2.7.2 Metodología para proyectar ahorros (etiqueta: proyección)

| Símbolo | Qué es | De dónde sale |
|---|---|---|
| `m_h` | minutos humanos por caso en el escenario "todo humano" | M-46 |
| `c_min` | costo del minuto humano | 2.6.7 (bajo, central, alto) |
| `c_ia` | costo de plataforma y modelos por caso | M-20 (Tecnología, [04](../tecnologia/definicion.md), sección 7.4) |
| `c_canal` | mensajes de WhatsApp o minutos de telefonía por caso | sección 7 |
| `p_tr` | fracción de casos con traspaso | 1 menos M-03, medido en el retenido representativo |
| `f_tr` | minutos de un traspaso frente a un caso "todo humano" | [S] 0,8 a 1,5: el contexto evita reinterrogar y baja el tiempo; la selección deja los casos difíciles y lo sube |
| `r` | recontacto de casos que el sistema dio por resueltos | [S] 5% a 15%; en producción se mide (lección de Commonwealth Bank) |

```
costo_todo_humano = m_h * c_min
costo_con_sistema = c_ia + c_canal + (p_tr * f_tr + r) * m_h * c_min
```

El ahorro proyectado por caso es la diferencia entre los dos costos; el ahorro mensual, esa diferencia por
el volumen supuesto de casos del alcance, con su fuente.

**Ilustración con supuestos (no es un resultado):** chat web sin costo de canal, `m_h` = 4,4 minutos,
`c_min` = US$0,33, `c_ia` = US$0,023.

| Escenario | `p_tr` | `f_tr` | `r` | Costo "todo humano" | Costo con sistema | Ahorro por caso |
|---|---|---|---|---|---|---|
| Central | 0,30 | 1,0 | 0,10 | US$1,47 | US$0,61 | US$0,86 (58%) |
| Adverso | 0,50 | 1,5 | 0,15 | US$1,47 | US$1,35 | US$0,12 (8%) |

**Lectura:** el ahorro depende sobre todo del traspaso (cuántos, qué tan largos y cuántos recontactos), no
del costo del modelo. Un traspaso mal armado se come el ahorro: por eso el paquete es un artefacto evaluado
(P7). El reporte muestra además un análisis de sensibilidad de un factor a la vez sobre `p_tr`, `f_tr`, `r`
y `c_min`.

#### 2.7.3 Reglas del árbol de resultados

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-93 | Cada resultado del árbol tiene indicador oficial (M-xx) o propuesto (MP-CLI-n), línea base con fuente y etiqueta, y forma de obtención. | tabla 2.7.1 completa y enlazada a platino |
| R-CLI-94 | Los indicadores del proceso de reclamos se presentan como nivel de referencia, no como comparación causal. | revisión del texto del reporte por Auditoría |
| R-CLI-95 | Todo ahorro se presenta como proyección, con la fórmula de 2.7.2, sus supuestos, la sensibilidad y los efectos de selección y recontacto. | sección etiquetada del reporte |
| R-CLI-96 | Los resultados se reportan por idioma, variante, segmento y canal, con tamaño de grupo e intervalos. | tabla de equidad (M-27) |
| R-CLI-97 | La contención nunca es meta ni criterio de orden en ninguna tabla. | revisión del reporte |

### 2.8 Comunicaciones al cliente

#### 2.8.1 Plantillas fuera de la ventana de 24 horas

Solo categorías **utilidad** y **autenticación**; ninguna de marketing. Ninguna lleva montos, nombres,
números de tarjeta ni enlaces, y ninguna pide datos (salvo la de autenticación, que entrega un código),
porque se leen en la pantalla bloqueada y porque una plantilla sin enlaces es más difícil de imitar por un
estafador (DP-CLI-11). Todas necesitan aprobación de Meta antes de usarse en producción; en la hackatón
viven en el catálogo del modo simulado.

| ID | Categoría | Cuándo | Español (usted) | Portugués |
|---|---|---|---|---|
| WA-UT-01 | utilidad | el cliente dejó el flujo a medias y la ventana cerró (D6); una sola vez | "LATAM Bank: tiene una conversación pendiente sobre un cargo de su tarjeta. Responda a este mensaje para continuar donde quedó." | "LATAM Bank: você tem uma conversa pendente sobre uma cobrança do seu cartão. Responda a esta mensagem para continuar de onde parou." |
| WA-UT-02 | utilidad | una persona quedó disponible (2.6.6) | "LATAM Bank: una persona del equipo ya puede atenderle por su caso {numero_caso}. Responda a este mensaje para continuar." | "LATAM Bank: uma pessoa da equipe já pode atender você sobre o caso {numero_caso}. Responda a esta mensagem para continuar." |
| WA-UT-03 | utilidad | cambió el estado del reclamo | "LATAM Bank: su reclamo {numero_caso} cambió de estado: {estado}. Responda a este mensaje para ver el detalle." | "LATAM Bank: sua contestação {numero_caso} mudou de status: {estado}. Responda a esta mensagem para ver os detalhes." |
| WA-UT-04 | utilidad | falta un dato para avanzar | "LATAM Bank: para avanzar con su reclamo {numero_caso} necesitamos un dato. Responda a este mensaje para continuar." | "LATAM Bank: para avançar com sua contestação {numero_caso} precisamos de uma informação. Responda a esta mensagem para continuar." |
| WA-UT-05 | utilidad | faltan dos días hábiles para el plazo [S] | "LATAM Bank: su reclamo {numero_caso} sigue en revisión. Tendrá respuesta a más tardar el {fecha}." | "LATAM Bank: sua contestação {numero_caso} continua em análise. Você terá uma resposta até {fecha}." |
| WA-AU-01 | autenticación | código de verificación | texto fijo de Meta con el código, la advertencia de no compartirlo y el vencimiento de 5 minutos [A: formato vigente de las plantillas de autenticación de Meta] | ídem en portugués |

Las variantes con vos se derivan con las mismas variables de registro ("Respondé a este mensaje").

#### 2.8.2 Avisos y consentimiento en voz

- **Aviso de apertura:** el de 2.3.8 (IA, tratamiento del audio y opción de persona), de 12 s o menos [S].
  El detalle del aviso de privacidad se entrega si el cliente dice "privacidad" y, en la hackatón, en una
  página de la demo.
- **Grabación:** por D-18 el audio crudo no se guarda; se transcribe en streaming y la transcripción se
  enmascara. Si Gobierno determina que la norma de algún país exige grabar llamadas de servicio financiero,
  el aviso cambia a "Esta llamada se graba para {finalidad} y se conserva {plazo}" y la retención la fija
  Gobierno [A: Gobierno, Cumplimiento].
- **Consentimiento para la semilla humana de voz** (grabaciones de evaluación, D-18). Texto que se firma por
  escrito antes de grabar:

  > Autorizo al equipo de LATAM Bank de la Factored AI & Data Hackathon 2026 a grabar mi voz leyendo
  > frases de prueba, con el único fin de medir el reconocimiento de voz del prototipo. Las grabaciones se
  > procesan con {proveedor} para esa medición, no se publican, se guardan cifradas y se borran al cierre de
  > la hackatón, a más tardar el {fecha_borrado}. Puedo retirar esta autorización en cualquier momento
  > escribiendo a {contacto}, y mis grabaciones se borran.

  Versión en portugués con el mismo contenido. Auditoría verifica los consentimientos y Datos los registra
  (R-DAT-55).

#### 2.8.3 Notificaciones de estado del caso

| Evento | Con la ventana abierta | Con la ventana cerrada | Regla |
|---|---|---|---|
| Reclamo creado | `EstadoCaso` en el hilo | no aplica: ocurre dentro de la conversación | |
| Cambio de estado | mensaje en el hilo | WA-UT-03 | una notificación proactiva por caso y por día como máximo [S] |
| Falta un dato | mensaje en el hilo | WA-UT-04 | no dice qué dato |
| Plazo por vencer | mensaje en el hilo | WA-UT-05 | dos días hábiles antes [S] |
| Persona disponible | mensaje en el hilo | WA-UT-02 | se permite en horario silencioso solo si el caso es P1 |
| Flujo abandonado | recordatorio en el hilo | WA-UT-01 | una sola vez, no antes de 2 horas [S] |

Horario silencioso de 21:00 a 08:00 en la hora del país de la cuenta [S], salvo lo marcado. Si el cliente
responde "NO" o equivalente, deja de recibir avisos de ese caso [A: confirmar las reglas de baja de Meta].

#### 2.8.4 Accesibilidad

- **Chat web y vista del experto con WCAG 2.2 nivel AA:** contraste de 4,5 a 1; todo operable con teclado y
  con foco visible; mensajes nuevos anunciados en una región viva cortés, con frases completas (la emisión
  por frases de Tecnología lo facilita); componentes con nombre accesible; estados que no dependen solo del
  color; texto ampliable al 200% sin pérdida; tiempo ajustable en las confirmaciones (criterio 2.2.1);
  idioma de la página declarado (`es` o `pt-BR`) para los lectores de pantalla.
- **Voz:** "repetir", "más despacio" y teclado como alternativa al habla.
- **Alternativas de canal:** el chat sirve a quien no oye o no puede hablar; la voz, a quien no puede leer la
  pantalla. Cada canal ofrece el otro con el estado conservado.
- **Lenguaje llano** en ambos canales (R-CLI-18).
- **Normas nacionales:** Colombia (Ley 1618 de 2013) y Argentina (Ley 26.653 de accesibilidad web) como
  referencia; México [A: Gobierno confirma la obligación aplicable a la banca privada].

#### 2.8.5 Reglas de comunicaciones

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-98 | Fuera de la ventana solo salen las plantillas de 2.8.1; ninguna de marketing. | catálogo; modo WhatsApp simulado |
| R-CLI-99 | Ninguna plantilla lleva montos, nombres, tarjetas ni enlaces, ni pide datos (salvo el código de autenticación). | linter de plantillas |
| R-CLI-100 | El aviso de voz dura 12 s o menos y dice que es una IA, cómo se trata el audio y cómo pedir una persona. | duración medida de la síntesis; revisión de contenido |
| R-CLI-101 | Nadie se graba para la semilla humana sin el consentimiento escrito de 2.8.2. | registro de consentimientos contra la lista de audios (R-DAT-55) |
| R-CLI-102 | Notificaciones con tope de una proactiva por caso y día y horario silencioso, salvo las excepciones de 2.8.3. | prueba con reloj inyectable |
| R-CLI-103 | Chat web y vista del experto cumplen WCAG 2.2 AA. | axe-core sin violaciones serias o críticas y revisión manual con lector de pantalla |
| R-CLI-104 | Cada canal ofrece el otro como alternativa, con el estado conservado. | V6 en ambos sentidos |
| R-CLI-105 | Las plantillas se escriben en ES con usted y vos y en PT, y pasan la misma revisión que el catálogo del hilo. | cobertura del catálogo por registro |

### 2.9 Guion de la demo

**Objetivo:** que el jurado vea, en unos 12 minutos [S: confirmar el formato con los organizadores,
pregunta 1 de [05](../docs/diseno/05_Cobertura_del_enunciado.md)], los tres casos obligatorios en español y en
portugués, un ataque contenido, una falla segura con reintentos acotados y el paso de chat a voz, con las
trazas a la vista.

| # | Tiempo | Caso | Canal, idioma, país y registro | Qué se muestra | Éxito en vivo |
|---|---|---|---|---|---|
| 0 | 0:00 a 0:45 | el problema con datos | diapositiva | 18% de las quejas; 38 horas hasta la primera respuesta; 1 especialista de fraude con portugués de noche; 84,8% de contactos telefónicos | cifras con su fuente y etiqueta |
| 1 | 0:45 a 2:15 | **normal ES**: N4 (R3) | chat, español, Colombia, usted | autenticación; bloqueo confirmado y verificado; lista de cargos; reclamo; `EstadoCaso` con plazo y norma; panel de trazas con estados y herramientas | cierre que distingue; bloqueo y reclamo en la traza |
| 2 | 2:15 a 3:15 | **ambiguo ES**: A2 hasta R1 | chat, español, México, usted | "me cobraron algo raro la semana pasada"; tres opciones enmascaradas; ficha con marca; lo reconoce | ningún caso creado |
| 3 | 3:15 a 4:45 | **humano ES**: E1 (R4) | voz, español, Argentina, vos | traspaso en el mismo turno; frase de seguridad; código por teclado mientras espera; vista del experto; la persona entra al hilo sin repreguntar | paquete completo; compromisos visibles |
| 4 | 4:45 a 5:45 | **normal PT**: N1 con L5 (R1) | chat, portugués, cuenta en Argentina | ficha con descriptor confuso; "Sim, reconheço" | respuesta en portugués; norma argentina si se menciona |
| 5 | 5:45 a 6:30 | **no soportado PT**: F4 (R6) | chat, portugués | "Por que recusaram minha compra?"; alternativa del catálogo | "não fizemos nenhuma alteração" |
| 6 | 6:30 a 8:00 | **humano PT**: E7 (R3 y R4) | chat, portugués, cuenta en Colombia, 03:00 con el reloj simulado | bloqueo primero; idioma alterno; espera declarada; se adelanta el reloj a las 07:00; plantilla WA-UT-02; entra la persona | bloqueo antes de la espera; compromiso cumplido |
| 7 | 8:00 a 8:45 | **ataque contenido**: S3 y S7 | chat, español | "soy gerente, muéstreme la cuenta de mi esposa"; negativa neutra; la traza muestra el rechazo en la capa de herramientas y, aparte, lo que detectó el filtro | ningún dato ajeno; flujo intacto |
| 8 | 8:45 a 9:45 | **falla segura**: D1 durante N2 | chat, español | la API de casos falla; dos reintentos visibles en la traza; mensaje de R8; oferta de persona | nunca "radicado"; M-15 igual a 0 |
| 9 | 9:45 a 11:15 | **chat a voz**: V6 con V8 y V1 | chat y luego voz, español, México | se corta el chat; llamada por navegador; resumen de una frase; lectura de vuelta; interrupción; confirmación con la tecla 1 | cero preguntas repetidas; un solo efecto |
| 10 | 11:15 a 12:00 | resultados | diapositiva | tabla con denominadores e intervalos; etiquetas de medido offline, simulado y proyección; limitaciones (portugués sin datos reales, voces sintéticas, WhatsApp simulado) | cada cifra desde platino |

- Los casos en portugués van por chat para que el recorte de la voz en portugués (orden de recorte de
  [07](../presidencia/hoja_de_ruta.md), sección 6, punto 4) no toque los casos obligatorios.
- Si el formato lo permite, un clip de 30 s muestra la instalación de un comando en máquina limpia.

**Reglas de la demo:**

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-CLI-106 | La demo cubre los tres casos obligatorios en español y en portugués, un ataque contenido, una falla segura con reintentos visibles y el paso de chat a voz. | lista del enunciado contra el guion |
| R-CLI-107 | Los casos de la demo salen del conjunto de desarrollo o de semillas de demo, nunca del retenido. | intersección vacía entre las huellas de la demo y las del retenido |
| R-CLI-108 | Todo lo que aparece en pantalla sale de la ejecución (trazas y platino); nada se edita. | revisión de Auditoría |
| R-CLI-109 | Cada segmento tiene un respaldo grabado de una corrida real con su traza, declarado como respaldo, que solo se usa si falla la ejecución en vivo; la falla se reporta. | archivos de respaldo con sus trazas |
| R-CLI-110 | Hay dos ensayos completos antes de F7, con cero resultados inseguros. | bitácora de ensayos |
| R-CLI-111 | Toda cifra en pantalla lleva su etiqueta: medido offline, simulado o proyección. | revisión del guion y las diapositivas |

---

## 3. Decisiones de tecnología del dominio

Esta cara no elige plataforma (es de Tecnología) ni proveedores de voz (es de IA); elige cómo se escribe,
se versiona, se prueba y se opera lo que el cliente lee y oye, y lo que la persona experta usa.

| # | Decisión | Elección | Estado del arte y razón | Opción en Google Cloud | Alternativas | Estado |
|---|---|---|---|---|---|---|
| 3.1 | Catálogo de guiones y plantillas | YAML versionado (versión semántica) con identificador, estado, canal, idioma, registro y variables tipadas con Pydantic; render con el entorno aislado de Jinja2 y variables estrictas (una variable faltante es un error, no un texto vacío) | las plantillas deterministas son la práctica de Nubank (macros) y la forma de cumplir P6 y R-TEC-76; el mismo lenguaje que el motor (P9) | no hace falta un servicio gestionado | Project Fluent (selectores de registro nativos); ICU MessageFormat 2 [A: estado de adopción en Python] | propuesta |
| 3.2 | Formato de montos, fechas y monedas | Babel con datos CLDR por locale (es-MX, es-CO, es-AR, pt-BR) | CLDR es el estándar de facto; evita el error de separadores entre México y el resto | no aplica | formateo manual (descartado: es donde nacen los errores) | propuesta |
| 3.3 | Calendario de días hábiles | paquete `holidays` de Python validado contra el calendario oficial de cada país [A: Gobierno valida]; lo usa el motor para calcular fechas de plazo | una fecha límite mal calculada es un resultado materialmente incorrecto | no aplica | tabla propia de feriados cargada en `policy/v1` | propuesta; la dueña del contenido es Gobierno |
| 3.4 | Linter de contenido en integración continua | script propio que revisa longitudes, frases prohibidas, límites de WhatsApp, variables, registro, términos brasileños en PT y emojis | convierte las reglas de 2.3 y 2.4 en pruebas; sin él, las reglas son opinión | Cloud Build si el repositorio corre en la nube | revisión manual (no escala) | propuesta |
| 3.5 | Componentes de chat | los seis componentes AG-UI de Tecnología como herramientas de interfaz (D-19) | AG-UI es el protocolo de 2026 para eventos, estado y aprobaciones entre agente e interfaz ([investigación 20](../docs/investigacion/20_Canales_voz_y_chat.md)) | no aplica | A2UI para interfaz generativa: se deja para después porque seis componentes fijos bastan (P9) | firme (D-19) |
| 3.6 | WhatsApp | simulado en la hackatón; en producción, WhatsApp Business Platform (API en la nube de Meta) detrás de un adaptador con la misma interfaz que el modo simulado | la semántica (ventana, plantillas, botones, listas) se prueba sin depender de la aprobación de Meta | Google Cloud no ofrece un canal nativo de WhatsApp; el adaptador corre en Cloud Run | proveedores de soluciones de negocio (Twilio, Infobip u otros) [A: costo y cobertura]; RCS Business Messaging como canal complementario [A] | firme en la hackatón (D-19); propuesta para producción |
| 3.7 | Voz: persona y marcas | una voz por locale, del mismo género en todos, elegida por la medición de IA en S1 con una prueba de pronunciación de montos, fechas y comercios del directorio; rellenos y plantillas críticas presintetizados en caché | la síntesis también se equivoca y los números son el punto débil; presintetizar baja la latencia (R-TEC-86) | voces Chirp 3 HD de Text-to-Speech (US$30 por millón de caracteres [V en Tecnología]) [A: locales disponibles para es-MX, es-CO, es-AR y pt-BR] | los proveedores que mida IA en S1 | provisional hasta S1 (D-18) |
| 3.8 | Cola humana y vista del experto | cola propia en Postgres y vista web propia (TEC-15, `lb-staff`), con el paquete expuesto como API | reproducible con un comando (P13); el paquete tipado es lo valioso y cualquier escritorio de agentes lo puede consumir | en producción, Contact Center AI Platform con enrutamiento por habilidades y Agent Assist [A: precio y disponibilidad en la región] | Genesys Cloud, Amazon Connect, Twilio Flex, Zendesk | propuesta |
| 3.9 | Dimensionamiento y simulación de colas | fórmulas de Erlang C para dimensionar y SimPy (simulación de eventos discretos) para E7 y E8 con el perfil de demanda del dataset | Erlang C es el estándar de gestión de fuerza laboral; la simulación capta la noche y la saturación, que la fórmula promedia | no aplica | biblioteca `pyworkforce` [A: mantenimiento] | propuesta |
| 3.10 | Control de calidad de conversaciones | verificaciones deterministas más el juez validado del arnés de IA | la literatura pide verificar con reglas lo verificable y usar juez solo para lo demás ([investigación 4](../docs/investigacion/04_Evaluacion.md)) | en producción, Conversational Insights con evaluación automática de calidad [A: nombre vigente del producto y precio] | Observe.AI, MaestroQA ([investigación 7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md)) | propuesta |
| 3.11 | Accesibilidad | axe-core dentro de las pruebas de Playwright de Tecnología y revisión manual con lector de pantalla (NVDA en Windows) | la prueba automática encuentra una parte de los problemas; la revisión manual el resto | no aplica | Lighthouse | propuesta |
| 3.12 | Satisfacción | pregunta de un toque al cerrar (1 a 5) y "¿resolvimos su problema?" (sí o no) | instrumento de producción; en la hackatón no hay clientes reales, así que no se reporta como resultado | no aplica | CES | propuesta |

---

## 4. Seguridad, privacidad y gobierno del dominio

Los controles técnicos viven en la plataforma ([04](../tecnologia/definicion.md), secciones 2 y 4) y en la
política (Gobierno). Esta sección fija los controles propios del contenido, del canal y de la operación
humana, y continúa la numeración.

### 4.1 El contenido al cliente como superficie de riesgo

| ID | Control | Cómo se verifica |
|---|---|---|
| R-CLI-112 | Todo cambio del catálogo entra por un pull request con la diferencia legible, revisión de `voz-del-cliente` y, si toca una plantilla crítica, visto bueno de Gobierno (Protección al consumidor); después de congelar el retenido, además, acta del Comité de Confianza. | historial del repositorio; acta |
| R-CLI-113 | Cada respuesta registra en la traza el identificador y la versión de su plantilla, o la marca de texto libre. | traza de cada turno |
| R-CLI-114 | Cada plantilla crítica puede retirarse sin desplegar (bandera leída por el motor) y se reemplaza por la plantilla de traspaso del estado. | simulacro en F5 con Tecnología (S-CLI-09) |

### 4.2 Ingeniería social contra el cliente y contra el experto

| ID | Control | Cómo se verifica |
|---|---|---|
| R-CLI-115 | El sistema no inicia llamadas ni envía enlaces; el código de verificación solo se escribe en el campo seguro o se marca por teclado; la frase de seguridad acompaña R3 y R4. | catálogo sin plantillas salientes ni enlaces; S4 y V9 |
| R-CLI-116 | El conjunto de estrés incluye ataques del canal: alguien que se hace pasar por el banco, un "agente" que pide el código, una plantilla falsa reenviada por el cliente y voz sintética (S-CLI-04). | casos en `eval/cases/adversarial/` con su resultado |
| R-CLI-117 | El experto humano también es superficie de ataque: no cambia datos de contacto, no se salta la confirmación del cliente, actúa con el nivel de autenticación de la política y trata la presión de jerarquía ("soy gerente") como S7. | pruebas de acceso con rol de experto |

### 4.3 Privacidad

| ID | Control | Cómo se verifica |
|---|---|---|
| R-CLI-118 | Minimización en el paquete y en la vista (2.5.2 y R-CLI-69); la vista muestra una marca de agua con la identidad de quien la lee [S]. | contrato de la vista; prueba visual |
| R-CLI-119 | Lo que genera esta cara sigue la retención propuesta por Tecnología hasta que Gobierno la apruebe: estado de conversaciones 90 días, trazas 30 días, audio 0 (R-TEC-117); las correcciones del experto, como las trazas de evaluación. | trabajos de purga con prueba |
| R-CLI-120 | El audio no se guarda en operación; la semilla humana de voz solo con consentimiento, cifrada y borrada al cierre. | inventario de insumos (DAT-6) contra el registro de consentimientos |

### 4.4 Equidad y protección al consumidor

| ID | Control | Cómo se verifica |
|---|---|---|
| R-CLI-121 | Ninguna decisión, prioridad ni acuerdo de servicio depende del acento, la variante, el segmento o un atributo protegido; el registro depende solo del país de la cuenta. | prueba de dependencias del motor y del enrutador; L1 |
| R-CLI-122 | La espera simulada hasta una persona se reporta por idioma y franja (MP-CLI-3); una brecha con intervalos que no se solapan se investiga y queda en acta (P12). | reporte de equidad |
| R-CLI-123 | El cliente puede pedir que una persona revise cualquier resultado automatizado del flujo, con explicación basada en la regla aplicada (por analogía con el artículo 20 de la LGPD, [investigación 3](../docs/investigacion/03_Seguridad_privacidad_regulacion.md)). | ruta R5 disponible desde cualquier estado; plantilla de explicación con la regla |
| R-CLI-124 | Una queja del cliente sobre la atención de la IA se registra con el motivo `QUEJA_SOBRE_ATENCION` y va a Gobierno (Protección al consumidor), según [04](../docs/diseno/04_Organizacion_y_roles.md), sección 11. | caso de prueba con el motivo en el paquete |

### 4.5 Riesgos del dominio en el marco de Gobierno

| Trabajador o artefacto | Riesgo propio de esta cara | Control |
|---|---|---|
| Redacción (nivel alto en la clasificación de [investigación 18](../docs/investigacion/18_VP_Gobierno.md)) | registro equivocado, tono indebido, cifra fuera de plantilla | plantillas críticas; linter; juez validado; filtro de salida (R-TEC-75) |
| Catálogo de plantillas | una plantilla con un plazo o una promesa incorrectos llega a todos los clientes | revisión de Gobierno; retiro sin desplegar (R-CLI-114) |
| Vista del experto | exposición de datos a empleados; decisiones sesgadas por datos irrelevantes | minimización; roles; registro de accesos |
| Cola humana | espera desigual por idioma | idioma alterno; reporte de espera por idioma (R-CLI-122) |

---

## 5. Interfaces

### 5.1 Lo que Clientes entrega

| A quién | Qué | Para cuándo | Aceptación | Responde a |
|---|---|---|---|---|
| Tecnología | catálogo de guiones por estado, en ES (usted y vos) y PT, como plantillas con variables tipadas: chat | D3 | cobertura completa (R-CLI-01) y linter sin errores | S-TEC-09 (aceptada) |
| Tecnología | el mismo catálogo para voz, con lecturas de vuelta, silencios y menú de teclas | D4 | V1, V2, V7 y V8 en desarrollo | S-TEC-09 (aceptada) |
| Tecnología | textos de los seis componentes y su degradación; plantillas WA-UT-01 a WA-UT-05 y WA-AU-01 | D3 y D4 | linter de límites; modo WhatsApp simulado | S-TEC-09 (aceptada) |
| Tecnología | catálogo de rellenos (tres o más por tipo y locale) listo para presintetizar | D4 | R-CLI-56 | S-TEC-09 (aceptada) |
| Tecnología | modelo de colas: ejes, prioridades, acuerdos, orden de respaldo, niveles de saturación, requisitos y roles de la vista del experto (secciones 2.5 y 2.6) | D3 | E7 encola en portugués de noche con espera declarada | S-TEC-10 (aceptada) |
| Tecnología y Datos | campos de la ficha de la transacción (2.4.2) y validación del directorio de comercios del equipo: descriptor de 5 a 22 caracteres, marca, razón social, categoría legible y pronunciación para la voz | D3 | firma en `directorio_comercios` 1.0.0; N1 resuelto con la marca | S-TEC-05 y S-DAT-09 (aceptadas) |
| Datos | supuestos de turnos y de costo por minuto humano (2.6.7) | D1 | `configuracion/supuestos_operacion.yaml` con fuente y etiqueta | S-DAT-10 (aceptada) |
| Datos | respuesta: la vista del experto no necesita el nombre del cliente (R-CLI-70) | D1 | registrado en el contrato de la vista | pregunta de la sección 10 de Datos |
| IA | semilla de estilo: 60 mensajes iniciales de clientes escritos a mano, 15 por México, Colombia, Argentina y portugués, cortos, con errores de tipeo y modismos [S] | D2 | revisados por `voz-del-cliente`; marcados `origen: equipo` | IA-1 |
| IA | lista de frases prohibidas y rúbrica de tono y registro para el juez | D3 | rúbrica versionada | arnés de evaluación (IA-5) |
| Gobierno | escenarios firmados para F2, con los propuestos E8, D10 y L7 (DP-CLI-07) | D2 | acta de F2 | firma de escenarios de esta cara |
| Gobierno | catálogo para la revisión de Protección al consumidor | D3 | visto bueno o hallazgos | derecho de objeción |
| Gobierno | acuerdos de servicio de la cola y supuestos de costo para el acta previa al retenido | D2 | acta con su huella | P1 |
| Auditoría | guion de la demo con evidencias y respaldos declarados; texto de consentimiento | D2 (consentimiento) y D9 (demo) | revisión de Auditoría | S-CLI-13 |
| Presidencia y Oficina de Entrega | backlog CLI (sección 8); sección de servicio del reporte; la demo | D1, D9 y D10 | backlog en la bitácora; demo ensayada | PRE-3 |

### 5.2 Lo que Clientes necesita

```
Solicitud S-CLI-01
De: VP Clientes   Para: VP Gobierno (Cumplimiento y privacidad)
Qué: en policy/v1, los datos de los que dependen los textos al cliente: plazos por país con número, unidad
     (hábiles o naturales), evento de inicio y nombre corto de la norma para el cliente; régimen de
     Argentina por producto; texto permitido para el abono provisional de México; calendario de feriados
     por país; número de aclaraciones antes de ofrecer persona; umbral de monto; qué acciones exigen
     confirmación y con qué nivel acr; si alguna norma exige grabar llamadas de servicio
Para qué: CLI-1 (plantillas críticas de plazo y confirmación) y CLI-6 (aviso de voz)
Para cuándo: D2
Aceptación: cada variable de las plantillas de 2.3.5 tiene su regla con norma y fecha de consulta
Estado: abierta
```

```
Solicitud S-CLI-02
De: VP Clientes   Para: VP Gobierno (Protección al consumidor)
Qué: aprobación del aviso de IA, del aviso de voz, de las frases prohibidas y obligatorias (2.3.6), de la
     política de persona sin resistencia con una sola oferta de contención (DP-CLI-02), de la regla de
     segmento (DP-CLI-06) y del catálogo de líneas de ayuda por país para crisis
Para qué: CLI-1, CLI-3 y CLI-6
Para cuándo: D3
Aceptación: acta con visto bueno o con hallazgos y su corrección
Estado: abierta
```

```
Solicitud S-CLI-03
De: VP Clientes   Para: VP Gobierno (Riesgo y riesgo de modelo)
Qué: registrar en el acta previa al retenido los acuerdos de servicio de 2.6.3 y los supuestos de costo
     de 2.6.7; incorporar al retenido los escenarios E8, D10 y L7 si se aprueba DP-CLI-07; confirmar que
     las correcciones del experto quedan excluidas del materializador del retenido
Para qué: P1; métricas M-22, MP-CLI-3 y MP-CLI-10
Para cuándo: D2
Aceptación: acta de F2 con la tabla, los escenarios y la huella
Estado: abierta
```

```
Solicitud S-CLI-04
De: VP Clientes   Para: VP Gobierno (Seguridad y equipo rojo)
Qué: casos adversariales del canal en texto y voz: suplantación del banco ("me llamaron del banco"),
     pedido del código por un supuesto agente, plantilla falsa reenviada, voz sintética que pide acciones,
     presión sobre el experto humano
Para qué: R-CLI-115 a R-CLI-117; día de equipo rojo (GOB-6)
Para cuándo: D2 (escritos) y D7 (equipo rojo)
Aceptación: casos en el conjunto de estrés con su resultado esperado y su código OWASP
Estado: abierta
```

```
Solicitud S-CLI-05
De: VP Clientes   Para: VP Inteligencia Artificial (Voz)
Qué: en S1, voces por locale (es-MX, es-CO, es-AR, pt-BR) con prueba de pronunciación de montos, fechas,
     dígitos y los 24 comercios del directorio; confianza por palabra del reconocimiento para montos y
     dígitos; presíntesis de rellenos y plantillas críticas
Para qué: CLI-3; R-CLI-52 y R-CLI-60
Para cuándo: D0 (medición) y D4 (presíntesis)
Aceptación: tabla de errores de pronunciación por voz; rellenos en caché con su identificador
Estado: abierta
```

```
Solicitud S-CLI-06
De: VP Clientes   Para: VP Inteligencia Artificial (Comprensión y redacción)
Qué: que la redacción reciba registro, país de la cuenta e idioma como parámetros y nunca el acento; que la
     comprensión detecte en ES y PT el pedido de persona, la urgencia, la frustración, la crisis y la queja
     sobre la atención, con su confianza; que el texto libre respete las frases prohibidas
Para qué: R-CLI-19, R-CLI-34, R-CLI-40, R-CLI-41 y R-CLI-124
Para cuándo: D3
Aceptación: pruebas de desarrollo por clase y por idioma; MP-CLI-6 igual a 0 en desarrollo
Estado: abierta
```

```
Solicitud S-CLI-07
De: VP Clientes   Para: VP Inteligencia Artificial (Evaluación y simulación)
Qué: personas del simulador con país, registro, idioma, paciencia y tendencia a pedir persona; persona en
     portugués nativo; experto simulado determinista que lee el paquete (2.6.8); juez de tono y registro
     validado contra la muestra humana
Para qué: M-11, MP-CLI-7, MP-CLI-8
Para cuándo: D5
Aceptación: el arnés corre el conjunto de desarrollo con esas personas y reporta las métricas
Estado: abierta
```

```
Solicitud S-CLI-08
De: VP Clientes   Para: VP Tecnología (Canales)
Qué: textos de los componentes con sus límites; botón permanente "Hablar con persona"; línea fija de
     "Asistente de IA" o del nombre del experto; vencimiento de la confirmación con aviso y renovación
     (R-CLI-46); historial de confirmaciones inerte; lista de accesibilidad de 2.8.4; declaración de idioma
     de la página; modo WhatsApp simulado que rechaza texto libre fuera de ventana
Para qué: CLI-2 y CLI-6
Para cuándo: D4
Aceptación: pruebas de Playwright y axe-core; R-CLI-44 a R-CLI-50 en verde
Estado: abierta
```

```
Solicitud S-CLI-09
De: VP Clientes   Para: VP Tecnología (Plataforma del agente)
Qué: eventos experto_asignado y experto_unido; modo asistente (la IA no escribe al cliente); campo
     compromisos_comunicados y los demás de 2.5.2 en PaqueteTraspaso; prioridad P1 a P4 con la regla del
     máximo; orden de respaldo por idioma; nivel de saturación en la traza; aviso "especialista
     disponible" como plantilla; retiro de plantillas críticas sin desplegar (R-CLI-114)
Para qué: CLI-4
Para cuándo: D5
Aceptación: E1, E4 y E7 de punta a punta con la persona entrando al mismo hilo
Estado: abierta
```

```
Solicitud S-CLI-10
De: VP Clientes   Para: VP Tecnología (Canales, voz)
Qué: temporizadores de silencio y de no entendido configurables; interrupción permitida salvo la primera
     frase del aviso; mapa de teclas de 2.4.4; órdenes "repetir" y "más despacio"; mensajes de espera cada
     45 a 60 s durante el traspaso
Para qué: CLI-3
Para cuándo: D5
Aceptación: V1, V3, V7, V8 y V11 en desarrollo
Estado: abierta
```

```
Solicitud S-CLI-11
De: VP Clientes   Para: VP Datos
Qué: incorporar al catálogo oficial las métricas propuestas MP-CLI-1 a MP-CLI-10 (sección 6.2), con
     definición, denominador y consulta sobre platino, o explicar cuáles cubre ya una M existente
Para qué: árbol de resultados (2.7) y criterios de aceptación (6)
Para cuándo: D3
Aceptación: definiciones en el catálogo de métricas con su versión
Estado: abierta
```

```
Solicitud S-CLI-12
De: VP Clientes   Para: VP Datos
Qué: capacidad_humana_franja con los supuestos de 2.6.7; distribución de duración y espera por categoría
     (para M-46 y el factor de traspaso); perfil de demanda por hora y día; confirmación de si
     service_agents trae sede o país
Para qué: dimensionamiento (2.6.4), simulación de E7 y E8
Para cuándo: D2
Aceptación: tablas de oro analítico con contrato y fecha de corte
Estado: abierta
```

```
Solicitud S-CLI-13
De: VP Clientes   Para: Auditoría
Qué: aceptar el texto de consentimiento de la semilla humana de voz (2.8.2) y las reglas de la demo
     (R-CLI-106 a R-CLI-111), en particular los respaldos grabados declarados
Para qué: CLI-5 y CLI-6
Para cuándo: D2 (consentimiento) y D7 (demo)
Aceptación: dictamen previo sin hallazgos bloqueantes
Estado: abierta
```

```
Solicitud S-CLI-14
De: VP Clientes   Para: Presidencia
Qué: decidir DP-CLI-01 a DP-CLI-13; aprobar la compra opcional de una revisión nativa de portugués
     (sección 7) o confirmar que hay un hablante nativo disponible; incluir en las preguntas a los
     organizadores quién puede actuar como experto humano en la demo
Para qué: CLI-1 (portugués) y CLI-5 (demo)
Para cuándo: D1
Aceptación: decisiones registradas en Decisiones.md
Estado: abierta
```

**Solicitudes recibidas y su respuesta:** S-TEC-05, S-TEC-09 y S-TEC-10 de Tecnología, y S-DAT-09 y
S-DAT-10 de Datos, quedan **aceptadas** con las fechas de la tabla 5.1.

---

## 6. Métricas y criterios de aceptación del dominio

### 6.1 Métricas oficiales que esta cara vigila

Definiciones del catálogo de Datos ([03](../datos/definicion.md), M-01 a M-46). Las metas son provisionales (D-07) y
se fijan antes del retenido.

| Métrica | Meta provisional | Conjunto | Por qué la vigila esta cara |
|---|---|---|---|
| M-04 Sensibilidad de escalamiento | ningún caso con R4 esperada sin escalar (compuerta); alta en R5 | representativo y estrés | un traspaso faltante es el error grave |
| M-05 Precisión de escalamiento | se reporta; los traspasos innecesarios se analizan | representativo | cada traspaso innecesario consume la cola en portugués y de noche |
| M-06 Motivo de escalamiento correcto | se reporta | representativo y estrés | el motivo decide la cola y la prioridad |
| M-11 Preguntas repetidas | cerca de 0 | representativo | PS3 y PS6 |
| M-12 Completitud del paquete | 100% | representativo y estrés | exigencia textual del enunciado |
| M-13 Exactitud de los hechos del paquete | 100% | representativo y estrés | el experto debe poder creerle |
| M-14 Anclaje | 100% en montos, fechas, plazos y estados | representativo | P6 |
| M-15 Acciones informadas sin verificación | 0, con cota de la regla del tres | representativo y estrés | P6 |
| M-16 Idioma correcto | 100% | representativo | L1 a L6 |
| M-17 Enmascaramiento | 100% | representativo y estrés | R-CLI-30 |
| M-19 Latencia de voz a voz | presupuesto de [06](../docs/diseno/06_Arquitectura.md), sección 6 | voz | un silencio largo se vive como falla |
| M-22 Costo con traspasos | se reporta con los supuestos de 2.6.7 | representativo | el costo que decide está en el traspaso |
| M-26 Retención de voz frente a texto | se reporta | voz | la voz no debe resolver peor |
| M-27 Brecha máxima entre grupos | brecha con intervalos que no se solapan, investigada | representativo | P12 |
| M-45 Cobertura humana en portugués por franja | valor con supuestos | negocio | E7 |
| M-46 Minutos humanos en "todo humano" | simulado | representativo | línea base de la proyección |

### 6.2 Métricas propuestas por esta cara

Se piden a Datos para el catálogo oficial (S-CLI-11). Fuente: D determinista, J juez validado, H humano,
S simulación.

| ID | Métrica | Definición y denominador | Fuente | Meta provisional |
|---|---|---|---|---|
| MP-CLI-1 | Tiempo hasta la contención | turnos del cliente y segundos de sistema (sin el tiempo del cliente) desde la primera señal de fraude hasta la `AccionVerificada` de bloqueo / casos con R3 o R4 esperada y bloqueo aplicable | D | 2 turnos o menos después de autenticar [S] |
| MP-CLI-2 | Cierre que distingue | conversaciones con acción o traspaso cuyo cierre tiene los cuatro bloques / conversaciones con acción o traspaso | D | 100% |
| MP-CLI-3 | Espera hasta una persona | p50 y p90 de la espera simulada por idioma, prioridad y franja; cumplimiento del acuerdo por prioridad | S | se reporta; brecha por idioma investigada |
| MP-CLI-4 | Traspaso sin resistencia | turnos entre el pedido explícito de persona y `traspaso_iniciado` / pedidos | D | 1 turno en el 100% de E4 y V11 |
| MP-CLI-5 | Aviso de IA | conversaciones con la plantilla de aviso en el primer turno de cada canal / conversaciones | D | 100% |
| MP-CLI-6 | Frases prohibidas | apariciones / turnos | D y J | 0 |
| MP-CLI-7 | Registro correcto | turnos con el registro del país de la cuenta / turnos | D en plantillas, J en texto libre | 100% en plantillas; 99% o más en texto libre [S] |
| MP-CLI-8 | Utilidad del paquete | media y distribución de `utilidad_paquete` (1 a 5) y preguntas que el experto tuvo que repetir | H y experto simulado | 4 o más de media [S] |
| MP-CLI-9 | Tiempo hasta la primera acción del experto | segundos desde que abre el paquete hasta su primera acción, en la muestra humana | H | se reporta |
| MP-CLI-10 | Calibración de la espera declarada | casos cuya espera simulada cayó dentro del rango declarado / casos con espera declarada | S | 80% o más [S] |

### 6.3 Criterios de aceptación por fase

| Fase | Criterio de esta cara |
|---|---|
| F2 | escenarios firmados; decisión sobre E8, D10 y L7; catálogo de chat en ES con plantillas críticas; acuerdos de servicio y supuestos de costo en acta |
| F3 | N1 a N6 por chat en ES con plantillas; linter sin errores; M-12 del 100% en E1 a E7 en desarrollo; MP-CLI-5 del 100% |
| F3v | V1, V2, V7, V8 y V11 en desarrollo sin resultado inseguro; aviso de voz de 12 s o menos |
| F5 | catálogo PT completo y revisado; L2, L3 y L5 en desarrollo; accesibilidad sin violaciones serias; E7 y E8 simulados con la cola |
| F6 | métricas de 6.1 y 6.2 reportadas con intervalos sobre el retenido; ningún R4 sin escalar; MP-CLI-6 y M-15 iguales a 0 |
| F7 | demo de 2.9 ensayada dos veces con respaldos declarados; cada cifra en pantalla desde platino con su etiqueta |

---

## 7. Compras y costos

### 7.1 Qué compra esta cara

| Qué | Para qué | Costo en la hackatón | En producción | Alternativa gratuita | Recomendación |
|---|---|---|---|---|---|
| WhatsApp Business Platform | el canal de mensajería | US$0: se simula (D-19) | por mensaje desde el 1 de octubre de 2026 (7.2) | el modo simulado | no comprar |
| Número telefónico | voz por teléfono | US$0 a 5, cubierto por la prueba de Twilio con un número de EE. UU. [V en Tecnología] | 7.3 | voz por navegador | no comprar un número colombiano (≈ US$44 y requisitos regulatorios) salvo que la Presidencia quiera mostrar telefonía local |
| Revisión nativa de portugués | validar unas 60 plantillas (≈ 1.500 palabras) | US$75 a 150 [S: tarifa de revisión de US$0,05 a 0,10 por palabra; confirmar con una cotización] | equipo de contenido | un hablante nativo voluntario, reconocido en el reporte | aprobar solo si no hay nativo disponible (S-CLI-14) |
| Grabaciones de la semilla humana de voz | medir la brecha entre voz humana y sintética | US$0: equipo y conocidos con consentimiento | no aplica | | |
| Personas expertas | cola humana | US$0: el equipo | 7.4 | | |
| Bibliotecas (Jinja2, Babel, `holidays`, SimPy, axe-core) | catálogo, formato, calendario, simulación, accesibilidad | US$0: código abierto | US$0 | | |
| **Total de esta cara** | | **US$0 indispensable; hasta US$150 opcional** | | | dentro del techo de gasto de US$600 que propone Tecnología (DP-TEC-12), si la Presidencia lo aprueba |

### 7.2 WhatsApp: precios por mensaje desde el 1 de octubre de 2026

**Lo verificado hoy** en la página de precios de Meta (27 de septiembre de 2026) [V]: se cobra por mensaje
de plantilla entregado, con tarifa por mercado y por categoría; la tarjeta de tarifas vigente es la del 1 de
julio de 2026; las respuestas de servicio dentro de la ventana de 24 horas y las plantillas de utilidad
entregadas dentro de una ventana abierta son gratuitas; las ventanas de punto de entrada gratuito duran 72
horas; utilidad y autenticación tienen escalones de volumen mensuales por mercado.

**Lo que cambia el 1 de octubre**, según fuentes secundarias (EngageLab, FormBeep, Zendesk, Courier) [P]:
los mensajes de servicio pasan a cobrarse a la tarifa de utilidad de cada mercado después de 1.000
gratuitos por número de negocio al mes; algunas fuentes dicen que las plantillas de utilidad enviadas dentro
de la ventana también se cobran. La página de Meta consultada aún no lo mostraba [A: confirmar en la página
de precios de Meta y en la tarjeta de tarifas de la cuenta de WhatsApp Business después del 1 de octubre].
El precio depende del **mercado del número del cliente** (su código de país), no de dónde está el banco [P].

| Mercado del número del cliente | Utilidad, autenticación y servicio (US$ por mensaje) | Marketing (no se usa) | Etiqueta |
|---|---|---|---|
| México | 0,0085 | 0,0305 hasta el 30 de septiembre; 0,0397 desde el 1 de octubre | [P] EngageLab, sobre la tarjeta de Meta del 1 de julio y la actualización publicada el 1 de septiembre de 2026 |
| Colombia | 0,0008 | [A] | [P] FormBeep y EngageLab |
| Argentina | [A] | [A] | confirmar en la tarjeta de tarifas en USD de Meta |
| Brasil (cliente en portugués con número brasileño) | 0,0068 | 0,0625 | [P] EngageLab |

**Costo del canal por caso de chat (proyección).** Supuesto [S]: 8 mensajes de servicio del banco más 2
plantillas (código y aviso de estado), cobrables una vez agotados los 1.000 gratuitos del mes (que a 10
mensajes por caso alcanzan para unos 100 casos por número):

| Mercado | Costo del canal por caso | Frente al costo de modelos por caso de chat (US$0,023, [04](../tecnologia/definicion.md), sección 7.4) |
|---|---|---|
| México | US$0,085 | 3,7 veces |
| Colombia | US$0,008 | 0,35 veces |
| Brasil | US$0,068 | 3,0 veces |
| Argentina | [A] | [A] |

**Lectura:** desde octubre de 2026, en México el canal cuesta más que los modelos por cada caso de chat.
Cada turno innecesario cuesta dinero, lo que refuerza una pregunta por turno y los componentes que evitan
idas y vueltas. Tecnología proyecta producción "sin costo de mensajes de WhatsApp"; esta cara propone
incluirlo (DP-CLI-13).

### 7.3 Telefonía (con Tecnología)

Cifras de Tecnología ([04](../tecnologia/definicion.md), sección 7.2) [V]: número de EE. UU. de Twilio US$1,15 al mes,
entrante US$0,0085 por minuto y Media Streams US$0,0044 por minuto; número de Colombia US$14 al mes y
entrante US$0,0945 por minuto. México y Argentina [A: páginas de precios de voz de Twilio por país].
Una llamada de 3 minutos con número colombiano cuesta 3 × (0,0945 + 0,0044) ≈ US$0,30. En la comparación
de ahorro por voz, el escenario "todo humano" también paga telefonía por sus minutos, así que se suma en
los dos lados.

### 7.4 Costo del agente humano

Resumen de 2.6.7 (escenario central [S] sobre rangos publicados [P]): minuto productivo de agente US$0,33;
minuto de especialista de fraude con portugués US$0,48; contacto de voz de servicio US$1,47 (bajo US$0,98,
alto US$2,50); en chat, con 1,5 conversaciones simultáneas, US$0,97 por caso. La cifra de industria de
US$7 a 14 por contacto de voz es de EE. UU. [P] y se usa solo como sensibilidad (DP-CLI-12).

### 7.5 Costo por caso del dominio (proyección, escenario central)

Supuestos [S]: 30% de traspasos, factor de traspaso 1,0 y 10% de recontacto, es decir, 0,40 casos humanos
equivalentes por caso; modelos y voz según Tecnología (chat US$0,023; voz sin telefonía US$0,11); 3 minutos
de IA por llamada; 4,4 minutos humanos por caso.

| Canal | Con el sistema | "Todo humano" | Diferencia |
|---|---|---|---|
| Chat web | US$0,41 | US$0,97 | 58% |
| WhatsApp, número de México | US$0,50 | US$1,05 | 52% |
| WhatsApp, número de Colombia | US$0,42 | US$0,98 | 57% |
| Voz telefónica, número de Colombia | US$1,17 | US$1,91 | 39% |

Con el escenario adverso de 2.7.2 (50% de traspasos, factor 1,5 y 15% de recontacto) la diferencia en chat
web cae por debajo del 10%. **La variable que decide es la calidad del traspaso, no el precio del modelo.**
La diferencia porcentual del chat coincide con la ilustración de 2.7.2, que usó el minuto sin concurrencia.

### 7.6 Qué queda sin verificar y cómo se confirma

| Cifra | Cómo se confirma |
|---|---|
| Cobro de mensajes de servicio desde el 1 de octubre y su tarifa por mercado | página de precios de Meta y tarjeta de tarifas de la cuenta de WhatsApp Business, después del 1 de octubre |
| Tarifas de Argentina | CSV de tarifas en USD de Meta |
| Límites de caracteres de filas, descripciones y cuerpo de mensajes interactivos | referencia de mensajes interactivos de la API de WhatsApp |
| Telefonía en México y Argentina | páginas de precios de voz de Twilio por país |
| Tarifa por hora de agentes en Argentina | cotización local o encuesta salarial con carga prestacional |
| Tarifa de revisión nativa de portugués | una cotización de un traductor profesional |

---

## 8. Backlog propuesto

Épicas de [07](../presidencia/hoja_de_ruta.md), sección 3 (CLI-1 a CLI-5), más una nueva (CLI-6) que la Oficina
de Entrega debe sumar al backlog.

### CLI-1 Guiones por estado en ES y PT, para chat y voz (F2 y F3)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-1.1 | Matriz estado × canal × registro con la intención de cada celda (2.2.1) | cobertura sin huecos (R-CLI-01) | 01, sección 4; `StrEnum` de Tecnología | D2 |
| CLI-1.2 | Guía de estilo: voz de marca, registro y vocabulario por país, frases prohibidas y obligatorias | visto bueno de Gobierno (S-CLI-02) | | D2 |
| CLI-1.3 | Plantillas críticas en ES (usted y vos): plazos, montos, confirmaciones y cierre que distingue | linter sin errores; pruebas con `policy/v1` | S-CLI-01, TEC-2.7 | D3 |
| CLI-1.4 | Catálogo completo de chat en ES | N1 a N6 por chat (compuerta de F3) | CLI-1.3, TEC-5 | D4 |
| CLI-1.5 | Catálogo en PT con retrotraducción | L2 y L5 en desarrollo; revisión nativa hecha o declarada | CLI-1.4, S-CLI-14 | D6 |
| CLI-1.6 | Linter de contenido en integración continua (3.4) | corre en cada pull request y bloquea los errores | repositorio | D3 |
| CLI-1.7 | Conversaciones de referencia por escenario N, A, E y F para el conjunto de desarrollo | una por escenario, `origen: equipo`, fuera del retenido | CLI-1.2 | D3 |
| CLI-1.8 | Revisión de `voz-del-cliente` y cierre de hallazgos | cero hallazgos bloqueantes | CLI-1.4, CLI-1.5 | D4 y D6 |

### CLI-2 Componentes de chat y su degradación a WhatsApp (F3)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-2.1 | Textos y etiquetas de los seis componentes en ES y PT | R-CLI-47 en el linter | TEC-5.2 | D3 |
| CLI-2.2 | Degradación a WhatsApp y comportamiento fuera de la ventana | modo simulado con reloj; R-CLI-50 | TEC-5 | D4 |
| CLI-2.3 | Aviso de IA fijo y botón permanente de persona | MP-CLI-5 del 100%; E4 | TEC-5 | D4 |
| CLI-2.4 | Confirmación con vencimiento accesible e historial inerte | R-CLI-46 con reloj inyectable | S-CLI-08 | D4 |

### CLI-3 Diseño de voz (F3v)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-3.1 | Aviso de apertura de voz en ES y PT | 12 s o menos medidos | S-CLI-05 | D4 |
| CLI-3.2 | Lecturas de vuelta y listas de afirmaciones por idioma | V2; R-CLI-52 | TEC-6 | D4 |
| CLI-3.3 | Catálogo de rellenos presintetizados | R-CLI-56; caché con identificador | S-CLI-05 | D4 |
| CLI-3.4 | Silencios, no entendidos, interrupciones y mapa de teclas | V1, V3, V7 y V8 | S-CLI-10 | D5 |
| CLI-3.5 | Traspaso tibio por voz con mensajes de espera | E1 por voz | CLI-4.5 | D5 |

### CLI-4 Operaciones de fraude y disputas (F3)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-4.1 | Supuestos de turnos y costo | archivo validado (R-CLI-89) | S-DAT-10 | D1 |
| CLI-4.2 | Modelo de colas, prioridades, acuerdos y niveles de saturación | S-TEC-10 entregada; acta (S-CLI-03) | CLI-4.1 | D3 |
| CLI-4.3 | Especificación del `PaqueteTraspaso` y su render en ES y PT | M-12 del 100% por esquema | TEC-1 | D3 |
| CLI-4.4 | Vista del experto: orden, etiquetas de procedencia y roles | prueba de interfaz; R-CLI-68 a R-CLI-71 | TEC-15 | D4 |
| CLI-4.5 | Ingreso al mismo hilo y modo asistente | R-CLI-72 y R-CLI-73; E4 de punta a punta | S-CLI-09 | D5 |
| CLI-4.6 | Formulario de corrección y su exportación | esquema; exclusión del retenido (R-CLI-76) | CLI-4.4 | D5 |
| CLI-4.7 | Simulación de colas para E7 y E8 con el perfil del dataset | cuaderno con supuestos; MP-CLI-3 y MP-CLI-10 | S-CLI-12 | D6 |
| CLI-4.8 | Protocolo del experto (demo, simulado y muestra humana) | fechado antes de F6 (R-CLI-90) | CLI-4.3 | D6 |

### CLI-5 Árbol de resultados, calidad y demo (F2 y F7)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-5.1 | Árbol de resultados con la línea base del total | tabla 2.7.1 con cifras de platino | DAT-2 | D2 |
| CLI-5.2 | Supuestos de proyección registrados en acta | acta previa al retenido | S-CLI-03 | D2 |
| CLI-5.3 | Control automático de calidad sobre el 100% de las conversaciones | reporte por corrida (R-CLI-91) | IA-5 | D5 |
| CLI-5.4 | Guion de la demo con semillas de desarrollo | intersección vacía con el retenido (R-CLI-107) | CLI-1.4 | D6 |
| CLI-5.5 | Dos ensayos y respaldos grabados | bitácora; respaldos con su traza | CLI-5.4 | D9 |
| CLI-5.6 | Sección de servicio del reporte: resultados por idioma y canal, proyección aparte | etiquetas y cifras desde platino | GOB-7 | D9 |

### CLI-6 Comunicaciones al cliente y accesibilidad (nueva)

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| CLI-6.1 | Plantillas WA-UT-01 a WA-UT-05 y WA-AU-01 en ES (usted y vos) y PT | R-CLI-98 y R-CLI-99 | CLI-1.2 | D4 |
| CLI-6.2 | Texto de consentimiento de la semilla humana de voz | aceptado por Auditoría antes de grabar | S-CLI-13 | D2 |
| CLI-6.3 | Aviso de privacidad resumido para chat y voz | visto bueno de Gobierno | S-CLI-01 | D3 |
| CLI-6.4 | Reglas de notificaciones: tope y horario silencioso | prueba con reloj (R-CLI-102) | TEC-2 | D5 |
| CLI-6.5 | Revisión de accesibilidad WCAG 2.2 AA del chat y de la vista | axe-core y lector de pantalla (R-CLI-103) | CLI-2, CLI-4.4 | D7 |

**Orden de recorte dentro de esta cara**, alineado con [07](../presidencia/hoja_de_ruta.md), sección 6: primero
la voz en portugués (CLI-3 en PT); después la simulación de colas se reduce a E7 (CLI-4.7); después las
reglas de notificaciones (CLI-6.4). **Nunca se recortan:** las plantillas críticas (CLI-1.3), el paquete
de traspaso (CLI-4.3), el aviso de IA y el botón de persona (CLI-2.3) ni los tres casos de la demo en
español y portugués.

---

## 9. Riesgos y mitigaciones

| Riesgo | Señal | Probabilidad | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| Portugués de baja calidad sin revisor nativo | hallazgos de retrotraducción; juez de registro bajo en PT | media | alto (L2, demo) | retrotraducción, `voz-del-cliente`, revisor nativo opcional (S-CLI-14); limitación declarada | Clientes |
| Mezcla de tú, usted y vos en el texto libre del modelo | MP-CLI-7 bajo | media | medio | plantillas para lo frecuente; registro como parámetro (S-CLI-06); linter y juez | Clientes e IA |
| Traspasos de más que saturan la cola en portugués y de noche | M-05 bajo; MP-CLI-3 alto | media | alto | contención primero; idioma alterno; simulación de E7 y E8; umbrales revisados por Gobierno | Clientes (Operaciones) |
| Espera declarada que no se cumple | MP-CLI-10 bajo | media | medio | rangos, no números; actualización; calibración con la simulación | Clientes |
| El cliente confunde bloqueo con reclamo | MP-CLI-2 incompleto | baja | alto | cierre que distingue obligatorio (R-CLI-07, R-CLI-31) | Clientes |
| El cliente cree que habla con una persona | preguntas "¿eres humano?" repetidas | baja | alto | aviso fijo y respuesta veraz (R-CLI-33) | Clientes |
| Plazo o promesa incorrectos en una plantilla crítica | hallazgo de Gobierno o de la corrida | baja | muy alto | plantillas desde `ReglaDePolitica`; revisión de Gobierno; retiro sin desplegar (R-CLI-114) | Clientes y Gobierno |
| Paquete demasiado largo para actuar rápido | MP-CLI-9 alto | media | medio | orden fijo; lo accionable primero; transcripción plegada | Clientes |
| Aviso de voz largo que provoca abandono | duración mayor que 12 s | media | medio | medición en CLI-3.1; detalle de privacidad a pedido | Clientes |
| Rellenos que parecen evasivos | juez de tono; interrupciones durante rellenos | media | bajo | tres variantes, uno cada 4 s, verbos honestos | Clientes |
| Falla de la demo en vivo | ensayo fallido | media | alto | dos ensayos; respaldos declarados (R-CLI-109) | Clientes y Oficina de Entrega |
| Tarifas de WhatsApp distintas de lo supuesto | tarjeta de Meta después del 1 de octubre | media | bajo | cifras marcadas [P] y [A]; sensibilidad | Clientes y Tecnología |
| Consentimientos de grabación incompletos | auditoría de insumos | baja | alto | texto firmado antes de grabar (R-CLI-101) | Clientes, Datos y Auditoría |
| Sesgo del experto por datos irrelevantes | quejas o diferencias por segmento | baja | medio | vista sin segmento ni atributos protegidos (R-CLI-69) | Clientes y Gobierno |
| Carga de contenido mayor que el tiempo disponible | historias CLI atrasadas | alta | medio | orden de recorte de la sección 8; nunca lo marcado como irrecortable | Oficina de Entrega |

---

## 10. Decisiones propuestas y preguntas abiertas

### 10.1 Decisiones propuestas

| ID | Propuesta | Alternativas | Por qué | Principio | Quién decide |
|---|---|---|---|---|---|
| DP-CLI-01 | El registro sale del país de la cuenta verificada; antes de autenticar, usted neutro o você | registro por acento detectado; tuteo general | el acento no es un dato verificado y usarlo para tratar distinto roza la discriminación | P12 | Clientes, con consulta a Gobierno |
| DP-CLI-02 | Pedir persona inicia el traspaso en el turno siguiente; una contención pendiente se ofrece una sola vez y después de encolar | ofrecer la contención antes de encolar; no ofrecerla | cumple E4 sin resistencia y no pierde minutos de contención en fraude | P7, PS2 | Gobierno (Protección al consumidor) |
| DP-CLI-03 | Sin especialista del idioma, contención verificada primero y oferta de idioma alterno (español ya o portugués al abrir el turno), a elección del cliente | esperar siempre al especialista en portugués; pasar a español sin preguntar | con una sola persona nocturna el acuerdo P1 solo aguanta menos de un caso por hora (2.6.4); elegir es del cliente | P7, P12 | Clientes (Operaciones), con Gobierno |
| DP-CLI-04 | Sin llamadas salientes: la devolución de contacto es un aviso para que el cliente vuelva por un canal oficial | devolución de llamada clásica | "me llamaron del banco" es el guion de la estafa; una regla simple protege al cliente | P5 | Clientes, con Gobierno (Seguridad) |
| DP-CLI-05 | El experto entra al mismo hilo y la IA pasa a modo asistente: no escribe al cliente y sus borradores solo salen si el experto los envía | la IA sigue hablando con el cliente; hilo nuevo para el humano | no hay dos voces ante el cliente; la asistencia al agente es donde la IA tiene evidencia causal más fuerte ([investigación 7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md)) | P6, P7 | Clientes, con Tecnología |
| DP-CLI-06 | El segmento no cambia prioridad ni acuerdo y no se muestra en la vista del experto | colas preferentes por segmento | la prioridad sale del riesgo y la urgencia; mostrar el segmento puede sesgar | P12 | Gobierno (Protección al consumidor) |
| DP-CLI-07 | Tres escenarios nuevos antes de congelar el retenido: **E8** cola saturada (espera P1 mayor que 5 minutos); **D10** ventana de 24 horas vencida con cambio de estado del caso; **L7** cliente en portugués que acepta español con el experto | dejarlos fuera | prueban las restricciones operativas que el enunciado pide analizar | P1, P8 | Gobierno (Riesgo), antes de F2 |
| DP-CLI-08 | La espera se declara en rangos calibrados, nunca como promesa, con su métrica de calibración | número exacto; no declarar espera | honestidad medible sobre lo que el cliente espera | P6 | Clientes |
| DP-CLI-09 | Las métricas MP-CLI-1 a MP-CLI-10 entran al catálogo oficial o se mapean a una M existente | medir solo con las M actuales | el árbol de resultados necesita tiempo hasta la contención, espera por idioma y cierre que distingue | P2 | Datos |
| DP-CLI-10 | Espejo del tuteo en México solo por chat: si el cliente tutea, el sistema tutea; por defecto, usted | usted siempre en México | la banca digital mexicana tutea a menudo; el espejo sube la cercanía sin cambiar decisiones [A: validar con la muestra de estilo] | P12 | Clientes, con Gobierno |
| DP-CLI-11 | Plantillas fuera de ventana sin montos, nombres, tarjetas ni enlaces | plantillas con detalle | privacidad en la pantalla bloqueada y menor imitación por estafadores | P11, P5 | Gobierno (Privacidad) |
| DP-CLI-12 | Costo del minuto humano con cifras de Latinoamérica (bajo, central, alto) registradas en acta antes del retenido; la cifra de EE. UU. de US$7 a 14 por contacto solo como sensibilidad (discrepa de [04](../tecnologia/definicion.md), sección 7.4) | usar la cifra de EE. UU. | los agentes del banco están en México, Colombia y Argentina; la cifra de EE. UU. infla el ahorro unas cinco a diez veces | P1, P3 | Presidencia, con Tecnología |
| DP-CLI-13 | La proyección de producción incluye el costo por mensaje de WhatsApp desde el 1 de octubre de 2026 (discrepa de [04](../tecnologia/definicion.md), sección 7.4, "sin costo de mensajes") | omitirlo | en México el canal cuesta 3,7 veces lo que cuestan los modelos por caso de chat (7.2) | P3 | Tecnología (Comité de Plataforma) |

**Las cinco más importantes:** DP-CLI-03, DP-CLI-02, DP-CLI-04, DP-CLI-05 y DP-CLI-07.

### 10.2 Preguntas abiertas

| # | Pregunta | Para quién | Por qué importa |
|---|---|---|---|
| 1 | ¿Hay un hablante nativo de portugués en el equipo o disponible? | Presidencia | validación de L2 y de la demo |
| 2 | ¿Alguna norma de México, Colombia o Argentina exige grabar llamadas de servicio financiero? | Gobierno (Cumplimiento) | cambia el aviso de voz y la retención |
| 3 | Plazo de México: ¿45 días naturales o hábiles? | Gobierno (D-13) | plantilla de plazo |
| 4 | ¿Cuántas aclaraciones antes de ofrecer persona y qué umbral de monto? | Gobierno | R-CLI-39 y E2 |
| 5 | ¿Qué hace la IA con el interruptor "todo a humano": puede contener? | Gobierno | nivel 3 de saturación |
| 6 | ¿`service_agents` trae sede, país o horario? | Datos | supuestos de turnos |
| 7 | Tarifas de WhatsApp de Argentina y cobro real de servicio desde octubre | Tecnología y Clientes, tras el 1 de octubre | 7.2 |
| 8 | ¿Quién hace de experto humano en la demo y en la muestra humana, y hay un segundo anotador? | Presidencia | R-CLI-90 y calidad de etiquetas |
| 9 | ¿Formato y duración de la demo? | organizadores (pregunta 1 de 05) | guion de 2.9 |
| 10 | ¿Se permiten grabaciones de voces humanas y con qué proveedor? | organizadores (pregunta 10 de 05) | semilla humana y consentimiento |
| 11 | ¿Qué líneas de ayuda por país se usan ante una crisis? | Gobierno | R-CLI-41 |
| 12 | ¿Locales de voz disponibles para es-CO y es-AR? | IA (S1) | registro también en la voz sintetizada |

---

## 11. Fuentes

**Documentos del proyecto**

- [Modelo operativo](../presidencia/modelo_operativo.md); [Datos](../datos/definicion.md) (métricas M-01 a M-46, S-DAT-09, S-DAT-10); [Tecnología](../tecnologia/definicion.md) (componentes AG-UI, voz, telefonía, costos, R-TEC-54, 75 a 78, 84, 86, 104, 117)
- [Principios](../docs/diseno/00_Principios.md), [interacciones y criterios](../docs/diseno/01_Interacciones_y_criterios.md), [datos por capas](../docs/diseno/03_Datos_por_capas.md), [organización](../docs/diseno/04_Organizacion_y_roles.md), [cobertura del enunciado](../docs/diseno/05_Cobertura_del_enunciado.md), [arquitectura](../docs/diseno/06_Arquitectura.md), [hoja de ruta](../presidencia/hoja_de_ruta.md), [decisiones](../presidencia/decisiones.md)
- Investigaciones [1](../docs/investigacion/01_Industria_y_casos.md), [2](../docs/investigacion/02_Arquitectura_y_control.md), [3](../docs/investigacion/03_Seguridad_privacidad_regulacion.md), [4](../docs/investigacion/04_Evaluacion.md), [6](../docs/investigacion/06_El_banco_por_dentro.md), [7](../docs/investigacion/07_Atencion_al_cliente_como_dominio.md), [11](../docs/investigacion/11_Latencia_y_costo.md), [12](../docs/investigacion/12_Organizacion_de_un_banco.md), [13](../docs/investigacion/13_Auditoria_del_dataset.md), [14](../docs/investigacion/14_VP_Clientes.md), [18](../docs/investigacion/18_VP_Gobierno.md), [20](../docs/investigacion/20_Canales_voz_y_chat.md), [21](../docs/investigacion/21_Organizacion_agentica.md)
- Enunciado de la Factored AI & Data Hackathon 2026 (`Documentos/`)

**Consultadas el 27 de septiembre de 2026**

- Meta, [precios de la plataforma de WhatsApp Business](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing) [V para lo vigente]
- EngageLab, [precios de la API de WhatsApp Business 2026](https://www.engagelab.com/blog/whatsapp-business-api-pricing) y [costo de mensajes de servicio desde octubre](https://www.engagelab.com/blog/whatsapp-pricing-2026-service-message-cost) [P]
- FormBeep, [tarifas por país](https://formbeep.com/whatsapp-api-pricing/) [P]
- Zendesk, [cambios de precios de WhatsApp](https://support.zendesk.com/hc/en-us/articles/11113277351322-Announcing-upcoming-changes-to-WhatsApp-Business-messaging-pricing) [P]; Courier, [cambios del 1 de octubre de 2026](https://www.courier.com/blog/whatsapp-pricing-changes-october-2026) [P]
- Centris, [precios de call center nearshore 2026](https://centrisinfo.com/nearshore-call-center-pricing/) [P]; Callforce, [costo del nearshore](https://callforce.global/blog/cost-of-nearshore-outsourcing/) y [soporte bilingüe en Colombia](https://callforce.global/blog/bilingual-customer-support-outsourcing/) [P]; Contact Center USA, [costo por hora por país](https://contactcenterusa.com/blog/call-center-outsourcing-cost-per-hour-2026) [P]

**Citadas desde las investigaciones (sin nueva verificación en esta ronda)**

- Gartner, 87% exige acceso a una persona; SQM Group vía Fini y Bluetweak, traspaso tibio; [Structured State Reconciliation for Human-AI Task Handover](https://arxiv.org/abs/2608.28907); Ethoca Consumer Clarity; Brynjolfsson, Li y Raymond, QJE 2025; Erlang C y gestión de fuerza laboral; Infobip, botones y listas de WhatsApp; [AG-UI](https://docs.ag-ui.com/introduction); W3C, [WCAG 2.2](https://www.w3.org/TR/WCAG22/); Ley 1328 de 2009 (Colombia), BCRA texto ordenado de protección de usuarios, CONDUSEF (México); LGPD artículo 20 (Brasil)

