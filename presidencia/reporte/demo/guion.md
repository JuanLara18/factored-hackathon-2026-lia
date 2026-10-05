# Guion de la demostración (5 a 7 minutos)

**Sitio:** https://latam-bank-hackaton-2026.web.app. **Consola del experto:** https://latam-bank-hackaton-2026.web.app/operador/. Volver al [reporte final](../00_reporte_final.md). Los datos son sintéticos y las personas son ficticias; el guion lo dice en voz alta al empezar.

## Antes de empezar (lista de verificación, 10 minutos antes)

| # | Verificar | Cómo |
|---|---|---|
| 1 | Servicio despierto | Cloud Run ya recibe un ping cada 5 minutos (Cloud Scheduler, `latam-chat-despierto`). El agente no: el paso 4 lo despierta. Si se quiere garantía total, `gcloud run services update latam-chat --region us-central1 --min-instances 1` y volver a 0 al terminar |
| 2 | Código del experto a mano | `gcloud run services describe latam-chat --region us-central1 --format="value(spec.template.spec.containers[0].env)"` y copiar `LATAM_OPERADOR_CODIGO` ([ESTADO](../../ESTADO.md)) |
| 3 | Estado limpio | `curl -sS -X POST "$LATAM_API/api/demo/restablecer" -H "Content-Type: application/json" -d "{\"codigo\": \"$LATAM_OPERADOR_CODIGO\"}"`, con `LATAM_API=https://latam-chat-47808508188.us-central1.run.app`; responde `{restablecido: true, ...}` ([ARRANQUE](../../../tecnologia/infra/ARRANQUE.md)) |
| 4 | Primer turno de calentamiento | abrir la banca, ingresar, pulsar "Hable con Lía" y enviar "Hola" (el primer turno tras un rato puede tardar más de diez segundos); luego restablecer de nuevo |
| 5 | Dos ventanas del navegador | una para el cliente y otra para `/operador/`, ambas ya cargadas |
| 6 | Pestañas de evidencia | Cloud Trace del proyecto `latam-bank-hackaton-2026`, [04_evaluacion](../04_evaluacion.md) y [datos/README](../../../datos/README.md) abiertos |
| 7 | Plan B listo | las páginas con `?demo=local` abren con fixtures sin backend |
| 8 | Modelo | no cambiar `LATAM_MODELO`; el modelo de guion solo como último recurso y se declara |

## Guion

### 0. Apertura (0:00 a 0:30)

**Hacer:** abrir https://latam-bank-hackaton-2026.web.app (inicio).

**Decir:** "LATAM Bank es un banco inventado con datos sintéticos de México, Colombia y Argentina. Elegimos un flujo: recibir cargos no reconocidos. En los datos, esa es la queja más grande, tarda 37 horas en tener primera respuesta y 75,5% no está cerrada ([01_problema](../01_problema.md)). El modelo entiende y redacta; el código decide."

### 1. Camino normal en español (0:30 a 2:00)

**Hacer:**

1. Ir a `/banca/`. En "Ingrese a la banca en línea", elegir el país Colombia (queda en español de usted y Camila Duarte preseleccionada) y pulsar "Ingresar a la demostración". Las seis personas son Valentina Ríos y Mateo Herrera (México), Camila Duarte y Santiago Vélez (Colombia), Isabela Mora y Andrés Quintero (Argentina).
2. En "Movimientos recientes", tocar un cargo de compra aprobado y pulsar "No reconozco este cargo".
3. Se abre el asistente con la transacción ya fijada. Escribir: "No reconozco este cargo, yo no compré ahí."
4. Cuando aparezca la pantalla de confirmación con monto y tarjeta enmascarada, aprobar para abrir el reclamo.
5. Ir a "Reclamos" en la barra del portal y mostrar el caso, el plazo y el historial.
6. Opcional: en una tarjeta de "Sus productos", mostrar las acciones del propio producto (Movimientos, Bloquear, Reportar un cargo).

**Decir:** "La transacción la fija el servidor, no el modelo. El agente leyó la ficha y propone abrir el reclamo; nada se ejecuta hasta que apruebo en pantalla. El monto y la tarjeta salen de la base. El mensaje final dice qué se hizo, qué no y qué sigue. El aviso de IA y el botón de persona están siempre visibles."

### 2. Solicitud ambigua o no soportada (2:00 a 3:00)

**Hacer (conversación abierta):** pulsar "Hable con Lía" sin abrir ningún movimiento y escribir: "Hola, ¿en qué me puede ayudar?" y luego "¿Me muestra mis últimos movimientos?"

**Decir:** "El asistente se llama Lía y se presenta siempre como inteligencia artificial. No es un formulario: conversa sobre cobros, tarjetas y reclamos, y lo que muestra sale de la base."

**Hacer (no soportada):** en el asistente, escribir: "¿Me pueden subir el cupo de la tarjeta?"

**Decir:** "Fuera de alcance: el agente se abstiene, no inventa reglas de crédito ni elegibilidad, recuerda en qué sí ayuda y la persona sigue a un clic. En la evaluación, los casos no soportados pasan 6 de 6 ([04](../04_evaluacion.md) sección 5.3)."

**Hacer (ambigua):** en esa misma conversación con Lía, escribir: "Hay un cobro raro de hace unos días." Como no se abrió ningún movimiento, no hay transacción fijada y el asistente tiene que aclarar.

**Decir:** "Sin monto ni comercio, el agente consulta los movimientos, pregunta lo mínimo y no radica a ciegas."

### 3. Traspaso a una persona (3:00 a 4:30)

**Hacer:**

1. En el asistente pulsar "Hablar con una persona".
2. Cambiar a la ventana `/operador/`. En "Ingreso del experto" escribir el código y pulsar "Entrar".
3. En "Cola de traspasos" abrir el nuevo traspaso (pulsar "Actualizar" si no aparece) y tomar el caso.
4. Recorrer el paquete: motivo y regla, prioridad, hechos verificados con fuente y hora, acciones realizadas y no realizadas, preguntas abiertas, plazos, evidencia.
5. Escribir un mensaje al cliente: "Hola, soy del equipo. Ya revisé su caso."
6. Volver a la ventana del cliente: el mensaje aparece en el mismo hilo.
7. En la consola, resolver el caso con una etiqueta y una nota.

**Decir:** "El paquete tiene 19 campos: lo que dijo, lo que verificamos, lo que hicimos y no hicimos, lo que falta y la regla con su versión. No lleva nombre, documento ni tarjeta completa. La persona escribe en el mismo hilo y su corrección queda como etiqueta que nunca entra a la evaluación."

### 4. Portugués (4:30 a 5:30)

**Hacer:**

1. Volver a `/banca/` y cerrar sesión. En el selector de país elegir Brasil: todo el sitio pasa a portugués. Elegir una persona distinta de la anterior (por ejemplo Isabela Mora), para no chocar con el reclamo ya abierto.
2. Abrir un cargo, pulsar el botón de reclamo y en el asistente escribir: "Não reconheço essa cobrança."
3. Aprobar en pantalla.
4. Opcional, mezcla: escribir "no reconozco este cobro, pode me ajudar?" y mostrar que responde en portugués.

**Decir:** "Es atención en portugués a clientes de la región, no cuentas brasileñas: el dataset no trae Brasil y las plantillas no las ha revisado un hablante nativo. El retenido tiene 13 de 32 casos en portugués ([04](../04_evaluacion.md) sección 3)."

### 5. Evidencia (5:30 a 7:00)

1. **Trazas.** En Cloud Trace abrir una traza reciente de `latam-chat`: spans `invoke_agent`, `chat <modelo>` y `execute_tool`, con `latam.trabajador.id` y versión, sin contenido. Decir: "Las explicaciones se apoyan en fuentes, reglas y registros de ejecución; no guardamos razonamiento del modelo."
2. **Evaluación.** Abrir [04_evaluacion](../04_evaluacion.md) sección 5.1. Decir: "Fuera de línea, 32 casos retenidos y 96 corridas: resolución segura 29 de 75 sobre todo el alcance y 29 de 36 sobre los que debían resolverse; 0 de 96 inseguros, con cota de 4%; p50 de 1,41 s y p95 de 4,61 s por turno; US$ 0,002 por caso. La línea base de reglas es igual de buena, y lo decimos. Hallamos fallas, como una inyección que subía la urgencia y una política que la herramienta no aplicaba, y el anexo muestra cómo se corrigieron y qué quedó abierto."
3. **Datos.** Abrir [datos/README](../../../datos/README.md). Decir: "Bronce a platino, contratos, reglas de calidad, manifiesto encadenado y un fixture de actualización. Dos modelos aprendidos: el motivo supera a las reglas con macro-F1 de 0,399 contra 0,343, y el riesgo de plazo es un resultado negativo que no usamos."
4. **Cierre.** "Lo que falta para operar está en [06_produccion](../06_produccion.md): una instancia, sesiones en memoria, Terraform sin aplicar, retención sin implementar."

## Plan B si algo falla en vivo

| Falla | Qué hacer |
|---|---|
| Primer turno lento (arranque en frío) | decir que Cloud Run y Agent Runtime escalan a cero y esperar hasta 90 s, el tope del turno |
| El asistente responde con error o silencio | pulsar "Hablar con una persona" y seguir con la consola: el traspaso no depende del modelo; es una muestra de caída segura |
| El cargo ya tiene reclamo | usar otro movimiento, o restablecer con el comando de la lista (requiere el código) |
| Agent Runtime caído | `LATAM_MODELO=guionado` en el servicio, declarando que es el modelo de guion; o abrir `?demo=local` en `/banca/` y `/operador/` |
| La consola no entra (401) | releer el código del entorno de Cloud Run; tras 5 fallos por minuto responde 429, esperar un minuto |
| Sin red | mostrar el modo `?demo=local` y los capítulos del reporte |
| Una respuesta del modelo sale rara | es una muestra de lo que el reporte documenta (fallas de ruta); no corregir en vivo |

## Después

Volver `--min-instances` a 0 y restablecer el estado. No dejar el código del experto en pantallas compartidas.
