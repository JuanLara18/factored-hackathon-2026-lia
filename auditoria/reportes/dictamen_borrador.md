# Dictamen preliminar de Auditoría (borrador)

**Estado:** borrador de la Oficina de Entrega con lista de verificación al estilo de una revisión independiente. **No es un dictamen sellado:** la independencia real exige que Auditoría lo corra en frío (plantillas en [auditoria/plantillas](../plantillas/)). **Fecha:** 4 de octubre de 2026, con una actualización del 5 de octubre (sección 8) que no reemplaza la revisión en frío. **Contra:** [enunciado](../../docs/enunciado/Enunciado_Factored_Hackathon_2026.pdf) y [reporte final](../../presidencia/reporte/00_reporte_final.md).

Escala: **cumple** (evidencia suficiente y verificable), **parcial** (existe con una brecha declarada), **no cumple** (falta). Cada fila cita su fuente.

## 1. Alcance y límites de datos

| Requisito | Veredicto | Evidencia y brecha |
|---|---|---|
| Un flujo coherente | cumple | disputas de cargo no reconocido, elegido con puntaje ([01_problema](../../presidencia/reporte/01_problema.md) sección 6) |
| Normal, ambiguo o no soportado, y humano | cumple | casos N, A, F y E del retenido ([04](../../presidencia/reporte/04_evaluacion.md) sección 3); demo en [guion](../../presidencia/reporte/demo/guion.md) |
| Español y portugués | parcial | demostrado, con 13 de 32 casos en portugués; sin hablante nativo y sin cuentas de Brasil ([LIMITACIONES](../../datos/LIMITACIONES.md)) |
| Límites de datos e idioma reportados | cumple | `LIMITACIONES.md`, [01_problema](../../presidencia/reporte/01_problema.md) sección 5 |
| Origen de los insumos (real, sintético, del equipo) | cumple | todo el dataset es sintético; lo del equipo está rotulado (`origen = 'equipo'`, fixture); inventario en `platino_inventario_insumos` |
| Sin datos privados ni credenciales en público | parcial | guarda `latam_gobierno.guardas` y gitleaks en CI ([ci.yml](../../.github/workflows/ci.yml)); falta confirmar con los organizadores el uso de Gemini con hechos mínimos (D-15 lo deja provisional); hay que revisar el perfil de AWS y el token de Hugging Face ([ESTADO](../../presidencia/ESTADO.md), pendientes 3) |
| Identidad con sesión de confianza, no solo un número | cumple | niveles `acr` y sesión con vencimiento ([02_solucion](../../presidencia/reporte/02_solucion.md) sección 5) |
| Acceso por cliente y permisos en la capa de servicio | cumple | firma de herramientas con `SesionAutenticada`; 0 datos ajenos en 18 corridas de ataque ([04](../../presidencia/reporte/04_evaluacion.md) 5.6) |
| Crédito: conversación, riesgo y política separados | cumple | el agente no evalúa elegibilidad; tope provisional por política ([credito_provisional.yaml](../../gobierno/politica/v1/credito_provisional.yaml)); el flujo no es de crédito |

## 2. Los seis criterios

| Criterio | Veredicto | Evidencia | Brechas encontradas |
|---|---|---|---|
| 1. Problema con datos | cumple | [01_problema](../../presidencia/reporte/01_problema.md) con n y figuras | el volumen de disputas es una cota inferior (quejas); el liderazgo cambia con peso de volumen de 40% o más; el costo por contacto es supuesto; sin abandono ni transcripciones útiles |
| 2. Sistema funcional | cumple | [02_solucion](../../presidencia/reporte/02_solucion.md); 70 pruebas e2e en producción el 30 sep | e2e anterior al rediseño del 4 oct: repetir antes de la demostración; ficha visual no se dibuja en modo remoto sin la herramienta del navegador |
| 3. Automatización controlada | parcial | política en código, aprobación de un solo uso, idempotencia | ESC-03 no se aplica en `abrir_disputa`; una orden inyectada de urgencia se obedeció 3 de 3; TRA-04 a TRA-07 con `en_motor: false`; umbrales provisionales (ESC-04, 48 h de México, tiempos por prioridad) |
| 4. Datos y ML | cumple | [03_datos_y_ml](../../presidencia/reporte/03_datos_y_ml.md) | clasificador con ganancia modesta y solo con señales posteriores al contacto; riesgo de plazo sin señal; etiquetas sintéticas generadas desde la clase; sin semilla humana de etiquetas (una rúbrica de coherencia interna) |
| 5. Calidad medida y fallas | parcial | [04](../../presidencia/reporte/04_evaluacion.md) | ver sección 3 |
| 6. Ruta a operación | parcial | [06_produccion](../../presidencia/reporte/06_produccion.md) | monitoreo y retención solo propuestos; sin carga; Terraform sin aplicar; Agent Identity bloqueada |

## 3. Evidencia de evaluación (definiciones del enunciado)

| Requisito | Veredicto | Evidencia | Brecha |
|---|---|---|---|
| Mismo retenido para línea base y propuesto | cumple | 32 casos para B-reglas, propuesto y sin herramientas ([04](../../presidencia/reporte/04_evaluacion.md) sección 2) | la línea sin herramientas cubrió solo 11 casos por presupuesto |
| Número y mezcla de casos, calidad de etiquetas | parcial | sección 3 de 04 | etiquetas de un solo autor, sin acuerdo entre etiquetadores; 3 de 32 casos (9%) con defecto de evaluación; 7 con `debe_escalar` indeterminado |
| Versiones de modelo y prompt | cumple | `gemini-3.1-flash-lite`, `disputas/agente@1.3.0`, trabajador 0.4.0, huella del conjunto | |
| Variabilidad entre corridas | cumple | k=3, pass^k 0,80 / 0,77 / 0,75 (04, 5.4) | las corridas de un caso no son independientes: los IC subestiman |
| Fallas en los resultados | cumple | 19 corridas fallidas analizadas | |
| Juez de modelo con rúbrica validada | parcial | no se usó juez; veredictos deterministas contra 43 corridas revisadas (acuerdo 77%) | el tono y la claridad no se midieron; el GenAI Evaluation Service del 29 sep (trayectoria exacta 52%, en orden 62%) no se repitió ([ESTADO](../../presidencia/ESTADO.md)) |
| Resolución automática segura sobre todos los casos en alcance, e intentada | cumple | 29/75 (39%) y 47/75 (63%) | cifra baja por la mezcla del conjunto (categorías E y X no resuelven por diseño) |
| Contención aparte de la resolución | cumple | 54/75 (72%) | |
| Calidad del escalamiento, perdidos e innecesarios | cumple | 3/18 y 8/57 | los tres perdidos son un mismo caso |
| Inseguros con denominadores | cumple | 0/96, IC95 0% a 4%; texto "cero observado no es cero riesgo" | cliente simulado más cooperativo que uno real |
| p50 y p95, costo por intentado y por resolución | parcial | 1,41 y 4,61 s por turno; US$ 0,00215 y US$ 0,00483 | latencia en proceso, sin red, carga ni arranque en frío; tarifa sin verificar contra la página de precios; costo sin infraestructura; mensual no definido |
| Comparación por idioma y segmento, con muestras pequeñas | parcial | [05_equidad](../../presidencia/reporte/05_equidad.md) y 04 sección 6 | país y segmento no evaluables (31 de 32 casos son de Colombia, ninguno de México, segmento único); es y pt con mezclas de categoría distintas |
| Separar offline, simulación y proyección | cumple | tablas de clases en [00_reporte_final](../../presidencia/reporte/00_reporte_final.md) sección 2 | |
| Entradas exigidas: datos incorrectos o faltantes, sesión vencida, acceso no autorizado, inyección, fallas, ambigüedad multilingüe | cumple | 11 casos X, 5 A, 2 sesiones vencidas, inyección directa e indirecta en es y pt, 3 fallas de infraestructura | el agente no informa al cliente ante una falla (hallazgo 5); el retenido está gastado |
| Independencia del generador, simulador y juez | no cumple | agente y cliente simulado son de la misma familia (R-IA-09 violada, [04](../../presidencia/reporte/04_evaluacion.md) sección 9) | usar otra familia de modelos para el simulador |

## 4. Datos y gobierno

| Requisito | Veredicto | Evidencia | Brecha |
|---|---|---|---|
| Contratos | cumple | 8 contratos ODCS de oro operacional, sin deriva | sin contrato de plata ni de platino |
| Calidad | cumple | Q-BRZ, 56 pruebas de dbt, 5 avisos y 0 bloqueantes | sin cuarentena por fila |
| Linaje | cumple | manifiesto encadenado (13 registros, cadena íntegra) | el `job_id` de la primera corrida es nulo |
| Frescura y actualización | cumple | [POLITICA_ACTUALIZACION](../../datos/POLITICA_ACTUALIZACION.md); fixture FX-01 a FX-10 | fixture del equipo, no un proceso de actualización real |
| Fugas y particiones | cumple | secciones 2 y 3 de [03](../../presidencia/reporte/03_datos_y_ml.md) | |
| Aprendido contra línea base | cumple | clasificador y riesgo de plazo con IC | un resultado negativo, declarado |
| Equidad | parcial | línea base histórica sin disparidad atribuible; herramienta `tabla_disparidad` | sin medición del sistema por país ni segmento; unas 600 comparaciones sin corrección múltiple |
| Fuentes de las decisiones | no cumple | `auditoria/fuentes/fuentes.yaml`: 66 fuentes, 3 verificadas, 1 con precisión, 1 secundaria, 1 en conflicto y 60 pendientes (R-AUD-34) | verificar las 60 pendientes o retirarlas |
| Plantillas de independencia e informe sellado | parcial | existen en `auditoria/plantillas/` | sin informe sellado ni paquete de independencia llenados |

## 5. Operación

| Requisito | Veredicto | Evidencia | Brecha |
|---|---|---|---|
| Trazas | cumple | Cloud Trace sin contenido ([06](../../presidencia/reporte/06_produccion.md) sección 2) | no se verificó en esta revisión una traza real del agente remoto |
| Reintentos acotados | cumple | un reintento del modelo y 90 s por turno | |
| Caída segura | parcial | 15 de 15 corridas con falla sin efectos ni fugas | muda para el cliente; solo con dobles inyectados |
| Instalación reproducible | parcial | `uv.lock`, CI, `just` | Terraform nunca aplicado ni planeado; estado local |
| Capacidad, monitoreo, accesos, retención | parcial | sección 5 a 8 de 06 | propuestas sin desplegar; retención sin implementar; cuotas sin llenar; Agent Identity bloqueada; secreto de referencias con valor por defecto y discrepancia sobre Secret Manager |
| Explicaciones por fuentes, reglas y registros | cumple | paquete con regla y versión, `AccionVerificada`; sin razonamiento oculto | |

## 6. Hallazgos de Auditoría, por prioridad

1. **Alta.** Resultado de seguridad por corregir: orden inyectada de urgencia obedecida (3 de 3) y ESC-03 no aplicado por la herramienta. Un frente corrige y documenta en un adendo de 04; Auditoría debe repetir la comprobación sobre un retenido nuevo, no sobre el gastado.
2. **Alta.** El simulador comparte familia con el sistema evaluado (R-IA-09).
3. **Alta.** La afirmación de la línea base no se sostiene a favor del modelo: el agente no supera a B-reglas. Cualquier texto del jurado o de la demo debe decirlo (el reporte lo hace).
4. **Media.** Cobertura de evaluación: sin México ni Brasil, sin segmento, etiquetas de un autor, tono sin medir.
5. **Media.** 60 de 66 fuentes sin verificar.
6. **Media.** Retención y monitoreo no implementados; Terraform sin aplicar; capacidad de una instancia.
7. **Media.** Discrepancia sobre Secret Manager y secreto con valor por defecto en el código.
8. **Baja.** Costo con tarifa supuesta y sin infraestructura; latencia sin carga.
9. **Baja.** Coherencia documental: el README anterior hablaba de chat, WhatsApp y voz; se corrigió a lo desplegado (solo chat web). Revisar que ninguna otra página afirme canales no desplegados.
10. **Baja.** Verificar que las cifras de [00_reporte_final](../../presidencia/reporte/00_reporte_final.md) coincidan con 04 tras el adendo de correcciones.

## 7. Qué falta para sellar

Correr a Auditoría en frío con el paquete de independencia; confirmar las cifras desde los JSON por corrida (`ia/evaluacion/reportes/retenido_casos_propuesto.json`); verificar las fuentes; revisar el adendo de correcciones de 04; y repetir los gates (`uv run pytest -q`, ruff, `uv run python -m latam_gobierno.guardas`).

## 8. Actualización del 5 de octubre (Oficina de Entrega, no es revisión independiente)

Las secciones 1 a 7 describen el sistema del 4 de octubre y se dejan como se escribieron. Esto cambió después; Auditoría debe comprobarlo en frío antes de sellar.

| Hallazgo o fila | Estado al 5 de octubre | Evidencia | Qué sigue abierto |
|---|---|---|---|
| Hallazgo 1: ESC-03 no aplicado por la herramienta | corregido | `abrir_disputa` rechaza el producto desconocido; R21 de 0/3 a 3/3 ([04](../../presidencia/reporte/04_evaluacion.md), anexo "Correcciones posteriores") | comprobación post hoc sobre un caso conocido; falta un retenido nuevo |
| Hallazgo 1: orden inyectada de urgencia | corregido en la prioridad | la urgencia sale de una lista cerrada de motivos (ESC-05); `E10_inyeccion_prioridad_pt` 8 de 8, 0 inseguras | un cliente que relate un engaño inventado puede obtener el motivo urgente |
| Criterio 3, fila "parcial" | pasa a cumple con la reserva anterior | [02_solucion](../../presidencia/reporte/02_solucion.md) sección 3 | TRA-04 a TRA-07 con `en_motor: false`; umbrales provisionales |
| Caída segura "muda" | corregido | plantilla `falla_segura.chat`; 15 de 15 corridas con texto | sin prueba con una caída real de Agent Runtime |
| Sistema funcional: e2e anterior al rediseño | repetido | 78 de 78 contra producción el 5 oct ([ESTADO](../../presidencia/ESTADO.md)) | |
| Hallazgo 7: Secret Manager y secreto con valor por defecto | corregido en código | Cloud Run monta `latam-ref-secreto` (verificado en la configuración del servicio); un servicio desplegado sin la clave no arranca (`refs.py`, `test_retencion_y_refs.py`) | el agente ya recibe la clave (desplegado el 5 oct); antes firmaba con la de demostración la referencia del movimiento en el paquete de traspaso |
| Hallazgo 6: retención y monitoreo no implementados; Terraform sin planear | retención de registros operativos implementada (TTL de 30 días); alertas de disponibilidad, errores y latencia como código; `terraform plan` corrido: 16 por adoptar, 30 por crear, 0 por destruir | [06_produccion](../../presidencia/reporte/06_produccion.md) secciones 4, 6 y 8 | TTL y alertas aplicados en el proyecto el 5 oct; falta adoptar el resto con Terraform; calidad y equidad en producción siguen como propuesta; una instancia |
| Hallazgo 8: tarifa supuesta | verificada | US$ 0,25 y US$ 1,50 por millón en la página de precios de la API de Gemini (5 oct) | costo sin infraestructura; latencia sin carga |
| Hallazgo 10: coherencia de 00 con 04 | corregido | 00, 02 y 06 citan el anexo y separan la corrida congelada de la comprobación post hoc | |

Sin cambio: hallazgo 2 (simulador de la misma familia), hallazgo 3 (el agente no supera a la línea base de reglas), hallazgo 4 (cobertura sin México ni Brasil, etiquetas de un autor, tono sin medir) y hallazgo 5 (60 de 66 fuentes sin verificar).
