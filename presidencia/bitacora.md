# Bitácora de la Oficina de Entrega

Una entrada por día: qué se cerró, qué bloquea, qué se recortó. La más reciente arriba.

---

## 4 de octubre de 2026

**Cerrado**
- Evaluación final (32 casos retenidos, k=3), reporte `presidencia/reporte/` 00 a 06 y guion de la demo.
- Portugués (você) de punta a punta, clasificador de motivo de contacto contra línea base, análisis del problema y equidad.
- Rediseño de banca, sitio y consola del experto.
- Correcciones tras la evaluación, desplegadas (prompt 1.5.0, trabajador 0.6.0): ESC-03 con producto desconocido,
  listado ampliado, falla dicha al cliente, prioridad solo por política, bloqueo de una sola tarjeta, negación compartida
  entre filtro y verificador, final de la tarjeta entregado por las herramientas.
- Producción verificada con la suite e2e (71 pruebas, ninguna omitida).

**Bloquea**
- Fecha de entrega sin confirmar; grabación de la demo; dictamen final de Auditoría; revisión del portugués por un nativo.

**Recortado**
- R27 queda abierto en 1/3; retención de datos, monitoreo y Terraform aplicado quedan como trabajo restante declarado.

---

## 29 de septiembre de 2026

**Cerrado**
- D-30: todo en Google Cloud, carga del dataset supuesta externa, capas como prefijo de tabla en `latam_bank`.
- Proyecto `latam-bank-hackaton-2026` en sandbox de BigQuery; dataset completo cargado (13 tablas, 23,5 M filas).
- Crítica en frío de datos (12 hallazgos) y correcciones: manifiesto encadenado, reglas robustas, limitaciones,
  plata y oro con dbt, seudonimización, contratos y fixture.
- Fusionadas a `develop` las diez ramas del arranque (gobierno, auditoría, tecnología, spikes S3 y S4,
  Terraform y datos).

- Tarde: policy/v1, Clientes (matriz, estilo, 50 plantillas), arnés de evaluación (23 de 23), D-31
  (bloquear tarjeta con acr1), escalamiento por monto ESC-04 y chat web de disputas.

- Noche: sitio en Firebase Hosting; facturación reabierta con presupuesto de COP 20.000; chat en Cloud Run;
  D-32: agente en Gemini Enterprise Agent Platform (Agent Runtime, Gemini 2.5 Flash-Lite, Cloud Trace,
  cuenta `latam-chat@` de mínimo privilegio), probado de punta a punta desde el sitio.

**Bloquea**
- Facturación cerrada (resuelto en la noche): sin Cloud Run ni Vertex AI hasta que la Presidencia decida reabrirla.

**Recortado**
- Cuatro fichas de oro operacional, cuarentena por fila y lotes en bronce.

## 28 de septiembre de 2026

**Cerrado**
- Repositorio privado con carpetas por cara, ramas `main` y `develop`, CI en verde y contratos del dominio.
- D-29: WhatsApp y teléfono reales en modo de prueba, todo en Google Cloud, pago real menor a US$20.
- Traspaso entre sesiones en `presidencia/ESTADO.md`.

**Bloquea**
- Pasos del usuario: prueba de Google Cloud y `gcloud auth`, Meta, Twilio, preguntas a organizadores.

## 27 de septiembre de 2026 (cierre)

**Cerrado**
- Definiciones de las seis caras (568 reglas), desafío de Gobierno, auditoría de definiciones,
  resolución de la Presidencia (D-22 a D-28) y acta de cierre de las reglas del juego.
- Backlog consolidado de 285 historias.

**Recortado**
- La segunda versión de las definiciones: se cortó tres veces por el límite de uso; se sustituyó por
  reglas de precedencia y correcciones como historias de primer día.

## 27 de septiembre de 2026

**Incidente**
- Los seis subagentes de definiciones se cortaron por el límite de uso de la sesión (reinicio a las
  00:40) antes de escribir sus archivos. No quedaron archivos parciales.

**En curso**
- Retomados en tandas para no volver a chocar con el límite: primero Datos, Tecnología y Gobierno;
  después IA, Clientes y Auditoría. Cada uno conserva lo que ya había leído.

## 26 de septiembre de 2026

**Cerrado**
- Investigaciones 1 a 21, incluida la auditoría del dataset y la ronda por cada cara.
- Diseño: principios, interacciones, plan, datos por capas, organización v2, cobertura del enunciado,
  arquitectura y hoja de ruta.
- Decisiones D-01 a D-21 firmes, salvo proveedores concretos y uso de modelos externos.
- Modelo operativo de LATAM Bank (roles, comunicación, resolución, plantilla de definiciones).
- Lanzada la primera versión de las definiciones de las seis caras, con subagentes en paralelo.

**Bloquea**
- Respuestas de los organizadores a las diez preguntas de la revisión 05 (fechas, equipo, modelos
  externos, repositorio público, términos de uso, preparación previa, APIs de voz).

**Recortado**
- Nada.
