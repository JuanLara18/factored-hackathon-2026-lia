# Criterio 6: ruta a operación

**Cara:** Presidencia con Tecnología, Gobierno y Datos. **Fecha:** 4 de octubre de 2026. Volver al [reporte final](00_reporte_final.md). Este capítulo separa lo **implementado y verificado** de lo **propuesto**. Nada aquí es una medición de producción con tráfico real: no lo hay.

## 1. Estado en una tabla

| Capacidad | Estado | Evidencia |
|---|---|---|
| Trazas | implementada | Cloud Trace, un span por turno, modelo y herramienta; prueba `tecnologia/tests/test_observabilidad.py` |
| Reintentos acotados | implementados | un reintento del modelo; tope de 90 s por turno |
| Caída segura | implementada y evaluada | 15 de 15 corridas con falla inyectada sin efectos ni fugas ([04](04_evaluacion.md) 5.1) y, desde el trabajador 0.5.0, con un mensaje al cliente |
| Instalación reproducible | implementada | `uv.lock`, CI, `just`; Terraform planea contra el proyecto sin destruir nada y se aplicó la parte aditiva (5 oct) |
| Capacidad | limitada por diseño | una instancia, sesiones en memoria |
| Monitoreo y alertas | disponibilidad, errores y latencia desplegadas (módulo `monitoreo` de Terraform); calidad y equidad, propuesta | sección 6 |
| Controles de acceso | parciales | sección 7 |
| Retención | implementada para los registros operativos: vencimiento a 30 días por documento y política de TTL de Firestore | sección 8 |

**Estado de despliegue de lo hecho el 5 de octubre.** El vencimiento de los documentos, el arranque que exige la clave de referencias y su entrega al agente están desplegados (hoy en la revisión `latam-chat-00023-8vw`, agente actualizado en el mismo recurso), y del plan de Terraform se aplicó la parte que solo crea: las cinco políticas de TTL de Firestore, la comprobación de disponibilidad y las tres alertas. Verificado el mismo día: 81 de 81 pruebas de extremo a extremo contra el backend de producción, políticas de TTL activas y documentos nuevos con `expira_en`. El resto del plan (adoptar el servicio, los datasets, el secreto y el ping, con cambios solo de etiquetas) no se ha aplicado ([ESTADO](../ESTADO.md)).

## 2. Trazas y explicaciones auditables

OpenTelemetry exporta a Cloud Trace: un span por turno (`invoke_agent`), por llamada al modelo (`chat <modelo>`) y por herramienta (`execute_tool`), con `latam.trabajador.id` y `latam.trabajador.version`. Se instrumenta con `include_content=False`: viajan nombres, duraciones y conteo de tokens, sin mensajes, argumentos ni resultados, así que sin PII ([observabilidad.py](../../tecnologia/src/latam_tecnologia/observabilidad.py)). El paquete de traspaso lleva la evidencia: reglas aplicadas con versión (`TRA-nn`, `ESC-nn`), plantillas y el enlace a la traza cuando existe (`traza_url` es nulo si no hay traza real; [API_BANCA](../../tecnologia/web/API_BANCA.md)).

Las explicaciones se basan en tres cosas verificables: la **fuente** de cada hecho (`transacciones`, `productos`, `casos`), la **regla** de política con identificador y versión, y el **registro de ejecución** (acción, resultado releído, hora). El razonamiento oculto del modelo no se guarda ni se usa como evidencia; el campo de "razonamiento" de las salidas estructuradas se excluye del paquete ([clientes/definicion.md](../../clientes/definicion.md) sección 2.5.2).

## 3. Reintentos acotados y caída segura

| Mecanismo | Valor | Fuente |
|---|---|---|
| Llamada al modelo malformada, 5xx, 429 o corte de conexión | un reintento tras 1,5 s con temperatura 0,8 | [geap.py](../../tecnologia/src/latam_tecnologia/canales/geap.py) |
| Turno que falla en el modelo antes de decir nada | un reintento; si no, el canal recibe `error` con código `modelo` | [agente.py](../../tecnologia/src/latam_tecnologia/runtime/agente.py) |
| Tope de un turno completo | 90 s; pasado, el cliente recibe aviso y puede reintentar | [runtime_cliente.py](../../tecnologia/src/latam_tecnologia/canales/runtime_cliente.py) |
| Efectos del banco | idempotentes por llave; reintentar no duplica; una reserva que falló se libera | [retoma.py](../../tecnologia/src/latam_tecnologia/motor/retoma.py) |
| Sesión vencida o de nivel insuficiente | `AccesoDenegado`, sin efectos | [catalogo.py](../../tecnologia/src/latam_tecnologia/herramientas/catalogo.py) |
| Confirmación vencida | vigencia de 5 minutos, de un solo uso | [chat_web.py](../../tecnologia/src/latam_tecnologia/canales/chat_web.py) |
| Interruptor del modelo | `LATAM_MODELO=guionado` fuerza el modelo de guion | [ia/README](../../ia/README.md) |
| Botón de persona | siempre visible; el traspaso funciona sin el modelo | [widget.js](../../tecnologia/web/sitio/assets/widget.js) |

**Brecha medida y corregida.** En la evaluación congelada, ante una falla el sistema era seguro pero **mudo**: el turno se cortaba con una excepción y el cliente no recibía nada ([04](04_evaluacion.md) hallazgo 5). Desde el trabajador 0.5.0 la falla del turno se le dice al cliente con la plantilla `falla_segura.chat`, con la opción de una persona, en proceso, en Agent Runtime y en el canal; las 15 corridas con falla inyectada lo comprueban post hoc ([04_evaluacion](04_evaluacion.md), anexo "Correcciones posteriores"). Sigue pendiente un mensaje distinto por tipo de falla y la comprobación con una caída real de Agent Runtime, no inyectada.

## 4. Instalación reproducible

- Dependencias fijadas en `uv.lock`; `uv sync --all-packages --all-groups` y `just check` (formato, tipos, pruebas) corren igual en CI ([ci.yml](../../.github/workflows/ci.yml)) con la guarda `latam_gobierno.guardas` y gitleaks.
- Datos: manifiesto encadenado y `just verificar-cadena`; análisis regenerable con `uv run python -m latam_datos.analisis`; dbt aislado con `uvx`.
- Agente: `tecnologia/infra/agent_runtime/desplegar.py` actualiza el mismo recurso; el chat se despliega con `just desplegar-chat-run-agente`.
- Terraform declara presupuesto, APIs, Firestore con su política de TTL, `latam-chat` con su secreto y su ping, alertas, buckets y BigQuery. El 5 de octubre se corrió `terraform plan` por primera vez contra el proyecto: 16 recursos por adoptar, 30 por crear y 0 por destruir. Ese plan encontró deriva que se corrigió en el código antes de cualquier `apply` (el vencimiento de 60 días del sandbox habría vuelto a los datasets, el código del experto habría salido del servicio y la versión del trabajador estaba fija en un valor viejo). No se ha aplicado por completo y el estado es local ([ARRANQUE](../../tecnologia/infra/ARRANQUE.md)). El agente de Agent Runtime y la imagen de Cloud Run quedan fuera de Terraform por diseño.
- Verificado en producción el 5 oct, con el prompt 1.7.0 y el trabajador 0.8.0 (revisión `latam-chat-00023-8vw`): la suite de Playwright en `tests/e2e/` pasó (81 de 81 contra el sitio y el backend publicados) ([ESTADO](../ESTADO.md)).

## 5. Capacidad y límites

| Límite | Valor | Consecuencia |
|---|---|---|
| Instancias de Cloud Run | de 0 a 1; 1 vCPU, 1 GiB; concurrencia 40 | no escala horizontalmente |
| Instancias de Agent Runtime | `min_instances` 0, `max_instances` 1 | arranque en frío tras inactividad |
| Estado del canal | sesiones, confirmaciones y operadores en memoria del proceso | se pierden al reiniciar; para varias instancias hay que moverlos a Firestore ([ESTADO](../ESTADO.md)) |
| Idempotencia | por instancia | vale con `max_instances = 1` |
| Arranque en frío | segundos; recomendado `--min-instances 1` el día de la demo | no se midió su distribución |
| Carga | no se ejecutó ninguna prueba de carga | la latencia de 04 es del agente en proceso, sin concurrencia, red ni arranque en frío |
| Cuotas | la tabla de [CUOTAS.md](../../tecnologia/infra/CUOTAS.md) está sin llenar (estado `[A]` en todas las filas) | límites de Vertex, Cloud Run y otros desconocidos |
| Bloqueo del bucle de eventos | detectado el 30 sep (la banca tardaba más de 20 s bajo carga) y corregido con handlers síncronos en hilos | prueba de regresión |

Orden de magnitud de costo, con la tarifa de lista de 04 (sección 5.5): US$ 0,00215 por caso intentado solo por el modelo, 7.056 tokens de entrada por corrida. No incluye Cloud Run, Agent Runtime, BigQuery ni Firestore; costo mensual **no definido** (no hay volumen). Agent Runtime cobra US$ 0,085 por vCPU-hora con 50 vCPU-horas gratis al mes y no cobra la espera (D-32); el presupuesto del proyecto es de COP 20.000 al mes con alertas al 25, 50 y 100%; la evaluación completa en GEAP costó unos US$ 0,07 ([ARRANQUE](../../tecnologia/infra/ARRANQUE.md)).

## 6. Monitoreo y alertas

Lo que hay: Cloud Trace, las alertas de presupuesto y, desplegadas desde `tecnologia/infra/terraform/modules/monitoreo`, una comprobación de disponibilidad de `/api/textos` cada 5 minutos y tres alertas con aviso por correo (el canal no responde, 5xx sobre 2% en 5 minutos, p95 de la petición sobre 5,76 s durante 10 minutos). Las filas de calidad, equidad, costo por caso y datos son propuesta: no salen de métricas de plataforma sino del registro por caso. La regla de vigilancia de equidad y seguridad ya está definida en [05_equidad](05_equidad.md) sección 7; aquí se completa con lo operativo.

| Señal | Métrica | Alerta propuesta | Fuente de datos |
|---|---|---|---|
| Resultados inseguros | conteo por versión | cualquier caso: aviso inmediato y veto de la versión | registro por caso y revisión de muestra |
| Disponibilidad | tasa de 5xx del canal y del agente | por encima de 2% en 5 minutos | métricas de Cloud Run y Agent Runtime |
| Latencia | p50 y p95 por turno | p95 mayor que 1,25 veces la línea de 04 (4,61 s) | Cloud Trace |
| Fallas del modelo | tasa del código `modelo` y de reintentos | tendencia al alza semanal | registro del canal |
| Costo | tokens por caso y gasto diario | presupuesto de COP 20.000 al 50 y 100% (ya existe) | Billing |
| Calidad | resolución segura, contención, traspasos perdidos e innecesarios | los mismos campos de 04 sobre una muestra revisada por dos personas | registro por caso |
| Equidad | resolución, traspasos, latencia por idioma, país y segmento | reglas de 05 sección 7 | platino |
| Datos | cadena del manifiesto, reglas Q-BRZ, frescura contra `AS_OF` | cadena rota o bloqueante: bloquea cifras oficiales | `just verificar-cadena`, `just validar` |

## 7. Controles de acceso

| Control | Estado |
|---|---|
| Cuenta `latam-chat@` de mínimo privilegio | `bigquery.dataViewer` a nivel de dataset sobre `latam_bank` (sin acceso a `latam_seguridad`), `bigquery.jobUser`, `aiplatform.user`, `cloudtrace.agent`, `datastore.user`; el agente en Agent Runtime corre con la misma cuenta ([tecnologia/README](../../tecnologia/README.md)) |
| Agent Identity | **bloqueada**: exige que el proyecto esté en una organización y hoy está "sin organización"; `iam.sh agente` queda para ese día |
| Cuenta de Compute | conserva `roles/editor` porque Cloud Build la usa; hay que retirarlo tras mover los builds a su propia cuenta |
| Consola del experto | código de demostración (`LATAM_OPERADOR_CODIGO` de Cloud Run), comparación en tiempo constante, 5 fallos por minuto antes de 429, sesión de 8 horas; no es un control de producción (sin identidad individual, sin MFA) |
| Endpoint de restablecimiento | exige ese mismo código y límite de intentos; solo borra a los clientes de demostración |
| Separación de datos restringidos | por construcción: el IAM es de proyecto y `projectReaders` lee todo; el destino son policy tags y vistas autorizadas ([datos/README](../../datos/README.md)) |
| Acceso del cliente a lo suyo | en la capa de herramientas por la sesión; el retenido incluye 6 casos de ataque (cuenta ajena, inyección directa e indirecta) con 0 datos ajenos en 18 corridas ([04](04_evaluacion.md) 5.6) |
| Cloud Run | acceso público por diseño (el sitio llama a la API); CORS limitado a los orígenes del sitio |
| Protección de ramas | no disponible en repositorios privados del plan gratuito; se cumple por disciplina y CI (D-29) |

## 8. Retención de datos

La política decidida (D-27, [decisiones](../decisiones.md)): registros operativos 30 días; evidencia de evaluación hasta el cierre más 90 días; al modelo externo solo hechos mínimos y enmascarados; ningún proveedor sin ficha de términos; audio crudo no se guarda por defecto. **Implementado para los registros operativos:** cada caso, bloqueo, traspaso, conversación y mensaje se escribe en Firestore con `expira_en`, una marca de tiempo a 30 días de su creación ([firestore.py](../../tecnologia/src/latam_tecnologia/banca/firestore.py)), y una política de TTL por grupo de colección los borra (módulo `firestore` de Terraform); pruebas en `tecnologia/tests/test_retencion_y_refs.py` y en la de integración contra Firestore. Límites: Firestore borra dentro de las 24 horas siguientes al vencimiento, no al instante; el plazo corre desde la creación y no se renueva con la actividad; los documentos anteriores a este cambio no llevan el campo y se limpian con el endpoint de restablecimiento. En un banco real los casos de disputa tienen plazos legales de conservación y vivirían en el sistema de registro, no en este almacén de demostración. Las tablas de BigQuery no vencen (se quitó el vencimiento del sandbox el 30 sep y el de particiones el 5 oct). Las trazas no llevan contenido y Cloud Trace las conserva 30 días por defecto. Los JSON crudos de evaluación, con conversaciones completas, quedan fuera de git y su borrado al cierre más 90 días es manual.

## 9. Seguridad

- **CSP** y cabeceras en Firebase Hosting: `default-src 'self'`, `script-src 'self'`, `frame-ancestors 'none'`, `connect-src` limitado al origen y a la API de Cloud Run, HSTS de un año, `nosniff`, `Permissions-Policy` sin cámara, micrófono ni geolocalización ([firebase.json](../../firebase.json)).
- **Guardas del repositorio**: `uv run python -m latam_gobierno.guardas` en pre-commit y CI bloquea datos del organizador y credenciales; gitleaks configurado.
- **Inyección**: el filtrado de salida por frases prohibidas (`clientes/estilo/estilo.yaml`) y la política en código limitan el daño. La evaluación congelada mostró que una orden inyectada de "escalar como urgente" se obedecía en 3 de 3 corridas ([04](04_evaluacion.md) hallazgo 2), sin filtrar datos; desde el trabajador 0.5.0 la prioridad urgente sale solo de una lista cerrada de motivos en `policy/v1` (ESC-05) y el argumento del modelo se ignora. Queda un límite declarado: un cliente que relate un engaño inventado puede obtener el motivo urgente ([04_evaluacion](04_evaluacion.md), anexo "Correcciones posteriores").
- **Secretos**: la clave de las referencias opacas vive en Secret Manager (`latam-ref-secreto`) y Cloud Run la monta como `LATAM_REF_SECRETO`, verificado en la configuración del servicio el 5 de octubre. El código ya no cae en silencio a la clave de demostración del repositorio: un servicio desplegado sin la variable no arranca ([refs.py](../../tecnologia/src/latam_tecnologia/banca/refs.py)). El despliegue del agente también entrega la clave a Agent Runtime, que antes firmaba con la de demostración la referencia del movimiento en el paquete de traspaso. El código de la consola del experto sigue como variable de entorno en texto plano, no como secreto.
- **Referencias opacas**: la API no expone identificadores internos, nombre, documento ni número completo de tarjeta.
- **Datos hacia modelos**: contenido de mensajes fuera de las trazas; el agente solo ve el oro operacional.

## 10. Trabajo pendiente antes de operar (lista honesta)

1. Aplicar el plan de Terraform ya revisado para adoptar lo desplegado; crear estado remoto (hoy es local).
2. Mover el proyecto a una organización y pasar de `latam-chat@` a Agent Identity; retirar `roles/editor` de la cuenta de Compute.
3. Mover sesiones, confirmaciones y operadores a Firestore; subir `max_instances` y repetir la evaluación con concurrencia; medir el arranque en frío.
4. Completar la retención: renovar el plazo con la actividad si la política lo pide, borrado automático de la evidencia de evaluación y prueba periódica de cumplimiento.
5. Completar el monitoreo de la sección 6 con las señales de calidad, equidad y costo por caso, y con una muestra revisada por dos personas.
6. Sustituir el código de demostración del experto por identidad individual con MFA y registro de acceso.
7. Repetir la evaluación del sistema actual con un retenido nuevo, con México y Argentina, segundo etiquetador y juez validado: los hallazgos de la evaluación congelada están corregidos, pero solo comprobados sobre casos ya conocidos.
8. Reemplazar los servicios bancarios simulados por contratos reales de un sandbox del banco, y fijar con Gobierno los umbrales provisionales (ESC-04, tiempos por prioridad de 120 a 3.600 s, las 48 horas de México).
9. Revisión de un hablante nativo de portugués y conversaciones reales en portugués; clientes brasileños si el banco los atiende.
10. Llenar la tabla de cuotas y dimensionar contra tráfico real; calcular el costo con infraestructura.
11. Verificar las 60 fuentes pendientes de [auditoria/fuentes/fuentes.yaml](../../auditoria/fuentes/fuentes.yaml) (3 verificadas y 1 con precisión); pasar el código del experto a Secret Manager.
12. Canales de WhatsApp y voz, si el alcance los incluye.
