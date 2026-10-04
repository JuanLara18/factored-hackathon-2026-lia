# Riesgo de incumplir el plazo de una disputa, reporte 2026-10-04

Segundo componente aprendido, atado al flujo de disputas: al radicar, ¿se puede anticipar que el caso incumplirá el SLA (o será escalado)? Reproducible con `uv run python -m latam_ia.experimentos.riesgo_plazo`. Datos: `latam_bank.plata_complaints` (67.095 quejas, sin texto libre), unida a clientes, productos y transacciones previas a la radicación. Todo lo de decisión es una simulación fuera de línea.

## Resumen

- **SLA incumplido** (prevalencia en prueba 20.2%): AUC-PR de los árboles calibrados 0.205 [0.196, 0.215] contra 0.201 de la mayoritaria, 0.205 de la regla por subcategoría y 0.207 de la logística; AUC 0.504 [0.492, 0.514]. Señal sobre las líneas base: **no**.
- **Escalada** (prevalencia en prueba 5.1%): AUC-PR de los árboles calibrados 0.050 [0.046, 0.055] contra 0.049 de la mayoritaria, 0.052 de la regla por subcategoría y 0.050 de la logística; AUC 0.506 [0.486, 0.526]. Señal sobre las líneas base: **no**.
- Auditoría: el SLA incumplido no guarda relación con lo que debería medirlo. Mediana de horas a la primera respuesta 38.0 h en incumplidos y 37.0 h en cumplidos (AUC 0.502); AUC con los días a la resolución 0.491; 19.6% de los 20.125 casos aún abiertos ya figuran como incumplidos (contra 20.1% en total).
- Conclusión: No hay señal verificable más allá de las líneas base. La pista se entrega como infraestructura que se abstiene siempre, y no se afirma ninguna ganancia.

## 1. Elección de la etiqueta y auditoría

Se comparan dos etiquetas, ambas resultados posteriores a la radicación. **SLA incumplido** (`sla_breached`) es la métrica de la línea base del problema (20,4% en cargos no reconocidos). **Escalada** es `status = Escalated` (4.9%).

- `sla_breached` no se deriva de los tiempos registrados: la primera respuesta tarda lo mismo en incumplidos y cumplidos (AUC 0.502; 0,5 es azar) y no hay relación con `resolution_days` (AUC 0.491). Tampoco con la prioridad (AUC 0.500) ni con el reincidente (AUC 0.500). La tasa mensual es plana (desviación estándar entre meses 0.009).
- Por estado (SLA incumplido y casos sin primera respuesta):

| Estado | Casos | SLA incumplido | Sin primera respuesta |
|---|---|---|---|
| Closed | 2.609 | 20.8% | 4.2% |
| Escalated | 3.321 | 20.9% | 100.0% |
| In Process | 26.823 | 20.5% | 5.0% |
| Open | 20.125 | 19.6% | 100.0% |
| Rejected | 705 | 21.4% | 100.0% |
| Resolved | 13.512 | 19.7% | 4.8% |

- `Escalated` es un estado final observado: 100.0% de las escaladas no tiene primera respuesta registrada. Los casos recientes pueden escalar después del corte (censura por la derecha), de modo que la etiqueta subestima los últimos meses.
- Calidad: 0 identificadores duplicados; monto reclamado vacío en 67.6%.

Veredicto: el SLA incumplido es la etiqueta de interés operativo, pero su validez es dudosa en estos datos (no responde a nada medible); la escalada es un estado real pero censurado. Se evalúan ambas con el mismo procedimiento y se reportan las dos sin escoger la que salga mejor.

## 2. Rasgos y fuga

Solo lo conocido al radicar: categoría, subcategoría, tipo de caso, canal de recepción, país y segmento del cliente, tipo del producto afectado, moneda, monto reclamado (con indicador de faltante), antigüedad del cliente, número de quejas previas del cliente (estrictamente anteriores a la creación), hora y día de la semana, y número y monto de transacciones del cliente en los 30 días previos (las quejas no se enlazan a una transacción).

**Excluidos por ser posteriores o derivados:** `status`, `assignment_date`, `first_response_date`, `resolution_date`, `closing_date`, `resolution_days`, `compensation_granted`, `resolution_satisfaction`, `assigned_agent_id`. También `priority` (no se sabe si la fija el cliente o el triaje) e `is_repeat_complainer` (no consta cuándo se calcula); ambos tienen AUC cercano a 0,5 con la etiqueta, así que excluirlos no cuesta señal. Los identificadores no son rasgos.

## 3. Partición

| Parte | Rango de creación | Casos | Prevalencia SLA | Prevalencia escalada |
|---|---|---|---|---|
| Entrenamiento | 2023-06-17 a 2025-02-28 | 38.125 | 20.2% | 4.8% |
| Validación | 2025-03-01 a 2025-09-30 | 12.905 | 19.7% | 5.3% |
| Prueba | 2025-10-01 a 2026-06-18 | 16.065 | 20.2% | 5.1% |

Partición temporal: calibración y umbrales solo con validación; la prueba se evalúa una vez. 22.1% de los clientes de prueba tienen quejas en entrenamiento; los IC son bootstrap por cliente (pesos Poisson, 1000 réplicas, semilla 202616737).

## 4. Modelos

- **Mayoritaria**: la prevalencia de entrenamiento para todos.
- **Regla por subcategoría**: tasa de entrenamiento de la subcategoría.
- **Regresión logística** (C = 0,1) sobre todos los rasgos.
- **Árboles de gradiente** (HistGradientBoosting; profundidad e iteraciones elegidas por AUC-PR en validación: SLA (4, 60), escalada (2, 60)) con escalado de Platt ajustado en validación. Control de azar: el mismo modelo con la etiqueta permutada rinde AUC-PR 0.205 (SLA) y 0.050 (escalada) en prueba, contra prevalencias 20.2% y 5.1%.

## 5. Resultados en prueba: SLA incumplido

Precisión objetivo para el recall a precisión fija: 0.296 (1,5 veces la prevalencia de validación, fijada antes de mirar prueba); el umbral de cada sistema se elige en validación.

| Sistema | AUC-PR | IC 95% | AUC | Recall a precisión objetivo | Precisión lograda |
|---|---|---|---|---|---|
| mayoritaria | 0.201 | [0.193, 0.210] | 0.497 | no alcanzable | n/a |
| regla por subcategoría | 0.205 | [0.196, 0.214] | 0.505 | no alcanzable | n/a |
| regresión logística | 0.207 | [0.198, 0.216] | 0.508 | no alcanzable | n/a |
| árboles calibrados | 0.205 | [0.196, 0.215] | 0.504 | no alcanzable | n/a |

Diferencias con IC: AUC-PR del modelo menos la prevalencia [-0.004, 0.010], menos la regla [-0.009, 0.010], menos la logística [-0.011, 0.006]; AUC menos 0,5 [-0.008, 0.014]. Control con etiqueta permutada: AUC-PR 0.205.

**Calibración (prueba).** ECE 0.0106 (validación 0.0093; sin calibrar 0.0101); Brier 0.1614 contra 0.1613 de la prevalencia. Por deciles de probabilidad:

| Decil | Probabilidad media | Frecuencia observada | Casos |
|---|---|---|---|
| 1 | 0.192 | 0.214 | 1.602 |
| 2 | 0.194 | 0.201 | 1.587 |
| 3 | 0.195 | 0.196 | 1.496 |
| 4 | 0.196 | 0.184 | 1.730 |
| 5 | 0.197 | 0.187 | 1.568 |
| 6 | 0.198 | 0.216 | 1.296 |
| 7 | 0.198 | 0.203 | 1.586 |
| 8 | 0.199 | 0.210 | 1.957 |
| 9 | 0.201 | 0.214 | 1.567 |
| 10 | 0.206 | 0.199 | 1.676 |

**Análisis de decisión (simulación fuera de línea, sin humanos reales).** Si el k% de mayor riesgo se prioriza a la cola humana, esta es la fracción de los incumplimientos (o escaladas) que se anticipa. Un orden al azar captura k%.

| k | Modelo | IC 95% | Regla por subcategoría | Azar |
|---|---|---|---|---|
| 5% | 4.9% | [0.042, 0.057] | 4.9% | 5.0% |
| 10% | 9.6% | [0.086, 0.107] | 10.1% | 10.0% |
| 20% | 20.4% | [0.190, 0.218] | 20.1% | 20.0% |

Subgrupo cargos no reconocidos en prueba (n = 2.976, prevalencia 20.9%): AUC-PR 0.211, AUC 0.499. Importancia por permutación en validación (caída de AUC-PR), mayores: monto_tx_30d_usd 0.0020, antiguedad_dias 0.0011, dia_semana 0.0011, segmento 0.0011, tipo_producto 0.0009.

Señal sobre las líneas base: **no** (se exige que los tres IC excluyan 0).

## 6. Resultados en prueba: Escalada

Precisión objetivo para el recall a precisión fija: 0.079 (1,5 veces la prevalencia de validación, fijada antes de mirar prueba); el umbral de cada sistema se elige en validación.

| Sistema | AUC-PR | IC 95% | AUC | Recall a precisión objetivo | Precisión lograda |
|---|---|---|---|---|---|
| mayoritaria | 0.049 | [0.045, 0.054] | 0.495 | no alcanzable | n/a |
| regla por subcategoría | 0.052 | [0.047, 0.057] | 0.506 | 0.196 | 0.054 |
| regresión logística | 0.050 | [0.046, 0.055] | 0.493 | no alcanzable | n/a |
| árboles calibrados | 0.050 | [0.046, 0.055] | 0.506 | 0.002 | 0.036 |

Diferencias con IC: AUC-PR del modelo menos la prevalencia [-0.003, 0.003], menos la regla [-0.006, 0.003], menos la logística [-0.003, 0.004]; AUC menos 0,5 [-0.014, 0.026]. Control con etiqueta permutada: AUC-PR 0.050.

**Calibración (prueba).** ECE 0.0035 (validación 0.0060; sin calibrar 0.0047); Brier 0.0481 contra 0.0481 de la prevalencia. Por deciles de probabilidad:

| Decil | Probabilidad media | Frecuencia observada | Casos |
|---|---|---|---|
| 1 | 0.049 | 0.049 | 1.604 |
| 2 | 0.051 | 0.047 | 1.394 |
| 3 | 0.051 | 0.052 | 1.719 |
| 4 | 0.052 | 0.050 | 1.703 |
| 5 | 0.052 | 0.050 | 1.454 |
| 6 | 0.052 | 0.046 | 1.754 |
| 7 | 0.053 | 0.058 | 1.218 |
| 8 | 0.053 | 0.055 | 2.005 |
| 9 | 0.054 | 0.055 | 1.586 |
| 10 | 0.057 | 0.045 | 1.628 |

**Análisis de decisión (simulación fuera de línea, sin humanos reales).** Si el k% de mayor riesgo se prioriza a la cola humana, esta es la fracción de los incumplimientos (o escaladas) que se anticipa. Un orden al azar captura k%.

| k | Modelo | IC 95% | Regla por subcategoría | Azar |
|---|---|---|---|---|
| 5% | 4.2% | [0.029, 0.056] | 5.3% | 5.0% |
| 10% | 8.9% | [0.069, 0.108] | 10.8% | 10.0% |
| 20% | 19.8% | [0.172, 0.224] | 20.5% | 20.0% |

Subgrupo cargos no reconocidos en prueba (n = 2.976, prevalencia 5.3%): AUC-PR 0.051, AUC 0.496. Importancia por permutación en validación (caída de AUC-PR), mayores: subcategoria 0.0024, tipo_producto 0.0018, antiguedad_dias 0.0011, monto_reclamado 0.0009, monto_tx_30d_usd 0.0008.

Señal sobre las líneas base: **no** (se exige que los tres IC excluyan 0).

## 7. Errores y límites

- Con una etiqueta sin relación con ningún rasgo medible, lo esperable es un AUC cercano a 0,5 y una captura por k% igual a k%; los resultados se leen contra ese techo.
- Las tasas por subcategoría, canal y país están todas entre 19% y 22%: las diferencias caen dentro del ruido de muestreo de cada celda.
- Las transacciones no se enlazan a la queja, así que ese rasgo describe al cliente y no a la disputa.
- Datos sintéticos: la ausencia de señal aquí no prueba que no exista en un banco real; solo que este experimento no sostiene una afirmación de mejora.

## 8. Integración

`riesgo_plazo(caso, modelo) -> PistaRiesgo` (probabilidad, banda, abstención) en `latam_ia.comprension.riesgo_plazo`. Devuelve probabilidad solo si el experimento halló señal y dentro de la región de validación (percentiles 1 a 99). `construir_paquete` la usa únicamente para subir un nivel la prioridad del traspaso (hasta P2) y agregar el plazo "En riesgo de plazo"; nunca para negar, decidir o ejecutar. Sin señal verificada no cambia nada.
