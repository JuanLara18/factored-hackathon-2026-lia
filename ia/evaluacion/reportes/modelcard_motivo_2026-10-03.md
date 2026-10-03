# Ficha del modelo: motivo de contacto, 2026-10-03

**Qué es.** Clasificador de seis clases (Comercial, Producto, Queja, Retención, Transaccional, Técnico) que sugiere el código de cierre de un contacto.
Versión `motivo-arboles-llamada-2026-10-03`. Es una pista de enrutamiento: no actúa, y se abstiene por debajo
de p = 0.81.

**Uso previsto.** Sugerir el motivo al agente humano al cerrar el contacto y dar contexto al paso de comprensión del
agente cuando ya existen duración, sentimiento y cierre. **Fuera de alcance:** enrutar antes de atender (el conjunto
`contacto` no tiene señal), decidir efectos sobre el cliente, y evaluar personas.

**Datos.** `latam_bank.plata_call_center_interactions` unido a `plata_customers`, 2023-06-17 a 2026-06-17, español,
sintéticos. Partición temporal: entrenamiento < 2025-07-01, validación < 2026-01-01, prueba posterior. Sin identificadores como
rasgos; sin campos derivados de la etiqueta.

**Modelo.** arboles sobre rasgos tabulares con imputación e indicadores de faltante; escalado de temperatura
T = 1.00 ajustado en validación; semilla 202616737.

**Desempeño en prueba (IC 95% por cliente).** Macro-F1 0.399 [0.396, 0.402]; línea base
de reglas 0.343; mayoritaria 0.086. ECE 0.0068,
Brier 0.5718. A p ≥ 0.81: cobertura 13.1%,
exactitud 85.0%.

**Limitaciones.** Datos sintéticos con señal generada a partir de la etiqueta; no hay texto del cliente; solo español;
no se midió equidad porque los rasgos protegidos no influyen; la calibración es válida solo en esta distribución
temporal y debe reverificarse si cambia el mezcla de motivos.

**Gobierno.** Pista sin acción permitida; el umbral es un parámetro de política y se reentrena con un nuevo
reporte, no a mano. Reporte completo: `clasificador_2026-10-03.md`.
