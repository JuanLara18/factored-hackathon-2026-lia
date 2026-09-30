# Hoja de ruta y backlog (v1)

**Propósito:** ordenar el trabajo para pasar del diseño al desarrollo. Lo mantiene la **Oficina de
Entrega** ([04](../docs/diseno/04_Organizacion_y_roles.md), sección 5); la arquitectura está en
[06](../docs/diseno/06_Arquitectura.md) y las decisiones en [Decisiones.md](Decisiones.md). Los criterios de
aceptación citan escenarios y métricas de [01](../docs/diseno/01_Interacciones_y_criterios.md).

---

## 1. Dónde estamos

| Frente | Estado |
|---|---|
| Investigación | 21 investigaciones, incluidas la auditoría del dataset y una por cada cara |
| Diseño | principios, interacciones, plan, datos, organización v2, cobertura del enunciado y arquitectura |
| Decisiones | D-01 a D-21 cerradas; abiertas solo las que dependen de terceros (proveedores, uso de modelos externos, tamaño del equipo) |
| Construcción | nada; el repositorio no existe |
| Bloqueos externos | las preguntas a los organizadores ([05](../docs/diseno/05_Cobertura_del_enunciado.md), sección 4) |

## 2. Antes del arranque (D0)

En este orden; los *spikes* cierran decisiones que quedaron provisionales.

1. **Enviar las preguntas a los organizadores** (son diez; las dos últimas se sumaron con la voz: si se
   puede preparar código antes del inicio oficial y si se permiten APIs de voz y grabaciones con
   consentimiento). Si no se puede preparar código antes, los puntos 2 a 5 esperan al D1.
2. **Crear el repositorio** fuera del Drive (D-03) con el esqueleto de [06](../docs/diseno/06_Arquitectura.md),
   sección 8, `.gitignore` para datos y secretos, `justfile`, `docker-compose.yml` (Postgres y
   Phoenix) y los ADR de D-11, D-12 y D-17 a D-20.
3. **Escribir los subagentes** en `.claude/agents/` con mandato, entradas, formato de salida y permisos
   ([04](../docs/diseno/04_Organizacion_y_roles.md), sección 10).
4. **Bronce completo** del bucket con manifiesto y las consultas de la investigación 13 sobre el total.
5. **Spikes:**

| Spike | Pregunta | Cierra | Tiempo |
|---|---|---|---|
| S1 Voz en cascada | ¿Pipecat con los candidatos de reconocimiento y síntesis da p50 de voz a voz ≤ 1 s en español y portugués? ¿Qué error por acento en 20 frases grabadas? | proveedores y marco de voz (D-18) | 1 día |
| S2 Frontend nativo | ¿gpt-realtime o Gemini Live delegan en un motor de prueba con una sola herramienta? ¿Con qué latencia? | el experimento de D-18, o su recorte | medio día |
| S3 Chat AG-UI | ¿PydanticAI y AG-UI llevan componentes, aprobaciones y texto filtrado por frases a una web mínima? | D-19 | medio día |
| S4 Estado entre canales | ¿un caso en Postgres se retoma de chat a voz sin repetir acciones? | D-20 y V6 | medio día |
| S5 Datos sobre el total | ¿se sostienen las cifras de la muestra (fraude, quejas, restricciones)? | D-14 y la revisión 05 | medio día |

## 3. Backlog por cara

Cada épica tiene dueño, fase, dependencias y criterio de aceptación.

### Presidencia y Oficina de Entrega

| ID | Épica | Fase | Aceptación |
|---|---|---|---|
| PRE-1 | Preguntas a organizadores y reglas confirmadas | D0 | respuestas registradas en Decisiones |
| PRE-2 | Revisión diaria y orden de recorte | continuo | registro de lo cerrado y lo recortado |
| PRE-3 | Ensamble del reporte y la demo | F7 | demo con los tres casos en ES y PT; reporte con medido, simulado y proyectado separados |

### VP Clientes

| ID | Épica | Fase | Depende de | Aceptación |
|---|---|---|---|---|
| CLI-1 | Guiones por estado del motor en ES y PT, para chat y voz | F2 y F3 | estados de 01 | N1 a N9 y A1 a A5 cubiertos; revisado por `voz-del-cliente` |
| CLI-2 | Componentes de chat y su degradación a WhatsApp | F3 | TEC-5 | ficha, opciones, confirmación, estado y traspaso; ≤ 3 botones y ≤ 10 filas |
| CLI-3 | Diseño de voz: lectura de vuelta, rellenos honestos, DTMF | F3v | TEC-6 | V1, V2 y V8 |
| CLI-4 | Operaciones de fraude y disputas: colas por idioma, turno y especialidad; vista del experto; corrección como etiqueta | F3 | TEC-2 | E1 a E7; paquete completo |
| CLI-5 | Árbol de resultados con línea base y guion de la demo | F2 y F7 | DAT-2 | indicadores con valor de referencia |

### VP Inteligencia Artificial

| ID | Épica | Fase | Depende de | Aceptación |
|---|---|---|---|---|
| IA-1 | Semilla humana de mensajes y generador de conversaciones desde rutas conocidas | F2 | GOB-1 | distancia de estilo reportada; auditoría de plantilla sin fuga |
| IA-2 | Comprensión: base, comparados, calibración, umbrales, ES a PT, análisis de errores | F4 | IA-1 | reporte del componente (D-14) |
| IA-3 | Redacción desde hechos y plantillas para lo crítico | F3 | TEC-1 | anclaje completo en montos, plazos y estados |
| IA-4 | Voz: medición de proveedores y detección de turno | F0 y F3v | S1 | error por acento y latencia medidos |
| IA-5 | Arnés de evaluación y simulador de usuario de texto | F2 | GOB-1 | corre el conjunto de desarrollo con pass^k y métricas oficiales |
| IA-6 | Simulador de voz: personas por locale, ruido del dataset, G.711, interrupciones | F5 | IA-4 e IA-5 | casos de voz generados desde los de texto |
| IA-7 | Registro de agentes y hojas de vida | F3 a F6 | TEC-1 | un registro por trabajador con evaluación que lo habilita |
| IA-8 | Experimento de frontend nativo | F5 | S2 | mismas métricas de 5.9 que la cascada |

### VP Datos

| ID | Épica | Fase | Depende de | Aceptación |
|---|---|---|---|---|
| DAT-1 | Bronce con manifiesto y vigilancia del bucket | F0 y F1 | repositorio | etags y conteos por archivo; alerta ante cambios |
| DAT-2 | Auditoría sobre el total, EDA de negocio, restricciones operativas y línea base | F1 | DAT-1 | cifras de 05 confirmadas o corregidas |
| DAT-3 | Contratos ODCS, plata incremental con cuarentena y *fixture* | F1 a F3 | DAT-1 | correr dos veces da la misma huella; el *fixture* da lo esperado |
| DAT-4 | Oro operacional: transacciones recientes, estado de productos, ficha y directorio de comercios del equipo | F3 | DAT-3 | sin PII directa; coherencia de dueño |
| DAT-5 | Métricas oficiales y linaje en platino | F3 a F6 | DAT-3 | cada cifra del reporte con su consulta |
| DAT-6 | Inventario de insumos con su origen | F2 a F7 | todos | cada tabla, caso y audio con su clase |

### VP Tecnología

| ID | Épica | Fase | Depende de | Aceptación |
|---|---|---|---|---|
| TEC-1 | Tipos del dominio ([06](../docs/diseno/06_Arquitectura.md), sección 5) | F3, primer día | | pyright estricto sin errores |
| TEC-2 | Motor de flujo con estados y estado durable con idempotencia | F3 | TEC-1 | secuencia de estados en la traza; V6 |
| TEC-3 | Servicios simulados BIAN e identidad (`acr`, OTP, reloj) | F3 | DAT-4 | D5 y S4 |
| TEC-4 | Capa de herramientas tipada y punto de decisión con registro | F3 | TEC-1 | S1 a S10 rechazados en la capa de herramientas |
| TEC-5 | Superficie de chat con AG-UI y web | F3 | S3 | N1 a N6 de punta a punta en ES |
| TEC-6 | Superficie de voz con Pipecat | F3v | S1 | los mismos casos por voz en ES |
| TEC-7 | Gateway con cuotas, costo y filtros | F3 a F5 | TEC-5 | costo por caso registrado |
| TEC-8 | Trazas y panel de trazas | F3 | TEC-2 | cada turno con sus etapas y latencias |
| TEC-9 | Prueba de capacidad | F5 | TEC-5 y TEC-6 | punto de quiebre y cuello de botella reportados |
| TEC-10 | Instalación de un comando | F0 a F7 | | `just setup demo` en máquina limpia |

### VP Gobierno

| ID | Épica | Fase | Depende de | Aceptación |
|---|---|---|---|---|
| GOB-1 | `policy/v1` con texto primario, matriz de autonomía y regla de riesgo | F2 | investigación 18 | cada regla con norma y fecha |
| GOB-2 | Retenido representativo y de estrés de texto, con huella en acta | F2 | GOB-1 | acta firmada antes de F3 |
| GOB-3 | Retenido de voz derivado y semilla humana de voz | F2 a F5 | GOB-2 e IA-6 | huella en acta |
| GOB-4 | Modelo de amenazas MAESTRO y casos adversariales de texto y voz | F2 | 06 | S1 a S10 y V9 a V10 mapeados a OWASP |
| GOB-5 | Pruebas de propiedades de los invariantes | F3 a F5 | TEC-4 | miles de secuencias sin violaciones |
| GOB-6 | Día de equipo rojo | F5 | TEC-5 y TEC-6 | hallazgos al conjunto de estrés |
| GOB-7 | Validación del componente, corrida final y reporte de equidad | F4 y F6 | IA-2 y GOB-2 | actas del Comité de Confianza |

### Auditoría

| ID | Épica | Fase | Aceptación |
|---|---|---|---|
| AUD-1 | Verificación de las fuentes restantes | antes de F7 | tabla de estado completa ([investigación 19](../docs/investigacion/19_Auditoria.md)) |
| AUD-2 | Matriz de trazabilidad con consulta por fila | F6 y F7 | ninguna exigencia sin evidencia |
| AUD-3 | Prueba en máquina limpia y dictamen | F7 | aprobado, con salvedades o devuelto |

## 4. Ruta crítica

```
DAT-1 ─► DAT-3 ─► DAT-4 ─► TEC-3 ─┐
TEC-1 ─► TEC-4 ─► TEC-2 ──────────┴─► TEC-5 (chat de punta a punta) ─► TEC-6 (voz) ─► GOB-6 y TEC-9 ─► GOB-7 ─► PRE-3
GOB-1 ─► GOB-2 (retenido congelado antes de construir)            IA-1 ─► IA-2 (componente aprendido)
                                   IA-5 (arnés) ────────────────────────────────────────► GOB-7
```

Lo que no depende del código (política, retenido, amenazas, semilla de mensajes) se adelanta: es lo
que más tiempo ahorra y lo que exige P1.

## 5. Calendario relativo

| Día | Fase | Se cierra | Compuerta |
|---|---|---|---|
| D0 | F0 | PRE-1, repositorio, subagentes, DAT-1, *spikes* S1 a S5 | instalación de un comando |
| D1 | F1 | DAT-2, borrador de GOB-1, TEC-1 | flujo con respaldo en el total |
| D2 | F2 | GOB-1, GOB-2, GOB-4, IA-1, IA-5 | **retenido congelado** (Comité de Confianza) |
| D3 | F3 | TEC-2, TEC-3, TEC-4, DAT-3, DAT-4 | |
| D4 | F3 | TEC-5 y chat de punta a punta en ES; IA-3; CLI-2 | N1 a N6 en chat |
| D5 | F3v | TEC-6 y voz de punta a punta en ES; CLI-3; CLI-4 (medio día de holgura) | los mismos casos por voz |
| D6 | F4 | portugués en chat y voz; IA-2; GOB-3 | componente aprendido validado |
| D7 | F5 | GOB-5, GOB-6, TEC-9, IA-6, TEC-7; IA-8 si hay tiempo | invariantes y equipo rojo |
| D8 | F6 | corridas de texto y voz, líneas base, puntos de operación | |
| D9 | F6 y F7 | reportes, equidad; inicio del ensamble (medio día de holgura) | criterios de salida evaluados |
| D10 | F7 | demo, reporte, AUD-1 a AUD-3, entrega | dictamen de Auditoría |

## 6. Orden de recorte

Si falta tiempo, se recorta en este orden, y cada recorte queda en el reporte como trabajo futuro:

1. Experimento de frontend nativo (IA-8).
2. Línea telefónica real (se queda la voz en el navegador).
3. Texto en streaming en el chat.
4. Voz en portugués (el portugués se mantiene en chat).
5. Semilla humana de voz (la brecha entre voz sintética y humana se reporta como no medida).
6. Día de equipo rojo reducido a los casos adversariales escritos.

**Nunca se recorta:** los invariantes de seguridad, la independencia del retenido, los tres casos de la
demo en español y portugués en al menos un canal, el capítulo de datos (contratos, calidad, linaje,
frescura, *fixture*), el componente aprendido con su línea base, las métricas separadas y la
honestidad del reporte.

## 7. Definición de terminado

| Tipo de entregable | Terminado cuando |
|---|---|
| Código | tipado (pyright estricto), con pruebas, con trazas y en `just test` |
| Componente con IA | con hoja de vida, línea base y evaluación de desarrollo reportada |
| Datos | con contrato validado y huella reproducible |
| Artefacto de Gobierno | con acta y firma del subagente |
| Documento | enlazado desde el README y sin contradicciones con las decisiones |
