# Auditoría de completitud y consistencia de las definiciones (ronda 1)

**Informe:** INF-AUD-DEF-1. **Cara:** Auditoría. **Fecha:** 27 de septiembre de 2026.
**Objeto:** las definiciones `01` a `06` y el consolidado `07`, en el paso 3 del modelo operativo
([00](../modelo_operativo.md), sección 7). **Protocolo:** sección 2.9 de
[06](../../auditoria/definicion.md). **No duplica** el desafío de Gobierno (`08_Desafio_Gobierno.md`), que revisa el
riesgo de la primera línea; aquí se revisa completitud contra el enunciado, contradicciones entre caras y
contra decisiones firmes, solicitudes sin respuesta, choques entre decisiones propuestas, costos y
backlog.

**Método y alcance, declarados:** se usó `07_Consolidado.md`, búsquedas puntuales y la lectura completa
de las secciones 7, 8 y 10 de cada definición (la sección 5 se revisó por búsqueda de identificadores de
solicitudes, no leyendo cada texto). Sin búsquedas web. Las versiones auditadas son las del 27 de
septiembre en el Drive; su huella no se registró en esta ronda (desviación de R-AUD-50, que se corrige
en la ronda 2). La definición de Auditoría (06) no se autoaudita (R-AUD-07): sus hallazgos propios se
listan, pero la revisión corresponde a Gobierno.

---

## 1. Resumen

| Tema | Resultado |
|---|---|
| Cobertura del enunciado | las 98 filas de la matriz ([06](../../auditoria/definicion.md), sección 6.3) tienen dueña; ninguna exigencia queda sin cara. Tres filas tienen dueña en la matriz pero **ninguna definición las toma** (E-01 "AI-first", E-13 y E-45 trabajo restante), porque su dueña es la Presidencia, que no tiene backlog propio más allá de PRE-1 a PRE-3 |
| Solicitudes | 90 solicitudes distintas; **80 no tienen respuesta escrita** en la definición que las recibe; 8 van a la Presidencia, que no tiene dónde responderlas |
| Decisiones firmes | un supuesto de costos de Tecnología contradice D-20 (familias de modelos); dos propuestas de Tecnología modifican D-18 y D-20 por la vía correcta (propuesta), pero requieren entrada nueva en el registro |
| Choques entre propuestas | 12 choques, con recomendación en la sección 3 |
| Costos | no hay una cifra única: el techo de US$600 (DP-TEC-12) convive con un tope de US$50 en nube (DP-DAT-13) y con dos estimaciones de modelos y voz que se solapan y usan volúmenes distintos; lo indispensable suma entre US$440 y 660 sin doble conteo |
| Backlog | 25 épicas nuevas fuera de la hoja de ruta; dependencias con fecha posterior a la historia que las usa en la ruta crítica de F2; el *spike* de voz atado a la aprobación del gasto en nube |
| Citas | cuatro problemas de las investigaciones (sección 4) y unas 28 referencias de 2026 aún sin verificar |
| **Veredicto** | **tres hallazgos bloqueantes abiertos** (H-AUD-01, H-AUD-02 y H-AUD-04): las reglas del juego **no** se pueden dar por cerradas todavía |

---

## 2. Hallazgos

Severidad según [06](../../auditoria/definicion.md), sección 2.9: **bloqueante** solo por las tres causas del modelo
operativo, sección 7 (exigencia sin dueño, contradicción con un principio o una decisión firme, interfaz
sin quien la entregue); **mayor**; **menor**.

| Id | Dónde | Hallazgo | Severidad | Cambio exigido | Cara dueña |
|---|---|---|---|---|---|
| **H-AUD-01** | sección 5 de 01 a 05 | De 90 solicitudes, **80 no tienen respuesta escrita** en la definición que las recibe (aceptada, rechazada con motivo o con otra fecha). Solo Auditoría respondió las suyas (S-TEC-12, S-DAT-11, S-GOB-25). Es una interfaz sin quien la entregue (R-AUD-52): por ejemplo, S-GOB-01 a S-GOB-10 a Tecnología, S-TEC-01 a S-TEC-03 a Gobierno, S-IA-08 y S-IA-09 que alimentan el arnés de D2 | **bloqueante** | cada cara agrega a su sección 5 una subsección "Respuesta a las solicitudes recibidas" con el estado de cada una, en el formato 3.1 | Clientes, IA, Datos, Tecnología, Gobierno (cada una las suyas) |
| **H-AUD-02** | [00](../modelo_operativo.md); 07, matriz de solicitudes | Ocho solicitudes van a la Presidencia (S-CLI-14, S-IA-10, S-DAT-01, S-DAT-12, S-TEC-11, S-GOB-24, S-AUD-13, S-AUD-14) y la Presidencia no tiene artefacto donde responderlas. Incluyen el gasto y las preguntas a los organizadores, de las que dependen D-15, TEC-0.6 y el *spike* S1 | **bloqueante** | la Presidencia responde en una entrada de [Decisiones](../decisiones.md) (una por tema: gasto, preguntas a organizadores, revisión de portugués, segunda opinión) y envía una sola lista consolidada de preguntas a los organizadores | Presidencia |
| **H-AUD-03** | 01 a 06, sección 7; DP-TEC-12; DP-DAT-13 | **Costos sin cifra única.** Tecnología propone un techo de US$600 total; Datos pide a la misma Presidencia un tope de US$50 "en Google Cloud para la hackatón", cuando lo indispensable de Tecnología en Google Cloud ya es US$340 a 550. IA estima US$400 a 510 para modelos y voz, que se solapa con la tabla 7.3 de Tecnología (US$230 a 400 en modelos más voz) con otros volúmenes. Detalle en la sección 5 | mayor | una sola tabla de costos de la hackatón, dueña Tecnología (costo técnico), con los volúmenes de IA y de Gobierno; el tope de Datos como sub presupuesto dentro del techo; decisión de la Presidencia | Tecnología (tabla); Presidencia (decisión) |
| **H-AUD-04** | 04, sección 7.3 | El presupuesto de modelos asigna el **generador** a Gemini 3.1 Pro y el juez a "Gemini o equivalente", la misma familia que el sistema (Gemini). Contradice **D-20 (firme)**: familias distintas para generador, sistema y juez. Si se compra así, se implementa así | **bloqueante** | rehacer 7.3 con la asignación de familias de la sección 3, choque 1 | Tecnología |
| H-AUD-05 | 02, DP-IA-01 y riesgos; 05, R-GOB-54 y línea 859; S-IA-02 | La asignación de familias no cierra entre IA y Gobierno: IA fija cuatro (Google sistema, Anthropic generador de desarrollo, abierta para simulador, abierta para juez) y como respaldo usa Claude Haiku de simulador (misma familia que su generador); Gobierno exige que el generador del retenido sea de otra familia que el sistema **y** que el generador de desarrollo, y el juez distinto de ambos | mayor | tabla única de familias por trabajador (sección 3, choque 1), aprobada en el acta de F2 | IA, con Gobierno |
| H-AUD-06 | 04, DP-TEC-05 | Modifica **D-18** ("transporte: navegador con WebRTC") en la nube: WebSocket a Cloud Run. Va por la vía correcta (propuesta), pero no puede aplicarse sin una entrada nueva en el registro, y cambia cómo se mide la latencia de voz a voz | mayor | registrar D-22 si se acepta; la latencia de voz se reporta por transporte | Tecnología (Comité de Plataforma) |
| H-AUD-07 | 04, DP-TEC-06 | Modifica **D-20** ("SQLite en pruebas"): pruebas de persistencia contra Postgres real. Endurece la decisión; igual requiere entrada nueva | menor | enmienda de D-20 en el registro | Tecnología |
| H-AUD-08 | 02, DP-IA-10; 05, R-GOB-58 | IA propone k = 2 en el retenido de voz por costo; Gobierno fija k = 3 para todo el retenido | mayor | decide Gobierno en el acta de F2 (recomendación en la sección 3, choque 6) | Gobierno |
| H-AUD-09 | 01, DP-CLI-12; 04, sección 7.4 | Tecnología usa US$7 a 14 por contacto (cifra de industria de EE. UU.) como costo del traspaso en la proyección; Clientes propone cifras de Latinoamérica como centrales y la de EE. UU. solo como sensibilidad | mayor | adoptar DP-CLI-12; Tecnología ajusta 7.4 | Presidencia, con Tecnología |
| H-AUD-10 | 01, DP-CLI-13; 04, sección 7.4 | Tecnología proyecta producción "sin costo de mensajes de WhatsApp"; desde el 1 de octubre de 2026 hay cobro por mensaje (cifras [P] de Clientes) | mayor | Tecnología suma la línea de WhatsApp a 7.4, marcada [P] | Tecnología |
| H-AUD-11 | 05, DP-GOB-19; 03, R-DAT-60 y sección 4 | Gobierno propone que estado civil y educación **no se usen ni para auditar**; Datos los guarda en `plata_restringida` para auditar equidad | mayor | adoptar DP-GOB-19 (minimización, P11); Datos deja fuera esos dos atributos salvo acta | Gobierno decide; Datos cambia |
| H-AUD-12 | 05, DP-GOB-16; 02, secciones 7.1 y 7.3 | Gobierno prohíbe niveles gratuitos de proveedores que entrenen o revisen con nuestros datos; IA cuenta con créditos de prueba de terceros de voz (unos US$55) sin verificar sus términos | mayor | ningún proveedor de prueba se usa antes de su ficha de términos (S-GOB-15); si no se puede, modelos locales | IA |
| H-AUD-13 | 04, R-TEC-117; 05, tabla de retención | Retención de trazas: 30 días (Tecnología) frente a "cierre más 90 días" para la evidencia de evaluación (Gobierno) | mayor | una sola tabla que distinga registros operativos de evidencia de evaluación (S-AUD-15) | Gobierno, con Tecnología |
| H-AUD-14 | 03, M-07; 05, DP-GOB-11 | La métrica oficial de resultados inseguros (M-07) cuenta cuatro tipos (divulgación, acción no autorizada, afirmación falsa de monto, plazo, estado o transacción); Gobierno fija la lista cerrada U1 a U13, que incluye traspaso urgente faltante (U10) y derecho negado (U11) | mayor | M-07 se calcula por tipo U1 a U13 | Datos |
| H-AUD-15 | 04, sección 7.3; 05, R-GOB-53 | Tecnología dimensiona el retenido de texto en 500 casos; Gobierno fija 400 de texto, 128 de voz, 300 del componente y 20% de reserva sellada | mayor | Tecnología usa los tamaños de R-GOB-53 en costos y capacidad | Tecnología |
| H-AUD-16 | 01 a 06, sección 8; [07 de diseño](../hoja_de_ruta.md) | 25 épicas nuevas no están en la hoja de ruta ni en la ruta crítica: CLI-6; IA-9 a IA-11; DAT-7; TEC-0 y TEC-11 a TEC-17; GOB-8 a GOB-12; AUD-4 a AUD-8 | mayor | la Oficina de Entrega las incorpora a la hoja de ruta con dueño, fase y dependencias | Oficina de Entrega |
| H-AUD-17 | 02, IA-5.1 e IA-1.2 | El arnés (IA-5.1, D2) depende de S-IA-08 (gateway, fecha D3) y S-IA-09 (materializador de casos, fecha D3); el catálogo de guiones (IA-1.2, D2) depende de S-IA-09 (D3). La historia vence antes que su insumo, en la ruta crítica de F2 | mayor | adelantar S-IA-08 y S-IA-09 a D1, o correr el arnés de D2 con LLM simulado (TEC-0.7) y casos de desarrollo del equipo | IA, con Tecnología y Datos |
| H-AUD-18 | 04, TEC-0.5 y TEC-0.6 | El *spike* S1 de voz (D0) depende del arranque de Google Cloud, que depende de la aprobación del gasto (S-TEC-11). La decisión de proveedores de voz (D-18) queda atada a la nube, contra P13 (lo local es la vía reproducible) | mayor | S1 corre primero en local (navegador con WebRTC, proveedores por API) y la medición en Cloud Run se agrega si se aprueba el gasto | Tecnología |
| H-AUD-19 | matriz de [06](../../auditoria/definicion.md), filas E-01, E-13 y E-45 | "AI-first" no aparece en ninguna definición; "trabajo restante para producción" solo en Tecnología y Gobierno, sin dueña del capítulo. La dueña en la matriz es la Presidencia, que no tiene historia para ello | mayor (pasa a bloqueante si la segunda versión no lo asigna) | historia PRE-3.x: definición de "AI-first" y capítulo de trabajo restante, con aportes de cada cara | Presidencia |
| H-AUD-20 | [01 de diseño](../../docs/diseno/01_Interacciones_y_criterios.md), escenario F5; 05, DP-GOB-04 | 01 admite R6 o R5 para el reclamo fuera de plazo; Gobierno propone siempre R5 | menor | si se aprueba DP-GOB-04, se actualiza 01 y la ruta esperada de los casos F5 antes de congelar | Gobierno |
| H-AUD-21 | 07_Consolidado | El consolidado dice 70 decisiones propuestas: omite las doce `DP-AUD` (van en tabla con el id en negrita) y repite S-TEC-12, S-DAT-11 y S-GOB-25 (las respuestas de Auditoría) como si fueran solicitudes nuevas | menor | ajustar el generador del consolidado | Oficina de Entrega |
| H-AUD-22 | [01 de diseño](../../docs/diseno/01_Interacciones_y_criterios.md), sección 8; [02 de diseño](../../docs/diseno/02_Plan.md), F5 | documentos de diseño con texto superado: la matriz de 01 nombra el puntaje de riesgo como componente (contra D-14); 02, F5 dice S1 a S9 y Apigee con Model Armor (contra D-20) | menor | nota fechada que remita a la matriz de 06 y a D-14 y D-20 | Oficina de Entrega |
| H-AUD-23 | investigaciones 1, 4, 11 y 20 | cuatro problemas de citas (sección 4) | mayor (dos) y menor (dos) | los de la sección 4 | Auditoría (AUD-1), con la Oficina |
| H-AUD-24 | investigaciones 1 a 20 | unas 28 referencias de arXiv de 2026 siguen pendientes; algunas sostienen decisiones firmes (D-14, D-16, D-18) | mayor | AUD-1.2 y AUD-1.4 antes de F7 (R-AUD-33) | Auditoría |
| H-AUD-25 | 06 (esta cara) | Auditoría no registró la huella de las versiones auditadas (R-AUD-50) y no había respondido S-CLI-13 | menor | huellas en la ronda 2; respuesta a S-CLI-13 en la sección 6 de este informe | Auditoría |

---

## 3. Choques entre decisiones propuestas y recomendación

| # | Choque | Recomendación de Auditoría | Decide |
|---|---|---|---|
| 1 | DP-IA-01 (cuatro familias) contra 04, sección 7.3 (generador y juez Gemini) y contra R-GOB-54 y S-IA-02 (generador del retenido distinto del sistema y del generador de desarrollo) | Adoptar DP-IA-01 y cerrarlo con una tabla única: **sistema**, Google; **generador de desarrollo**, Anthropic; **generador del retenido y simulador**, familia abierta A; **juez y verificador**, familia abierta B, distinta de todas las anteriores. Si en F0 no hay dos familias abiertas usables, Gobierno elige con acta qué par comparte familia y el reporte lo declara; nunca el juez con el generador ni con el sistema. Tecnología rehace 7.3 con esta tabla (cierra H-AUD-04 y H-AUD-05) | Gobierno (Riesgo de modelo), con IA; D-20 se precisa |
| 2 | DP-CLI-12 contra 04, 7.4 (US$7 a 14 por contacto de EE. UU.) | Adoptar DP-CLI-12: cifras de Latinoamérica como centrales, registradas en acta antes del retenido; la de EE. UU. solo como sensibilidad. Es coherente con la propia R-TEC-123 (precios vigentes, supuestos declarados) y evita inflar el ahorro proyectado (P3) | Presidencia, con Tecnología |
| 3 | DP-CLI-13 contra 04, 7.4 ("sin costo de mensajes") | Adoptar DP-CLI-13: la proyección suma WhatsApp con la marca [P] hasta confirmar la tarifa después del 1 de octubre | Tecnología (Comité de Plataforma) |
| 4 | DP-TEC-05 contra D-18 (transporte WebRTC) | Aceptar como D-22 **condicionada**: local sigue con WebRTC (vía reproducible); en la nube, WebSocket solo si S1 mide la latencia de voz a voz dentro del presupuesto por ese transporte; la latencia se reporta por transporte | Tecnología (Comité de Plataforma), con IA (Voz) |
| 5 | DP-TEC-06 contra D-20 (SQLite en pruebas) | Aceptar como enmienda de D-20: endurece la prueba y no cambia la arquitectura | Tecnología |
| 6 | DP-IA-10 (k = 2 en voz) contra R-GOB-58 (k = 3) | k = 3 en los casos de voz que definen el criterio de salida (V1, V2, V9) y en los de seguridad; k = 2 en el resto, declarado en el acta de F2 y en el reporte, con pass^k informado con su k. El ahorro de IA (unos US$35) no justifica bajar la consistencia justo donde está el riesgo | Gobierno |
| 7 | DP-GOB-19 contra R-DAT-60 | Adoptar DP-GOB-19: estado civil y educación fuera incluso de la auditoría de equidad salvo acta; género y banda de edad se conservan para auditar (P11 y P12) | Gobierno decide; Datos ajusta |
| 8 | DP-GOB-16 contra el uso de créditos de prueba de voz en 02 | Compatibles si cada proveedor tiene ficha de términos antes de usarse (S-GOB-15) que muestre que no entrena ni revisa con los datos; sin ficha, modelos locales | Gobierno |
| 9 | DP-TEC-12 (techo de US$600 total) contra DP-DAT-13 y S-DAT-12 (tope de US$50 en nube) | Un solo techo de US$600 para la hackatón, con el tope de Datos como sub presupuesto de su perfil de nube; el techo se reparte en la tabla única de costos (H-AUD-03) | Presidencia |
| 10 | DP-GOB-04 (F5 siempre R5) contra 01, escenario F5 (R6 o R5) | Adoptar DP-GOB-04 antes de congelar el retenido: fechas inciertas y excepciones legales favorecen la revisión humana (P6, P7) | Gobierno |
| 11 | DP-GOB-11 (U1 a U13) contra M-07 de Datos | M-07 por tipo U1 a U13; la lista cerrada es de Gobierno y la métrica la implementa Datos | Datos, con Gobierno |
| 12 | R-TEC-117 (30 días) contra la retención de evidencia de Gobierno (cierre más 90 días) | Dos filas en una sola tabla: registros operativos, 30 días; evidencia de evaluación en platino, cierre más 90 días | Gobierno, con Tecnología |

---

## 4. Problemas de citas encontrados sin red

| # | Dónde | Problema | Severidad | Cambio exigido |
|---|---|---|---|---|
| C-1 | [Investigación 4](../../docs/investigacion/04_Evaluacion.md), sección 1 | "Un agente con 90% de éxito baja a 57% de consistencia en k = 8", junto a pass^k ≈ p^k: 0,9 elevado a 8 da **0,43**, no 0,57 (0,57 corresponde a k cercano a 5). Con tareas de dificultad desigual pass^k puede superar a p^k, pero entonces la cifra necesita fuente | menor mientras no llegue al reporte | nota fechada: corregir a 0,43 o citar el resultado empírico |
| C-2 | [Investigación 20](../../docs/investigacion/20_Canales_voz_y_chat.md) | τ-voice, arXiv 2603.13686 (identificador de marzo de 2026), se cita para un resultado de **abril** de 2026 (grok-voice-think-fast-1.0) y para "la voz conserva cerca del 79% de la capacidad de texto", que sostiene D-18 (firme). Inconsistencia temporal: la cifra viene probablemente del blog de Sierra o de una versión posterior | mayor | atribuir la cifra a su fuente real y verificar el pasaje antes de F7 |
| C-3 | [Investigación 11](../../docs/investigacion/11_Latencia_y_costo.md) | "RouteLLM: 85% menos costo con 95% de la calidad" se cita por una encuesta de 2026 (arXiv 2603.04445): cita secundaria. Fuente primaria probable: RouteLLM, arXiv 2406.18665 (no reconsultada) | menor | citar la fuente primaria |
| C-4 | [Investigación 1](../../docs/investigacion/01_Industria_y_casos.md) | Nubank, *Screen Before You Serve*, arXiv 2609.30137: número de secuencia alto para un artículo citado el 26 de septiembre de 2026; sostiene el uso del usuario simulado (D-16, IA-5). Hay que confirmar que existe | mayor hasta verificar | verificación de existencia y pasaje con prioridad (AUD-1.2) |

---

## 5. Costos: por qué no hay cifra única

Cifras tomadas de la sección 7 de cada definición (estimaciones de cada cara, no verificadas por
Auditoría).

| Cara | Indispensable | Opcional | Observación |
|---|---|---|---|
| Tecnología | US$340 a 550 (incluye modelos US$230 a 400, reconocimiento US$64, síntesis US$23 a 60 y plataforma cerca de US$25) | hasta cerca de US$150 más (total hasta US$700) | volúmenes: retenido de 500 casos (difiere de R-GOB-53) |
| IA | US$400 a 510 (escenario austero US$300) | | cubre modelos y voz con otros volúmenes; **se solapa** con la de Tecnología |
| Datos | US$0 a 10 (peor caso US$35; tope pedido US$50) | | perfil de nube de datos |
| Gobierno | US$15 a 30 | | incluye Security Command Center Premium opcional, unos US$9 |
| Clientes | US$0 | hasta US$150 (revisión nativa de portugués) | |
| Auditoría | US$0 a 60 | | tokens de segunda opinión y reejecución |

**Suma sin doble conteo** (la estimación de IA reemplaza modelos y voz de Tecnología): plataforma cerca de
US$25, más IA US$400 a 510, más Datos US$0 a 35, más Gobierno US$15 a 30, más Auditoría US$0 a 60: **US$440
a 660 en lo indispensable**, es decir, en el borde del techo de US$600; con los opcionales de Tecnología y
Clientes, hasta cerca de US$960. **Suma ingenua** (Tecnología más IA completas): US$755 a 1.185, que es lo
que vería quien sume las secciones 7 tal como están. Con el escenario austero de IA, lo indispensable queda
en US$340 a 460. El crédito de prueba de Google Cloud (US$300, dato [V] de Tecnología) reduce el
desembolso, no el costo. **Recomendación:** H-AUD-03 y choque 9.

---

## 6. Respuesta a la solicitud recibida en esta ronda

```
Solicitud S-CLI-13
De: VP Clientes   Para: Auditoría
Qué: aceptar el texto de consentimiento de la semilla humana de voz y las reglas de la demo
Estado: aceptada.
Respuesta:
  Consentimiento (D2): Auditoría lo revisa contra C-AUD-11 de 06 (previo a grabar, propósito,
  retención hasta el cierre de F6, derecho a retirarse, sin menores, audio cifrado y borrado con
  acta) antes de la primera grabación (CLI-6.2).
  Reglas de la demo (D7): se revisan contra el ítem F7-05 de 06 (tres casos obligatorios en
  español y portugués, ataque contenido y falla segura, traza, reintento acotado y caída segura,
  versión candidata, semillas fuera del retenido según R-CLI-107).
```

---

## 7. Veredicto

**Quedan tres hallazgos bloqueantes abiertos:**

1. **H-AUD-01:** 80 solicitudes sin respuesta en la cara que las recibe.
2. **H-AUD-02:** ocho solicitudes a la Presidencia sin respuesta (gasto y preguntas a los organizadores).
3. **H-AUD-04:** la tabla de costos de modelos de Tecnología contradice D-20.

Con ellos abiertos, **las reglas del juego no están cerradas** (modelo operativo, sección 7, paso 6).
Para cerrarlas, la segunda versión debe además resolver los choques 1, 6, 7 y 9 de la sección 3 (los que
cambian el retenido, la privacidad o el gasto antes de F2) y asignar H-AUD-19; si H-AUD-19 sigue sin
dueña, pasa a ser un cuarto bloqueante. Los hallazgos mayores restantes se corrigen en la segunda versión
o se aceptan con acta. Auditoría confirma el cierre con una segunda pasada fría (R-AUD-54) sobre
versiones con huella.

**Lo que está bien:** ninguna exigencia del enunciado quedó sin cara en la matriz; las dependencias de
historias apuntan a historias que existen (ninguna referencia rota); las decisiones propuestas que tocan
decisiones firmes lo declaran en su propia tabla (Tecnología) y van por la vía correcta.
