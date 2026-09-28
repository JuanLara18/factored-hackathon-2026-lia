# Desafío de Gobierno a la primera línea

**Cara:** VP Gobierno. **Versión:** 1 (27 de septiembre de 2026). **Paso:** 2 del ciclo de iteración
([modelo operativo](00_Presidencia_Modelo_operativo.md), sección 7).
**Qué se revisó:** el [consolidado](07_Consolidado.md) completo y, de
[Clientes](01_VP_Clientes.md), [IA](02_VP_Inteligencia_Artificial.md), [Datos](03_VP_Datos.md) y
[Tecnología](04_VP_Tecnologia.md), las secciones de reglas, seguridad, interfaces y decisiones propuestas,
más búsquedas puntuales. La vara es la [definición de Gobierno](05_VP_Gobierno.md) (R-GOB-01 a R-GOB-93).
Sin búsquedas web.

## 1. Resumen

La primera línea llega bien alineada en lo esencial: nadie usa atributos protegidos ni acento para
decidir; el traspaso a persona es sin resistencia; el audio crudo no se guarda; la redacción y la
comprensión trabajan con marcadores (DP-IA-02); los servicios autorizan también por su cuenta (DP-TEC-10);
la llave del organizador tiene una regla más estricta que la mía (Datos, 4.7); el mapeo de 01 ya no usa
ASI04 para el acceso no autorizado.

Hay **14 hallazgos: 0 bloqueantes, 4 mayores y 10 menores**. Los mayores son:

- **H-GOB-01:** Clientes deja que un reclamo termine "fuera de plazo" (R6) y lo afirma como vencido.
- **H-GOB-02:** Tecnología exige OTP también para **bloquear**, lo que retrasa la contención.
- **H-GOB-03:** Datos admite copiar el dataset a la nube con solo el visto bueno de Gobierno si los
  organizadores no responden. Gobierno **no** puede autorizar en nombre del dueño del dato.
- **H-GOB-04:** Datos y Tecnología todavía describen "campos mínimos enmascarados" hacia el modelo, en vez
  de marcadores sin valores.

Cuatro menores son correcciones a mi propia definición (H-GOB-06, 09, 10 y 14), que haré en la versión 2.
Respondo las 19 solicitudes dirigidas a Gobierno: 13 aceptadas, 5 aceptadas con ajuste y 1 rechazada
en parte (S-DAT-05, la copia en nube). De las 43 decisiones propuestas que tocan mi dominio (de la
primera línea, más DP-AUD-08): 27 se aprueban, 15 se aprueban con condición y 1 se objeta en parte
(DP-DAT-12).

## 2. Hallazgos

Severidad según la sección 7 del modelo operativo: **bloqueante** si deja una exigencia del enunciado sin
dueño, contradice un principio o una decisión firme, o deja una interfaz sin quien la entregue; **mayor** si
debilita un control de Gobierno o arriesga un resultado inseguro; **menor** si es inconsistencia o hueco sin
riesgo inmediato.

| ID | Definición y sección | Regla afectada | Hallazgo | Severidad | Cambio exigido | Dueño |
|---|---|---|---|---|---|---|
| H-GOB-01 | Clientes: tabla de escenarios (F5 "R6 o R5"), plantilla de fuera de plazo, código `FUERA_DE_PLAZO` "si el cliente acepta revisión" | R-GOB-23, DP-GOB-04; U6 y U11 | El sistema afirma "ese plazo venció el {fecha}" y, si el cliente no acepta la revisión, termina en R6. Con fecha de corte desconocida, desfase de fechas (D8) y excepciones legales, esa afirmación puede ser materialmente falsa y quita un derecho | **mayor** | F5 termina siempre en R5. La plantilla dice que el reclamo "podría estar fuera del plazo de {norma}" y que una persona lo revisa, sin afirmar el vencimiento. Si el cliente no quiere esperar, el caso igual queda registrado para revisión humana | Clientes |
| H-GOB-02 | Tecnología: R-TEC-68 ("toda acción con efecto exige `accion`") | R-GOB-25, DP-GOB-10; N4 | Pedir OTP antes de **bloquear** demora la contención justo cuando más importa: tarjeta perdida, fraude en curso, portugués de noche (E7). El bloqueo protege al cliente y se revierte con la reexpedición | **mayor** | Nivel `consulta` más confirmación explícita para bloquear; `accion` (OTP de 300 s o menos) para radicar. La tabla de `policy/v1` manda y Tecnología la lee de ahí | Tecnología |
| H-GOB-03 | Datos: 4.6, "copia en Google Cloud" | D-15, R-GOB-81; P11 | Sin respuesta de los organizadores al D1, Datos procedería con el visto bueno de Gobierno. Pero el dato no es de Gobierno: su perímetro lo fija el organizador | **mayor** | Sin autorización escrita de los organizadores, el perfil de nube corre solo con el *fixture* y los datos del equipo. Gobierno no dará un visto bueno supletorio | Datos |
| H-GOB-04 | Datos: 4.6, "modelos externos"; Tecnología: R-TEC-135 | R-GOB-80, DP-GOB-08 | Describen "campos mínimos de oro operacional con enmascaramiento" hacia el modelo. Es más débil que los marcadores que ya adoptó IA (DP-IA-02): un monto o un comercio enmascarado a medias sigue siendo dato del organizador | **mayor** | Alinear ambas definiciones con los marcadores: ningún valor del dataset sale; las plantillas rellenan después del modelo. La prueba de intercepción (S-GOB-05) es la evidencia | Datos y Tecnología |
| H-GOB-05 | Datos: R-DAT-60 y DP-DAT-12 | R-GOB-46, DP-GOB-19, R-GOB-42 | Estado civil y educación se cargan para auditar. Además, los segmentos autorizados no incluyen la franja de edad, aunque el 31% de los clientes tiene 65 años o más | menor | Agregar la franja de edad (menos de 65, 65 o más) a los segmentos autorizados. Estado civil y educación no se cargan en `plata_restringida` salvo acta que lo justifique | Datos |
| H-GOB-06 | Tecnología: R-TEC-117; Gobierno: 05, sección 4.9.3 (S-AUD-15) | R-GOB-85 | Dos tablas de retención distintas | menor | Una sola tabla: registros y trazas operativos, 30 días (Tecnología); evidencia de evaluación en platino, hasta el cierre más 90 días (Gobierno); desafíos OTP, 24 horas y solo como huella, nunca el código en claro (I-13) | Gobierno con Tecnología |
| H-GOB-07 | Tecnología: escalera N0 a N6; Gobierno: modos de R-GOB-10 | R-GOB-10, PB-4 | Hay dos vocabularios para la degradación, y la escalera no dice qué pasa si también cae el filtro local | menor | Mapeo único: `normal` es N0 y N1; `solo_informacion` es N4; `solo_humano` es N6; `apagado` se agrega como N7. Nueva condición: sin ningún filtro disponible, no se radica (se sigue conteniendo y traspasando) | Tecnología |
| H-GOB-08 | IA: DP-IA-10, k = 2 en voz | R-GOB-58 | Con k = 2 baja la probabilidad de ver la inestabilidad justo en el canal más frágil | menor | k = 2 solo en la parte representativa de voz; k = 3 en el estrés de voz y en V1, V2 y V9 | IA |
| H-GOB-09 | IA: S-IA-01 (r* de 2%, 5% y 10%); Gobierno: R-GOB-27 (1%, 2% y 5%) | R-GOB-27 | Umbrales distintos para el mismo punto de operación | menor | Se adopta la propuesta de IA, con dos condiciones: la urgencia (R4) nunca depende de r* sino de las señales deterministas de R-GOB-28, y toda acción se confirma con datos de la base. Gobierno corrige R-GOB-27 | Gobierno e IA |
| H-GOB-10 | Datos: 4.7; Gobierno: 05, sección 4.2 | R-GOB-70 | Datos prohíbe guardar la llave del organizador en Secret Manager, y mi tabla le daba a `sa-pipeline` lectura de ese secreto | menor | Gobierno adopta la regla de Datos, más estricta: la llave vive solo en la máquina de ingesta y se pide su revocación al cierre. Se corrige la sección 4.2 de 05 | Gobierno |
| H-GOB-11 | Tecnología: DP-TEC-12 (US$600); Datos: DP-DAT-13 (US$50); Gobierno: sección 7 | R-GOB-93 | Tres techos de gasto distintos | menor | La Presidencia fija un techo único. Opinión de Gobierno: la capa de seguridad cabe en US$30 | Presidencia |
| H-GOB-12 | Tecnología: DP-TEC-05, Twilio con número de EE. UU. | R-GOB-87, R-GOB-90 | Un proveedor de telefonía recibiría audio sin haber pasado la evaluación de terceros | menor | Twilio solo después del cuestionario de la sección 4.10 de 05: sin grabación, y solo con llamadas del equipo con audio sintético o de voluntarios con consentimiento que lo nombre | Tecnología |
| H-GOB-13 | IA: DP-IA-07, Live API de Gemini como experimento | R-GOB-06, R-GOB-84, R-GOB-87 | El experimento manda audio a un proveedor y es de nivel alto | menor | Solo audio sintético o de voluntarios cuyo consentimiento nombre al proveedor. Queda fuera de la versión candidata salvo acta | IA |
| H-GOB-14 | Clientes: pregunta abierta 2 y S-CLI-01 | R-GOB-82 | Clientes pregunta si alguna norma exige grabar la atención; mi definición no lo respondía | menor | Respuesta (sección 3): ninguna norma verificada lo exige; mientras tanto no se graba y queda **a confirmar** | Gobierno |

## 3. Respuesta a las solicitudes dirigidas a Gobierno

| Solicitud | De | Respuesta | Detalle |
|---|---|---|---|
| S-CLI-01 | Clientes | **aceptada con ajuste** | Todas las variables quedan en `policy/v1` con norma y fecha: plazos, régimen argentino por producto (sección 2.3 de 05), texto permitido del abono de México ("tiene derecho; quedó registrado", nunca "ya le abonamos"), aclaraciones antes de ofrecer persona (2), umbral de monto por país y nivel `acr` por acción (DP-GOB-10). Los calendarios de feriados los entrega Datos (S-GOB-19). **Grabación:** ninguna norma verificada exige grabar la atención; no se graba y queda a confirmar (H-GOB-14). Entrega: D2 |
| S-CLI-02 | Clientes | **aceptada** | Acta de Protección al consumidor en D3 sobre los avisos, las frases prohibidas y obligatorias, DP-CLI-02 (con condición, sección 4) y DP-CLI-06. El catálogo de líneas de crisis se aprueba si cada número trae fuente oficial y fecha de consulta |
| S-CLI-03 | Clientes | **aceptada** | El acta de F2 registra los acuerdos de servicio y los supuestos de costo. E8, D10 y L7 entran al retenido si DP-CLI-07 se aprueba **antes** del congelamiento. Las correcciones del experto quedan fuera del materializador del retenido |
| S-CLI-04 | Clientes | **aceptada** | Se suman al catálogo AT-33 (suplantación del banco), AT-34 (un supuesto agente pide el código), AT-35 (plantilla falsa reenviada), AT-36 (voz sintética que pide acciones) y AT-37 (presión sobre el experto), con resultado esperado y código OWASP. Escritos en D2; en el equipo rojo en D7 |
| S-IA-01 | IA | **aceptada con ajuste** | La taxonomía y la guía de anotación entran como anexo versionado de `policy/v1`. Se adoptan r* de 2%, 5% y 10% (H-GOB-09). Objetivo de urgencia: 100% en las señales deterministas de R-GOB-28 y recuperación de 0,98 o más para la urgencia aprendida |
| S-IA-02 | IA | **aceptada** | El generador del retenido será de una familia abierta distinta de Google y de Anthropic. El manifiesto declara la familia y la fracción escrita a mano (25% o más), también en el retenido del componente |
| S-IA-03 | IA | **aceptada con ajuste** | k según H-GOB-08. La redacción y la comprensión deslexicalizadas se aceptan como cumplimiento de D-15 en modo restrictivo, siempre que la prueba de intercepción (S-GOB-05) salga limpia en la corrida oficial |
| S-IA-04 | IA | **aceptada** | Inspeccionar en la entrada y restringir el turno (sin bloquear al cliente); bloquear en la salida y responder por plantilla (sección 4.3 de 05). Falsos positivos aceptables: 5% o menos por idioma sobre casos legítimos de desarrollo |
| S-IA-05 | IA | **aceptada** | Los clientes del retenido son disjuntos de los de desarrollo y sus transacciones son posteriores. La prueba de disjunción, con huella, va al acta de F2 |
| S-DAT-05 | Datos | **rechazada en parte** | Se aprueban la clasificación y los *policy tags* (con H-GOB-05), el uso de atributos protegidos solo para equidad y la retención por insumo (tabla única de H-GOB-06). Se **rechaza** la interpretación de D-15 que permitiría copiar el dataset a la nube con el visto bueno de Gobierno (H-GOB-03) |
| S-DAT-06 | Datos | **aceptada** | Los parámetros quedan en `policy/v1/riesgo.yaml` y `umbrales.yaml`. `ventana_dias` debe ser al menos 210, porque el plazo más largo del cliente es el de 180 días de México más 30. La firma de congelamiento incluye `version_datos` y `huella_contexto` |
| S-TEC-01 | Tecnología | **aceptada** | `policy/v1` valida contra el JSON Schema de Tecnología si este llega en D1; cada regla lleva norma y fecha |
| S-TEC-02 | Tecnología | **aceptada con ajuste** | Matriz: sin Model Armor (N1) se sigue con Presidio y el clasificador local; sin ningún filtro no se radica (H-GOB-07); cualquier filtro de salida caído fuerza plantillas. Recuperación de datos personales: 0,95 o más por tipo en el conjunto etiquetado y cero números completos de tarjeta. La plantilla de Model Armor es la de la sección 4.3 de 05. LiteLLM se acepta con sus controles |
| S-TEC-03 | Tecnología | **aceptada con ajuste** | Retención según H-GOB-06. Sesión `consulta`: 15 minutos de inactividad o 60 absolutos; OTP de 300 s y un solo uso. Retoma y presupuesto por conversación: se aceptan los valores de Tecnología si la retoma exige reautenticación. Vertex AI con endpoint **regional**, no global, para poder declarar dónde se procesa |
| S-TEC-13 | Tecnología | **aceptada** | La corrida la hace el ejecutor de Gobierno (`sa-eval`) en el proyecto o la carpeta de evaluación, contra el digest del acta. Registra versiones, huella de resultados y apertura del retenido (R-GOB-55 y R-GOB-58). Entrega: D8 |
| S-AUD-07 | Auditoría | **aceptada** | Huellas en el acta de F2 y en la etiqueta `retenido-v1`; la de voz, en su acta. DP-AUD-08 se aprueba: el retenido va cifrado con `age` (R-GOB-55) |
| S-AUD-08 | Auditoría | **aceptada** | La lista está en las tablas de la sección 2.3 de 05 y se entrega como `normas.yaml` en D1 |
| S-AUD-09 | Auditoría | **aceptada** | Actas de F2, F4, F5 y F6 selladas con huella el mismo día, más el informe de validación del juez |
| S-AUD-15 | Auditoría | **aceptada** | Una sola tabla de retención según H-GOB-06, copiada igual en 04 y en 05 |

## 4. Posición sobre las decisiones propuestas

Solo las que tocan riesgo, seguridad, privacidad, cumplimiento, equidad o la honestidad de la medición.

| Decisión | Posición | Condición o motivo |
|---|---|---|
| DP-CLI-01 | aprobar | el registro no cambia la ruta (R-GOB-41) |
| DP-CLI-02 | aprobar con condición | la oferta de contención llega después de `traspaso_iniciado`, una sola vez y sin demorar la cola (U11) |
| DP-CLI-03 | aprobar | contener primero y elegir idioma sin presión (R-GOB-36) |
| DP-CLI-04 | aprobar | es coherente con AT-32: el banco no llama a números dictados |
| DP-CLI-05 | aprobar con condición | los borradores de la IA para el experto pasan igual por el filtro de salida y llevan marcadores |
| DP-CLI-06 | aprobar | coincide con DP-GOB-15 |
| DP-CLI-07 | aprobar con condición | los tres escenarios entran antes del congelamiento de F2; si no, van a la suite posterior |
| DP-CLI-08 | aprobar | rangos calibrados y nunca como promesa (R-GOB-36) |
| DP-CLI-10 | aprobar | afecta el registro, no la decisión |
| DP-CLI-11 | aprobar | minimización en plantillas fuera de ventana |
| DP-CLI-12 | aprobar | supuestos de costo en acta antes del retenido (P1, P3) |
| DP-CLI-13 | aprobar | honestidad de la proyección |
| DP-IA-01 | aprobar con condición | el generador del retenido es una quinta familia abierta (S-IA-02); ninguna familia es a la vez generador, sistema y juez |
| DP-IA-02 | aprobar | es DP-GOB-08 |
| DP-IA-03 | aprobar | el clasificador local reduce lo que sale (P9, P11) |
| DP-IA-04 | aprobar con condición | la taxonomía se versiona dentro de `policy/v1` y cada etiqueta cita esa versión (R-GOB-19) |
| DP-IA-05 | aprobar | valores sintéticos y verbalizador local |
| DP-IA-06 | aprobar con condición | condiciones de H-GOB-09 |
| DP-IA-07 | aprobar con condición | condiciones de H-GOB-13 |
| DP-IA-08 | aprobar con condición | el error por acento de cada proveedor candidato se reporta completo en equidad, no solo el del peor acento |
| DP-IA-10 | aprobar con condición | condiciones de H-GOB-08 |
| DP-DAT-01 | aprobar con condición | el perfil de nube solo recibe datos del organizador con su autorización escrita (H-GOB-03) |
| DP-DAT-03 | aprobar | prueba de cero caminos de PII a oro operacional y platino |
| DP-DAT-04 | aprobar | tokenización con llave en la zona `seguridad`; SDP como control detectivo |
| DP-DAT-05 | aprobar | fuente autorizada `data/` |
| DP-DAT-06 | aprobar | instantánea de solo lectura con huella |
| DP-DAT-07 | aprobar | más estricta que 05; la adopto (H-GOB-10) |
| DP-DAT-11 | aprobar | protege contra mezclar generaciones |
| DP-DAT-12 | **objetar en parte** | falta la franja de edad entre los segmentos autorizados, y estado civil y educación no deben cargarse (H-GOB-05) |
| DP-DAT-13 | aprobar con condición | región declarada en el reporte; el techo lo fija la Presidencia (H-GOB-11) |
| DP-DAT-14 | aprobar | destruir la llave de tokenización es el borrado más fuerte |
| DP-TEC-01 | aprobar con condición | la región de producción la fija la residencia de datos y se declara en la EIPD |
| DP-TEC-02 | aprobar | Presidio siempre y Model Armor en la nube, con aporte medido (R-GOB-69) |
| DP-TEC-03 | aprobar con condición | a Cloud Logging y Trace solo llega lo ya redactado (R-GOB-78) |
| DP-TEC-04 | aprobar | llave de firma en Cloud KMS e IAP para lo interno |
| DP-TEC-05 | aprobar con condición | condiciones de H-GOB-12 |
| DP-TEC-07 | aprobar | sin autorización, datos del equipo |
| DP-TEC-08 | aprobar | federación sin llaves de cuentas de servicio (R-GOB-71) |
| DP-TEC-10 | aprobar | defensa en profundidad |
| DP-TEC-11 | aprobar | confirmación con *nonce* (R-GOB-25) |
| DP-TEC-12 | aprobar con condición | techo único de la Presidencia (H-GOB-11) |
| DP-TEC-13 | aprobar | cadena de suministro (T-22) |
| DP-AUD-08 | aprobar | es R-GOB-55 |

## 5. Cambios que Gobierno hará en su versión 2

- **R-GOB-27:** puntos de operación de la comprensión con r* de 2%, 5% y 10% (H-GOB-09).
- **Sección 4.2:** sin secreto del organizador en Secret Manager; `sa-pipeline` no lo lee (H-GOB-10).
- **Sección 4.9.3:** tabla única de retención con Tecnología (H-GOB-06).
- **R-GOB-58:** k = 2 en el representativo de voz (H-GOB-08).
- **R-GOB-82:** respuesta sobre la grabación, a confirmar (H-GOB-14).
- **Sección 4.7:** AT-33 a AT-37 (S-CLI-04).
- **R-GOB-10:** equivalencias con la escalera N0 a N7 de Tecnología (H-GOB-07).
