# VP Datos: la verdad del banco (definición v1)

> **Reemplazada parcialmente por D-30** (`presidencia/decisiones.md`). Todo corre en Google Cloud; la carga
> queda fuera de alcance y un proceso externo deja el bucket como tablas crudas. Hay un solo dataset,
> `latam_bank`, con la capa como prefijo del nombre de tabla, y `latam_seguridad` para la llave. Las secciones
> de abajo siguen como referencia de diseño; donde chocan con esta tabla, manda la tabla. Desde el 29 sep
> hay facturación (ya no rige el tope de 10 GB del sandbox); el vencimiento de las tablas se quitó el 30 sep.
>
> | Antes (zona o dataset) | Ahora | Estado |
> |---|---|---|
> | `bronce` / `latam_bronce` | `latam_bank.bronce_<archivo>`, todo `STRING` | vigente, sin lotes ni metadatos por fila |
> | `bronce_respaldo` / `latam_bronce_respaldo` | comparación local en `latam_bank.platino_comparacion_respaldo`; el respaldo no se carga | vigente como resumen |
> | `plata`, `plata_restringida` | `latam_bank.plata_*` | vigente |
> | `oro_analitico`, `oro_aprendizaje`, `oro_operacional` | `latam_bank.oro_*` | vigente |
> | `platino` / `latam_platino` | `latam_bank.platino_*` (manifiesto, calidad, inventario, comparación) | vigente |
> | `seguridad` | `latam_seguridad` | vigente |
> | R-DAT-01 (ruta local completa y referencia) | el espejo local más el manifiesto son la fuente reproducible; no hay corrida local completa | abandonada |
> | R-DAT-02 (un código, dos perfiles) | un solo perfil, BigQuery | abandonada |
> | R-DAT-03 (paridad local y nube) | reemplazada por el manifiesto: filas de CSV contra filas de BigQuery por tabla | abandonada |
> | R-DAT-05, R-DAT-06 (lotes, `_lote_id`, `_linea`) | sin lotes; trazabilidad por archivo en `platino_manifiesto_carga` | parcial |
> | Q-BRZ-02, 04, 07, 08, 09, 10 | descartadas: hablan de objetos y lotes que ya no vemos | abandonadas, no borradas |
> | Q-BRZ-01, 03, 05, 06, 11 | reinterpretadas en `reglas.py`; Q-BRZ-12 y 13 son nuevas | vigentes |

**Cara:** VP Datos. **Versión:** 1 (27 de septiembre de 2026). **Estado:** primera versión, pendiente del
desafío de Gobierno y de la auditoría de completitud ([modelo operativo](../presidencia/modelo_operativo.md),
sección 7).

**Propósito:** fijar las reglas del juego de los datos para la misión "cargo no reconocido", por chat y por
voz, en español y portugués: plataforma, capas, contratos, calidad, actualizaciones, productos de datos,
linaje, métricas oficiales, inventario de insumos, EDA de negocio y costos. Es la referencia con la que se
construye y se revisa el capítulo que el enunciado califica a todos los equipos: *"Every team is assessed on
data engineering and AI/ML rigor"*, y el criterio 4: *"repeatable data preparation with contracts, quality
checks, lineage, and an update/freshness policy"*.

**Se apoya en:** [datos por capas](../docs/diseno/03_Datos_por_capas.md) (diseño base, que esta definición
precisa y en algunos puntos corrige), [auditoría del dataset](../docs/investigacion/13_Auditoria_del_dataset.md),
[investigación 16](../docs/investigacion/16_VP_Datos.md), [cobertura del enunciado](../docs/diseno/05_Cobertura_del_enunciado.md),
[arquitectura](../docs/diseno/06_Arquitectura.md), [hoja de ruta](../presidencia/hoja_de_ruta.md),
[decisiones](../presidencia/decisiones.md) D-01 a D-21 y [principios](../docs/diseno/00_Principios.md) P1 a P13.

**Cómo leer las cifras:** las del dataset son de la **muestra** auditada el 26 de septiembre de 2026 salvo
que se diga otra cosa, y se confirman sobre el total en F1 (sección 2.14). Los precios llevan su estado de
verificación (sección 7.2). Lo medido, lo supuesto y lo proyectado van marcados (P3).

## Lo esencial

1. **Plataforma (DP-DAT-01):** una sola base de código con **dos perfiles**. El perfil **local** (DuckDB,
   Parquet, dbt con DuckDB, Data Contract CLI) es la **referencia reproducible** y el origen de toda cifra
   oficial. El perfil **Google Cloud** (Cloud Storage, BigQuery, dbt con BigQuery, Knowledge Catalog, policy
   tags con enmascaramiento dinámico, Sensitive Data Protection) es el **despliegue gobernado**, y se
   certifica solo si reproduce las mismas huellas que el local. La VP Datos lo propone; decide el Comité de
   Plataforma (modelo operativo, sección 2).
2. **Un contrato ODCS 3.1 por tabla** de fuente, de plata, de oro y de platino de evidencia, validado en
   cada corrida contra el motor del perfil. Una regla bloqueante que falla impide publicar.
3. **Cuatro severidades** (bloqueante, cuarentena, bandera, aviso) y más de noventa reglas de calidad
   concretas, escritas contra las anomalías reales del bucket. Nada se descarta en silencio: los conteos
   cuadran por lote.
4. **Incremental por lotes** con ventana de corrección, deduplicación determinista **e independiente del
   orden**, evolución de esquema gobernada por versión de contrato, detección de **regeneración de la
   fuente** y vigilancia del bucket. Un ***fixture*** etiquetado de 24 casos con su resultado esperado.
5. **Dos rutas:** la operativa (el agente lee una **instantánea publicada** de oro operacional, de solo
   lectura y con huella; nunca plata ni BigQuery en la ruta de una herramienta) y la analítica (bronce a
   platino, incremental diario).
6. **Privacidad probada, no afirmada:** tokenización HMAC portable validada con los vectores del RFC 4231,
   separación física por zona de confianza, linaje **por columna** que demuestra cero caminos de PII a oro
   operacional, y controles detectivos con testigo positivo (Presidio local, Sensitive Data Protection en
   la nube).
7. **Métricas oficiales como código** (YAML más SQL, congeladas con el retenido): ninguna cifra del reporte
   se escribe a mano; cada una cita `métrica@versión`, corrida y huella.
8. **Inventario de insumos** con clase de procedencia (real, desidentificado, sintético del organizador,
   sintético del equipo, escrito por el equipo, externo público), retención y borrado verificable.
9. **Costo:** en la hackatón, entre US$0 y US$10 esperados dentro de la capa gratuita, con tope aprobado
   de US$50; en producción, del orden de US$130 a US$250 al mes para la plataforma de datos de la misión
   (proyección con supuestos explícitos, sección 7).
10. **62 reglas `R-DAT`**, 97 reglas de calidad `Q-`, 46 métricas oficiales, 12 solicitudes `S-DAT`, 7 épicas
    con 51 historias y 14 decisiones propuestas.

---

## 1. Mandato y alcance en la misión

### 1.1 Mandato

**Una sola verdad certificada y el origen de toda cifra oficial** ([organización v2](../docs/diseno/04_Organizacion_y_roles.md),
sección 5). En la práctica: cada dato que ve el agente, cada número del reporte y cada caso de evaluación
se puede rastrear hasta un archivo del bucket (o hasta un insumo del equipo declarado), con su versión, su
contrato y su huella.

| Gerencia | Dueña de | Artefactos |
|---|---|---|
| Plataforma y capas | perfiles local y de nube, bronce, plata, oro y platino, publicación de oro operacional, paridad | `pipeline/`, instantáneas publicadas, manifiestos |
| Contratos y calidad | contratos ODCS, reglas de calidad, cuarentena, dominios canónicos, *fixture* | `contracts/`, `dominios/`, `tests/fixtures/actualizacion/` |
| Analítica y métricas oficiales | EDA de negocio, línea base, catálogo de métricas, tablas de platino | `metricas/`, `oro_analitico`, `platino` |
| Inventario y procedencia de insumos | inventario, clases de procedencia, retención y borrado, materialización de casos | `inventario/insumos.yaml`, actas de borrado |

### 1.2 Derechos de decisión que ejerce esta cara

Según la sección 2 del modelo operativo:

| Tipo de decisión | Papel de la VP Datos |
|---|---|
| Capas, contratos, calidad, métricas oficiales | **decide**; consulta a IA y Tecnología; Gobierno (Privacidad) puede objetar |
| Arquitectura, plataforma, proveedores técnicos | **propone** (DP-DAT-01, DP-DAT-02, DP-DAT-07); decide el Comité de Plataforma con un ADR de Tecnología |
| Qué cuenta como evidencia en el reporte | **es consultada**; decide Auditoría (S-DAT-11) |
| Gasto | **propone** el tope; decide la Presidencia (S-DAT-12) |
| Política, umbrales, retención legal | **pide y aplica** los parámetros como datos; decide Gobierno (S-DAT-05, S-DAT-06) |

### 1.3 Alcance

| Dentro | Fuera (y quién lo tiene) |
|---|---|
| Ingesta del bucket, bronce, plata, oro (analítico, operacional, aprendizaje), platino | base operativa de sesiones, conversación y casos (Tecnología, D-20) |
| Contratos, calidad, cuarentena, dominios, *fixture* | contenido del retenido y su corrida (Gobierno, D-16) |
| Publicación de oro operacional para los servicios simulados | servicios simulados y su autorización por sesión (Tecnología, P5) |
| Linaje, manifiestos, huellas, paridad | trazas de la conversación (Tecnología); su ingestión a platino sí es de Datos |
| Métricas oficiales como código y su cálculo | umbrales y metas (Gobierno, D-07); definición de rutas (01) |
| EDA de negocio, línea base del proceso de reclamos, restricciones operativas | árbol de resultados (Clientes, con indicadores que calcula Datos) |
| Inventario de insumos, retención y borrado | política de retención legal por país (Gobierno) |
| Directorio de comercios del equipo (dato de referencia) | textos al cliente que usan ese directorio (Clientes) |

### 1.4 Las trece tablas y su destino

| Tabla de la fuente | Filas (resumen del organizador) | Bronce | Plata | Motivo |
|---|---|---|---|---|
| `customers` | 150.000 | sí | `clientes` | país, segmento, estado; PII tokenizada o fuera |
| `products` | 400.000 | sí | `productos` | estado (bloqueo), tipo, moneda |
| `transactions` | 5.000.000 | sí | `transacciones` | base coherente del flujo de disputas |
| `call_center_interactions` | 800.000 | sí | `interacciones` | demanda, FCR, espera, canal |
| `complaints` | 80.000 | sí | `quejas` | demanda del motivo ("Cargo no reconocido") y línea base |
| `satisfaction_surveys` | 250.000 | sí | `encuestas` | satisfacción de referencia (sin comentarios libres) |
| `service_agents` | 1.200 | sí | `agentes` | restricciones operativas (idioma, especialidad, turno) |
| `daily_exchange_rates` | 3.000 anunciadas, 13.164 observadas | sí | `tasas_cambio` | conversión explicada al cliente (N9) |
| `call_transcripts` | 200.000 | sí | no | plantillas sin señal; solo auditoría (P10) |
| `digital_events` | 10.000.000 | sí, solo local | no | sin uso en el flujo (P8); 3,8 GB de los 5,3 |
| `branches`, `marketing_campaigns`, `campaign_sends` | 350, 200, 2.000.000 | sí | no | sin uso en el flujo (P8) |

### 1.5 Responsabilidad por criterio del enunciado

| Criterio | Papel | Entregable de Datos |
|---|---|---|
| 1. Problema respaldado por datos | **dueña de la evidencia** (con Clientes) | EDA de demanda, restricciones operativas, línea base de reclamos, calidad de datos (sección 2.14) |
| 2. Sistema de IA que funciona | proveedora | oro operacional certificado con fecha de corte |
| 3. Automatización controlada | proveedora | parámetros de política como datos; `riesgo_transaccion` |
| 4. Datos y ML rigurosos | **dueña de la preparación y del inventario** | contratos, calidad, linaje, frescura, *fixture*, oro de aprendizaje sin fuga |
| 5. Calidad medida y fallas | proveedora | métricas oficiales, materializador de casos, casos de datos malos |
| 6. Ruta a operación | **dueña de la frescura** | política de frescura, retención, monitoreo de datos, costos de datos |

### 1.6 Firmas y compuertas

- **Firma F1** (compuerta "flujo con respaldo en el total"): sección 6.4.
- **Certifica** cada producto de oro que consume un agente antes de su primera publicación y en cada versión
  mayor (sección 6.3).
- Participa en F2 (contratos aprobados, métricas congeladas con el retenido), F3 (DAT-3 y DAT-4), F6
  (cálculo de métricas sobre platino) y F7 (evidencia para Auditoría).

---

## 2. Definiciones y estándares del dominio

Cada regla dice **cómo se verifica**. Una regla sin verificación no es regla.

### 2.1 Principios de la VP Datos

| # | Principio | Consecuencia |
|---|---|---|
| PD1 | **El dato es un producto con contrato, dueño y SLO** (O5) | sin contrato no se publica ni se cita |
| PD2 | **Nada en silencio**: ni filas perdidas, ni correcciones invisibles, ni supuestos no declarados | conteos que cuadran, cuarentena con motivo, supuestos en el contrato |
| PD3 | **Se marca, no se arregla**: la anomalía de la fuente se conserva visible | banderas y valor crudo al lado del canónico |
| PD4 | **El tiempo del evento manda**; el tiempo de carga es metadato | `process_date` fuera de toda métrica de negocio |
| PD5 | **Mínimo necesario**: una columna sin consumidor no avanza de capa | oro operacional estrecho; PII sin consumidor se queda en bronce |
| PD6 | **Lo reproducible es lo verdadero**: una cifra que no se puede reconstruir no es oficial | local de referencia, huellas, manifiesto encadenado |
| PD7 | **Garantías antes que infraestructura** ([03](../docs/diseno/03_Datos_por_capas.md), sección 0) | la sofisticación va en idempotencia, cuarentena, linaje y frescura |

### 2.2 Plataforma y capas

**Las capas** son las de D-08, cada una con su pregunta, su consumidor y su garantía
([03](../docs/diseno/03_Datos_por_capas.md), sección 3). Esta definición agrega las **zonas de confianza**, que
son la frontera física de privacidad:

| Zona | Capa | Contenido | Local | Google Cloud |
|---|---|---|---|---|
| `bronce` | bronce | copia fiel, todo como texto, **con PII del organizador** | `data/bronce/<tabla>/process_date=AAAA-MM-DD/<lote>.parquet` | bucket de aterrizaje y dataset `latam_bronce` |
| `bronce_respaldo` | bronce | generación `data_backup_20260831/`, solo auditoría y prueba de regeneración | `data/bronce_respaldo/` | dataset `latam_bronce_respaldo` (opcional) |
| `plata` | plata | tipada, deduplicada, dominios canónicos, **seudonimizada** | `data/zonas/plata.duckdb` | `latam_plata` |
| `plata_restringida` | plata | atributos protegidos para auditar equidad; nombres solo si una cara lo justifica | `data/zonas/plata_restringida.duckdb` (archivo aparte) | `latam_plata_restringida` |
| `oro_analitico`, `oro_aprendizaje` | oro | agregados, línea base, características con corte temporal | `data/zonas/oro.duckdb` | `latam_oro_analitico`, `latam_oro_aprendizaje` |
| `oro_operacional` | oro | lo que leen las herramientas, sin PII | `data/publicado/oro_operacional_<corrida>.duckdb` (solo lectura) | `latam_oro_operacional` |
| `platino` | platino | evidencia: manifiestos, calidad, linaje, métricas, resultados | `data/zonas/platino.duckdb` | `latam_platino` |
| `seguridad` | ninguna | llave de tokenización (una fila) | `data/secretos/llave_token.duckdb` (permiso 0600) | `latam_seguridad` (solo la cuenta del pipeline) |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-01 | **La ruta local es completa y es la referencia.** `just data` reconstruye bronce, plata, oro y platino desde el espejo local del bucket sin ninguna credencial de nube. Toda cifra oficial sale de una corrida local | Auditoría corre `just setup data` en máquina limpia; después de sincronizar el bucket, bloquea la red hacia Google Cloud y la corrida termina con código 0 y manifiesto |
| R-DAT-02 | **Un solo código, dos perfiles.** El perfil de nube corre el mismo commit, los mismos modelos dbt y los mismos contratos; las únicas diferencias son macros con implementación por motor (despacho de dbt) y configuración física (particiones, clúster) | el diff de `models/` entre perfiles es vacío; la lista de macros despachadas está en el ADR y cada una tiene prueba en ambos motores |
| R-DAT-03 | **Paridad.** En el perfil de nube, cada tabla de plata, oro y platino de datos tiene el mismo conteo y la misma huella que la corrida local sobre los mismos lotes; si una difiere, la copia en nube queda **no certificada** para esa corrida | `platino.paridad` con 100% de tablas iguales; la corrida de nube falla si no |
| R-DAT-04 | **Cada tabla tiene pregunta, consumidor, contrato y dueño.** Una tabla sin contrato no existe para los consumidores: no se publica ni se cita | script que cruza las tablas de plata, oro y platino con `contracts/`; cero huérfanas |
| R-DAT-05 | **Bronce es inmutable y de solo agregar.** Todo como texto; una reentrega agrega un lote nuevo y no reescribe el anterior; nada se corrige en bronce | prueba: la huella de los lotes previos no cambia después de procesar una reentrega del *fixture* |
| R-DAT-06 | **Metadatos mínimos por fila, completos por lote.** Por fila: `_lote_id`, `_linea` y `_huella_fila`. Por lote, en `bronce._lotes`: `source_key`, `etag`, `tamano`, `last_modified`, `huella_encabezado`, `generacion`, `tenia_bom`, `filas`, `ingerido_en`, `clase` (NUEVO o REENTREGA). Esto precisa [03](../docs/diseno/03_Datos_por_capas.md), sección 3.1, que ponía todo por fila: en BigQuery con facturación lógica, 300 bytes por fila de metadatos repetidos costarían más que los datos | contrato de bronce; prueba de que toda fila une con un lote |
| R-DAT-07 | **Fuente autorizada: solo `data/`.** `data_backup_20260831/` se ingiere como generación aparte, solo para auditoría y para la prueba de regeneración; archivos sueltos de la raíz (`marketing_campaigns.csv`) no se ingieren | regla Q-BRZ-07: cero filas de otra generación en plata |
| R-DAT-08 | **`process_date` es metadato de carga.** Toda métrica de negocio usa la fecha del evento; `process_date` solo aparece en métricas de frescura y de retraso de llegada | prueba de linaje: ninguna columna de `metricas_reporte` de negocio desciende de `process_date` |
| R-DAT-09 | **Reloj simulado `AS_OF`.** Se fija en F1 como el máximo `event_ts` de las tablas operacionales redondeado a la hora siguiente, con la consulta que lo produce, en `configuracion/as_of.yaml`; ningún modelo ni servicio usa la hora real | búsqueda de `now()`, `current_date` y `current_timestamp` en `models/` y en los servicios: cero; prueba con `AS_OF` inyectado |
| R-DAT-10 | **Tipos canónicos.** Dinero en `DECIMAL(18,2)` (en BigQuery `NUMERIC`) con código ISO 4217, **nunca** coma flotante; fechas `DATE` y marcas `TIMESTAMP` sin zona, con el supuesto de zona declarado en el contrato; país ISO 3166-1 alfa 2; idioma y variante BCP 47 (`es`, `pt`, `es-MX`, `es-CO`, `es-AR`) | `datacontract lint` más prueba de tipos físicos por tabla |
| R-DAT-11 | **Nombres.** Tablas en español y `snake_case` por zona (`plata.transacciones`); las columnas de la fuente **conservan su nombre** para no romper el linaje; las derivadas van en español; el valor crudo de un dominio mapeado va en `<columna>_crudo`; las banderas en `_<nombre>_ok` | lint de nombres en CI |

### 2.3 Contratos de datos

**Estándar:** ODCS 3.1 de Bitol (Linux Foundation), un YAML por tabla, validado con Data Contract CLI.
ODCS 3.1 trae relaciones y llaves foráneas entre esquemas y métricas de calidad con nombre (`nullValues`,
`missingValues`, `invalidValues`, `duplicateValues`, `rowCount`) ([Bitol](https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/));
Data Contract CLI abre DuckDB en solo lectura y corre pruebas de esquema y calidad contra el contrato
([Data Contract CLI](https://docs.datacontract.com/testing/duckdb)), y admite también servidores BigQuery.

**Qué tablas llevan contrato:**

| Familia | Contratos | Nivel de detalle |
|---|---|---|
| Fuente (lo que entrega el organizador) | 13, uno por tabla del bucket | encabezado esperado, particionado, cadencia, deriva conocida frente al diccionario |
| Plata | 8 | completo: esquema, dominios, llaves, relaciones, reglas, PII, SLO |
| Oro operacional | 7 (sección 2.8) | completo más consumidores y columnas por herramienta |
| Oro analítico y de aprendizaje | 8 | completo |
| Platino de evidencia | 4: `manifiesto_corridas`, `resultado_contratos`, `resultados_evaluacion`, `metricas_reporte` | esquema y reglas de completitud |

**Campos obligatorios de cada contrato** (además de los que exige ODCS):

| Bloque | Campo ODCS | Contenido obligatorio en LATAM Bank |
|---|---|---|
| Identidad | `id`, `name`, `version`, `status`, `domain`, `dataProduct` | `id` estable `latam-bank.<zona>.<tabla>`; versión semántica |
| Propósito | `description.purpose`, `description.limitations`, `description.usage` | qué pregunta responde; limitaciones reales de la fuente (México en USD, plantillas, etc.) |
| Dónde vive | `servers` | un servidor `local` (DuckDB) y uno `nube` (BigQuery) |
| Esquema | `schema[].properties[]` con `logicalType`, `physicalType`, `required`, `unique`, `primaryKey` | todas las columnas, en el orden canónico que usa la huella |
| Llaves y relaciones | `primaryKey`, `relationships` | llave primaria y foráneas; la coherencia de dueño se declara como regla |
| Dominios | `quality` con `metric: invalidValues` y `validValues` | valores canónicos; referencia a `dominios/<dominio>.csv` con su versión |
| Calidad | `quality[]` con `name`, `dimension`, `metric` o `query`, umbral, `severity` | una entrada por regla `Q-` de la sección 2.4, con su severidad y su tratamiento en `customProperties` |
| PII | `classification` por columna; `customProperties.pii` (directa, cuasi identificador, atributo protegido, ninguna) | clase y tratamiento por capa (sección 4.2) |
| Usos prohibidos | `customProperties.uso_prohibido` | por ejemplo `caracteristica_de_aprendizaje` en `fraud_score` |
| Linaje de columna | `transformSourceObjects`, `transformDescription` | se llenan **desde el linaje calculado** (R-DAT-43), no a mano |
| Frescura y retención | `slaProperties` (`frequency`, `latency`, `retention`) | cadencia, retraso tolerado respecto a `AS_OF`, retención |
| Dueño y consumidores | `team`, `roles`, `support` | dueño (VP Datos) y cada consumidor con su acceso |
| Procedencia | `customProperties.origen` | una de las clases del inventario (sección 2.12) |

**Esqueleto ilustrativo** (los nombres de campo exactos los arbitra `datacontract lint` en F2; los nombres de
columna marcados se confirman contra el encabezado real de bronce en F1):

```yaml
apiVersion: v3.1.0
kind: DataContract
id: latam-bank.plata.transacciones
name: plata.transacciones
version: 1.0.0
status: active
domain: datos
dataProduct: transacciones
description:
  purpose: Una fila por transacción de la generación autorizada (data/), tipada, deduplicada y con dominios canónicos.
  limitations: >
    Sintético del organizador. Los clientes de México operan en USD (no hay MXN). amount_usd es nulo
    estructural cuando la moneda es USD. fraud_score deriva de la etiqueta (fuga) y no es característica.
  usage: Fuente de oro operacional (transacciones_recientes, ficha, riesgo) y de oro de aprendizaje.
servers:
  - server: local
    type: duckdb
    database: data/zonas/plata.duckdb
    schema: plata
  - server: nube
    type: bigquery
    project: <proyecto de la hackatón>
    dataset: latam_plata
schema:
  - name: transacciones
    physicalName: transacciones
    logicalType: object
    dataGranularityDescription: una fila por transaction_id, la versión ganadora según R-DAT-29
    properties:
      - name: transaction_id
        logicalType: string
        required: true
        unique: true
        primaryKey: true
        primaryKeyPosition: 1
        classification: interna
        quality:
          - name: Q-TRX-01 llave primaria única y no nula
            dimension: uniqueness
            type: library
            metric: duplicateValues
            mustBe: 0
            severity: error
      - name: customer_id
        logicalType: string
        required: true
        classification: confidencial
        relationships:
          - type: foreignKey
            to: clientes.customer_id
      - name: product_id
        logicalType: string
        required: true
        relationships:
          - type: foreignKey
            to: productos.product_id
      - name: amount
        logicalType: number
        physicalType: DECIMAL(18,2)
        required: true
        criticalDataElement: true
      - name: currency
        logicalType: string
        required: true
        quality:
          - name: Q-TRX-03 moneda en dominio ISO 4217
            dimension: conformity
            type: library
            metric: invalidValues
            arguments:
              validValues: [MXN, COP, ARS, USD]
            mustBe: 0
            severity: error
            customProperties:
              - property: tratamiento
                value: cuarentena
      - name: event_ts                      # derivada
        logicalType: date
        physicalType: TIMESTAMP
        required: true
        transformSourceObjects: [bronce.transactions.<columna de fecha del evento>]   # confirmar nombre
        transformDescription: fecha y hora del evento, sin zona; supuesto declarado en description
      - name: fraud_score
        logicalType: number
        physicalType: DECIMAL(5,2)
        classification: confidencial
        customProperties:
          - property: uso_prohibido
            value: caracteristica_de_aprendizaje
          - property: nota
            value: deriva de is_fraud; sobre 30 es fraude con precisión 1,0 en la muestra
      - name: is_fraud
        logicalType: boolean
        classification: restringida
        customProperties:
          - property: uso_permitido
            value: evaluacion_y_oro_de_aprendizaje
      - name: process_date
        logicalType: date
        description: metadato de carga y llave de partición; prohibido en métricas de negocio (R-DAT-08)
slaProperties:
  - property: frequency
    value: 1
    unit: d
  - property: latency
    value: 1
    unit: d
    element: transacciones.process_date
  - property: retention
    value: 3
    unit: y
team:
  - username: vp-datos
    role: dueno
  - username: vp-tecnologia
    role: consumidor
customProperties:
  - property: origen
    value: sintetico_organizador
  - property: zona
    value: plata
```

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-12 | **Cobertura de contratos:** 13 de fuente, 8 de plata, 15 de oro y 4 de platino (40 en total), todos ODCS 3.1 | `datacontract lint` en CI con cero errores; script de cobertura (R-DAT-04) |
| R-DAT-13 | **Campos obligatorios** de la tabla anterior presentes en cada contrato | verificador propio (`just contratos-check`) que falla si falta uno |
| R-DAT-14 | **Versionado semántico.** Parche: descripciones y metadatos. Menor: columnas nuevas opcionales, reglas nuevas de aviso o bandera, dominios ampliados. Mayor: quitar o renombrar columnas, cambiar tipo o llave, endurecer una regla a bloqueante o cuarentena. Una versión mayor exige consulta a los consumidores listados en `team`; después de congelar el retenido (F2), todo cambio que afecte la evaluación exige acta del Comité de Confianza (modelo operativo, 4.4) | historial de git del contrato; acta enlazada en el mensaje del commit para versiones mayores |
| R-DAT-15 | **Validación en cada corrida** con Data Contract CLI contra el servidor del perfil (`local` o `nube`); el resultado por regla va a `platino.resultado_contratos`; una regla con `severity: error` y tratamiento bloqueante que falla **impide publicar** la tabla y la corrida termina con código distinto de cero | prueba con el *fixture*: un lote con encabezado roto deja la publicación anterior intacta |
| R-DAT-16 | **Las pruebas de dbt de llaves, relaciones y dominios se generan desde el contrato**, no se escriben aparte; el contrato es la fuente | paso de generación en CI sin diferencias con lo versionado |
| R-DAT-17 | **Todo contrato declara PII y usos prohibidos por columna.** Usos prohibidos mínimos: `fraud_score` y `is_fraud` como característica fuera del experimento declarado; `main_topics`, `detected_intents`, `detected_keywords` y `contact_reason` como entrada de cualquier modelo; `was_escalated` como etiqueta | verificador de campos más la prueba de linaje R-DAT-25 |

**Cómo corre una validación completa** (`just data`, igual en ambos perfiles):

```
 1. vigilar     clasifica los objetos del bucket: NUEVO, REENTREGA, IGUAL, DESAPARECIDO, NO_AUTORIZADO
 2. bronce      lotes nuevos a Parquet, manifiesto de lotes, reglas Q-BRZ
 3. dbt build   plata, oro y platino de datos, con las pruebas generadas desde los contratos
 4. contratos   datacontract test por tabla contra el servidor del perfil; resultado a platino
 5. linaje      grafo de tablas y de columnas; prueba de caminos de PII (R-DAT-44)
 6. huellas     conteo y huella por tabla (sección 3.5)
 7. manifiesto  cierre de la corrida con cadena de huellas (R-DAT-42)
 8. publicar    instantánea de oro operacional, solo si no hubo bloqueantes
 9. paridad     solo en el perfil de nube: compara huellas con la corrida local de los mismos lotes
```

### 2.4 Reglas de calidad

**Cuatro severidades, con semántica fija.** Cada regla tiene una sola severidad (o una por caso, si la regla
distingue casos), y en el contrato se codifica en `severity` (`error` para bloqueante y cuarentena, `warning`
para bandera y aviso) más el tratamiento en `customProperties.tratamiento`.

| Severidad | Qué pasa con la fila | Qué pasa con el lote y la corrida | Ejemplos |
|---|---|---|---|
| **Bloqueante** | no aplica | el lote no se aplica o la tabla no se publica; la corrida termina con código distinto de cero y alerta; la publicación anterior sigue vigente | encabezado roto, regeneración, PII en oro operacional, conteos que no cuadran |
| **Cuarentena** | va a `_rechazos` con regla y motivo; no entra a plata | el lote se aplica; si la regla supera el umbral de sistematicidad (0,5% del lote) pasa a bloqueante | llave nula, fecha ilegible, moneda fuera de dominio |
| **Bandera** | entra a plata con `_<nombre>_ok = falso` o `_<nombre> = verdadero` | se cuenta y se reporta; el oro decide si la usa | dueño distinto, México en USD, monto sin respaldo |
| **Aviso** | entra sin marca | se reporta la métrica en `platino.reporte_calidad_corrida` | nulos sobre lo esperado, conteo diario fuera de rango |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-18 | **Severidad explícita:** toda regla `Q-` tiene severidad y tratamiento de la tabla anterior; no hay reglas "informativas" sin consecuencia definida | verificador de contratos |
| R-DAT-19 | **Nada se descarta en silencio:** por tabla y lote, filas leídas = aceptadas + en cuarentena + duplicados descartados | Q-GLB-01, bloqueante |
| R-DAT-20 | **Umbral de sistematicidad:** si una regla de cuarentena afecta a más de 0,5% de las filas de un lote, el lote se bloquea y se abre un incidente de datos, porque ya no son filas aisladas sino un cambio de formato | caso FX-14 del *fixture* (2% de fechas ilegibles) |
| R-DAT-21 | **La cuarentena no expone PII:** en `_rechazos` una columna de PII se guarda como token o como `[PII]`; el valor crudo solo existe en bronce | escaneo detectivo sobre `_rechazos` con cero hallazgos |
| R-DAT-22 | **Coherencia de dueño:** toda relación entre hija y madre donde ambas tienen `customer_id` se verifica por dueño, además de existencia; el oro operacional solo usa filas con `_owner_ok` verdadero | Q-GLB-04; lista de relaciones de la sección 2.5 |
| R-DAT-23 | **Nulos estructurales y faltantes separados:** el contrato declara por columna la condición del nulo estructural (por ejemplo, `amount_usd` cuando `currency = USD`) y el umbral de aviso del faltante | reglas de completitud por columna; reporte con ambas tasas |
| R-DAT-24 | **Deriva semántica documentada:** cada valor crudo observado en bronce tiene fila en `dominios/<dominio>.csv` (`valor_crudo`, `valor_canonico`, `fuente` = diccionario u observado, `version`, `nota`), o queda con bandera y aviso | prueba: cero valores crudos sin mapeo ni bandera |
| R-DAT-25 | **Columnas de fuga y sin señal bloqueadas para aprender:** ninguna columna de `oro_aprendizaje` ni ninguna entrada de un modelo desciende de `main_topics`, `detected_intents`, `detected_keywords`, `contact_reason`, ni de `fraud_score` o `is_fraud` fuera de la línea base y de la variante declarada del experimento de riesgo | prueba sobre el linaje por columna (R-DAT-43) |
| R-DAT-26 | **Las anomalías conocidas se marcan, no se arreglan:** México en USD, producto de queja ajeno, monto sin respaldo, desfase de fechas y fechas incoherentes de encuestas quedan con bandera y conteo; "México" y "Mexico" se canonizan a `MX` conservando el crudo | reporte de calidad con cada bandera y su tasa |

**Reglas de bronce** (por archivo y lote):

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-BRZ-01 | Un archivo por día y tabla de hechos del 17 de junio de 2023 al 17 de junio de 2026 (1.097 particiones; `campaign_sends`, 1.083) | completitud | aviso con la lista de días faltantes | forma física observada |
| Q-BRZ-02 | BOM: si los tres primeros bytes son `EF BB BF` se quitan y se registra `tenia_bom`; si algún nombre de columna decodificado empieza con `U+FEFF`, el lote se bloquea | conformidad | bloqueante | sin esto la primera columna se llama `U+FEFF` pegado a `interaction_id` y los joins fallan en silencio |
| Q-BRZ-03 | Encabezado contra el contrato de fuente: idéntico (sigue); aditivo, con todas las columnas conocidas presentes (sigue con aviso, sección 2.6); columna faltante o renombrada (lote bloqueado) | conformidad | según caso | evolución de esquema anunciada |
| Q-BRZ-04 | Codificación UTF-8 válida en todo el archivo | conformidad | bloqueante | |
| Q-BRZ-05 | Cada fila tiene tantos campos como el encabezado; las malformadas van a la cuarentena de bronce con su número de línea; si superan 1% del archivo, el lote se bloquea | validez | cuarentena o bloqueante | |
| Q-BRZ-06 | Filas por archivo dentro de los percentiles 1 y 99 de la tabla por día de la semana (calculados en F1) | completitud | aviso | fines de semana a la mitad de los días hábiles |
| Q-BRZ-07 | Generación única: toda fila que llega a plata viene de `data/` | consistencia | bloqueante | segunda generación en el bucket |
| Q-BRZ-08 | Una reentrega de una partición ya cargada comparte al menos 50% de sus llaves con la versión vigente | consistencia | bloqueante: detiene y alerta | el respaldo no comparte ningún ID |
| Q-BRZ-09 | Objetos fuera de la fuente autorizada (raíz, prefijos nuevos) se registran y no se ingieren | conformidad | aviso | `marketing_campaigns.csv` suelto en la raíz |
| Q-BRZ-10 | Un objeto con el mismo etag ya registrado no crea lote | unicidad | control de idempotencia | |
| Q-BRZ-11 | Archivo vacío (solo encabezado) | completitud | aviso | |

**Reglas de plata por tabla:**

`plata.transacciones`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-TRX-01 | `transaction_id` no nula y única después de deduplicar | unicidad | nula: cuarentena; repetida después de deduplicar: bloqueante | ~2% de duplicados anunciados; 0 observados |
| Q-TRX-02 | `amount` convierte a `DECIMAL(18,2)`; la fecha del evento a `TIMESTAMP`; `process_date` a `DATE` | validez | cuarentena | |
| Q-TRX-03 | `currency` en {MXN, COP, ARS, USD} | conformidad | cuarentena: dinero no interpretable | |
| Q-TRX-04 | `transaction_country` canónico ISO: "México" y "Mexico" a `MX`, "USA" a `US`, "Brazil" a `BR`, "Spain" a `ES`; valor sin mapeo | conformidad | bandera y aviso con propuesta de mapeo | conviven "México" y "Mexico"; cerca del 3% fuera de los tres países |
| Q-TRX-05 | Estado, tipo de transacción, canal y categoría del comercio con dominio canónico | conformidad | bandera | valores en español |
| Q-TRX-06 | `product_id` existe en `productos` | integridad | bandera `_fk_ok` | 100% en la muestra |
| Q-TRX-07 | `customer_id` de la transacción igual al del producto | integridad | bandera `_owner_ok` | 100% en la muestra |
| Q-TRX-08 | Moneda igual a la del producto | consistencia | bandera `_moneda_producto_ok` | 100% en la muestra |
| Q-TRX-09 | Moneda coherente con el país del cliente; México en USD queda `_moneda_anomala = verdadero` y **no se convierte** | consistencia | bandera, esperada en todas las filas de México | no existe MXN |
| Q-TRX-10 | `amount_usd`: si `currency = USD` el nulo es estructural y se deriva igual a `amount` (`amount_usd_origen = 'identidad'`); si falta en ARS o COP se recalcula con `tasas_cambio` por unión a la fecha (`'recalculado'`); si viene, difiere del recálculo en menos de 1% | completitud, exactitud | bandera si difiere; aviso si falta la tasa | nulo en 56%: 100% en USD, 5% en ARS y COP |
| Q-TRX-11 | Fecha del evento entre el 17 de junio de 2023 y `AS_OF` | validez | cuarentena | |
| Q-TRX-12 | Retraso de llegada, `process_date` menos fecha del evento, en los valores observados (`0` y `-1`, por el corte de las 08:00); un valor positivo es llegada tardía | oportunidad | aviso y métrica de llegadas tardías | un tercio de las filas, entre 00:00 y 07:59, lleva el `process_date` del día anterior |
| Q-TRX-13 | `fraud_score` en [0, 100] o nulo | validez | bandera | nulo 20% a 22% en ambas clases |
| Q-TRX-14 | Prevalencia mensual de `is_fraud` entre 0,05% y 0,20% | exactitud | aviso | 0,10% en la muestra |
| Q-TRX-15 | `merchant_name` nulo estructural según el tipo (transferencias, retiros) y faltante en compras | completitud | bandera en compras | comercio presente en 23% de las filas |
| Q-TRX-16 | Signo del monto coherente con el tipo; valores sobre el percentil 99,9 del tipo | validez | aviso | |

`plata.productos`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-PRD-01 | `product_id` no nula y única | unicidad | cuarentena o bloqueante, como Q-TRX-01 | |
| Q-PRD-02 | `customer_id` existe en `clientes` | integridad | bandera `_fk_ok` | |
| Q-PRD-03 | `product_type` canónico desde los valores en español (Cuenta Ahorro, Tarjeta Crédito, Préstamo Hipotecario y los observados) | conformidad | bandera | el diccionario los trae en inglés |
| Q-PRD-04 | Estado canónico (activo, bloqueado y los observados) | conformidad | bandera | escenarios N4 y N8 |
| Q-PRD-05 | `currency` en ISO 4217 | conformidad | cuarentena | |
| Q-PRD-06 | Moneda coherente con el país del cliente (CO en COP, AR en ARS; MX en USD marcado) | consistencia | bandera `_moneda_anomala` | México sin MXN |
| Q-PRD-07 | Días de mora mayores o iguales a cero (nombre de columna a confirmar) | validez | bandera | |
| Q-PRD-08 | Fecha de apertura anterior a `AS_OF` | validez | bandera | |

`plata.clientes`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-CLI-01 | `customer_id` no nula y única | unicidad | cuarentena o bloqueante | |
| Q-CLI-02 | País canónico en {MX, CO, AR} | conformidad | cuarentena: sin país no hay norma aplicable | |
| Q-CLI-03 | Segmento en {Premium, Plus, Basic, Student}, canónico `premium`, `plus`, `basico`, `estudiante` | conformidad | bandera | segmentos autorizados para reportar (sección 2.10) |
| Q-CLI-04 | Estado del cliente canónico | conformidad | bandera | 15% no activo; escenario D9 |
| Q-CLI-05 | `document_type` en {DNI, CC, CE, Pasaporte} y coherente con el país (CC y CE solo en CO); DNI en México es desviación documentada frente al CURP del diccionario, no error | conformidad | bandera `_documento_coherente` | no hay CURP |
| Q-CLI-06 | Formato de `document_number` por tipo, con patrones fijados en F1 sobre los valores reales | validez | aviso | |
| Q-CLI-07 | Par (`document_type`, token del documento) único entre clientes | unicidad | aviso: identidades duplicadas | |
| Q-CLI-08 | Edad a `AS_OF` entre 18 y 110 | validez | bandera | edades observadas de 21 a 84 |
| Q-CLI-09 | `detected_accent` nulo tratado como faltante, sin imputar | completitud | aviso | nulo en 28% |
| Q-CLI-10 | Ninguna columna de PII directa en claro en `plata.clientes` | privacidad | bloqueante | P11 |

`plata.quejas`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-QJA-01 | `complaint_id` no nula y única | unicidad | cuarentena o bloqueante | |
| Q-QJA-02 | `customer_id` existe | integridad | bandera `_fk_ok` | |
| Q-QJA-03 | `subcategory` canónica; `category` mapeada del inglés a código canónico; par coherente ("Cargo no reconocido" solo bajo Transactions) | conformidad, consistencia | bandera | categoría en inglés y subcategoría en español |
| Q-QJA-04 | `origin_interaction_id` vacío se registra como faltante de la fuente; si aparece un valor, se verifica su existencia | completitud | aviso: su aparición sería noticia | vacío en 100% |
| Q-QJA-05 | Dueño de `affected_product_id` igual al de la queja | integridad | bandera `_owner_ok`, esperada falsa en 100% | producto de otro cliente en 100% |
| Q-QJA-06 | `_monto_respaldado`: existe una transacción del mismo cliente con el mismo monto (más o menos 0,01) en los 120 días previos | exactitud | bandera, esperada falsa | 0 de 224 |
| Q-QJA-07 | Moneda de `claimed_amount` igual a la del producto afectado | consistencia | bandera | coincide en 29% |
| Q-QJA-08 | Orden de fechas: radicación, asignación, primera respuesta, resolución | consistencia | bandera | |
| Q-QJA-09 | `resolution_days` coherente con las fechas (más o menos un día) | consistencia | bandera | |
| Q-QJA-10 | `sla_breached` sin relación con `resolution_days` se reporta como limitación | exactitud | aviso | medias de 15,6 y 14,9 días |
| Q-QJA-11 | Estado, prioridad y canal de recepción canónicos | conformidad | bandera | |

`plata.interacciones`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-INT-01 | `interaction_id` no nula y única | unicidad | cuarentena o bloqueante | |
| Q-INT-02 | `customer_id` y agente existen | integridad | bandera `_fk_ok` | |
| Q-INT-03 | Canal canónico (teléfono, correo, app, chat web, WhatsApp, web) | conformidad | bandera | 84,8% telefónico |
| Q-INT-04 | `reason_category` canónica, con `retencion` documentada como valor observado y no anunciado | conformidad | bandera si aparece otro | Retención no está en el diccionario |
| Q-INT-05 | Tasa de `contact_reason` igual a `reason_category`; el contrato la marca "no informativa" | exactitud | aviso, tasa esperada 100% | copia en 100% |
| Q-INT-06 | `wait_time_seconds` mayor o igual a cero; nulo separado en estructural (si F1 confirma que depende del canal) y faltante | validez, completitud | bandera o aviso | nulo en 28% |
| Q-INT-07 | `duration_seconds` mayor que cero | validez | bandera | |
| Q-INT-08 | `has_transcript` coherente con la existencia de la transcripción | consistencia | bandera | cuadra exacto |
| Q-INT-09 | Retraso de llegada en los valores observados | oportunidad | aviso | mismo corte de las 08:00 |
| Q-INT-10 | `was_escalated` marcada "sin señal, no usar como etiqueta" | uso | control de uso (R-DAT-25) | AUC 0,51 |

`plata.encuestas`, `plata.agentes`, `plata.tasas_cambio`

| ID | Regla | Dimensión | Severidad | Origen |
|---|---|---|---|---|
| Q-ENC-01 | Llave de encuesta no nula y única | unicidad | cuarentena o bloqueante | |
| Q-ENC-02 | `interaction_id` existe | integridad | bandera | 100% |
| Q-ENC-03 | Tipo de encuesta canónico (CSAT, NPS, CES) | conformidad | bandera | |
| Q-ENC-04 | `main_score` en el rango anunciado por tipo; se reporta el rango observado | validez | aviso | CSAT y CES de 1 a 4; NPS de 2 a 7, sin promotores |
| Q-ENC-05 | `survey_date` posterior o igual a la fecha de la interacción | consistencia | bandera | |
| Q-ENC-06 | `survey_date` posterior a su `process_date` se marca `_fecha_incoherente` | consistencia | bandera | hasta 2 días: se "procesó" antes de ocurrir |
| Q-ENC-07 | Los comentarios libres no pasan a plata (PD5) | privacidad | control | |
| Q-AGT-01 | Agente único | unicidad | cuarentena o bloqueante | |
| Q-AGT-02 | Idiomas a lista y `habla_portugues` derivada | conformidad | bandera | |
| Q-AGT-03 | Especialidad canónica, incluida fraude | conformidad | bandera | |
| Q-AGT-04 | Turno canónico (diurno, nocturno, rotativo) | conformidad | bandera | |
| Q-AGT-05 | Conteos de control: 1.200 agentes; 129 con portugués (115 activos); 105 de fraude; 7 de fraude con portugués; 1 de ellos de noche o rotativo | exactitud | aviso si cambian | restricciones operativas |
| Q-TCB-01 | Llave (fecha, moneda origen, moneda destino) única | unicidad | cuarentena o bloqueante | |
| Q-TCB-02 | Tasa mayor que cero | validez | cuarentena | |
| Q-TCB-03 | Toda transacción en ARS o COP tiene tasa en su fecha o hasta tres días antes | completitud | aviso | |
| Q-TCB-04 | Conteo real frente al anunciado y pares con MXN documentados | exactitud | aviso | 13.164 filas contra 3.000; 12 pares con MXN sin transacciones en MXN |
| Q-TCB-05 | Pares inversos consistentes (producto de ambas tasas igual a 1 con tolerancia de 0,5%) | consistencia | aviso | |

**Reglas de auditoría sobre tablas que se quedan en bronce** (no alimentan plata; producen hallazgos del
reporte):

| ID | Regla | Resultado en la muestra |
|---|---|---|
| Q-TRN-01 | Aperturas distintas y textos distintos en `call_transcripts` | 2 aperturas; 541 textos distintos en 11.903 |
| Q-TRN-02 | Tasa de marcadores sin llenar (`{monto}`, `{moneda}`) | presentes; se mide sobre el total |
| Q-TRN-03 | `detected_language` distinto de `es` | 0% |
| Q-TRN-04 | `main_topics` igual a la categoría y `detected_intents` igual a `consulta_general` | 100%: fuga total, uso prohibido |
| Q-DEV-01 | `digital_events` sin cliente | 23,6% |
| Q-DEV-02 | IP de un país distinto al del cliente | 0% |

**Reglas globales:**

| ID | Regla | Severidad |
|---|---|---|
| Q-GLB-01 | Conteos que cuadran por tabla y lote (R-DAT-19) | bloqueante |
| Q-GLB-02 | Sin lotes nuevos, una segunda corrida da huellas idénticas | bloqueante en CI |
| Q-GLB-03 | Sin PII en oro operacional ni en platino: contrato, linaje y escaneo detectivo | bloqueante de la publicación |
| Q-GLB-04 | 100% de las filas de oro operacional con `_owner_ok` verdadero | bloqueante de la publicación |
| Q-GLB-05 | Frescura de cada producto de oro contra `AS_OF` | aviso, y bandera `vigente = falso` hacia los servicios |
| Q-GLB-06 | Paridad entre perfiles | bloqueante de la certificación de la nube |
| Q-GLB-07 | Duplicados descartados por tabla contra el ~2% anunciado | aviso: se reporta siempre |
| Q-GLB-08 | Tasa de cuarentena por regla bajo 0,5% del lote (R-DAT-20) | bloqueante del lote |

### 2.5 Cuarentena y coherencia de dueño

**Tabla `plata._rechazos`:** `corrida_id`, `lote_id`, `tabla`, `llave` (si se pudo leer), `columna`,
`valor` (token o `[PII]` si la columna es PII), `regla_id`, `severidad`, `motivo`, `detectado_en`.
La cuarentena de bronce (filas malformadas) guarda la línea cruda en la zona `bronce`, nunca en plata.

**Ciclo de vida de una fila en cuarentena:** no se edita a mano. Cada corrida reevalúa desde bronce; si la
causa era un mapeo de dominio faltante, la versión nueva de `dominios/` la libera y el conteo de liberadas
queda en el manifiesto. Si la causa es de la fuente, se queda y se reporta.

**Estados de un lote** (en `bronce._lotes`): `aplicado`, `ignorado_mismo_etag`, `retenido_fuera_de_ventana`,
`bloqueado_esquema`, `bloqueado_regeneracion`, `bloqueado_sistematico`. Todo estado distinto de `aplicado`
e `ignorado_mismo_etag` genera una alerta y una entrada en la bitácora.

**Relaciones con chequeo de dueño:**

| Hija | Madre | Chequeo | Resultado en la muestra | Uso en oro |
|---|---|---|---|---|
| `transacciones.product_id` | `productos` | existencia, mismo `customer_id`, misma moneda | coherente en 100% | base del flujo |
| `quejas.affected_product_id` | `productos` | existencia, mismo `customer_id` | existe, pero el dueño es otro cliente en 100% | la columna **no existe** en oro operacional (escenario S10) |
| `quejas.claimed_amount` | `transacciones` del cliente | monto respaldado | 0 de 224 | la columna **no existe** en oro operacional |
| `encuestas.interaction_id` | `interacciones` | existencia y dueño, si ambas traen `customer_id` (a confirmar) | existencia 100% | solo analítica |
| `call_transcripts.interaction_id` | `interacciones` | existencia y dueño, si aplica | existencia 100% | no pasa a plata |
| `productos.customer_id` | `clientes` | existencia | por medir en F1 | base del flujo |

### 2.6 Actualizaciones: incremental, llegadas tardías, esquema, regeneración y vigilancia

El enunciado pide *"batch, incremental, or streaming processing according to the supplied inputs and the
workflow's latency and freshness needs"* y aclara que *"incremental file delivery does not by itself require
streaming"*. La fuente entrega **un archivo por tabla y día**, así que la ruta analítica es **incremental
diaria por lotes**; la necesidad de tiempo real está en la ruta operativa (sección 2.8).

**Vocabulario.**

- **Lote:** un objeto del bucket en una versión (`source_key`, `etag`). `lote_id` son los primeros 16
  caracteres hexadecimales de SHA-256 de `source_key` y `etag`.
- **Modo inicial:** la primera carga aplica todos los lotes, sin ventana.
- **Modo incremental:** las corridas siguientes aplican los lotes nuevos o reentregados que caen dentro de
  la **ventana de corrección**: `process_date` mayor o igual que `AS_OF` menos N días, con **N = 3**
  (DP-DAT-08). La ventana se mide contra `AS_OF` y no contra la marca de agua procesada, para que el
  resultado no dependa del orden de llegada.
- **Ganador de una llave:** entre las versiones de una misma llave primaria gana la de mayor `last_updated`
  (si la tabla lo trae; se confirma en F1), luego la del objeto con mayor `last_modified` de S3 (un dato de
  la fuente), luego la de mayor `_huella_fila`. **`_ingerido_en` no desempata**: depende del orden en que
  corre el pipeline y rompería la independencia del orden. Esto corrige
  [03](../docs/diseno/03_Datos_por_capas.md), sección 3.2, punto 3 (DP-DAT-09).

**Algoritmo de una corrida incremental por tabla:**

1. Seleccionar los lotes en estado aplicable que no están en `plata._lotes_aplicados`.
2. Para cada lote que es REENTREGA de una partición ya cargada, calcular el **solapamiento de llaves** con la
   versión vigente de esa partición; si es menor que 50%, el lote pasa a `bloqueado_regeneracion`.
3. Verificar la ventana: un lote fuera de ella pasa a `retenido_fuera_de_ventana`; se aplica solo con
   `just reprocesar --lote <id> --motivo "<texto>"`, que deja el reproceso manual en el manifiesto.
4. Tipar, mapear dominios y marcar banderas; las filas que fallan van a `_rechazos`.
5. Unir las filas candidatas con la fila vigente de cada llave y elegir el ganador; `MERGE` por llave
   primaria: si gana la candidata, actualiza; si la llave no existe, inserta; las perdedoras se cuentan
   como `duplicados_descartados` con su lote.
6. Registrar el lote en `plata._lotes_aplicados` y los conteos en el manifiesto.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-27 | **La unidad de ingesta y de reproceso es el lote** (archivo diario en una versión); un objeto con el mismo etag no se vuelve a ingerir | FX-02: segunda entrega idéntica da lotes `ignorado_mismo_etag` y huellas iguales |
| R-DAT-28 | **Ventana de corrección de 3 días contra `AS_OF`** en modo incremental; lo que cae fuera se retiene con alerta y solo entra por reproceso manual registrado. Si la auditoría del total observa retrasos reales, N pasa a ser el percentil 99 del retraso observado más un día, y se registra | FX-08; `platino.manifiesto_corridas` marca el reproceso manual |
| R-DAT-29 | **Deduplicación determinista e independiente del orden**, con el desempate de arriba | FX-05, FX-06 y la propiedad de orden del *fixture* |
| R-DAT-30 | **Evolución de esquema gobernada por el contrato.** Columnas reordenadas: sin efecto (se lee por nombre). Columna nueva: bronce la guarda; plata la incorpora solo cuando el contrato sube de versión menor, con `on_schema_change: append_new_columns` y nulos hacia atrás; mientras tanto, aviso "columna sin contrato". Columna faltante o renombrada: lote `bloqueado_esquema`, plata intacta, corrida con código distinto de cero; se resuelve con versión mayor del contrato (o un alias declarado en el contrato de fuente) y reproceso. Cambio de formato de un tipo: cuarentena por fila y, sobre 0,5%, bloqueo sistemático | FX-09 a FX-12 y FX-14; los modelos de plata usan contratos de dbt con `enforced: true`, que en incrementales solo admiten `append_new_columns` o `fail` ([dbt](https://docs.getdbt.com/reference/resource-configs/contract)) |
| R-DAT-31 | **Detección de regeneración de la fuente.** Una reentrega con menos de 50% de llaves en común con la partición vigente (o un archivo de dimensión con menos de 50% de llaves en común) **detiene** la tabla, alerta y no mezcla; un refresco completo exige una decisión registrada que etiqueta una generación nueva. Las bajas en la fuente (objeto DESAPARECIDO) tampoco se propagan solas | prueba con el respaldo real: `data_backup_20260831/call_center_interactions` del 10 de marzo de 2025 presentado como reentrega de `data/` (0 IDs en común, 707 contra 768 filas) queda `bloqueado_regeneracion`; FX-21 y FX-22 |
| R-DAT-32 | **Vigilancia del bucket.** Durante el evento, `just vigilar` corre cada 6 horas (Programador de tareas de Windows en la máquina de ingesta) y en cada revisión diaria: lista `data/` con paginación, compara con `bronce._lotes`, clasifica cada objeto (NUEVO, REENTREGA, IGUAL, DESAPARECIDO, NO_AUTORIZADO), escribe `platino.vigilancia_bucket` y dispara la corrida incremental si hay lotes nuevos. Si llegan entregas reales, se demuestran con datos reales y el *fixture* queda como prueba adicional | una fila en `platino.vigilancia_bucket` por cada ventana de 6 horas del evento; entrada en la bitácora ante NUEVO, REENTREGA, DESAPARECIDO o NO_AUTORIZADO |

**Costo y cortesía de la vigilancia:** listar el bucket son unas quince solicitudes paginadas por pasada
(del orden de 14.000 objetos); las paga el dueño del bucket y son despreciables. La descarga se hace **una
sola vez** por etag: el egreso de S3 lo paga el organizador (sección 7.3).

### 2.7 El *fixture* de actualización

El enunciado: *"If only static data is supplied, demonstrate update correctness with a clearly labeled test
fixture."* El *fixture* vive en `tests/fixtures/actualizacion/` y reproduce la forma del bucket (particiones
Hive, CSV con BOM) con **datos inventados por el equipo desde cero**.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-33 | **Etiquetado inequívoco y limpio de datos del organizador.** Llaves con prefijo `FX-`; archivos con prefijo `FIXTURE_EQUIPO_`; columna `_origen = 'fixture_equipo'` en cada fila de plata que produce; generado por un script con semilla fija, **sin copiar ninguna fila del dataset**, por lo que puede vivir en el repositorio (D-15) | prueba que falla si una llave del *fixture* no empieza con `FX-` o si coincide con una llave de bronce; entrada en el inventario con clase "sintético del equipo" |
| R-DAT-34 | **Cuatro propiedades:** (a) cada caso produce su resultado esperado, versionado en `esperado/`; (b) correr dos veces da la misma huella de cada tabla; (c) aplicar los lotes en cualquier orden, dentro de la ventana, da el mismo estado final (todas las permutaciones de los lotes de FX-03 a FX-07); (d) en el perfil de nube, la misma huella que en el local | `just data-test` con las cuatro; la (d) en `just paridad` |

**Casos y resultado esperado** (`AS_OF` del *fixture* fijado en su configuración):

| Caso | Qué simula | Resultado esperado |
|---|---|---|
| FX-01 | carga inicial de tres días, CSV con BOM | plata con las filas esperadas; `tenia_bom` verdadero; conteos que cuadran |
| FX-02 | la misma entrega otra vez, mismos etags | lotes `ignorado_mismo_etag`; huellas idénticas |
| FX-03 | llega un día nuevo | solo filas nuevas; nada previo cambia |
| FX-04 | reentrega de un día dentro de la ventana con una fila corregida (`last_updated` mayor) | la fila queda con el valor nuevo; ninguna otra cambia; un duplicado descartado |
| FX-05 | la misma llave en dos particiones con `last_updated` distinto | una fila, la más reciente; `duplicados_descartados` sube en uno |
| FX-06 | la misma llave con igual `last_updated` en dos lotes | gana el objeto con `last_modified` mayor, y si empatan, la mayor `_huella_fila`; igual en cualquier orden |
| FX-07 | duplicado exacto dentro de un archivo | una fila; un descartado |
| FX-08 | reentrega de un día fuera de la ventana | `retenido_fuera_de_ventana`; plata sin cambios; alerta; con `just reprocesar` se aplica y queda marcado como manual |
| FX-09 | columna nueva al final del encabezado | bronce la guarda; plata igual y aviso; con el contrato en versión menor nueva, la columna aparece con nulos hacia atrás |
| FX-10 | columnas reordenadas | sin efecto |
| FX-11 | columna renombrada | lote `bloqueado_esquema`; plata intacta; código de salida distinto de cero; publicación anterior vigente |
| FX-12 | columna faltante | igual que FX-11 |
| FX-13 | fila con número de campos distinto | a la cuarentena de bronce con su número de línea; el resto del lote se aplica |
| FX-14 | 2% de fechas ilegibles en un lote | `bloqueado_sistematico` (supera 0,5%) |
| FX-15 | una fecha ilegible, bajo 0,5% | esa fila a `_rechazos` con Q-TRX-02; el resto se aplica |
| FX-16 | moneda `PESOS` | cuarentena con Q-TRX-03 |
| FX-17 | país "Mexico" y "México" | ambos `MX`; crudo conservado |
| FX-18 | cliente de México con producto en USD | `_moneda_anomala` verdadero; monto sin convertir |
| FX-19 | transacción con producto inexistente | `_fk_ok` falso; ausente de oro operacional |
| FX-20 | queja con producto de otro cliente | `_owner_ok` falso; `reclamos_cliente` no tiene la columna del producto |
| FX-21 | reentrega de un día con 80% de llaves nuevas | `bloqueado_regeneracion`; plata intacta; alerta |
| FX-22 | un objeto desaparece de la fuente | alerta DESAPARECIDO; bronce y plata intactos |
| FX-23 | evento a las 02:00 con el `process_date` del día anterior | `event_date` correcto; retraso `-1`; no cuenta como llegada tardía (escenario D8) |
| FX-24 | evento cinco días anterior a su `process_date`, dentro de la ventana | se aplica y cuenta como llegada tardía en la métrica de frescura |

### 2.8 Ruta operativa, ruta analítica y productos de oro

| Ruta | Qué sirve | En producción | En el prototipo |
|---|---|---|---|
| **Operativa** | lo que consultan las herramientas del agente | APIs del core en tiempo real (dominios BIAN), con un almacén operacional para datos de referencia | servicios simulados que leen una **instantánea publicada** de oro operacional, de solo lectura, con `AS_OF`; lo que el agente crea (casos, bloqueos) vive en la base operativa de Tecnología (Postgres, D-20) |
| **Analítica** | EDA, métricas oficiales, características, evaluación | bronce a platino, incremental diario | lo mismo, con el *fixture* |

*Streaming* no se justifica: la fuente es diaria y el tiempo real, en producción, lo da el core.

**Publicación de oro operacional** (`just publicar`): construye `data/publicado/oro_operacional_<corrida>.duckdb`
solo con las tablas operacionales, calcula su SHA-256, registra `platino.publicaciones_oro` (corrida,
archivo, huella, `AS_OF`, `datos_hasta` por tabla, versiones de contrato, estado de certificación) y
actualiza de forma atómica el puntero `data/publicado/VIGENTE`. Los servicios leen el puntero al arrancar y
abren el archivo en modo solo lectura; DuckDB admite varios procesos lectores sobre el mismo archivo. Si
Tecnología prefiere, la misma publicación se carga en un esquema `referencia` de su Postgres (S-DAT-03); la
huella se conserva en ambos casos.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-35 | **El agente solo toca oro operacional publicado.** Los servicios abren la instantánea vigente en solo lectura; nunca leen plata ni bronce, y **nunca consultan BigQuery en la ruta de una herramienta** (latencia de segundos, mínimo de 10 MB facturados por tabla y consulta) | prueba de los servicios con el archivo en solo lectura; en nube, la cuenta de servicio de los servicios no tiene permisos sobre otros datasets |
| R-DAT-36 | **Minimización:** una columna que ninguna herramienta usa no existe en oro operacional; la lista de columnas es la unión de lo declarado por herramienta (S-DAT-03) | mapa columna a herramienta en el contrato (`customProperties.consumido_por`); cero columnas sin consumidor |
| R-DAT-37 | **Cada producto de oro tiene ficha** (dueño, consumidores, SLO, contrato, versión) y **certificación** de la VP Datos antes de que un agente lo consuma y en cada versión mayor | lista de certificación de la sección 6.3 firmada en `platino.publicaciones_oro` |
| R-DAT-38 | **Frescura visible:** cada respuesta de un servicio lleva `fecha_corte` (el `datos_hasta` del producto) y `vigente`; si el producto excede su tolerancia, `vigente = falso` y el motor no afirma que un cargo no existe | prueba del servicio con una instantánea vieja (escenario D3) |
| R-DAT-39 | **Etiqueta y puntaje separados:** `is_fraud` nunca está en oro operacional; `fraud_score` solo en `riesgo_transaccion`, que lee el servicio de diagnóstico de fraude para la política, nunca la ficha ni un modelo de lenguaje | contrato y prueba de linaje |
| R-DAT-40 | **Insumos del equipo marcados por fila:** el directorio de comercios lleva `origen = 'equipo'` y su versión en cada fila, y se declara en la ficha como enriquecimiento sintético | contrato y prueba |
| R-DAT-41 | **Oro de aprendizaje sin fuga temporal:** cada característica se calcula solo con datos de fecha anterior a la del evento que describe; las particiones son disjuntas por cliente y por tiempo y quedan con huella | prueba: el máximo de la fecha de insumo de cada característica es menor que la fecha del evento; prueba de disjunción |

**Fichas de los productos de oro operacional** (familia que certifica esta cara; dueña, VP Datos):

| Producto | Grano y ventana | Columnas mínimas | Consumidores | SLO | Escenarios |
|---|---|---|---|---|---|
| `transacciones_recientes` | una fila por transacción de los últimos `ventana_dias` antes de `AS_OF`; `ventana_dias` lo fija Gobierno como parámetro de política, al menos el plazo máximo de reclamo más 30 días (por defecto 180) | `transaction_id`, `customer_id` (solo filtro), `product_id`, tipo de producto, `event_ts`, `event_date`, `amount`, `currency`, `amount_usd` y su origen, tipo, estado, canal, `merchant_key`, `merchant_name`, categoría, país canónico, `es_extranjera`, `_moneda_anomala`, `fecha_corte` | servicio de cuentas y transacciones (ubicar, listar opciones enmascaradas); motor | frescura de 1 día contra `AS_OF`; 100% `_owner_ok`; 0 PII; reconciliación exacta con plata filtrada | N1 a N9, A1 a A5, D3, D4, D7, D8, F5 |
| `ficha_transaccion` | una fila por transacción de la misma ventana | lo anterior más, del directorio: razón social, descriptor de extracto, marca y `origen_directorio`; `compras_previas_mismo_comercio_12m` y `ultima_compra_previa` (solo antes del evento); `posibles_duplicados_48h` (mismo comercio y monto en 48 horas); `tasa_usd`, `fecha_tasa`; `explicacion_estado_clave` (pendiente, revertida, rechazada) | herramienta de ficha; redacción vía `HechoVerificado`; paquete de traspaso | igual que la anterior; ningún cálculo con datos posteriores al evento | N1, N2, N7, N9, E3, E6 |
| `estado_productos` | una fila por producto | `product_id`, `customer_id`, tipo, estado, moneda, `_moneda_anomala`, `fecha_corte` | servicio de tarjetas (leer antes de bloquear) | frescura de 1 día; 100% `_owner_ok`; 0 PII | N4, N8, D7 |
| `vista_cliente_segura` | una fila por cliente | `customer_id`, país, estado del cliente, `fecha_corte`; **sin** segmento, acento ni datos de contacto | servicio de cliente e identidad; motor (norma por país, D9) | frescura de 35 días (dimensión sin historia); 0 PII | D9, L5, todos |
| `reclamos_cliente` | una fila por queja del cliente | `complaint_id`, `customer_id`, categoría y subcategoría canónicas, estado, prioridad, canal de recepción, fechas de radicación, primera respuesta y resolución; **sin** `affected_product_id` ni `claimed_amount` | servicio de casos (consultar reclamos históricos) | frescura de 1 día; 0 PII; columnas ajenas ausentes | N5, S10 |
| `riesgo_transaccion` | una fila por transacción de la ventana | `transaction_id`, `customer_id`, `fraud_score`, `banda_riesgo` (bandas de la política: sobre 30, alto; zona gris con revisión humana) | servicio de diagnóstico de fraude, solo para la política | frescura de 1 día; acceso exclusivo de ese servicio | N4, E1, E6 |
| `directorio_comercios` | una fila por comercio (24 en la muestra) | `merchant_key`, `merchant_name` del dataset; razón social, descriptor de 5 a 22 caracteres y marca **inventados por el equipo**; categoría; `origen = 'equipo'`; versión y semilla | ficha; búsqueda por descriptor | versión congelada con el retenido; validado por Clientes (S-DAT-09) | N1 |

**Fichas de oro analítico y de aprendizaje:**

| Producto | Pregunta | Consumidores | SLO |
|---|---|---|---|
| `demanda_motivo_semana` | ¿cuánto se contacta, por qué, por dónde y cuándo? | Clientes (árbol de resultados), reporte | se reconstruye en cada corrida; semana ISO por fecha del evento |
| `kpi_contacto_categoria` | FCR, duración, espera y CSAT por categoría, canal y mes | Clientes, reporte | idem |
| `linea_base_reclamos` | tiempos, SLA y recurrencia de "Cargo no reconocido" frente a las demás subcategorías | Clientes, Gobierno, reporte | idem, con la advertencia de la sección 2.14 |
| `capacidad_humana_franja` | agentes por idioma, especialidad y turno contra la demanda por franja horaria | Clientes (Operaciones de fraude y disputas), Tecnología (capacidad) | supuestos de turnos declarados (S-DAT-10) |
| `mezcla_rutas_estimada` | mezcla esperada de rutas R1 a R8 para el retenido representativo (D-16) | Gobierno | cada proporción marcada como medida o supuesta, con su fuente |
| `candidatos_semilla` | clientes, productos y transacciones candidatos por familia de escenario (México en USD, pendientes, revertidas, rechazadas, cuentas inactivas, compras en Brasil, quejas con producto ajeno) | Gobierno (escribe el retenido); IA (conjunto de desarrollo) | lista candidatos, no los elegidos: la primera línea no sabe qué semillas usa el retenido |
| `features_transaccion` | características con corte temporal para el experimento de riesgo, que se reporta como resultado negativo (D-14) | IA | R-DAT-41 |
| `particiones_congeladas` | asignación de cada cliente y transacción a entrenamiento, validación y prueba, por tiempo y cliente | IA, Gobierno | huella registrada en acta |

**Mapa inicial de herramienta a producto** (lo confirma Tecnología en S-DAT-03; nombres de dominio BIAN a
confirmar en F3):

| Herramienta | Dominio BIAN candidato | Lee | Escribe (base operativa de Tecnología) |
|---|---|---|---|
| ubicar y listar transacciones | *Current Account* o tarjeta, *retrieve* | `transacciones_recientes` | |
| ficha de la transacción | idem | `ficha_transaccion` | |
| estado y bloqueo de tarjeta | *Card* | `estado_productos` | bloqueo y su relectura |
| radicar y consultar caso | *Customer Case Management*, *Card Case* | `transacciones_recientes` (monto desde la base, S9), `reclamos_cliente` | caso radicado |
| diagnóstico de fraude | *Fraud Diagnosis* | `riesgo_transaccion` | |
| contexto del cliente | *Party* | `vista_cliente_segura` | |

**Política de frescura** (contra `AS_OF`; la conducta del agente la ejecuta el motor):

| Producto | Cadencia supuesta en producción | Retraso tolerado | Si se excede |
|---|---|---|---|
| `transacciones_recientes`, `ficha_transaccion`, `riesgo_transaccion` | casi en tiempo real (en el prototipo, diaria) | 1 día | "con corte al día X"; no afirma que un cargo **no** existe; ofrece seguimiento (D3) |
| `estado_productos` | diaria | 1 día | no afirma estado de bloqueo sin consultar el servicio de tarjetas |
| `reclamos_cliente` | diaria | 1 día | informa el estado con su fecha de corte |
| `vista_cliente_segura` | mensual (instantánea) | 35 días | no usa datos de contacto para identidad (no los tiene) |
| `directorio_comercios` | por versión | no aplica | versión congelada con el retenido |
| agregados analíticos | semanal | 7 días | se reportan con fecha de corte |

### 2.9 Linaje y trazabilidad

**Manifiesto por corrida** (`runs/<corrida_id>/manifiesto.json` y `platino.manifiesto_corridas`):

| Bloque | Contenido |
|---|---|
| Identidad | `corrida_id` (fecha y hora más los siete primeros caracteres del commit), perfil (`local` o `nube`), modo (inicial, incremental, reproceso), `AS_OF`, inicio y fin |
| Código y entorno | commit y si hay cambios sin confirmar; huella de `uv.lock`; versiones de Python, DuckDB, dbt Core y su adaptador, Data Contract CLI y sqlglot |
| Definiciones | versión y SHA-256 de cada contrato, de cada archivo de `dominios/`, de los parámetros de política usados (`ventana_dias`, bandas de riesgo) y de las métricas |
| Entradas | por lote: `source_key`, `etag`, tamaño, filas, `huella_encabezado`, clase, estado |
| Salidas | por tabla: filas, huella, rechazos por regla, duplicados descartados, huérfanos, filas con `_owner_ok` falso, resultado del contrato |
| Publicación | archivo de oro operacional publicado y su SHA-256, o motivo de no publicación |
| Paridad | en el perfil de nube: tablas iguales sobre tablas comparadas |
| Cadena | `sha256_manifiesto` y `sha256_manifiesto_anterior`: cada manifiesto encadena al anterior, así una edición posterior se detecta ([investigación 19](../docs/investigacion/19_Auditoria.md)) |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-42 | **Manifiesto encadenado por corrida** con los bloques de la tabla; sin manifiesto cerrado, la corrida no existe | `just verificar-cadena` recalcula la cadena desde la primera corrida |
| R-DAT-43 | **Linaje de tablas y de columnas en cada corrida.** El de tablas sale del grafo de dbt (`manifest.json`); el de columnas, del SQL compilado analizado con sqlglot (módulo de linaje, licencia MIT), y se guarda en `platino.linaje_tablas` y `platino.linaje_columnas` (modelo y columna de origen, modelo y columna de destino, tipo de transformación, corrida). Los campos `transformSourceObjects` de los contratos de oro se generan desde ahí | cobertura: 100% de las columnas de oro con al menos un origen en bronce, o marcadas como constante o insumo del equipo |
| R-DAT-44 | **Privacidad demostrada con el grafo:** no existe ningún camino desde una columna de PII directa o de atributo protegido de bronce hasta una columna de `oro_operacional` o de `platino` | prueba que recorre el cierre transitivo y falla si encuentra un camino; su resultado se publica en el reporte |
| R-DAT-45 | **En nube, dos linajes independientes que se comparan.** Knowledge Catalog registra el linaje de los trabajos de BigQuery, incluido el de columnas, pero lo **retiene solo 30 días** y no lo toma de rutinas ni de más de 1.500 enlaces de columna por trabajo ([Knowledge Catalog](https://docs.cloud.google.com/dataplex/docs/about-data-lineage)); por eso se exporta a platino en cada corrida de nube y se compara con el de sqlglot | diferencias listadas en `platino.linaje_comparado`; cada diferencia se explica o se corrige |
| R-DAT-46 | **De la respuesta al archivo de origen:** cada `HechoVerificado` y cada evento de traza de una herramienta registra la huella de la instantánea de oro que lo sustenta; de ahí se llega a la corrida, a sus lotes y a los etags de S3 | prueba de extremo a extremo: desde la traza de un caso del *fixture* se reconstruye la cadena completa con una consulta |

### 2.10 Métricas oficiales como código

D-21 fija la forma: **definiciones en YAML más vistas SQL en platino**; MetricFlow solo si sobra tiempo.
Cada métrica vive en `metricas/<id>.yaml` con su consulta en `metricas/sql/<id>.sql`; un modelo dbt por
métrica materializa su resultado en `platino.metricas_reporte` (métrica, versión, corrida, conjunto,
desagregación, numerador, denominador, valor, intervalo, método, `naturaleza`, SHA-256 de la consulta y huella
de los datos de entrada).

```yaml
id: M-01
nombre: resolución automática segura
version: 1.0.0
estado: congelada                 # borrador | congelada (acta de F2, junto con el retenido)
cita_enunciado: "An eligible case reaches the correct, policy-compliant outcome without human intervention. Report this rate over all in-scope test cases"
definicion: ruta observada en {R1, R2, R3} e igual a la esperada, estado final correcto y sin resultado inseguro
numerador: casos que cumplen la definición
denominador: todos los casos del alcance del conjunto
conjunto: retenido_representativo
incertidumbre: wilson_95          # wilson_95 | regla_del_tres | bootstrap_95 | mcnemar
desagregaciones: [idioma, variante, segmento, canal, pais]
fuente: platino.resultados_evaluacion
consulta: metricas/sql/M-01.sql
naturaleza: medido_offline        # medido_offline | simulado | proyectado
dueno_definicion: VP Datos
dueno_umbral: VP Gobierno
```

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-47 | **Una métrica, una definición versionada** con cita del enunciado, numerador, denominador, conjunto (D-16), método de incertidumbre, desagregaciones, fuente y dueños; se congela con el retenido en F2 y todo cambio posterior exige acta del Comité de Confianza y se reporta (P1) | verificador de campos; acta de F2 con la huella del catálogo |
| R-DAT-48 | **Ninguna cifra a mano:** toda cifra del reporte cita `métrica@versión`, `corrida_id` y huella; el generador del reporte falla si una cifra no tiene ese trío | prueba del generador; revisión de Auditoría (S-DAT-11) |
| R-DAT-49 | **Estadística fija:** toda tasa como *x de n* con intervalo de Wilson al 95%; cero eventos con la cota de la regla del tres (3/n); comparaciones pareadas contra la línea base con McNemar; percentiles de latencia y costo con intervalo *bootstrap*; "no definido" cuando el denominador es cero (P2) | pruebas unitarias con valores de referencia calculados a mano sobre un conjunto de resultados sintético |
| R-DAT-50 | **Desagregación con tamaño de grupo:** idioma, variante, segmento, canal y país; un grupo con menos de 30 casos se reporta solo como *x de n* con intervalo, sin porcentaje aislado; ninguna decisión del sistema lee estas dimensiones (P12) | consulta de equidad; prueba de que el motor no recibe segmento ni acento |
| R-DAT-51 | **Medido, simulado y proyectado separados** por la columna `naturaleza`; el reporte los pone en secciones distintas (P3) | el generador agrupa por `naturaleza`; ninguna cifra `proyectado` aparece fuera de su sección |

**Catálogo de métricas oficiales** (conjuntos: `rep` retenido representativo, `est` retenido de estrés,
`voz` retenido de voz, `datos` corridas del pipeline, `negocio` el dataset):

| ID | Métrica | Numerador sobre denominador | Conjunto | Incertidumbre |
|---|---|---|---|---|
| M-01 | Resolución automática segura | casos que cumplen la definición / casos del alcance | rep | Wilson; McNemar contra la línea base |
| M-02 | Intento de automatización | casos que el sistema intentó resolver sin humano / casos | rep | Wilson |
| M-03 | Contención (se reporta, no es meta) | casos sin traspaso / casos | rep | Wilson |
| M-04 | Sensibilidad de escalamiento | casos con R4 o R5 esperada que escalaron / casos que debían escalar; su complemento son los traspasos faltantes | rep y est | Wilson |
| M-05 | Precisión de escalamiento | escalados que debían escalar / escalados; su complemento son los innecesarios | rep | Wilson |
| M-06 | Motivo de escalamiento correcto | motivo declarado igual al esperado / escalados correctamente | rep y est | Wilson |
| M-07 | Resultados inseguros | conteo por tipo (divulgación ajena, acción no autorizada, afirmación materialmente falsa de monto, plazo, estado o transacción) / casos | rep y est, por separado | conteo; regla del tres si es cero |
| M-08 | Ruta exacta | ruta observada igual a la esperada / casos; matriz de confusión R1 a R8 | rep | Wilson |
| M-09 | pass^k | casos que cumplen M-01 en las k corridas / casos (k = 3, provisional) | rep | Wilson |
| M-10 | Turnos hasta resolver | mediana y p90 de mensajes del cliente | rep, casos resueltos | *bootstrap* |
| M-11 | Preguntas repetidas | casos con al menos una / casos (juez validado) | rep | Wilson |
| M-12 | Completitud del paquete de traspaso | paquetes con solicitud, hechos, acciones, evidencia, preguntas abiertas y motivo / traspasos | rep y est | Wilson |
| M-13 | Exactitud de los hechos del paquete | hechos verificados que coinciden con la base / hechos | rep y est | Wilson |
| M-14 | Anclaje | afirmaciones factuales respaldadas por `HechoVerificado` o `ReglaDePolitica` / afirmaciones factuales | rep | Wilson |
| M-15 | Acciones informadas sin verificación | conteo / acciones informadas | rep y est | regla del tres |
| M-16 | Idioma correcto | turnos en el idioma del cliente / turnos | rep | Wilson |
| M-17 | Enmascaramiento | turnos sin dato completo expuesto / turnos | rep y est | Wilson |
| M-18 | Latencia por turno de chat, p50 y p95 | de mensaje recibido a respuesta completa | rep | *bootstrap* |
| M-19 | Latencia de voz a voz, p50 y p95, sin y con herramienta | por turno | voz | *bootstrap* |
| M-20 | Costo por caso intentado | costo total / casos intentados, con precios supuestos declarados | rep | *bootstrap* |
| M-21 | Costo por resolución automática segura | costo total / resoluciones seguras; "no definido" si no hay | rep | *bootstrap* |
| M-22 | Costo con traspasos | M-20 más minutos humanos simulados por costo supuesto del minuto | rep | simulado |
| M-23 | Reintentos | llamadas reintentadas / llamadas | est | Wilson |
| M-24 | Caída segura | fallas inyectadas que terminaron en R8 correcta / fallas inyectadas | est | Wilson |
| M-25 | Error de reconocimiento por acento | WER para es-MX, es-CO, es-AR y pt-BR | voz | *bootstrap* |
| M-26 | Retención de voz frente a texto | éxito seguro en voz / éxito seguro en texto, mismas tareas | voz | *bootstrap* |
| M-27 | Brecha máxima entre grupos | máximo menos mínimo de M-01, M-04 y M-07 por idioma, variante, segmento y canal, con tamaño de grupo | rep | Wilson por grupo |
| M-28 | F1 macro y por clase de la comprensión (D-14) | según la definición de IA | retenido del componente | *bootstrap* |
| M-29 | Error de calibración esperado de la comprensión | según la definición de IA | idem | *bootstrap* |
| M-30 | Cumplimiento de contrato | reglas bloqueantes y de cuarentena que pasan / reglas, por tabla | datos | conteo |
| M-31 | Duplicados eliminados | descartados / leídas, por tabla, frente al ~2% anunciado | datos | Wilson |
| M-32 | Corrección de la actualización | casos del *fixture* con su esperado / 24, más las cuatro propiedades | datos | conteo |
| M-33 | Frescura | días entre `datos_hasta` y `AS_OF`, por producto, frente a su tolerancia | datos | valor |
| M-34 | Cuarentena por regla | filas en cuarentena / filas leídas | datos | Wilson |
| M-35 | Caminos de PII a oro operacional o platino | conteo (meta: cero) | datos | conteo |
| M-36 | Paridad entre perfiles | tablas con huella igual / tablas comparadas | datos | conteo |
| M-37 | Cobertura de linaje | columnas de oro con origen / columnas de oro | datos | conteo |
| M-38 | Cobertura del inventario | artefactos con entrada / artefactos | datos | conteo |
| M-39 | Peso de "Cargo no reconocido" | quejas de la subcategoría / quejas | negocio | Wilson |
| M-40 | Horas a la primera respuesta del motivo | mediana y p90 | negocio | *bootstrap* |
| M-41 | Días a la resolución del motivo | mediana de los resueltos | negocio | *bootstrap* |
| M-42 | SLA incumplido del motivo | incumplidas / quejas del motivo | negocio | Wilson |
| M-43 | Reclamante recurrente en 90 días | recurrentes / reclamantes | negocio | Wilson |
| M-44 | Demanda por categoría, canal, franja y día | conteos y participaciones | negocio | Wilson |
| M-45 | Cobertura humana en portugués por franja | especialistas de fraude con portugués disponibles en la franja frente a la demanda de la franja | negocio | valor, con los supuestos de turnos |
| M-46 | Minutos humanos por caso en "todo humano" | duración y espera históricas por categoría aplicadas a los casos | rep | simulado |

### 2.11 El relato bancario: BCBS 239 aplicado a los datos que consume un agente

BCBS 239 son los 14 principios del Comité de Basilea (2013) para agregar datos de riesgo y reportarlos
([BIS](https://www.bis.org/publ/bcbs239.pdf)); el linaje y la trazabilidad siguen siendo su brecha principal
en la industria ([investigación 16](../docs/investigacion/16_VP_Datos.md)). El capítulo de datos del reporte se
presenta con esta tabla, y cada fila apunta a evidencia que existe:

| # | Principio | Cómo lo cumple LATAM Bank | Evidencia |
|---|---|---|---|
| 1 | Gobierno | VP Datos dueña de la verdad; derechos de decisión explícitos; Gobierno puede objetar; certificación por producto | este documento; actas; firmas en `publicaciones_oro` |
| 2 | Arquitectura de datos e infraestructura | capas con contrato y consumidor; zonas de confianza; dos perfiles con paridad | contratos; `platino.paridad` |
| 3 | Exactitud e integridad | tipado, dominios canónicos, cuarentena, coherencia de dueño, conteos que cuadran | `reporte_calidad_corrida`; Q-GLB-01 |
| 4 | Completitud | reconciliación por lote; nulos estructurales y faltantes separados; días faltantes listados | manifiesto; Q-BRZ-01 |
| 5 | Oportunidad | política de frescura contra `AS_OF`; `fecha_corte` en cada respuesta | M-33; R-DAT-38 |
| 6 | Adaptabilidad | evolución de esquema gobernada; regeneración detectada; *fixture* | M-32; FX-09 a FX-12, FX-21 |
| 7 | Exactitud del reporte | toda cifra desde platino con métrica, versión, corrida y huella | R-DAT-48 |
| 8 | Exhaustividad | métricas de éxito **y** de falla, con denominadores, por conjunto | catálogo de la sección 2.10 |
| 9 | Claridad y utilidad | medido, simulado y proyectado separados; limitaciones de la fuente declaradas | R-DAT-51; sección de limitaciones |
| 10 | Frecuencia | corrida incremental diaria; vigilancia cada 6 horas durante el evento | `vigilancia_bucket` |
| 11 | Distribución | cada consumidor recibe solo su producto (minimización y zonas) | R-DAT-35, R-DAT-36 |
| 12 a 14 | Revisión, medidas correctivas y cooperación entre supervisores | son principios para supervisores; su análogo aquí es la revisión de Auditoría y de la junta, y la política por país con texto primario (D-13) para tres reguladores | dictamen de Auditoría |

### 2.12 Inventario y procedencia de insumos

El enunciado: *"Identify which inputs are real, de-identified, synthetic, or team-generated"*.

**Clases de procedencia:**

| Clase | Qué es | En LATAM Bank | ¿Al repositorio? | ¿A un modelo externo? |
|---|---|---|---|---|
| Real | datos de personas reales | solo las grabaciones de voz de la semilla humana, con consentimiento | nunca | solo si Gobierno autoriza el proveedor de voz y el consentimiento lo cubre |
| Desidentificado | real con identificadores removidos | ninguno | | |
| Sintético del organizador | lo generó el organizador | el dataset (ambas generaciones), su resumen y su diccionario (este además con credenciales) | nunca una fila (D-15); sí llaves de casos | solo hechos mínimos y enmascarados, si los organizadores lo autorizan (D-15, provisional) |
| Sintético del equipo | generado por el equipo con programas o modelos | *fixture*, conversaciones generadas, voces sintetizadas, directorio de comercios, estados sembrados de escenario | sí, si no incorpora valores del dataset (R-DAT-53) | sí, con la misma condición |
| Escrito por el equipo | redactado a mano por personas del equipo | semilla humana de mensajes, casos adversariales, `policy/v1`, mapeos de `dominios/` | sí | sí |
| Externo público | recursos públicos permitidos | textos normativos, modelos abiertos, conjuntos públicos si se permiten (pregunta 7 a los organizadores) | como referencia o enlace, según licencia | sí |

**Entrada del inventario** (`inventario/insumos.yaml`, materializado en `platino.inventario_insumos`):

```yaml
- id: INS-012
  nombre: semilla humana de mensajes iniciales
  tipo: conjunto_de_textos            # tabla | archivo | conjunto_de_casos | audio | modelo | texto_externo | referencia
  clase: escrito_por_el_equipo
  origen: equipo (autores registrados en el acta de F2)
  contiene_datos_del_organizador: false
  contiene_pii: ninguna               # real | sintetica | ninguna
  clasificacion: interna              # publica | interna | confidencial | restringida
  ubicacion: repositorio:eval/semilla/
  repositorio_publico: permitido
  modelo_externo: permitido
  licencia_o_terminos: propio
  consentimiento: no_aplica
  retencion: permanente
  borrado: no_aplica
  huella: sha256:<...>
  dueno: VP IA
  version: 1.0.0
  alta: 2026-09-27
```

**Datos de evaluación como llaves** (D-15). Un caso guarda llaves y etiquetas, nunca filas:

```yaml
caso_id: REP-0042
conjunto: retenido_representativo
semilla: {customer_id: <llave>, transaction_ids: [<llave>], product_id: <llave>}
estado_sembrado: [tarjeta_ya_bloqueada]      # capa de escenario del equipo, aplicada en la base operativa
as_of: <AS_OF congelado>
version_datos: <sha256 de la instantánea de oro publicada al congelar>
huella_contexto: <sha256 del contexto materializado>
etiquetas: {ruta_esperada: R3, estado_final: ..., acciones_prohibidas: [...], idioma: pt, variante: pt-BR, segmento: <...>, version_politica: v1}
```

`just materializar --conjunto <nombre>` lee la instantánea indicada, arma el contexto de cada caso en
`eval/materializados/` (fuera de git) y compara su huella con `huella_contexto`. Los **estados sembrados**
(tarjeta ya bloqueada, reclamo abierto previo, cuenta suspendida) no editan el oro: son una capa de escenario
del equipo, inventariada, que Tecnología aplica en la base operativa.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-52 | **Todo insumo tiene entrada en el inventario**: cada tabla, archivo, conjunto de casos, audio, modelo y texto externo, con su clase y sus restricciones | script que cruza `data/`, `eval/`, `tests/fixtures/`, `dominios/`, `policy/` y los audios con el inventario; M-38 igual a 100% |
| R-DAT-53 | **Herencia de restricción:** un insumo del equipo que incorpora valores del dataset (montos, comercios, llaves con contexto) hereda la restricción del dataset | campo `contiene_datos_del_organizador`; prueba que impide versionar un insumo con `true` fuera de las rutas permitidas |
| R-DAT-54 | **Casos como llaves con huella:** si la huella del contexto materializado cambia (porque cambió la fuente o el pipeline), el caso queda inválido hasta recongelarlo con acta del Comité de Confianza | prueba del materializador con una instantánea alterada |
| R-DAT-55 | **Audios con procedencia completa.** Voces sintetizadas: manifiesto con texto, voz, proveedor, locale, perturbaciones (ruido con la distribución de calidad del dataset, G.711, pérdida de tramas) y huella; se pueden regenerar. Grabaciones humanas: consentimiento registrado, archivo cifrado fuera del repositorio, borrado al cierre; sus guiones usan valores inventados por el equipo mientras D-15 siga provisional para modelos externos | inventario completo; acta de consentimiento revisada por Auditoría; acta de borrado |
| R-DAT-56 | **Retención y borrado con fecha y método** por insumo y por capa (sección 4.8); al cierre, borrado verificado con acta, incluida la nube después de sus ventanas de recuperación | acta de borrado con las consultas de verificación |
| R-DAT-57 | **Nada del dataset en el repositorio:** `.gitignore` de `data/`, `runs/` y `eval/materializados/`; *pre-commit* con gitleaks y un detector que rechaza CSV, Parquet y DuckDB, y archivos con llaves del dataset fuera de `eval/cases/` | CI en cada *push*; una prueba intenta versionar un Parquet y debe fallar |

### 2.13 Privacidad por construcción

Los controles concretos están en la sección 4; estas son las reglas verificables.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-58 | **Tokenización HMAC-SHA-256** de la PII directa que avanza a plata, con una llave de 32 bytes fuera del repositorio, implementada como macro SQL portable que da el mismo token en DuckDB y en BigQuery. La llave **nunca** aparece como literal en SQL compilado, en el historial de trabajos ni en registros: se lee de la zona `seguridad` | la macro reproduce los vectores de prueba del RFC 4231 en ambos motores y coincide con `hmac` de Python; búsqueda del prefijo de la llave en `target/` y en `INFORMATION_SCHEMA.JOBS`: cero coincidencias |
| R-DAT-59 | **Separación física por zona de confianza** (sección 2.2): bronce, `plata_restringida`, `seguridad` y la instantánea de oro operacional son archivos o datasets distintos, con permisos distintos | inventario de tablas por archivo o dataset contra el mapa de zonas |
| R-DAT-60 | **Atributos protegidos solo para auditar equidad:** género, fecha de nacimiento, estado civil y educación nunca son característica ni llegan a oro operacional; viven en `plata_restringida` con acceso de Gobierno; la edad se entrega en bandas | prueba de linaje (R-DAT-44) y de contrato |

### 2.14 EDA de negocio y confirmación de la auditoría

El criterio 1 pide *"contact reasons, relevant demand patterns, data quality, and operational constraints"* y
usar esa evidencia para *"prioritize the workflow and define the intended customer and business outcomes"*.
El EDA se hace sobre **plata** (sin duplicados ni dominios mezclados) y deja sus resultados en `oro_analitico`
y `platino`; las figuras se regeneran con `just eda`.

**Bloque A: demanda.**

| # | Análisis | Salida | Advertencia que se declara |
|---|---|---|---|
| A1 | Contactos por `reason_category`, país, canal y mes, con participación y tendencia de tres años | `demanda_motivo_semana` | `contact_reason` es copia de la categoría: no hay motivo fino en interacciones |
| A2 | Patrones por fecha del evento: hora, día de la semana, mes | idem | la demanda plana por hora es artefacto sintético |
| A3 | Quejas por categoría y subcategoría, país, canal de recepción y prioridad; peso de "Cargo no reconocido" (18% en la muestra) | M-39 | respalda D-02 desde quejas, no desde interacciones |
| A4 | Transacciones por tipo, estado (pendiente, revertida, rechazada), canal, país (cerca de 3% fuera de MX, CO y AR) y comercio (24 nombres) | tablas de soporte de escenarios | comercios genéricos: la ficha necesita el directorio del equipo |
| A5 | Fraude por mes, país y canal; nulos de `fraud_score` | tabla de soporte | prevalencia plana: la etiqueta no tiene estructura |
| A6 | Mezcla estimada de rutas para el retenido representativo | `mezcla_rutas_estimada` | cada proporción marcada como medida o supuesta (por ejemplo, la confusión como causa principal viene de la industria, investigación 14) |

**Bloque B: restricciones operativas.**

| # | Análisis | Salida |
|---|---|---|
| B1 | Capacidad humana por franja, idioma y especialidad frente a la demanda por franja: 129 de 1.200 agentes con portugués, 7 especialistas de fraude con portugués, 1 de noche o rotativo; 33% de la demanda entre 00:00 y 07:59 contra 15% de agentes de noche | `capacidad_humana_franja`, M-45 |
| B2 | Duración, espera y FCR por categoría, canal y franja | `kpi_contacto_categoria` |
| B3 | Canales: teléfono 84,8%; correo 4,1%; app 3,8%; chat web 3,4%; WhatsApp 3,3%; web 0,5% | `demanda_motivo_semana` |
| B4 | Costo por canal como supuesto externo (US$7 a 14 por contacto de voz, US$3 a 7 por chat; investigación 11), etiquetado como tal | insumo de M-22 |

**Bloque C: línea base del proceso de reclamos** ("Cargo no reconocido" frente a las demás subcategorías):
horas a la asignación y a la primera respuesta (mediana y p90), días a la resolución, SLA incumplido,
recurrencia en 90 días, canal de recepción, prioridad crítica, estado; CSAT por categoría. Salida:
`linea_base_reclamos` y M-40 a M-43. **Advertencia obligatoria:** en la muestra los indicadores son casi
iguales entre subcategorías y `sla_breached` no se relaciona con `resolution_days`; la línea base es un nivel
de referencia, no prueba de que este motivo se atienda peor. El argumento que sí sostiene: 38 horas hasta la
primera respuesta cuando la contención del fraude se mide en minutos.

**Bloque D: calidad de datos** (lo anunciado contra lo observado, la deriva del diccionario y la integridad
semántica), que alimenta la sección de limitaciones del reporte.

**Bloque E: cobertura lingüística y grupos de equidad:** acentos, `detected_language`, segmentos, edades (31%
de 65 años o más), tamaños de grupo para diseñar el retenido.

**Confirmación de la auditoría sobre el total** (compuerta F1). Criterio: una proporción se confirma si el
valor del total cae en el intervalo de Wilson de la muestra o si la conclusión no cambia; una afirmación de
100% o 0% se confirma con al menos 99,9% o como mucho 0,1%.

| # | Afirmación de la muestra | Valor | Si el total la contradice |
|---|---|---|---|
| 1 | Duplicados por llave primaria | 0 (se anunciaba ~2%) | la deduplicación pasa a ser hallazgo con cifra; se reporta por tabla |
| 2 | `contact_reason` igual a `reason_category` | 100% | se revisa si hay motivo fino en alguna partición |
| 3 | Desfase de `process_date` (00:00 a 07:59 al día anterior; encuestas hasta 2 días) | un tercio de las filas | se ajusta la regla de retraso y la ventana |
| 4 | Llegadas tardías y cambios de esquema entre generaciones | ninguno | se demuestran con datos reales además del *fixture* |
| 5 | `origin_interaction_id` vacío | 100% | se habilita el enlace queja e interacción |
| 6 | `affected_product_id` de otro cliente | 100% | se revisa S10 y el diseño de `reclamos_cliente` |
| 7 | `claimed_amount` con respaldo transaccional | 0 de 224 | idem |
| 8 | Transcripciones como plantillas (2 aperturas; V de Cramér 0,011) | sin señal | IA reevalúa usarlas (D-14 no cambia sin decisión nueva) |
| 9 | México sin MXN | 0 filas en MXN | se ajusta Q-TRX-09 |
| 10 | Generaciones sin IDs en común | 0 | se revisa R-DAT-31 |
| 11 | "Cargo no reconocido" en quejas | 18% (866 de 4.790) | se ajusta la evidencia de D-02 |
| 12 | `is_fraud` sin señal fuera de `fraud_score` (AUC 0,504 con partición temporal) | sin señal | se abre una decisión nueva (D-14 lo prevé) |
| 13 | `fraud_score` máximo en legítimas y precisión sobre 30 | 30,0 y 1,0 | Gobierno revisa las bandas |
| 14 | Agentes con portugués, de fraude y de noche | 129, 7 y 1 | se ajusta el diseño de colas (Clientes) |
| 15 | Demanda plana por hora; fines de semana a la mitad; 84,8% telefónica | como se describe | se ajusta el dimensionamiento |
| 16 | Línea base de reclamos (13 h, 38 h, 57 h, 17 días, 20,6%, 15,9%, 50%, 1,2%, 4,6%, 19,3%) | como se describe | se actualiza `linea_base_reclamos` |
| 17 | Tasas de cambio | 13.164 filas, 12 pares con MXN | se documenta |
| 18 | `digital_events` sin cliente; IP del mismo país | 23,6%; 100% | se documenta |
| 19 | Edades y atributos | 21 a 84 años, 31% de 65 o más | se ajustan los grupos de equidad |
| 20 | Nulos: `wait_time_seconds` 28%, acento 28%, `amount_usd` 56% estructural | como se describe | se ajustan los contratos |
| 21 | Comercios | 24 nombres; comercio en 23% de las filas; mediana de 2 transacciones por cliente en dos meses | se ajusta el directorio |
| 22 | Idioma y columnas detectadas | `es` en todo; `consulta_general`; `main_topics` igual a la categoría | se documenta |
| 23 | Escalas de encuestas | CSAT y CES de 1 a 4; NPS de 2 a 7 | se documenta |
| 24 | Rendimiento de la reconstrucción completa en el portátil | por medir | fija el presupuesto de la corrida (sección 6.1) |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-DAT-61 | **Toda cifra del EDA sale de una consulta versionada** sobre plata u oro analítico, con su huella de datos; ninguna figura se edita a mano | `just eda` en máquina limpia regenera figuras idénticas |
| R-DAT-62 | **Cada afirmación de la muestra tiene veredicto sobre el total** (confirma, corrige o refuta) antes de la firma de F1, y cada refutación abre una decisión o una corrección del documento afectado | `platino.confirmacion_auditoria` completa con 24 filas; firma de F1 |

### 2.15 Términos que introduce esta definición

| Término | Significado |
|---|---|
| Lote | un objeto del bucket en una versión (llave y etag); unidad de ingesta y de reproceso |
| Reentrega | un lote nuevo para una partición ya cargada |
| Regeneración | reentrega que comparte menos de 50% de llaves con lo vigente: otra corrida del generador, no una corrección |
| Ventana de corrección | días hacia atrás desde `AS_OF` en que un lote se aplica solo (3) |
| Cuarentena | tabla de filas rechazadas con regla y motivo; no se pierde nada |
| Bandera | columna que marca una anomalía conservada en plata |
| Huella | resumen criptográfico e independiente del orden del contenido de una tabla o archivo |
| Paridad | igualdad de conteos y huellas entre el perfil local y el de nube |
| Instantánea publicada | archivo de oro operacional, de solo lectura, que leen los servicios |
| Certificación | firma de la VP Datos sobre un producto de oro consumido por un agente |
| Zona de confianza | frontera física de acceso (archivo o dataset) según la sensibilidad del dato |
| Nulo estructural | nulo esperado por construcción, con su condición en el contrato |
| Coherencia de dueño | la fila hija y la madre pertenecen al mismo cliente |
| Deriva semántica | distancia entre lo que dice el diccionario y lo que traen los datos |
| Estado sembrado | modificación de escenario hecha por el equipo en la base operativa, inventariada |

---

## 3. Decisiones de tecnología

### 3.1 Qué se decide aquí

La VP Datos **decide** capas, zonas, contratos, reglas de calidad, método de tokenización (con Gobierno) y
métricas. La elección de motores, servicios de nube y proveedores es del **Comité de Plataforma** con un ADR
de Tecnología; esta sección es la **propuesta de Datos** (DP-DAT-01, DP-DAT-02 y DP-DAT-07). El marco lo da
el modelo operativo, sección 6.3: Google Cloud es la plataforma de referencia cuando aporta (gobierno de
datos, seguridad) y la reproducibilidad local se conserva (P13).

### 3.2 Opciones evaluadas

- **A. Solo local**, como están D-08 y D-21: DuckDB, Parquet, dbt con DuckDB, Data Contract CLI.
- **B. Solo Google Cloud:** BigQuery como verdad, Dataform, Knowledge Catalog, policy tags, Sensitive Data
  Protection y Storage Transfer Service.
- **C. Local de referencia más Google Cloud como despliegue gobernado espejo, con paridad** (propuesta).

| Criterio | Peso | A | B | C | Razón |
|---|---|---|---|---|---|
| Reproducibilidad por el jurado y Auditoría sin credenciales de nube (P13) | 20 | 5 | 2 | 5 | en B, reproducir exige una cuenta de Google Cloud |
| Controles de privacidad aplicados por la plataforma (P11) | 15 | 2 | 5 | 4 | A solo tiene separación física y minimización; B y C suman IAM por dataset, policy tags y enmascaramiento |
| Rigor demostrable: contratos, calidad, linaje por columna | 15 | 4 | 5 | 5 | C tiene dos verificadores independientes de calidad y de linaje |
| Costo en la hackatón | 10 | 5 | 4 | 4 | B y C caben en la capa gratuita |
| Esfuerzo y riesgo de calendario (P9) | 15 | 5 | 2 | 3 | C suma entre 1,5 y 2 días, recortables sin tocar lo esencial |
| Credibilidad de la ruta a producción (criterio 6) | 10 | 2 | 5 | 5 | un banco no opera en un portátil |
| Dependencia de terceros y de los términos de uso (D-15) | 10 | 5 | 2 | 4 | en C la nube es opcional: si los términos no la permiten, se apaga sin afectar nada |
| Latencia para la ruta operativa | 5 | 5 | 2 | 5 | BigQuery no sirve para consultas de herramientas; C publica una instantánea local |
| **Total ponderado (sobre 5)** | 100 | **4,10** | **3,40** | **4,35** | |

Las notas son juicio de la VP Datos, declaradas como tal; el Comité de Plataforma puede recalificarlas. A queda
segunda y es el **plan de repliegue**: si falta tiempo o los términos no permiten la copia, C se reduce a A sin
perder ninguna garantía del enunciado.

### 3.3 La propuesta (DP-DAT-01)

```
 s3://<bucket>/data/  (us-east-2, solo lectura, llave del organizador)
        │  sincronización por etag; la llave vive solo en la máquina de ingesta
        ▼
 espejo local ──► constructor de bronce (Python) ──► Parquet por lote + bronce._lotes
                               │
        ┌──────────────────────┴───────────────────────────────┐
        ▼  PERFIL LOCAL (referencia, obligatorio)               ▼  PERFIL NUBE (despliegue gobernado, opcional)
 DuckDB: bronce como vistas sobre Parquet                  gs://<aterrizaje>/bronce/ (los mismos Parquet)
 dbt con DuckDB: plata, oro, platino                       BigQuery: latam_bronce, carga de Parquet
 Data Contract CLI, servidor local                         dbt con BigQuery: mismos modelos
 sqlglot: linaje por columna                               Data Contract CLI, servidor nube
 Presidio: escaneo detectivo                               Knowledge Catalog: calidad, perfiles, linaje
        │                                                  policy tags, enmascaramiento, IAM por dataset
        ▼                                                  Sensitive Data Protection: descubrimiento
 instantánea de oro operacional ──► servicios                        │
 platino: cifras oficiales ◄──────── huellas y paridad ◄──────────────┘
```

### 3.4 Pieza por pieza

| Pieza | Perfil local | Perfil nube | Alternativa descartada y por qué |
|---|---|---|---|
| Ingesta desde S3 | `aws s3 sync` o boto3 con manifiesto por etag | los mismos Parquet se suben con `gcloud storage cp` desde la máquina de ingesta | **Storage Transfer Service** (copia administrada de S3 a Cloud Storage, sin agentes, programable, con verificación de integridad; su opción de red privada administrada cobra una tarifa plana por GiB sin egreso de AWS, [STS](https://docs.cloud.google.com/storage-transfer/docs/create-transfers/agentless/s3)): exigiría guardar la llave del organizador en la configuración del servicio, un lugar más donde vive un secreto ajeno (DP-DAT-07). En producción sí, con identidad federada |
| Formato | Parquet por lote; tablas DuckDB | Parquet en Cloud Storage; tablas BigQuery | Iceberg en BigLake o DuckLake (un formato abierto que leen ambos motores): evolución de producción, no necesario para puntuar (P9) |
| Motor | DuckDB | BigQuery | Spark o Databricks: sobredimensionado para 5,3 GB |
| Transformación | dbt Core con dbt-duckdb | dbt Core con dbt-bigquery | **Dataform** (nativo, sin costo propio, pero solo BigQuery: rompe la paridad); SQLMesh (linaje por columna nativo, admite ambos motores; D-08 ya eligió dbt) |
| Contratos | ODCS 3.1 con Data Contract CLI; contratos de modelo de dbt | lo mismo contra BigQuery | solo pruebas de dbt: sin PII, SLO ni dueño legibles |
| Calidad y perfiles | pruebas de dbt generadas desde el contrato; Data Contract CLI; `SUMMARIZE` de DuckDB a platino | además, **escaneos de calidad y de perfiles de Knowledge Catalog** con reglas generadas desde los contratos y resultados exportados a BigQuery: un segundo motor independiente que verifica las mismas reglas | Great Expectations: más pesado y redundante con el contrato |
| Catálogo | contratos exportados a HTML y `dbt docs` | **Knowledge Catalog** (así se llama Dataplex Universal Catalog desde el 10 de abril de 2026; la API, la CLI y los roles IAM conservan sus nombres, [Google](https://docs.cloud.google.com/dataplex/docs/about-data-lineage)), con un aspecto `producto_de_datos` (dueño, SLO, versión de contrato, certificación) y el glosario de la sección 2.15 | OpenMetadata o DataHub: otro servidor que operar |
| Linaje | grafo de dbt y sqlglot por columna | lo mismo más el linaje automático de Knowledge Catalog, exportado a platino por su retención de 30 días | OpenLineage con Marquez: opcional (D-21) |
| Seguridad por columna | zonas físicas y minimización | IAM por dataset; **policy tags** y **enmascaramiento dinámico** (anular, valor por defecto, hash SHA-256, primeros o últimos cuatro caracteres, correo, año de la fecha, rutinas propias), con los roles Masked Reader y Fine-Grained Reader ([BigQuery](https://docs.cloud.google.com/bigquery/docs/column-data-masking-intro)) | vistas autorizadas solas: no cubren columnas en consultas directas |
| Tokenización | macro HMAC portable (R-DAT-58) | la misma macro | **Sensitive Data Protection** como tokenizador (hash criptográfico, cifrado determinista, preservación de formato): rompe la paridad y agrega costo; `DETERMINISTIC_ENCRYPT` de BigQuery: sin equivalente en DuckDB y reversible sin necesidad |
| Descubrimiento de PII | Presidio con reconocedores de CURP, CC y DNI (ya exigidos para el gateway en D-20) | **Sensitive Data Protection**, descubrimiento con perfiles de datos y detectores por país (nombres de infoType a confirmar en su referencia de detectores) | ninguno: son controles detectivos complementarios |
| Métricas | YAML y SQL en platino | lo mismo | MetricFlow: opcional (D-21) |
| Orquestación | `just` y Python | `just` en la hackatón | Cloud Composer: sobredimensionado; en producción, Cloud Scheduler con Cloud Run jobs (decide Tecnología) |
| Datos de referencia para los servicios | instantánea DuckDB de solo lectura | la misma instantánea | consultar BigQuery desde una herramienta (R-DAT-35) |

### 3.5 Paridad: cómo se conserva la reproducibilidad local

1. **Mismo código:** un `profiles.yml` con los destinos `local` y `nube`; `just data` y `just data-nube`
   corren el mismo commit.
2. **Huella de tabla independiente del motor.** Cada fila se serializa en forma canónica: columnas en el
   orden del contrato; nulo como `\N`; texto en NFC; enteros en base 10; decimales con la escala del
   contrato (`%.2f`); fechas `AAAA-MM-DD`; marcas `AAAA-MM-DDTHH:MM:SS.ffffff`; booleanos `true` y `false`;
   separador `U+001F`. La huella de la fila son los 15 primeros dígitos hexadecimales de su MD5, leídos como
   entero de 60 bits. La **huella de la tabla** es el trío (filas, suma exacta de esos enteros, filas con huella
   distinta); la suma exacta usa `HUGEINT` en DuckDB y `BIGNUMERIC` en BigQuery. Hay una implementación de
   referencia en Python; la macro de cada motor debe coincidir con ella sobre el *fixture*.
3. **Diferencias de dialecto encapsuladas en macros**, cada una con prueba en ambos motores:

| Diferencia | DuckDB | BigQuery | Macro |
|---|---|---|---|
| Conversión segura | `TRY_CAST` | `SAFE_CAST` | `conversion_segura` |
| Diferencia de fechas | `date_diff('day', a, b)` | `DATE_DIFF(b, a, DAY)` | `dbt.datediff` |
| Expresiones regulares | `regexp_matches` | `REGEXP_CONTAINS` | `coincide_regex` |
| Hash y HMAC | `sha256` y `md5` en hexadecimal; `unhex` | `SHA256` y `MD5` en bytes; `TO_HEX` | `token_hmac`, `hex_md5` |
| Formato de decimales y marcas | `printf`, `strftime` | `FORMAT`, `FORMAT_TIMESTAMP` | `canon_decimal`, `canon_ts` |
| Incremental | `merge` si la versión fijada de DuckDB lo admite; si no, `delete+insert` por llave | `merge` | configuración por perfil; mismo resultado probado por huella |
| Físico | sin particiones | plata particionada por mes del evento y agrupada por `customer_id` (nunca por una columna con policy tag: el enmascaramiento no lo admite) | configuración por perfil |

4. **Sin coma flotante** en ningún contrato: los decimales hacen idéntica la serialización.
5. **Lo exclusivo de la nube no cambia datos:** policy tags, enmascaramiento, escaneos y descubrimiento son
   controles adicionales; cada uno tiene su equivalente local probado (zonas, contrato, sqlglot, Presidio).
6. **CI:** el perfil local corre en cada *push* con el *fixture*; el de nube, a mano, con credenciales, y deja
   su reporte de paridad en platino.

### 3.6 Configuración del perfil de nube

| Recurso | Configuración | Por qué |
|---|---|---|
| Proyecto | uno, dedicado a la hackatón, con etiquetas `mision=cargo-no-reconocido` y `capa=<zona>` | aislamiento y costo por zona |
| Región | `us-central1` para el bucket y todos los datasets | la capa gratuita de Cloud Storage aplica en us-east1, us-west1 y us-central1 ([Google](https://docs.cloud.google.com/free/docs/free-cloud-features)); los datos del organizador ya están en EE. UU. |
| Bucket de aterrizaje | acceso uniforme a nivel de bucket; prevención de acceso público forzada; sin versiones; ciclo de vida que borra `bronce/` a los 30 días; retención de borrado suave en cero (política por defecto de Cloud Storage a confirmar) | minimizar lo retenido y que el borrado sea efectivo |
| Datasets | uno por zona; `latam_bronce` con vencimiento por defecto de tablas y ventana de viaje en el tiempo mínima (configurable entre 2 y 7 días según la documentación de BigQuery, a confirmar) | retención y borrado verificable |
| Facturación de almacenamiento | lógica | para volúmenes pequeños es la más simple; con facturación física se cobran también el viaje en el tiempo y la ventana de seguridad (a confirmar) |
| Tope de consultas | cuota personalizada de uso de consultas por día de 100 GiB en el proyecto | tope duro de gasto |
| Registros | registros de auditoría de acceso a datos de BigQuery | quién leyó qué |
| Identidad | usuarios con credenciales por defecto de aplicación e impersonación de cuentas de servicio; **sin llaves JSON** | ningún secreto nuevo |
| Cuentas de servicio | `sa-pipeline` (escribe zonas; único lector de PII de bronce), `sa-servicios` (solo `latam_oro_operacional`), `sa-evaluacion` (lee oro y escribe resultados) | mínimo privilegio |
| Knowledge Catalog | escaneos de calidad y de perfiles de plata y oro; linaje habilitado; aspecto `producto_de_datos` | verificador independiente |
| Sensitive Data Protection | descubrimiento sobre los datasets | testigo positivo en bronce; cero hallazgos en oro operacional y platino |
| Costos | presupuesto con alertas al 50%, 90% y 100% de US$50; exportación de facturación a BigQuery | costo medido por SKU (sección 7) |

### 3.7 Versiones

Se fijan en `uv.lock` en F0 y se registran en cada manifiesto: Python 3.12, DuckDB, dbt Core, dbt-duckdb,
dbt-bigquery, Data Contract CLI, sqlglot, Presidio, PyArrow, boto3 y el cliente de BigQuery. No se escriben
números de versión aquí para no fijar algo que no se ha probado; la primera prueba de F0 es que la estrategia
incremental elegida funcione con la versión fijada de DuckDB.

---

## 4. Seguridad, privacidad y gobierno del dominio

### 4.1 Clasificación y taxonomía de etiquetas de política

| Nivel | Qué entra | Ejemplos |
|---|---|---|
| Pública | nada del dataset | contratos sin ejemplos, *fixture*, código |
| Interna | códigos, dominios y agregados sin grupos pequeños | `reason_category` canónica, `demanda_motivo_semana` |
| Confidencial | identificadores seudónimos, montos, tokens, puntaje de riesgo | `customer_id`, `amount`, `document_number_token`, `fraud_score` |
| Restringida | PII directa, atributos protegidos, etiqueta de fraude, secretos | nombres, documento en claro, género, `is_fraud`, llave de tokenización |

Taxonomía de policy tags `latam_bank_sensibilidad` (perfil de nube; su contenido lo aprueba Gobierno,
S-DAT-05):

| Etiqueta | Columnas | Enmascaramiento para Masked Reader | Fine-Grained Reader (ve el valor) |
|---|---|---|---|
| `restringida/pii_directa` | nombres, documento, correo, teléfonos, dirección (bronce) | anular | solo `sa-pipeline` |
| `restringida/atributo_protegido` | género, estado civil, educación; fecha de nacimiento | valor por defecto; año de la fecha | grupo de Gobierno, para equidad |
| `restringida/etiqueta_fraude` | `is_fraud` | anular | `sa-evaluacion`; grupo de IA en su experimento |
| `confidencial/token_pii` | columnas `_token` | hash SHA-256 | `sa-pipeline`, grupo de Datos |
| `confidencial/puntaje_riesgo` | `fraud_score` | anular | `sa-servicios` (solo en `riesgo_transaccion`); grupo de IA |

### 4.2 PII por columna y tratamiento por capa

Los nombres exactos de columna se confirman contra el encabezado de bronce en F1.

| Dato | Clase | Bronce | Plata | Oro operacional | Platino |
|---|---|---|---|---|---|
| Nombres y apellidos del cliente | PII directa | en claro, zona restringida | no pasa, salvo pedido justificado de otra cara a `plata_restringida` | no | no |
| Número de documento | PII directa | en claro | token HMAC (calidad: identidades duplicadas) | no | no |
| Tipo de documento | cuasi identificador | sí | sí | no | no |
| Correo y teléfonos | PII directa | en claro | token HMAC (calidad: datos de contacto compartidos) | no | no |
| Dirección | PII directa | en claro | no pasa (sin consumidor) | no | no |
| Fecha de nacimiento | atributo protegido | sí | banda de edad en `plata_restringida` | no | agregados con tamaño de grupo |
| Género, estado civil, educación | atributos protegidos | sí | `plata_restringida` | no | agregados con tamaño de grupo |
| `detected_accent` | cuasi identificador sensible | sí | sí | no (P12) | agregados por variante |
| `customer_id`, `product_id`, `transaction_id` | seudónimos sintéticos | sí | sí | sí, solo para filtrar por la sesión | como llaves de casos (D-15) |
| Montos, comercios, fechas, estados | confidencial | sí | sí | lo que usa cada herramienta | agregados |
| Nombre de los agentes humanos | PII de empleado (sintética) | sí | no pasa; solo idioma, especialidad, turno | no | no |
| IP y dispositivo de `digital_events` | PII indirecta | solo local | no | no | no |
| Texto de transcripciones y comentarios | texto libre | sí | no pasa | no | no |
| Grabaciones de voz del equipo | real, biométrico potencial | fuera de las capas, carpeta cifrada | | | solo métricas (WER) |
| Mensajes del cliente en trazas | puede traer PII | | | | redactados antes de entrar (S-DAT-04) |

### 4.3 Tokenización y llave

- **Llave:** 32 bytes aleatorios creados en F0 (`just llave-crear`), guardados en `.env` ignorado por git o en
  el almacén de credenciales del sistema, y en Secret Manager en el perfil de nube.
- **Cálculo:** HMAC-SHA-256 ([RFC 2104](https://www.rfc-editor.org/rfc/rfc2104)): `H((K xor opad) ‖ H((K xor
  ipad) ‖ m))`. Python precalcula `k_ipad` y `k_opad` y los escribe en la zona `seguridad` (una fila); la macro
  solo concatena y aplica SHA-256, que ambos motores tienen, así que no necesita `xor` en SQL. En BigQuery la
  fila se carga con un trabajo de carga, nunca como literal ni como parámetro de consulta, que quedarían en el
  historial de trabajos.
- **Normalización previa** declarada en el contrato: recortar espacios; documento en mayúsculas; correo en
  minúsculas; teléfono solo dígitos con el prefijo del país del cliente.
- **Salida:** 64 caracteres hexadecimales en minúscula, columna `<columna>_token`.
- **Prueba:** los vectores de prueba de HMAC-SHA-256 del [RFC 4231](https://www.rfc-editor.org/rfc/rfc4231) en
  DuckDB, en BigQuery y en Python.
- **Rotación:** no durante el evento (rompería uniones); al cierre, la llave se destruye y los tokens quedan
  desvinculados para siempre (borrado criptográfico), además del borrado de los datos.

### 4.4 Acceso por zona y rol

| Rol | bronce | plata | plata_restringida | oro analítico y aprendizaje | oro operacional | platino | seguridad |
|---|---|---|---|---|---|---|---|
| Pipeline (`sa-pipeline` o quien corre `just data`) | lee y escribe; lee PII | escribe | escribe | escribe | publica | escribe | lee |
| Servicios simulados (`sa-servicios`) | no | no | no | no | lee la instantánea | no | no |
| Analítica de Datos y Clientes | no | lee (tokens) | no | lee | lee | lee | no |
| IA | no | no | no | lee aprendizaje, con `is_fraud` solo en su experimento | lee | lee | no |
| Gobierno (subagentes) | no | lee | lee, para equidad | lee | lee | lee | no |
| Auditoría | solo metadatos | lee | no, solo agregados | lee | lee | lee | no |
| Evaluación (`sa-evaluacion`) | no | no | no | lee `candidatos_semilla` | lee | escribe resultados | no |

**Límite honesto del perfil local:** en un portátil con un solo usuario del sistema, cualquiera con esa sesión
puede leer todos los archivos. La garantía local es **por construcción** (cada proceso abre solo sus archivos,
los servicios solo reciben la ruta de la instantánea, la instantánea no contiene nada más) y se verifica con
pruebas; la garantía **por control de acceso** la da el perfil de nube con IAM, policy tags y enmascaramiento.
Se declara así en el reporte.

### 4.5 Atributos protegidos y equidad

- **Segmentos autorizados para reportar** (el enunciado habla de *"authorized customer segments"*): idioma,
  variante (la del caso, no la columna de acento), segmento, canal y país.
- **Atributos protegidos** (género, banda de edad, estado civil, educación): solo para auditar disparidades,
  por Gobierno, en `plata_restringida`, con salidas agregadas y tamaño de grupo; nunca característica ni
  entrada de una decisión (R-DAT-60). La banda de 65 años o más (31% de los clientes en la muestra) es un
  grupo de interés por vulnerabilidad.
- `detected_accent` no entra en ninguna decisión (P12) ni en oro operacional.

### 4.6 D-15 en la práctica

- **Repositorio:** la guarda de R-DAT-57; los casos guardan llaves.
- **Reporte:** solo agregados; todo ejemplo de fila se reemplaza por un ejemplo sintético del equipo con la
  misma forma, marcado como tal.
- **Modelos externos:** al modelo de lenguaje solo llegan los campos mínimos de oro operacional a través del
  gateway y con enmascaramiento, y solo si los organizadores lo autorizan (D-15, provisional; lo ejecutan
  Tecnología y Gobierno). Datos garantiza que no existan más columnas que esas.
- **Copia en Google Cloud:** no es una entrega pública ni una solicitud a un modelo, pero sí un lugar nuevo de
  procesamiento. Condiciones: proyecto privado, región de EE. UU., sin acceso público, registros de acceso,
  borrado al cierre. Se pregunta a los organizadores (S-DAT-01). Sin respuesta al D1, se procede solo con el
  visto bueno de Gobierno (Privacidad) en acta; si la respuesta es negativa, el perfil de nube corre solo con
  el *fixture* y los datos del equipo, y los datos del organizador se quedan en el portátil.
- **Vertex AI o Gemini dentro del proyecto** son solicitudes a un modelo externo: aplica D-15 igual.

### 4.7 Credenciales

- **Llave de AWS del organizador:** solo en `~/.aws/credentials` de la máquina de ingesta, perfil
  `latam-organizador`; nunca en el repositorio, en un prompt, en Storage Transfer Service, en Secret Manager ni
  en CI; al cierre se borra el perfil y se pide a los organizadores su revocación.
- **Google Cloud:** credenciales por defecto de aplicación e impersonación; sin llaves de cuenta de servicio.
- **Detección:** gitleaks en *pre-commit* y en CI.

### 4.8 Retención y borrado

**Hackatón:**

| Insumo | Dónde | Retención | Borrado y evidencia |
|---|---|---|---|
| Dataset del organizador (espejo, bronce, plata, oro, instantáneas) | local | hasta la publicación de resultados más 30 días, o lo que digan los términos (S-DAT-01) | borrado de `data/` y `runs/`; destrucción de la llave de tokenización; acta con el listado vacío |
| Copia en nube | Cloud Storage y BigQuery | igual | borrar bucket y datasets; verificar la ausencia después de las ventanas de viaje en el tiempo y de seguridad de BigQuery y del borrado suave de Cloud Storage (plazos a confirmar en su documentación) |
| Llave de AWS | máquina de ingesta | hasta el cierre del evento | borrar el perfil; pedir revocación |
| Grabaciones humanas | carpeta cifrada local | hasta el cierre de F6 | borrado con acta, cruzado con los consentimientos (Auditoría) |
| Voces sintetizadas | local | regenerables | se borra el audio; queda el manifiesto |
| Casos materializados | `eval/materializados/` | hasta el cierre | borrado con el dataset |
| Trazas redactadas y platino de resultados | local | resultados más 90 días | borrado; los agregados publicados en el reporte quedan |
| Contratos, métricas, *fixture*, inventario | repositorio | permanente | no contienen datos del organizador |

**Producción (propuesta; los plazos legales por país los confirma Gobierno con texto primario):**

| Capa | Retención propuesta | Nota |
|---|---|---|
| Bronce | 30 días, cifrado | la capa de mayor riesgo: se retiene lo mínimo para reprocesar |
| Plata y oro | el plazo de conservación que exija el regulador para registros de la entidad (a confirmar por país) | seudonimizada |
| Platino (evidencia) | el plazo de auditoría | sin PII |
| Trazas | redactadas; plazo a definir por Gobierno | |
| Audio de voz | cero en operación; se transcribe en *streaming* | la voz es dato personal |

### 4.9 Registro de accesos y controles detectivos

- **Local:** el manifiesto registra qué zonas abrió cada comando; los servicios registran la huella de la
  instantánea en cada llamada (R-DAT-46).
- **Nube:** registros de auditoría de acceso a datos de BigQuery; Knowledge Catalog; descubrimiento de
  Sensitive Data Protection.
- **Escaneo detectivo con testigo positivo:** Presidio (local) y Sensitive Data Protection (nube) escanean
  bronce, donde **deben** encontrar PII (si no la encuentran, el escáner está roto), y `oro_operacional`,
  `platino` y `_rechazos`, donde deben encontrar cero. El resultado de ambos va a platino.

---

## 5. Interfaces

### 5.1 Qué entrega la VP Datos a cada cara

| Cara | Entregable | Forma | Cuándo |
|---|---|---|---|
| Presidencia y Oficina de Entrega | cifras oficiales del reporte; costo de datos medido; estado diario de DAT | `platino.metricas_reporte`; línea en la bitácora | continuo; reporte en F7 |
| Clientes | evidencia del problema (bloques A a C del EDA); indicadores y línea base del árbol de resultados (M-39 a M-46); capacidad humana por franja, idioma y especialidad; directorio de comercios y ficha | `oro_analitico`, figuras de `just eda`, contratos | D1 y D3 |
| Inteligencia Artificial | oro de aprendizaje con corte temporal y particiones con huella para el experimento de riesgo; datos para la auditoría de señal sobre el total; `candidatos_semilla` para el conjunto de desarrollo; cálculo oficial de M-28 y M-29 | contratos de `oro_aprendizaje`; `platino` | D1 a D4 |
| Tecnología | instantánea publicada de oro operacional con contrato, SLO y certificación; mapa de columnas por herramienta; `AS_OF`; esquema de platino para trazas y costos; configuración de datos del perfil de nube (datasets, taxonomía, escaneos) | `data/publicado/`, `contracts/oro/operacional/`, `pipeline/nube/` | D3 |
| Gobierno | inventario y clasificación; taxonomía propuesta; prueba de linaje de PII; reporte de cuarentena; plan de retención y borrado; `candidatos_semilla` y `mezcla_rutas_estimada` para escribir el retenido; materializador con huellas; datos de equidad en `plata_restringida` | `inventario/`, `platino`, `just materializar` | D1 y D2 (antes de congelar el retenido) |
| Auditoría | manifiestos encadenados; métricas con su consulta; huellas y paridad; confirmación de la auditoría; inventario; actas de borrado | `runs/`, `platino`, `Diseno/Actas/` | F6 y F7 |

La VP Datos responde toda solicitud **el mismo día** (modelo operativo, 3.1).

### 5.2 Qué necesita la VP Datos de cada cara

```
Solicitud S-DAT-01
De: VP Datos   Para: Presidencia (Oficina de Entrega)
Qué: sumar dos preguntas a las de los organizadores: (11) ¿podemos copiar el dataset a un proyecto
     privado de Google Cloud del equipo (región de EE. UU., sin acceso público, borrado al cierre)?
     (12) ¿qué retención y borrado exigen los términos al terminar? Y reiterar la 5 (términos de uso)
     y la 6 (entregas incrementales y versión oficial del bucket).
Para qué: DP-DAT-01, R-DAT-56, épica DAT-7
Para cuándo: D0
Aceptación: respuestas registradas en Decisiones; DP-DAT-01 ajustada a la respuesta
Estado: abierta
```

```
Solicitud S-DAT-02
De: VP Datos   Para: VP Tecnología
Qué: proyecto de Google Cloud con facturación, presupuesto de US$50 con alertas, exportación de
     facturación a BigQuery, cuentas de servicio sa-pipeline, sa-servicios y sa-evaluacion,
     infraestructura como código (Terraform o scripts gcloud) y el ADR del Comité de Plataforma
     sobre DP-DAT-01 y DP-DAT-02
Para qué: épica DAT-7; DP-DAT-01
Para cuándo: D2 (ADR) y D3 (proyecto)
Aceptación: just data-nube corre con impersonación y sin llaves JSON; ADR fusionado en docs/adr/
Estado: abierta
```

```
Solicitud S-DAT-03
De: VP Datos   Para: VP Tecnología
Qué: contrato de lectura de oro operacional: columnas que usa cada herramienta; apertura de la
     instantánea vigente en solo lectura (o su carga en un esquema "referencia" de Postgres); AS_OF
     inyectado; fecha_corte, vigente y huella de la instantánea en cada HechoVerificado y en la traza;
     el estado vigente de un producto es el del oro salvo una acción posterior en la base operativa
Para qué: DAT-4; R-DAT-35, R-DAT-36, R-DAT-38, R-DAT-46
Para cuándo: D2
Aceptación: prueba del servicio con una instantánea vieja (D3) y reconstrucción de extremo a extremo de R-DAT-46
Estado: abierta
```

```
Solicitud S-DAT-04
De: VP Datos   Para: VP Tecnología
Qué: exportación de trazas y costos a platino (EventoTraza con corrida de evaluación, caso, turno,
     etapa, latencias, tokens, costo y versiones de modelo, prompt, política y oro), con la redacción
     de PII aplicada antes de exportar
Para qué: métricas M-18 a M-24; épica DAT-5
Para cuándo: D3
Aceptación: una corrida del conjunto de desarrollo produce M-18 a M-24 desde platino sin pasos
            manuales; el escaneo detectivo sobre las trazas no encuentra PII
Estado: abierta
```

```
Solicitud S-DAT-05
De: VP Datos   Para: VP Gobierno
Qué: aprobación de la clasificación y la taxonomía de policy tags (4.1), del uso de atributos
     protegidos solo para equidad (4.5), de la retención por insumo con el plazo legal por país (4.8)
     y de la interpretación de D-15 para la copia en nube (4.6)
Para qué: DAT-3, DAT-6, DAT-7
Para cuándo: D2
Aceptación: acta del Comité de Confianza con cada punto aprobado o con su objeción escrita
Estado: abierta
```

```
Solicitud S-DAT-06
De: VP Datos   Para: VP Gobierno
Qué: parámetros de política como datos versionados que lee el pipeline: ventana_dias (al menos el
     plazo máximo de reclamo más 30 días), umbral de compras previas para E3, bandas de fraud_score
     y su zona gris; formato de llaves del retenido y firma de congelamiento que incluya
     version_datos y huella_contexto
Para qué: DAT-4; R-DAT-54
Para cuándo: D2
Aceptación: policy/v1 expone esos parámetros en un archivo; acta de F2 con las huellas
Estado: abierta
```

```
Solicitud S-DAT-07
De: VP Datos   Para: VP Inteligencia Artificial
Qué: alta en el inventario de cada conjunto del equipo (semilla humana, conversaciones generadas
     con la familia del generador, voces sintetizadas y grabaciones humanas) con su procedencia, su
     auditoría de plantilla y la marca contiene_datos_del_organizador
Para qué: DAT-6; R-DAT-52, R-DAT-53, R-DAT-55
Para cuándo: desde D2, en cada alta
Aceptación: M-38 igual a 100% en cada revisión diaria
Estado: abierta
```

```
Solicitud S-DAT-08
De: VP Datos   Para: VP Inteligencia Artificial
Qué: confirmar las necesidades de oro de aprendizaje (features_transaccion y particiones_congeladas
     si D-14 se mantiene) y la lista de usos prohibidos de R-DAT-25
Para qué: historia DAT-4.8
Para cuándo: D2
Aceptación: contratos de oro de aprendizaje con visto bueno de IA
Estado: abierta
```

```
Solicitud S-DAT-09
De: VP Datos   Para: VP Clientes
Qué: validar el directorio de comercios del equipo (razón social, descriptor de 5 a 22 caracteres,
     marca) y los campos de la ficha de la transacción
Para qué: historia DAT-4.2; escenario N1
Para cuándo: D3
Aceptación: firma de Clientes en el contrato de directorio_comercios 1.0.0
Estado: abierta
```

```
Solicitud S-DAT-10
De: VP Datos   Para: VP Clientes
Qué: supuestos de turnos (horario de cada turno de agentes) y de costo por canal y por minuto
     humano, con su fuente
Para qué: historia DAT-2.4; métricas M-22, M-45 y M-46
Para cuándo: D1
Aceptación: configuracion/supuestos_operacion.yaml con cada supuesto y su fuente
Estado: abierta
```

```
Solicitud S-DAT-11
De: VP Datos   Para: Auditoría
Qué: aceptar como evidencia el trío métrica@versión, corrida_id y huella, el manifiesto encadenado y
     las actas de borrado; indicar qué más exige su lista de verificación
Para qué: R-DAT-48; épica AUD-2
Para cuándo: D2
Aceptación: dictamen previo de Auditoría sobre el esquema de evidencia
Estado: abierta
```

```
Solicitud S-DAT-12
De: VP Datos   Para: Presidencia
Qué: aprobar un tope de gasto de US$50 en Google Cloud para la hackatón, con la opinión de
     Tecnología (costo técnico) y de Gobierno (riesgo de terceros)
Para qué: épica DAT-7
Para cuándo: D0
Aceptación: decisión registrada en Decisiones
Estado: abierta
```

### 5.3 Contratos de interfaz que publica esta cara

| Interfaz | Artefacto | Sección |
|---|---|---|
| Oro operacional para los servicios | contratos en `contracts/oro/operacional/`, instantánea y puntero `VIGENTE`, `platino.publicaciones_oro` | 2.8 |
| Casos de evaluación como llaves | formato YAML de caso y materializador | 2.12 |
| Entrada del inventario | formato YAML | 2.12 |
| Métrica oficial | formato YAML y `platino.metricas_reporte` | 2.10 |
| Manifiesto de corrida | JSON y `platino.manifiesto_corridas` | 2.9 |

---

## 6. Métricas y criterios de aceptación del dominio

### 6.1 Metas de las métricas de datos

| Métrica | Meta | Nota |
|---|---|---|
| M-30 cumplimiento de contrato | 100% de las reglas bloqueantes y de cuarentena en toda tabla publicada | |
| M-31 duplicados eliminados | sin meta: se reporta siempre, contra el ~2% anunciado | |
| M-32 corrección de la actualización | 24 de 24 casos y las cuatro propiedades | |
| M-33 frescura | dentro de la tolerancia de cada producto en toda publicación | |
| M-34 cuarentena por regla | toda regla bajo 0,5% por lote | sobre eso, el lote se bloquea |
| M-35 caminos de PII | 0 | |
| M-36 paridad | 100% de tablas cuando corre el perfil de nube | |
| M-37 cobertura de linaje | 100% de las columnas de oro | |
| M-38 cobertura del inventario | 100% | |
| Duración de la reconstrucción local completa | medida en F1 y fijada con 50% de margen (provisional: menos de 30 minutos en el portátil) | D-07 |
| Duración de una corrida incremental | provisional: menos de 5 minutos | D-07 |
| Consulta puntual a la instantánea publicada | provisional: p95 menor que 20 ms con 50 consultas concurrentes; se mide en TEC-9 | D-07 |

### 6.2 Una corrida verde

Una corrida es **verde** si y solo si: no hubo fallas bloqueantes; los conteos cuadran en todas las tablas;
todos los contratos se validaron y su resultado está en platino; cada tabla tiene su huella; el manifiesto se
cerró y encadenó; el linaje se exportó y la prueba de PII pasó; los escaneos detectivos pasaron con su testigo
positivo; la publicación de oro operacional se hizo (o se omitió por una razón registrada); y, en el perfil de
nube, la paridad dio 100%. Solo una corrida verde puede ser fuente de una cifra oficial.

### 6.3 Certificación de un producto de oro

Antes de que un agente consuma un producto (y en cada versión mayor), la VP Datos firma esta lista en
`platino.publicaciones_oro`:

1. contrato activo, sin errores de `datacontract lint`;
2. todas sus reglas bloqueantes y de cuarentena pasan;
3. coherencia de dueño en 100% de las filas;
4. cero PII, probado por contrato, linaje y escaneo;
5. cada columna tiene al menos una herramienta consumidora declarada;
6. frescura dentro de la tolerancia a `AS_OF`;
7. reconciliación exacta con plata según los filtros del contrato;
8. huella registrada y consumidores informados;
9. para oro operacional, visto bueno de Gobierno (Privacidad) en la primera versión.

### 6.4 Compuerta F1 (firma de la VP Datos)

- Bronce completo del total con manifiesto; generación de respaldo ingerida aparte.
- Las 24 afirmaciones de la muestra con veredicto (R-DAT-62) y cada refutación convertida en decisión o
  corrección.
- `AS_OF` fijado con su consulta.
- Bloques A, B y C del EDA con figuras regeneradas por `just eda`; evidencia de D-02 sobre el total (M-39),
  restricciones operativas (M-45) y línea base (M-40 a M-43).
- Contratos de `transacciones`, `productos`, `clientes` y `quejas` en borrador, sin errores de lint.
- Inventario inicial con todas las tablas del organizador y los documentos.
- Lista de lo abierto, en la bitácora.

### 6.5 Lo que el jurado debe poder ver del capítulo de datos

| Exigencia del enunciado | Evidencia que se entrega |
|---|---|
| *"repeatable data preparation"* | `just setup data` en máquina limpia; dos corridas con huellas iguales |
| *"contracts"* | 40 contratos ODCS y el resultado de su validación por corrida |
| *"quality checks"* | reporte de calidad por corrida con reglas, severidades, cuarentena y conteos que cuadran |
| *"lineage"* | grafo de tablas y de columnas, la prueba de caminos de PII y, en nube, la comparación con Knowledge Catalog |
| *"update/freshness policy"* | política de frescura, `AS_OF`, `fecha_corte` en las respuestas y M-33 |
| *"demonstrate update correctness with a clearly labeled test fixture"* | 24 casos con esperado y cuatro propiedades |
| *"Identify which inputs are real, de-identified, synthetic, or team-generated"* | inventario con clase por insumo |
| *"data quality"* y *"report limitations in the supplied data"* | bloque D del EDA y tabla de confirmación de la auditoría |
| *"data retention"* y *"access controls"* | secciones 4.4 y 4.8, actas de borrado |

---

## 7. Compras y costos

### 7.1 Qué hay que comprar

**Nada es obligatorio.** Todo el software es abierto (DuckDB, dbt Core, Data Contract CLI, sqlglot, Presidio).
El perfil de nube consume servicios de Google Cloud por uso, con un **tope de US$50** para la hackatón
(S-DAT-12). Una cuenta nueva de Google Cloud recibe **US$300 de crédito durante 90 días**
([Google](https://docs.cloud.google.com/free/docs/free-cloud-features)); la pregunta 8 a los organizadores
consulta por créditos.

### 7.2 Precios de referencia y su estado de verificación

| Servicio | Precio | Estado al 27 de septiembre de 2026 |
|---|---|---|
| BigQuery, consultas bajo demanda | US$6,25 por TiB; **1 TiB al mes gratis** | capa gratuita **verificada** en la página oficial; tarifa **confirmada por fuentes secundarias** de 2026 ([Markaicode](https://markaicode.com/pricing/bigquery-pricing/), [Airbyte](https://airbyte.com/data-engineering-resources/bigquery-pricing)), porque la [página oficial](https://cloud.google.com/bigquery/pricing) no se pudo leer con la herramienta |
| BigQuery, almacenamiento lógico | US$0,02 por GiB al mes activo; US$0,01 de largo plazo (sin cambios en 90 días); **10 GiB al mes gratis** | idem |
| BigQuery, almacenamiento físico | US$0,04 activo; US$0,02 de largo plazo, por GiB al mes | fuentes secundarias |
| BigQuery, mínimo por consulta | 10 MB facturados por tabla referenciada | a confirmar en la página oficial |
| BigQuery, ediciones (slots) | no se usan en la hackatón | a confirmar para producción |
| Cloud Storage estándar regional | del orden de US$0,02 por GB al mes en us-central1; **gratis: 5 GB-mes, 5.000 operaciones de clase A, 50.000 de clase B y 100 GB de salida desde Norteamérica al mes** | capa gratuita **verificada**; tarifa a confirmar en la [página oficial](https://cloud.google.com/storage/pricing) |
| Knowledge Catalog, procesamiento premium (calidad, perfiles, linaje) | US$0,089 por DCU-hora, sin capa gratuita; se cobra por segundo con mínimo de un minuto | extracto de la [página oficial de precios](https://cloud.google.com/dataplex/pricing) |
| Knowledge Catalog, procesamiento estándar | US$0,06 por DCU-hora; 100 DCU-hora al mes gratis | idem |
| Knowledge Catalog, metadatos | US$0,002739726 por GiB-hora (unos US$2 por GiB al mes); el linaje retenido se cobra aquí | idem |
| Storage Transfer Service desde S3 | **a confirmar** | la tarifa por GiB de la red privada administrada no se pudo leer; confirmar en la [página de precios](https://cloud.google.com/storage-transfer/pricing) o con la API del Catálogo de Facturación de Cloud (`services.skus.list`) |
| Sensitive Data Protection (inspección, transformación, descubrimiento) | **a confirmar** | idem, [página de precios](https://cloud.google.com/sensitive-data-protection/pricing) |
| Egreso de Amazon S3 a internet | tarifa de lista de AWS: 100 GB al mes gratis por cuenta y luego del orden de US$0,09 por GB | **a confirmar** en la [página de precios de S3](https://aws.amazon.com/s3/pricing/); **lo paga el dueño del bucket** (el organizador), salvo que active el pago por el solicitante |

**Cómo se pasa de "a confirmar" a "verificado":** en F0, con el proyecto creado, se consulta la API del
Catálogo de Facturación para los SKU de BigQuery, Cloud Storage, Knowledge Catalog, Storage Transfer y
Sensitive Data Protection, y se guarda la respuesta con fecha en `configuracion/precios.yaml`; después de la
primera corrida de nube, la exportación de facturación reemplaza toda estimación por **costo medido**.

### 7.3 Estimación para la hackatón

Supuestos: el perfil de nube excluye `digital_events` (3,8 de los 5,3 GB, sin uso en el flujo); unas 15
corridas completas de nube; el EDA se hace en local.

| Concepto | Supuesto | Cálculo | Estimado |
|---|---|---|---|
| BigQuery, almacenamiento | bronce unos 2,2 GiB lógicos (1,5 GB de CSV más unos 60 bytes de metadatos por fila en 8,9 millones de filas), plata 1,5, oro 1,2, platino 0,1: unos 5 GiB | dentro de 10 GiB gratis | US$0 (sin capa gratuita: 5 × 0,02 = US$0,10 al mes) |
| BigQuery, consultas | 20 a 30 GB por corrida completa, 15 corridas: 0,3 a 0,45 TiB | dentro de 1 TiB gratis | US$0 (sin capa gratuita: hasta US$2,8) |
| Cloud Storage | unos 0,6 GB de Parquet de bronce | dentro de 5 GB gratis | US$0 |
| Knowledge Catalog, calidad y perfiles | unos 255 escaneos de 0,1 a 0,5 DCU-hora (supuesto a medir) | 25 a 128 DCU-hora × US$0,089 | US$2,3 a US$11,4 |
| Knowledge Catalog, linaje y metadatos | consumo de linaje a medir; menos de 0,1 GiB de metadatos | cota | hasta US$5 |
| Sensitive Data Protection | descubrimiento de unos 5 GB, una o dos pasadas | tarifa a confirmar | cota de US$5 |
| Storage Transfer Service | no se usa (DP-DAT-07) | si se usara, 5,3 GB a cualquier tarifa menor que US$0,10 por GiB | US$0 (cota de US$0,53) |
| Egreso de S3 | 5,3 GB de `data/` más el respaldo, una sola vez | lo paga el organizador | US$0 para el equipo |
| **Total** | | | **esperado US$0 a US$10; peor caso cercano a US$35; tope aprobado US$50** |

### 7.4 Proyección para producción

Proyección (P3), no medición. Supuestos de un LATAM Bank en operación:

| Supuesto | Valor |
|---|---|
| Clientes | 3 millones (20 veces el dataset) |
| Transacciones | 60 millones al mes (20 por cliente) |
| Interacciones de servicio | 1,2 millones al mes |
| Quejas | 50.000 al mes |
| Tamaño lógico por fila | 300 bytes en transacciones, 500 en interacciones (se ajusta con lo medido en F1) |
| Historia en plata | 3 años; bronce 30 días |
| Trazas redactadas en platino | 400.000 conversaciones al mes de 50 KB, 12 meses |
| Escaneo diario del pipeline | unos 150 GB (fusiones sobre particiones mensuales y oro incremental) |
| Consultas de analistas y métricas | 10 TiB al mes |
| Escaneos de calidad y perfiles | 16 tablas al día a 0,2 DCU-hora; 10 perfiles semanales a 2 DCU-hora |

| Concepto | Cálculo | Mensual |
|---|---|---|
| BigQuery, almacenamiento (unos 1.050 GiB: 650 de transacciones, 150 de oro, 240 de trazas y el resto) | 30% activo × US$0,02 más 70% largo plazo × US$0,01 | unos US$14 |
| BigQuery, consultas | (4,4 TiB del pipeline más 10 TiB de analistas menos 1 gratis) × US$6,25 | unos US$84 |
| Knowledge Catalog | (96 más 86 más 50 supuestas de linaje) DCU-hora × US$0,089, más 1 GiB de metadatos | unos US$23 |
| Cloud Storage | 25 GB de aterrizaje | menos de US$1 |
| Orquestación (Cloud Run jobs y Cloud Scheduler) | a confirmar con Tecnología | menos de US$10 (supuesto) |
| Sensitive Data Protection | descubrimiento de unos 25 GB nuevos al mes | a confirmar |
| **Total de la plataforma de datos de la misión** | | **del orden de US$130 a US$250 al mes** |

Con este volumen, **bajo demanda con cuotas** es más barato que reservar capacidad; se reevalúa con precios
confirmados de ediciones si el escaneo de analistas creciera por encima de unas decenas de TiB al mes. Quedan
fuera el core, la captura de cambios desde el core (a confirmar), los modelos de lenguaje y la voz (IA y
Tecnología) y las personas.

### 7.5 Alternativa gratuita

El **perfil local** cuesta US$0 y cumple todo lo que el enunciado exige del capítulo de datos. Lo que se pierde
sin la nube: el control de acceso aplicado por la plataforma, el segundo verificador independiente de calidad
y de linaje, y parte de la credibilidad de la ruta a producción.

### 7.6 Controles de costo

- Presupuesto con alertas al 50%, 90% y 100% de US$50.
- Cuota personalizada de consultas de 100 GiB por día en el proyecto.
- `maximum_bytes_billed` en el perfil de dbt-bigquery y ensayo en seco antes de consultas pesadas.
- Etiquetas por zona y exportación de facturación a BigQuery: el costo por zona es una consulta.
- El EDA y la exploración se hacen en local.

---

## 8. Backlog propuesto

Las épicas DAT-1 a DAT-6 son las de la [hoja de ruta](../presidencia/hoja_de_ruta.md); DAT-7 es nueva y es la
**primera en recortarse** dentro del capítulo de datos. Días según el calendario relativo de 07.

### DAT-1 Bronce con manifiesto y vigilancia (F0 y F1)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-1.1 | Espejo local del bucket con el perfil `latam-organizador`, sincronización por etag y listado completo a `platino.inventario_bucket` | 1.097 particiones por tabla de hechos (1.083 en `campaign_sends`); gitleaks limpio | TEC-10 (repositorio) | D0 |
| DAT-1.2 | Constructor de bronce: CSV a Parquet todo texto, BOM, metadatos mínimos por fila y `bronce._lotes` | dos corridas con huellas iguales; Q-BRZ-02 probado con y sin BOM | DAT-1.1 | D0 |
| DAT-1.3 | Reglas Q-BRZ-01 a Q-BRZ-11 con reporte en platino | reporte por corrida con cada regla | DAT-1.2 | D0 y D1 |
| DAT-1.4 | Generación de respaldo en `bronce_respaldo` y prueba real de regeneración | la reentrega simulada queda `bloqueado_regeneracion` con 0 IDs en común | DAT-1.2, DAT-3.5 | D1 a D3 |
| DAT-1.5 | `just vigilar` con clasificación de objetos y programación cada 6 horas | pruebas con un bucket simulado; filas en `vigilancia_bucket` | DAT-1.2 | D1 |
| DAT-1.6 | Manifiesto encadenado y `just verificar-cadena` | una edición de un manifiesto viejo se detecta | DAT-1.2 | D1 |

### DAT-2 Auditoría del total, EDA de negocio, restricciones y línea base (F1)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-2.1 | Veredicto sobre el total de las 24 afirmaciones | `platino.confirmacion_auditoria` completa (R-DAT-62) | DAT-1 | D1 |
| DAT-2.2 | Reporte de deriva del diccionario y primera versión de `dominios/` | cero valores crudos sin mapeo ni bandera | DAT-1 | D1 |
| DAT-2.3 | Bloque A del EDA: demanda | `just eda` regenera figuras idénticas | DAT-2.2 | D1 y D2 |
| DAT-2.4 | Bloque B: restricciones operativas y `capacidad_humana_franja` | M-45 con sus supuestos | S-DAT-10 | D1 y D2 |
| DAT-2.5 | Bloque C: línea base de reclamos con su advertencia | M-40 a M-43 | DAT-2.2 | D1 y D2 |
| DAT-2.6 | Datos para la auditoría de señal sobre el total (*spike* S5): particiones temporales y tablas | AUC reportada por IA con la huella de los datos; validada por Gobierno | DAT-1 | D0 y D1 |
| DAT-2.7 | `AS_OF` fijado con su consulta | `configuracion/as_of.yaml` versionado | DAT-1 | D1 |
| DAT-2.8 | Rendimiento de la reconstrucción completa medido | presupuestos de la sección 6.1 fijados | DAT-3.4 | D1 a D3 |

### DAT-3 Contratos, plata incremental, cuarentena y *fixture* (F1 a F3)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-3.1 | Plantilla ODCS, verificador de campos obligatorios y lint en CI | CI falla con un contrato incompleto | | D1 |
| DAT-3.2 | 13 contratos de fuente y 8 de plata, primero `transacciones`, `productos`, `clientes` y `quejas` | lint sin errores; consulta a IA y Tecnología | DAT-3.1, DAT-2.2 | D1 y D2 |
| DAT-3.3 | Proyecto dbt con dos perfiles y macros despachadas (`conversion_segura`, `coincide_regex`, `hex_md5`, `canon_decimal`, `canon_ts`, `token_hmac`, `huella_tabla`) | cada macro coincide con la referencia en Python | DAT-3.1 | D1 y D2 |
| DAT-3.4 | Plata incremental por lotes, ventana contra `AS_OF`, ganador determinista y banderas | FX-01 a FX-08, FX-23 y FX-24 | DAT-3.2, DAT-3.3 | D2 y D3 |
| DAT-3.5 | Evolución de esquema y detector de regeneración | FX-09 a FX-12, FX-21 y FX-22 | DAT-3.4 | D2 y D3 |
| DAT-3.6 | Cuarentena, umbral de sistematicidad y conteos que cuadran | FX-13 a FX-16; Q-GLB-01 | DAT-3.4 | D2 y D3 |
| DAT-3.7 | Tokenización con la llave en la zona `seguridad`; `plata_restringida` | vectores del RFC 4231 y búsqueda de la llave con cero coincidencias (R-DAT-58) | DAT-3.3 | D2 |
| DAT-3.8 | *Fixture* de 24 casos con esperados y las propiedades (a) a (c) | `just data-test` verde | DAT-3.4 a DAT-3.6 | D2 y D3 |
| DAT-3.9 | Data Contract CLI por corrida a `platino.resultado_contratos` y bloqueo de la publicación | FX-11 deja vigente la publicación anterior | DAT-3.2 | D3 |
| DAT-3.10 | Pruebas de dbt generadas desde los contratos | generación sin diferencias en CI (R-DAT-16) | DAT-3.2 | D2 |

### DAT-4 Oro operacional, analítico y de aprendizaje (F2 y F3)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-4.1 | `transacciones_recientes`, `estado_productos`, `vista_cliente_segura` y `reclamos_cliente` con contrato | lista de certificación (6.3) sin fallas | DAT-3, S-DAT-03, S-DAT-06 | D3 |
| DAT-4.2 | `directorio_comercios` del equipo: 24 comercios, descriptores, semilla y versión | firma de Clientes (S-DAT-09) | DAT-2.3 | D2 y D3 |
| DAT-4.3 | `ficha_transaccion` con compras previas anteriores al evento, posibles duplicados, tasa aplicada y clave del estado | prueba de corte temporal; N1, N2, N7 y N9 con datos | DAT-4.1, DAT-4.2 | D3 |
| DAT-4.4 | `riesgo_transaccion` con acceso exclusivo del diagnóstico de fraude | prueba de acceso; bandas de S-DAT-06 | DAT-4.1 | D3 |
| DAT-4.5 | Publicación de la instantánea con puntero `VIGENTE` y `publicaciones_oro` | los servicios abren la instantánea en solo lectura | DAT-4.1, TEC-3 | D3 |
| DAT-4.6 | Certificación de cada producto de oro operacional | firma de la VP Datos y visto bueno de Gobierno | DAT-4.1 a DAT-4.5 | D3 y D4 |
| DAT-4.7 | `candidatos_semilla`, `mezcla_rutas_estimada` y materializador de casos con huellas | Gobierno escribe el retenido con ellos antes de congelarlo | DAT-3.4, S-DAT-06 | D2 |
| DAT-4.8 | `features_transaccion` y `particiones_congeladas` sin fuga temporal | R-DAT-41 y R-DAT-25 | DAT-3.4, S-DAT-08 | D3 y D4 |

### DAT-5 Linaje, métricas oficiales y platino (F3 a F7)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-5.1 | Linaje por columna con sqlglot y prueba de caminos de PII | R-DAT-43 y R-DAT-44 | DAT-3.4 | D3 |
| DAT-5.2 | Catálogo M-01 a M-46 en YAML y SQL con pruebas estadísticas | valores de referencia (R-DAT-49); huella del catálogo en el acta de F2 | S-DAT-11 | D2 a D4 |
| DAT-5.3 | Trazas y costos a platino | M-18 a M-24 sin pasos manuales | S-DAT-04 | D4 y D5 |
| DAT-5.4 | Generador de tablas del reporte que exige el trío y separa por naturaleza | R-DAT-48 y R-DAT-51 | DAT-5.2 | D8 y D9 |
| DAT-5.5 | Escaneo detectivo con Presidio y testigo positivo | hallazgos en bronce; cero en oro operacional, platino y `_rechazos` | DAT-3.7 | D3 |
| DAT-5.6 | Tabla BCBS 239 y capítulo de datos del reporte | cada fila apunta a evidencia existente | DAT-5.2 | D9 |
| DAT-5.7 | Reconstrucción de la traza al etag | R-DAT-46 con una consulta | DAT-4.5, S-DAT-03 | D5 |

### DAT-6 Inventario y procedencia (F0 a F7)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-6.1 | Esquema del inventario y alta de los insumos del organizador y de los documentos | entradas con clase y restricciones | | D1 y D2 |
| DAT-6.2 | Verificador de cobertura y marca de herencia | M-38 igual a 100%; R-DAT-53 | DAT-6.1 | D2 |
| DAT-6.3 | Guardas del repositorio | un Parquet versionado a propósito hace fallar CI (R-DAT-57) | TEC-10 | D0 |
| DAT-6.4 | Procedencia de audios y registro de consentimientos, con IA y Auditoría | R-DAT-55 | S-DAT-07 | D5 a D7 |
| DAT-6.5 | Plan de retención y acta de borrado al cierre | acta con las consultas de verificación (R-DAT-56) | S-DAT-05 | D10 y después |

### DAT-7 Despliegue gobernado en Google Cloud (F3 a F5; recortable)

| ID | Historia | Aceptación | Depende de | Día |
|---|---|---|---|---|
| DAT-7.1 | Proyecto, bucket, datasets por zona, cuentas de servicio, presupuesto, cuota y exportación de facturación, con Tecnología | configuración de 3.6 aplicada como código | S-DAT-02, S-DAT-12 | D3 |
| DAT-7.2 | Carga de bronce y `just data-nube` con dbt-bigquery y contratos contra el servidor `nube` | corrida verde en nube | DAT-7.1, DAT-3 | D4 |
| DAT-7.3 | Taxonomía, reglas de enmascaramiento e IAM, probadas impersonando cada rol | cada rol ve exactamente lo de las tablas de 4.1 y 4.4 | S-DAT-05 | D5 |
| DAT-7.4 | Knowledge Catalog: reglas generadas desde los contratos, perfiles, linaje, aspecto de producto y comparación de linajes | resultados en platino; diferencias explicadas | DAT-7.2 | D5 y D6 |
| DAT-7.5 | Descubrimiento de Sensitive Data Protection con testigo positivo | hallazgos en bronce; cero en oro operacional y platino | DAT-7.2 | D6 |
| DAT-7.6 | Paridad y propiedad (d) del *fixture* | M-36 igual a 100% | DAT-7.2 | D6 |
| DAT-7.7 | Desmontaje y verificación del borrado | acta de borrado en nube | DAT-6.5 | D10 |

**Orden de recorte dentro del capítulo de datos:** DAT-7.5, DAT-7.4, luego DAT-7 completa (el perfil local
queda como la opción A). **Nunca se recortan:** contratos de plata y de oro operacional, reglas de calidad y
cuarentena, *fixture* con sus propiedades, manifiesto, linaje por columna con la prueba de PII, frescura,
inventario y métricas oficiales (hoja de ruta, sección 6).

---

## 9. Riesgos y mitigaciones

| Riesgo | Señal | Prob. | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| El total contradice la muestra (duplicados, llegadas tardías, señal en `is_fraud`) | DAT-2.1 | media | alto | reglas y ventana ajustables; cada refutación abre una decisión antes de F1 | Datos |
| Regeneración o entrega nueva durante el evento | vigilancia | media | alto | R-DAT-31 detiene sin mezclar; los casos llevan huella de contexto (R-DAT-54) | Datos |
| Los organizadores no permiten la copia en nube o no responden | S-DAT-01 | media | medio | perfil de nube solo con *fixture*, o apagado; la opción A cumple el enunciado | Datos, Gobierno |
| Sin cuenta de facturación ni créditos | S-DAT-02 | baja | medio | perfil local; tope de US$50 | Tecnología |
| Diferencias de dialecto rompen la paridad | M-36 menor que 100% | media | medio | macros con prueba en ambos motores; si persiste, la nube queda no certificada y se reporta | Datos |
| El perfil de nube consume más de dos días | bitácora | media | medio | orden de recorte de la sección 8 | Oficina de Entrega |
| Fuga de PII por cuarentena, registros, SQL compilado o historial de trabajos | escaneos | baja | alto | R-DAT-21, R-DAT-58, escaneos con testigo positivo | Datos, Gobierno |
| Bloqueo entre el pipeline que publica y los servicios que leen DuckDB | errores de apertura | media | medio | una instantánea nueva por publicación y puntero atómico; nunca se escribe sobre un archivo abierto | Datos, Tecnología |
| El linaje de Knowledge Catalog se pierde a los 30 días | fecha | alta | bajo | exportación a platino en cada corrida | Datos |
| El enmascaramiento no aplica a columnas de partición o clúster | error de consulta | baja | medio | nunca particionar ni agrupar por una columna con policy tag | Datos |
| La capa gratuita ya la consume otro proyecto de la misma cuenta | facturación | baja | bajo | cuota diaria, presupuesto; el peor caso ronda US$35 | Tecnología |
| Escribir 40 contratos a mano no alcanza | avance de DAT-3.2 | media | medio | plantilla; importación inicial desde el SQL o desde dbt con Data Contract CLI; contratos de fuente ligeros | Datos |
| Insumos del equipo contaminados con datos del organizador | verificador de R-DAT-53 | media | alto | marca de herencia y rutas permitidas | Datos, IA |
| El jurado no puede reproducir sin la llave de AWS | pregunta de Auditoría | media | medio | el README explica el uso de la llave de cada participante; el *fixture* y todas las pruebas corren sin llave | Datos, Tecnología |
| Grabaciones humanas sin consentimiento o retenidas de más | inventario | baja | alto | R-DAT-55; acta de borrado revisada por Auditoría | Datos, Gobierno |
| Métricas o contratos cambiados después de congelar el retenido | diff de huellas | baja | alto | huella del catálogo en el acta de F2; cambios solo con acta (P1) | Gobierno |

---

## 10. Decisiones propuestas y preguntas abiertas

### 10.1 Decisiones propuestas

| ID | Decisión | Cambia | Decide | Principio |
|---|---|---|---|---|
| DP-DAT-01 | **Un código, dos perfiles:** local (DuckDB, Parquet, dbt con DuckDB, Data Contract CLI) como referencia y origen de toda cifra oficial; Google Cloud (Cloud Storage, BigQuery, dbt con BigQuery, Knowledge Catalog, policy tags con enmascaramiento, Sensitive Data Protection) como despliegue gobernado, certificado solo por paridad de huellas | **modifica D-08** (agrega el segundo perfil; DuckDB sigue como referencia) y la fila 16 de la tabla de componentes de [06](../docs/diseno/06_Arquitectura.md) | Comité de Plataforma, con ADR | P9, P11, P13 |
| DP-DAT-02 | dbt Core en ambos perfiles; Dataform descartado porque rompe la paridad | precisa D-08 | Comité de Plataforma | P13 |
| DP-DAT-03 | **Linaje por columna obligatorio** con sqlglot y prueba de cero caminos de PII a oro operacional y platino; en nube, linaje de Knowledge Catalog exportado a platino (retención de 30 días) y comparado; OpenLineage y MetricFlow siguen opcionales | **modifica D-21**, que dejaba el linaje en el manifiesto y el grafo de dbt | VP Datos | P11, P13 |
| DP-DAT-04 | Tokenización HMAC-SHA-256 portable con la llave en la zona `seguridad` y vectores del RFC 4231; Sensitive Data Protection como control detectivo, no como tokenizador | precisa [03](../docs/diseno/03_Datos_por_capas.md), sección 3.2, punto 7 | VP Datos, con visto bueno de Gobierno | P11 |
| DP-DAT-05 | Fuente autorizada `data/`; el respaldo solo como generación aparte para auditoría y prueba de regeneración, hasta que los organizadores digan otra cosa | ninguno | VP Datos | P13 |
| DP-DAT-06 | Oro operacional como instantánea publicada de solo lectura con huella; nunca BigQuery en la ruta de una herramienta; como alternativa, carga en un esquema `referencia` de Postgres | precisa [06](../docs/diseno/06_Arquitectura.md) y D-20 | VP Datos con Tecnología | P5, P13 |
| DP-DAT-07 | La llave de AWS del organizador vive solo en la máquina de ingesta; Storage Transfer Service no se usa en la hackatón y en producción va con identidad federada | ninguno | Comité de Plataforma | P11 |
| DP-DAT-08 | Ventana de corrección de 3 días medida contra `AS_OF`, con modo inicial y reproceso manual registrado | precisa 03, sección 3.2, punto 8 | VP Datos | P13 |
| DP-DAT-09 | Ganador determinista por `last_updated`, `last_modified` del objeto y huella de fila, **sin** `_ingerido_en` | **corrige** 03, sección 3.2, punto 3 | VP Datos | P13 |
| DP-DAT-10 | Metadatos mínimos por fila y completos por lote | precisa 03, sección 3.1 | VP Datos | P9 |
| DP-DAT-11 | Umbrales de regeneración (50% de llaves en común) y de sistematicidad (0,5% del lote), revisables tras la auditoría del total | ninguno | VP Datos | P2 |
| DP-DAT-12 | Atributos protegidos solo en `plata_restringida` para auditar equidad; segmentos autorizados: idioma, variante, segmento, canal y país | ninguno | VP Gobierno (Protección al consumidor), a propuesta de Datos | P12 |
| DP-DAT-13 | Región `us-central1` y tope de US$50 para el perfil de nube en la hackatón | ninguno | Presidencia (gasto) y Comité de Plataforma | P9 |
| DP-DAT-14 | Borrado al cierre con destrucción de la llave de tokenización, acta y verificación en nube después de sus ventanas de recuperación | ninguno | VP Datos con Gobierno | P11 |

### 10.2 Preguntas abiertas

**A los organizadores** (vía S-DAT-01): la 11 (copia en un proyecto privado de Google Cloud) y la 12 (retención
y borrado exigidos), además de la 5 (términos de uso), la 6 (entregas incrementales y versión oficial) y la 8
(créditos).

**A Gobierno:** plazos legales de conservación por país; valor de `ventana_dias`; aprobación de la taxonomía;
alcance del uso de atributos protegidos en la auditoría de equidad.

**A Tecnología:** ¿instantánea DuckDB o esquema `referencia` en Postgres? ¿Terraform o scripts? ¿Quién
administra la cuenta de facturación?

**A IA:** volumen de conversaciones y audios del equipo; si algún proveedor externo de voz procesará las
grabaciones humanas.

**A Clientes:** horarios de turnos y costo por minuto humano; si la vista del experto necesita el nombre del
cliente (lo que justificaría `plata_restringida` para nombres).

**Verificaciones pendientes de esta cara:** tarifas de Storage Transfer Service, Sensitive Data Protection,
Cloud Storage y egreso de S3; DCU por escaneo de Knowledge Catalog; ventanas de viaje en el tiempo de BigQuery
y de borrado suave de Cloud Storage; nombres de los infoType por país; nombres exactos de campos de ODCS 3.1
(`severity`, `relationships`) frente a `datacontract lint`; si la versión fijada de DuckDB admite la
estrategia `merge`; nombres exactos de las columnas marcadas "a confirmar" contra el encabezado de bronce.

---

## 11. Fuentes

**Del proyecto:** [principios](../docs/diseno/00_Principios.md), [interacciones y criterios](../docs/diseno/01_Interacciones_y_criterios.md),
[datos por capas](../docs/diseno/03_Datos_por_capas.md), [organización v2](../docs/diseno/04_Organizacion_y_roles.md),
[cobertura del enunciado](../docs/diseno/05_Cobertura_del_enunciado.md), [arquitectura](../docs/diseno/06_Arquitectura.md),
[hoja de ruta](../presidencia/hoja_de_ruta.md), [decisiones](../presidencia/decisiones.md),
[modelo operativo](../presidencia/modelo_operativo.md), investigaciones
[05](../docs/investigacion/05_Datos_ML_y_operacion.md), [09](../docs/investigacion/09_Grafos.md),
[13](../docs/investigacion/13_Auditoria_del_dataset.md), [14](../docs/investigacion/14_VP_Clientes.md),
[16](../docs/investigacion/16_VP_Datos.md), [18](../docs/investigacion/18_VP_Gobierno.md),
[19](../docs/investigacion/19_Auditoria.md) y [20](../docs/investigacion/20_Canales_voz_y_chat.md); el enunciado y el
resumen del dataset en `Documentos/`. El diccionario no se abrió (contiene credenciales).

**Externas** (consultadas el 26 y el 27 de septiembre de 2026; las marcadas "a confirmar" en la sección 7.2 no
se pudieron leer con la herramienta):

- Bitol, [ODCS 3.1](https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/) y su
  [especificación](https://github.com/bitol-io/open-data-contract-standard).
- [Data Contract CLI con DuckDB](https://docs.datacontract.com/testing/duckdb).
- dbt, [estrategias incrementales](https://docs.getdbt.com/docs/build/incremental-strategy),
  [contratos de modelo](https://docs.getdbt.com/reference/resource-configs/contract) y
  [dbt-duckdb](https://github.com/duckdb/dbt-duckdb).
- [sqlglot](https://github.com/tobymao/sqlglot) (módulo de linaje).
- Google Cloud: [linaje de Knowledge Catalog](https://docs.cloud.google.com/dataplex/docs/about-data-lineage)
  (renombre del 10 de abril de 2026, retención de 30 días, límites del linaje por columna);
  [precios de Knowledge Catalog](https://cloud.google.com/dataplex/pricing);
  [enmascaramiento de datos en BigQuery](https://docs.cloud.google.com/bigquery/docs/column-data-masking-intro);
  [precios de BigQuery](https://cloud.google.com/bigquery/pricing);
  [capa gratuita y prueba](https://docs.cloud.google.com/free/docs/free-cloud-features);
  [precios de Cloud Storage](https://cloud.google.com/storage/pricing);
  [Storage Transfer Service desde S3](https://docs.cloud.google.com/storage-transfer/docs/create-transfers/agentless/s3),
  [red privada administrada](https://docs.cloud.google.com/storage-transfer/docs/create-transfers/agentless/managed-private-network)
  y [precios](https://cloud.google.com/storage-transfer/pricing);
  [precios de Sensitive Data Protection](https://cloud.google.com/sensitive-data-protection/pricing) y
  [desidentificación](https://docs.cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data).
- Fuentes secundarias de precios de BigQuery: [Markaicode, agosto de 2026](https://markaicode.com/pricing/bigquery-pricing/)
  y [Airbyte](https://airbyte.com/data-engineering-resources/bigquery-pricing).
- [Precios de Amazon S3](https://aws.amazon.com/s3/pricing/).
- Comité de Supervisión Bancaria de Basilea, [BCBS 239](https://www.bis.org/publ/bcbs239.pdf); guía de
  [Atlan](https://atlan.com/bcbs-239-guide/).
- [RFC 2104, HMAC](https://www.rfc-editor.org/rfc/rfc2104) y [RFC 4231, vectores de HMAC-SHA-256](https://www.rfc-editor.org/rfc/rfc4231).
- [OpenLineage con dbt](https://openlineage.io/docs/integrations/dbt/) y
  [Microsoft Presidio](https://microsoft.github.io/presidio/).
