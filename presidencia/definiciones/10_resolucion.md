# Resolución de la Presidencia (ronda 1)

**Cara:** Presidencia y Oficina de Entrega. **Fecha:** 27 de septiembre de 2026.
**Objeto:** paso 4 del ciclo ([modelo operativo](../modelo_operativo.md), sección 7):
resolver los hallazgos del [desafío de Gobierno](08_Desafio_Gobierno.md) y de la
[auditoría de definiciones](09_Auditoria_de_definiciones.md), los doce choques entre decisiones
propuestas y las ocho solicitudes dirigidas a la Presidencia (H-AUD-02). Las decisiones que salen de
aquí quedan en [Decisiones.md](../decisiones.md) como D-22 a D-28.

---

## 1. Los tres bloqueantes

| Hallazgo | Resolución |
|---|---|
| H-AUD-01 (80 solicitudes sin respuesta) | cada cara agrega en su segunda versión, dentro de la sección 5, la subsección "Respuesta a las solicitudes recibidas", con el estado de cada una en el formato 3.1. Gobierno ya respondió las suyas en 08 |
| H-AUD-02 (solicitudes a la Presidencia sin respuesta) | respondidas en la sección 3 de este documento |
| H-AUD-04 (tabla de costos contra D-20) | resuelta por el choque 1 y D-24: Tecnología rehace su sección 7.3 con la tabla única de familias |

## 2. Los doce choques: se adoptan las recomendaciones de Auditoría

| # | Choque | Resolución | Decisión |
|---|---|---|---|
| 1 | familias de modelos | tabla única: **sistema**, Google (Gemini en Vertex AI); **generador de desarrollo**, Anthropic (Claude en Vertex AI); **generador del retenido y simulador**, familia abierta A; **juez y verificador**, familia abierta B distinta de todas. Si en F0 no hay dos familias abiertas usables, Gobierno decide con acta qué par comparte familia y el reporte lo declara; nunca el juez con el generador ni con el sistema | D-24 |
| 2 | costo humano del traspaso | se adopta DP-CLI-12: cifras de Latinoamérica como centrales, la de EE. UU. solo como sensibilidad, registradas en acta antes del retenido | D-25 |
| 3 | WhatsApp en la proyección | se adopta DP-CLI-13: la proyección de producción suma los mensajes de WhatsApp con la marca [P] | D-25 |
| 4 | transporte de voz | WebRTC en local (vía reproducible); WebSocket a Cloud Run en la nube **solo si** S1 mide la latencia de voz a voz dentro del presupuesto por ese transporte; la latencia se reporta por transporte | D-22 |
| 5 | pruebas de persistencia | Postgres real en contenedor para las pruebas de persistencia; SQLite solo en unitarias sin SQL (enmienda de D-20) | D-23 |
| 6 | repeticiones en voz | k = 3 en V1, V2, V9 y los casos de seguridad; k = 2 en el resto del retenido de voz, declarado en el acta de F2 y en el reporte | D-26 |
| 7 | estado civil y educación | se adopta DP-GOB-19: fuera incluso de la auditoría de equidad salvo acta; género y banda de edad se conservan para auditar; la banda de edad se suma a los segmentos autorizados para auditar | D-27 |
| 8 | créditos de prueba de voz | ningún proveedor se usa antes de su ficha de términos (S-GOB-15) que muestre que no entrena ni revisa con nuestros datos; sin ficha, modelos locales | D-27 |
| 9 | techo de gasto | un solo techo (sección 3.1); el tope de Datos es un sub presupuesto | D-25 |
| 10 | reclamo fuera de plazo | se adopta DP-GOB-04: F5 termina siempre en R5, sin afirmar que el plazo venció (también H-GOB-01) | D-27 |
| 11 | resultados inseguros | M-07 se calcula por tipo U1 a U13 (lista cerrada de Gobierno) | D-27 |
| 12 | retención de trazas | una sola tabla con dos filas: registros operativos, 30 días; evidencia de evaluación en platino, cierre más 90 días | D-27 |

## 3. Respuesta a las solicitudes dirigidas a la Presidencia

### 3.1 Gasto (S-TEC-11, S-DAT-12, S-IA-10 en lo de presupuesto, S-AUD-14 en lo de gasto)

```
Estado: aceptadas con ajuste.
Respuesta:
  Techo único de US$600 para la hackatón, antes de créditos, con alertas al 50, 80 y 100%.
  Sub presupuestos: Datos (perfil de nube) US$50; Gobierno US$30; Auditoría US$60; el resto para
  modelos, voz y plataforma. IA arranca en su escenario austero (cerca de US$300) y sube solo con
  acta de la Oficina si la evaluación lo necesita. Lo indispensable queda en US$340 a 460.
  La tabla única de costos es de Tecnología, con los volúmenes de IA y de Gobierno (R-GOB-53:
  400 casos de texto, 128 de voz, 300 del componente, 20% de reserva sellada).
  Condición: abrir la cuenta de facturación y registrar un medio de pago es un gasto real y lo
  aprueba la presidencia humana (el usuario) antes de ejecutarlo. Hasta entonces todo corre en el
  perfil local y el spike S1 se hace en local (H-AUD-18).
```

### 3.2 Preguntas a los organizadores (S-DAT-01, S-GOB-24, S-IA-10)

```
Estado: aceptadas.
Respuesta: se suman a Diseno/Preguntas_organizadores.md:
  11. ¿Podemos copiar el dataset a un proyecto privado de Google Cloud del equipo (región de EE. UU.,
      sin acceso público, borrado al cierre)?
  12. ¿Qué retención y borrado exigen los términos al terminar el evento?
  Y se amplían la 3 (si pueden salir marcadores sin valores y texto escrito por el equipo hacia
  modelos externos), la 7 (corpus públicos de voz con acento y de ruido, como Common Voice y FLEURS)
  y la 10 (si las APIs de voz pueden recibir audio sintético y grabaciones de voluntarios).
  Mientras no respondan: el dataset no se copia a la nube (H-GOB-03; Gobierno no puede autorizar en
  nombre del dueño del dato) y hacia modelos externos solo salen marcadores sin valores (H-GOB-04).
```

### 3.3 Voluntarios y revisión de portugués (S-IA-10, S-CLI-14)

```
Estado: aceptada con ajuste.
Respuesta: la presidencia humana busca voluntarios con consentimiento (texto y voz, idealmente un
  hablante nativo de portugués). La compra opcional de una revisión nativa de portugués (hasta
  US$150) queda aprobada dentro del techo solo si al D2 no hay voluntario.
```

### 3.4 Decisiones propuestas de Clientes (S-CLI-14)

```
Estado: aceptada.
Respuesta: las DP-CLI de su dominio quedan aprobadas, salvo las objeciones de Gobierno en 08, que se
  ajustan en la segunda versión; DP-CLI-12 y DP-CLI-13 se resuelven en el choque 2 y 3.
```

### 3.5 Segunda opinión de Auditoría (S-AUD-14)

```
Estado: aceptada.
Respuesta: sí. La segunda opinión sobre hallazgos bloqueantes usa, por el gateway, una familia
  distinta de la que produjo lo revisado; por defecto Anthropic cuando se revisan salidas del
  sistema (Google). Gasto dentro del sub presupuesto de Auditoría.
```

### 3.6 Borrador del reporte (S-AUD-13)

```
Estado: aceptada.
Respuesta: el borrador completo del reporte, generado desde platino, llega a Auditoría 24 horas antes
  de la entrega (D9), junto con la bitácora.
```

## 4. Otros hallazgos que asume la Presidencia o la Oficina de Entrega

| Hallazgo | Resolución |
|---|---|
| H-AUD-19 ("AI-first" y trabajo restante sin dueña) | nuevas historias **PRE-3.4** (definición de "AI-first" para el reporte) y **PRE-3.5** (capítulo de trabajo restante para producción, con aportes de cada cara); dueña: Presidencia |
| H-AUD-16 (25 épicas fuera de la hoja de ruta) | se incorporan en el backlog organizado (siguiente paso del objetivo), con dueño, fase y dependencias |
| H-AUD-17 (arnés antes que sus insumos) | el arnés de D2 corre con LLM simulado (TEC-0.7) y casos de desarrollo del equipo; S-IA-08 y S-IA-09 se adelantan a D1 |
| H-AUD-18 (S1 atado a la nube) | S1 corre primero en local (navegador con WebRTC, proveedores por API); la medición en Cloud Run se agrega si se aprueba el gasto |
| H-AUD-21 (consolidado) | se corrige el generador |
| H-AUD-22 (texto superado en 01 y 02) | notas fechadas en ambos documentos |
| C-1 (0,9^8 = 0,43) | nota fechada en la investigación 4 |

## 5. Hallazgos mayores de Gobierno que se adoptan

| Hallazgo | Resolución |
|---|---|
| H-GOB-01 | F5 siempre en R5; la plantilla no afirma el vencimiento |
| H-GOB-02 | bloquear la tarjeta: nivel `consulta` más confirmación explícita, sin OTP; el OTP solo para radicar |
| H-GOB-03 | sin copia del dataset a la nube hasta que respondan los organizadores |
| H-GOB-04 | hacia modelos externos solo marcadores sin valores, nunca campos enmascarados |

## 6. Qué sigue

1. **Segunda versión** de las seis definiciones con todo lo anterior (paso 5).
2. **Pasada fría de Auditoría** sobre versiones con huella (paso 6). Si no quedan bloqueantes, las
   reglas del juego quedan dadas.
3. **Backlog organizado**, plataforma y compras, y arranque del desarrollo.
