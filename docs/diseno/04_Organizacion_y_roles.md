# Organización de LATAM Bank y roles del desarrollo (v2)

**Propósito:** definir las caras con las que se trabaja el reto, de modo que cada especialidad tenga
mandato, artefactos y compuertas, y que todo converja en una sola entrega. Se apoya en las
investigaciones [12](../Investigacion/12_Organizacion_de_un_banco.md) y
[21](../Investigacion/21_Organizacion_agentica.md).

**Historia de versiones**

| Versión | Fecha | Cambio |
|---|---|---|
| v0 | 26 sep 2026 | organigrama calcado de un banco tradicional (tres líneas de defensa, comités) |
| v1 | 26 sep 2026 | banco inventado con la estructura correcta; Seguridad dentro de la VP Gobierno; roles en modo mixto |
| v2 | 26 sep 2026 | **misión** como unidad de entrega; operación humana de fraude y disputas; voz en tres VP; ingeniería de evaluación y operación de agentes; equipo rojo; **Oficina de Entrega**; lista concreta de subagentes; decisiones cerradas (D-10) |

---

## 1. El punto de partida

Los bancos existentes están organizados por productos y funciones heredadas, y cambian despacio.
Diseñamos **LATAM Bank** como si naciera hoy, con dos restricciones que no se negocian:

1. **Independencia de quien desafía:** quien construye no se aprueba a sí mismo (regulación de MX, CO y
   AR; tres líneas de defensa; P1).
2. **Funciones obligatorias:** riesgo, cumplimiento, lavado de activos, protección al consumidor, datos
   personales, seguridad y auditoría existen y tienen dueño. Se pueden agrupar distinto, no desaparecer.

Todo lo demás responde a la pregunta: **¿qué tiene que hacer excepcionalmente bien un banco donde la IA
atiende primero, por chat y por voz?**

## 2. Principios de diseño de la organización

| # | Principio | Cómo se diferencia de un banco tradicional |
|---|---|---|
| O1 | **Por viajes del cliente, no por productos:** un problema del cliente tiene un solo dueño de punta a punta | el tradicional reparte la disputa entre tarjetas, canales, fraude y operaciones |
| O2 | **Los agentes de IA son fuerza laboral:** identidad, permisos mínimos, supervisor humano, métricas, hoja de vida y baja | el tradicional los trata como proyecto de TI |
| O3 | **El gobierno es código:** políticas, umbrales, permisos y reglas por país versionados y ejecutados | el tradicional escribe manuales y audita después |
| O4 | **La confianza es una sola voz:** riesgo, seguridad, cumplimiento, privacidad y protección al consumidor en una segunda línea con veto | el tradicional tiene cinco áreas que opinan tarde |
| O5 | **El dato es un producto con contrato** y hay un dueño de las cifras oficiales | el tradicional tiene cifras distintas por área |
| O6 | **Las personas suben de nivel:** de contestar a resolver excepciones, supervisar y enseñar a los agentes | el tradicional mide al humano por volumen |
| O7 | **Cada cara tiene artefacto, compuerta y veto**, o no existe | evita el cargo decorativo |
| O8 | **La unidad de entrega es la misión, no la VP:** un equipo pequeño orientado a un resultado, con personas por encima del circuito; las VP son capacidades que aportan a la misión | el tradicional entrega por silos funcionales |

## 3. Organigrama v2

```
                           Junta directiva (el jurado)
                            │                      │
             Presidencia ── Oficina de Entrega     Auditoría (reporta a la junta)
                            │
   ┌────────────────────────┼────────────────────────────────────────────┐
   │  MISIÓN "cargo no reconocido" (equipo agéntico, dueña: VP Clientes)  │
   │  sombreros de Clientes, IA, Datos y Tecnología                       │
   └────────────────────────┼────────────────────────────────────────────┘
     ┌──────────────┬───────┴──────┬──────────────┬──────────────┐        ┌──────────────┐
 VP Clientes   VP Inteligencia   VP Datos      VP Tecnología            VP Gobierno
 (viajes y     Artificial        (la verdad    (plataforma y            (confianza,
 servicio)     (fuerza laboral   del banco)    arquitectura)            segunda línea)
               digital)
 ├ Diseño      ├ Comprensión     ├ Plataforma  ├ Arquitectura            ├ Riesgo y riesgo
 │ conversa-   │ y redacción     │ y capas     ├ Plataforma del           │ de modelo
 │ cional de   ├ Voz (habla y    ├ Contratos   │ agente (motor,           ├ Seguridad y
 │ chat y voz  │ turnos)         │ y calidad   │ herramientas,            │ equipo rojo
 ├ Operaciones ├ Evaluación de   ├ Analítica y │ identidad)               ├ Cumplimiento
 │ de fraude   │ desarrollo y    │ métricas    ├ Canales (chat y          │ y privacidad
 │ y disputas  │ simulación      │ oficiales   │ tiempo real)             └ Protección al
 └ Calidad de  └ Operación de    └ Inventario  └ Observabilidad,            consumidor
   servicio      agentes           de insumos    SRE y costo
```

**Primera línea:** Clientes, IA, Datos y Tecnología. **Segunda línea:** Gobierno, fuera de la misión.
**Tercera línea:** Auditoría, fuera de la cadena de la presidencia.

## 4. La misión "cargo no reconocido"

- **Qué es:** el equipo agéntico que entrega el resultado de punta a punta (O8): recepción de disputas
  por cargos no reconocidos, por chat y por voz, en español y portugués.
- **Dueña del resultado:** VP Clientes. **Resultados:** el árbol de la
  [revisión 05](05_Cobertura_del_enunciado.md), sección 5 (contención rápida, caso bien radicado,
  explicar sin disputar, no repetir, plazos correctos, menos minutos humanos).
- **Composición:** un sombrero de cada VP de primera línea; Gobierno y Auditoría quedan **afuera** para
  conservar la independencia.
- **Backlog:** el de la [hoja de ruta](../../presidencia/hoja_de_ruta.md), ordenado por la Oficina de Entrega.
- **Roles humanos** (investigación 21): la Presidencia es el supervisor en forma de M, por encima del
  circuito; los especialistas de fraude son los expertos en forma de T, dentro del circuito en las
  excepciones; los agentes humanos son la primera línea aumentada que recibe el traspaso.

## 5. Las caras

### Presidencia y Oficina de Entrega
- **Mandato:** que exista una entrega coherente que cuente una sola historia.
- **Oficina de Entrega:** mantiene el backlog y el calendario de compuertas, corre la revisión diaria,
  aplica el **orden de recorte** cuando falta tiempo, integra el reporte y la demo.
- **Firma:** F7. Desempata comités, pero **no puede levantar un veto de Gobierno** sin acta.
- **La ejerce:** tú, con la sesión principal de Claude como oficina.

### VP Clientes (viajes y servicio)
- **Mandato:** que el cliente resuelva y que, cuando interviene un humano, reciba el caso listo.
- **Gerencias:**

| Gerencia | Dueña de |
|---|---|
| Diseño conversacional de chat y voz | guiones por estado del motor en ES y PT, componentes de chat, lectura de vuelta y confirmaciones de voz, rellenos honestos mientras corre una herramienta |
| Operaciones de fraude y disputas | la cola humana destino del traspaso: por idioma, turno y especialidad (solo 7 especialistas de fraude hablan portugués); vista del experto; sus correcciones como etiquetas |
| Calidad de servicio | métricas de experiencia, traspaso y preguntas repetidas; guion de la demo |

- **Firma:** escenarios en F2; demo en F7.

### VP Inteligencia Artificial (fuerza laboral digital)
- **Mandato:** construir y operar agentes y modelos como trabajadores con rol, permisos, supervisor,
  métricas y hoja de vida.
- **Gerencias:**

| Gerencia | Dueña de |
|---|---|
| Comprensión y redacción | el componente aprendido (D-14), prompts versionados, redacción desde hechos verificados |
| Voz | selección y medición de reconocimiento y síntesis por acento, detección de turnos, frontend nativo experimental (D-18) |
| Evaluación de desarrollo y simulación | el **arnés** de evaluación y los simuladores de usuario de texto y voz (el contenido del retenido es de Gobierno) |
| Operación de agentes | registro de agentes, monitoreo, deriva, incidentes de modelo |

- **Firma:** F4.

### VP Datos (la verdad del banco)
- **Mandato:** una sola verdad certificada y el origen de toda cifra oficial.
- **Gerencias:** plataforma y capas; contratos y calidad; analítica y métricas oficiales; **inventario y
  procedencia de insumos** (real, sintético, del equipo, externo; incluidos los audios de evaluación).
- **Firma:** F1; certifica cada tabla de oro que consume un agente.

### VP Tecnología (plataforma y arquitectura)
- **Mandato:** que el sistema sea correcto por construcción, observable, reproducible y barato.
- **Gerencias:**

| Gerencia | Dueña de |
|---|---|
| Arquitectura | ADR y la [arquitectura](06_Arquitectura.md) |
| Plataforma del agente | motor de flujo, capa de herramientas tipada, servicios simulados BIAN, identidad, base operativa |
| Canales | chat con AG-UI y componentes; voz en tiempo real (WebRTC y, si hay tiempo, telefonía) |
| Observabilidad, SRE y costo | trazas, latencia por etapa, prueba de capacidad, costo por caso con voz incluida |

- **Hace cumplir** lo que Gobierno define. **Firma:** F0 y F3.

### VP Gobierno (confianza)
- **Mandato:** que nada llegue al cliente sin validación independiente, dentro del apetito de riesgo,
  seguro, conforme a la norma de cada país y justo con todos.

| Gerencia | Dueña de | Veto |
|---|---|---|
| Riesgo y riesgo de modelo | contenido del retenido (texto y voz) y su huella, corrida final, validación del componente aprendido, umbrales | versión candidata |
| Seguridad y equipo rojo | modelo de amenazas, casos adversariales de texto y voz, día de equipo rojo, invariantes, secretos | cualquier invariante roto |
| Cumplimiento y privacidad | `policy/v1` con texto primario (D-13), retención (incluido el audio), minimización, D-15 | política sin norma que la respalde |
| Protección al consumidor | derecho a un humano, explicaciones, reporte de equidad por idioma, variante, acento y segmento | disparidad no investigada |

- **Firma:** F2, F5 y F6. Única cara con veto sobre la salida.

### Auditoría
- **Mandato:** que lo que se afirma sea verdad y se pueda reproducir.
- **Dueña de:** matriz de trazabilidad, prueba en máquina limpia, verificación de fuentes y de que cada
  cifra salga de platino, consentimiento de las grabaciones de voz.
- **Firma:** F7; puede **devolver** la entrega.

**Fuera de la estructura:** Finanzas (el costo lo calcula Tecnología), Jurídica (en Cumplimiento),
Marketing, Talento. Riesgo de crédito aparecería en Gobierno solo con un flujo de crédito.

## 6. Contrapesos

| Quiere | Lo frena | Por qué |
|---|---|---|
| Clientes: más automatización | Gobierno | autonomía contra seguridad |
| IA: modelos más capaces | Datos (lo que come) y Gobierno (lo que sale) | complejidad contra línea base (P9) |
| IA y Clientes: moverse rápido | Tecnología | velocidad contra estabilidad |
| IA: escalar menos | Operaciones de fraude y disputas | la capacidad humana es finita (portugués, noche): escalar mal satura la cola |
| Oficina de Entrega: cumplir fechas | Gobierno | alcance contra calidad; se recorta alcance, nunca un principio |
| Todos: afirmar resultados | Auditoría | relato contra evidencia |

## 7. Quién responde por cada criterio del enunciado

D = dueño, R = revisa y desafía, C = certifica.

| Criterio | Clientes | IA | Datos | Tecnología | Gobierno | Auditoría |
|---|---|---|---|---|---|---|
| 1. Problema respaldado por datos | D (resultados, restricciones operativas) | | D (evidencia) | | R | C |
| 2. Sistema de IA que funciona | D (conversación de chat y voz) | D | | D (herramientas, canales) | R | C |
| 3. Automatización controlada | D (qué se ofrece) | | | D (hace cumplir) | **D (define la política)** | C |
| 4. Datos y ML rigurosos | | D (componente aprendido) | D (preparación, inventario) | | R (validación) | C |
| 5. Calidad medida y fallas | | D (arnés, desarrollo) | | | **D (retenido y corrida)** | C |
| 6. Ruta a operación | R | D (operación de agentes) | D (frescura) | D (capacidad, trazas) | R | C |

## 8. Quién hace qué en cada fase

| Fase | Lidera | Participan | Firma |
|---|---|---|---|
| F0 Preparación | Tecnología | Oficina de Entrega (preguntas a organizadores), Datos, Gobierno (secretos) | Tecnología |
| F1 Evidencia | Datos | Clientes (restricciones operativas), Gobierno (auditoría de señal) | Datos |
| F2 Especificación | Gobierno (política, retenido de texto y voz), Clientes (escenarios) | IA (arnés), Datos | **Comité de Confianza** |
| F3 Núcleo y chat | Tecnología | IA, Clientes | Tecnología |
| F3v Voz | Tecnología (canales) e IA (voz) | Clientes (diseño de voz) | Tecnología |
| F4 Componente aprendido | IA | Datos, Gobierno (validación) | Gobierno |
| F5 Endurecimiento | Gobierno (seguridad y equipo rojo) | Tecnología (capacidad), IA, Clientes (portugués) | Gobierno |
| F6 Evaluación | Gobierno | nadie de primera línea toca el retenido | Comité de Confianza |
| F7 Entrega | Presidencia y Oficina de Entrega | Clientes (demo) | Auditoría |

## 9. Comités, actas y cadencia

- **Comité de Plataforma** (Tecnología preside; IA, Datos): ADR, contratos de datos, interfaces de
  herramientas y de canales.
- **Comité de Confianza** (Gobierno preside; Clientes, IA y Datos como invitados sin voto): congela el
  retenido, aprueba política y umbrales, valida el componente aprendido, autoriza la versión candidata.
- **Revisión diaria** de la Oficina de Entrega (quince minutos): qué se cerró, qué bloquea, qué se
  recorta. No decide diseño; decide orden.

Cada sesión de comité deja un acta en `Diseno/Actas/` con lo que se pidió aprobar, **los desafíos de
cada cara**, la respuesta, la decisión y la firma; el acta alimenta [Decisiones.md](../../presidencia/decisiones.md).

## 10. Cómo se ejercen las caras (modo mixto)

- **Tú** ejerces la Presidencia y, con la sesión principal de Claude como Oficina de Entrega, construyes
  la primera línea.
- **Gobierno** y **Auditoría** son subagentes de Claude Code en `.claude/agents/` del repositorio,
  invocados **en frío**: no ven la conversación de construcción, reciben artefactos y devuelven un
  documento con formato fijo (hallazgos, severidad, veto o visto bueno) que se vuelve acta.

| Subagente | Cara | Se invoca en | Escribe en | Solo lee |
|---|---|---|---|---|
| `gobierno-riesgo-modelo` | Riesgo y riesgo de modelo | F2 (escribe el retenido de texto y voz), F4 (valida), F6 (corre) | `eval/cases/holdout/`, `eval/reports/`, `Diseno/Actas/` | código, oro, trazas |
| `gobierno-seguridad` | Seguridad y equipo rojo | F2 (casos adversariales), F5 (día de equipo rojo), cambios en herramientas | `eval/cases/adversarial/`, `tests/properties/`, `Diseno/Actas/` | código |
| `gobierno-cumplimiento` | Cumplimiento, privacidad y Protección al consumidor | F2 (`policy/v1`), F6 (equidad) | `policy/`, `eval/reports/equidad/`, `Diseno/Actas/` | código, reportes |
| `auditoria` | Auditoría | F7 y verificaciones puntuales | `Diseno/Actas/` | todo |
| `voz-del-cliente` (consultivo, sin firma) | Clientes | revisión de guiones de chat y voz | comentarios | guiones |

- La primera línea **no lee** `eval/cases/holdout/`.
- **Límite honesto:** con una sola persona en la presidencia y la primera línea, la independencia es
  **emulada**. Se defiende con tres hechos verificables: el retenido lo escribe el subagente de Riesgo y
  su huella queda en el acta antes de construir; los revisores arrancan sin el contexto de construcción;
  cada acta queda en el repositorio con fecha. Se declara así en el reporte.

## 11. El mismo organigrama en producción

| Evento | Decide | Ejecuta |
|---|---|---|
| Alta de un agente o de una versión | Comité de Confianza | IA |
| Cambio de prompt, modelo, reconocimiento o síntesis de voz | Gobierno, según materialidad; revalidación por acento si es voz | IA |
| Cambio de umbral o de regla por país | Gobierno (política como código) | Tecnología despliega |
| Incidente de seguridad (inyección, voz sintética) | Gobierno (Seguridad) | Tecnología degrada o apaga; Clientes comunica |
| Deriva de intenciones, calidad o error de reconocimiento | IA detecta; Gobierno decide revalidar | IA |
| Saturación de la cola humana (portugués, noche) | Clientes (Operaciones) | Tecnología ajusta capacidad; Gobierno revisa umbrales |
| Queja de un cliente sobre el agente | Gobierno (Protección al consumidor) | Clientes |
| Métricas oficiales del mes | Datos | Datos |

## 12. Investigación de cada cara

| Ronda | Investigaciones | Estado |
|---|---|---|
| Una por cara | [14](../Investigacion/14_VP_Clientes.md) a [19](../Investigacion/19_Auditoria.md) | hecha |
| Canales y organización | [20](../Investigacion/20_Canales_voz_y_chat.md) y [21](../Investigacion/21_Organizacion_agentica.md) | hecha |

## 13. Decisiones de organización (cerradas en D-10)

| # | Pregunta | Decisión |
|---|---|---|
| A | ¿Datos e IA separadas? | **sí**: Datos certifica lo que IA consume |
| B | ¿Seguridad? | dentro de Gobierno, con equipo rojo explícito |
| C | ¿Dueño de la evaluación final? | Gobierno (Riesgo de modelo); el arnés es de IA, el contenido y la corrida de Gobierno |
| D | ¿Modo de trabajo? | mixto, con los subagentes de la sección 10 |
| E | ¿Gobierno concentra demasiado? | revisiones cortas con formato fijo; si una revisión bloquea más de un día, Seguridad se separa como VP |
| F | ¿Nombres? | los de esta versión |
| G | ¿Hay compañeros humanos? | pendiente (pregunta 2 a los organizadores); si llegan, toman caras de primera línea o de Gobierno, nunca las dos |
