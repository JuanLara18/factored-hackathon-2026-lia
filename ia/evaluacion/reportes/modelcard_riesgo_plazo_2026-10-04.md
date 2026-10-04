# Ficha del modelo: riesgo de plazo de una disputa, 2026-10-04

Versión `riesgo-plazo-2026-10-04`. Pista de prioridad al radicar una disputa: no actúa, no niega, no decide.

**Uso previsto.** Subir un nivel la prioridad del traspaso a una persona y mostrar "en riesgo de plazo" cuando la banda es alta y la calibración está verificada. **Fuera de alcance:** denegar, retrasar o decidir sobre un caso, evaluar agentes o clientes, y cualquier uso con efecto en el cliente.

**Datos.** `latam_bank.plata_complaints` con clientes, productos y transacciones previas; 2023-06-17 a 2026-06-18; sintéticos. Partición temporal: entrenamiento antes de 2025-03-01, validación antes de 2025-10-01, prueba posterior. Sin campos posteriores a la radicación.

**Modelo.** Árboles de gradiente con escalado de Platt (validación); semilla 202616737. Etiquetas: SLA incumplido y escalada.

**Desempeño en prueba (IC 95% por cliente).** SLA incumplido: AUC-PR 0.205 [0.196, 0.215] con prevalencia 20.2%; AUC 0.504 [0.492, 0.514]. Escalada: AUC-PR 0.050 [0.046, 0.055] con prevalencia 5.1%. Señal sobre las líneas base: **no**. ECE (SLA) 0.0106.

**Limitaciones.** Etiqueta de SLA sin relación con los tiempos registrados; escalada censurada por la derecha; datos sintéticos; las quejas no se enlazan a una transacción; sin texto del cliente. La pista se abstiene siempre porque no hubo señal.

**Gobierno.** Pista sin acción permitida; los umbrales son un parámetro de política y se reentrenan con un nuevo reporte, no a mano. Reporte completo: `riesgo_plazo_2026-10-04.md`.
