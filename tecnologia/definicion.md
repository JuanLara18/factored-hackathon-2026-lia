# VP Tecnología: plataforma, arquitectura, canales, confiabilidad y costo técnico

**Cara:** VP Tecnología, con sus cuatro gerencias (Arquitectura; Plataforma del agente; Canales;
Observabilidad, SRE y costo). **Versión:** 1 (27 de septiembre de 2026). **Estado:** primera versión,
lista para el desafío de Gobierno y la auditoría de completitud
([modelo operativo](00_Presidencia_Modelo_operativo.md), sección 7).
**Se apoya en:** [principios](../Diseno/00_Principios.md), [interacciones](../Diseno/01_Interacciones_y_criterios.md),
[datos por capas](../Diseno/03_Datos_por_capas.md), [organización](../Diseno/04_Organizacion_y_roles.md),
[cobertura del enunciado](../Diseno/05_Cobertura_del_enunciado.md), [arquitectura](../Diseno/06_Arquitectura.md),
[hoja de ruta](../Diseno/07_Hoja_de_ruta.md), [decisiones D-01 a D-21](../Diseno/Decisiones.md) y las
investigaciones [2](../Investigacion/02_Arquitectura_y_control.md), [8](../Investigacion/08_IA_con_tipos_seguros.md),
[10](../Investigacion/10_Gobernanza_y_gateway.md), [11](../Investigacion/11_Latencia_y_costo.md),
[17](../Investigacion/17_VP_Tecnologia.md) y [20](../Investigacion/20_Canales_voz_y_chat.md).

**Cómo leer este documento**

- La sección 2 son las **reglas del juego** de la plataforma, numeradas `R-TEC-nn`, cada una con su forma de
  verificación. La sección 4 continúa la numeración con las reglas de seguridad técnica.
- Las cifras llevan etiqueta, para separar lo verificado de lo supuesto (P3):
  **[V]** verificado en la fuente oficial el 27 de septiembre de 2026; **[P]** cifra del proveedor sin
  verificación independiente; **[S]** supuesto nuestro, que se reemplaza por una medición; **[A]** a
  confirmar, con el cómo al lado.
- Nada de lo aquí escrito cambia una decisión firme. Donde conviene cambiar o precisar una, se propone
  como `DP-TEC-nn` (sección 10) y se registra solo si el Comité de Plataforma la aprueba.

**Resumen de decisiones de plataforma**

| Tema | Decisión | Estado |
|---|---|---|
| Plataforma | Google Cloud como referencia; el entorno local es la vía reproducible oficial (P13); demo en `us-central1` | DP-TEC-01 |
| Cómputo | Cloud Run: seis servicios y tres trabajos (jobs); el núcleo es una biblioteca que importan las superficies | DP-TEC-09 |
| Estado | Cloud SQL para PostgreSQL (`db-g1-small` en la demo); Postgres en contenedor en local y en pruebas de integración | D-20, DP-TEC-06 |
| Gateway de IA | LiteLLM en todos los entornos, con Presidio siempre y Model Armor en la nube; Apigee queda como ruta a producción documentada | D-20, DP-TEC-02 |
| Modelos | Vertex AI detrás del gateway, con alias por trabajador; modelo abierto propio como plan B | D-15, D-20 |
| Voz | Pipecat en cascada; WebRTC en local; WebSocket hacia Cloud Run en la nube; teléfono opcional con Twilio | D-18, DP-TEC-05 |
| Identidad | propia (D-20) con llave de firma en Cloud KMS; personal interno por IAP; Identity Platform descartado para clientes | D-20, DP-TEC-04 |
| Trazas | OpenTelemetry con convenciones GenAI; Phoenix en local y en la nube, más Cloud Trace, Logging y Monitoring en la nube | DP-TEC-03 |
| Infraestructura y entrega | Terraform; GitHub Actions con Workload Identity Federation; despliegue sin tráfico, humo, promoción y reversión en un comando | DP-TEC-08 |
| Gasto | techo de US$600 de gasto total (antes de créditos) con alertas; lo indispensable es consumo de modelos y de voz, ≈ US$340 a 550 | DP-TEC-12 |

---

## 1. Mandato y alcance

### 1.1 Mandato

Que el sistema sea **correcto por construcción, observable, reproducible y barato**
([organización](../Diseno/04_Organizacion_y_roles.md), sección 5). En la misión "cargo no reconocido",
Tecnología construye y opera la plataforma sobre la que la misión entrega el resultado: el núcleo (motor
de flujo, capa de herramientas, identidad, estado durable), las superficies de chat y de voz, el gateway de
IA (con Gobierno), los servicios simulados, la observabilidad, la infraestructura, la entrega continua y el
costo técnico. **Hace cumplir** lo que Gobierno define (política como código) y **ejecuta** lo que IA
entrena (modelos detrás del gateway); no decide ninguna de las dos cosas.

### 1.2 Qué es de Tecnología y qué no

La numeración de componentes es la de [06](../Diseno/06_Arquitectura.md), sección 2.

| # | Componente | Tecnología es | Otra cara es |
|---|---|---|---|
| 1 | Superficie de chat | dueña (Canales): protocolo, frontend, streaming, filtro por frases | Clientes: contenido de guiones y componentes |
| 2 | Superficie de voz | dueña del transporte, la tubería, la latencia y la telefonía | IA (Voz): proveedores y detección de turno; Clientes: diseño de voz |
| 3 | Frontend nativo (experimento) | habilita la plataforma, la bandera y la medición | IA (Voz): dueña del experimento |
| 4 | Gateway de IA | dueña de la operación | Gobierno: qué se filtra, umbrales y fallas abiertas o cerradas |
| 5 | Motor de flujo | dueña | Clientes: estados y guiones; Gobierno: política |
| 6 | Estado durable | dueña | |
| 7 | Comprensión | integra, sirve y mide latencia | IA: modelo, datos y evaluación |
| 8 | Política | cargador, evaluador y registro de decisiones | Gobierno: contenido de `policy/v1` |
| 9 | Capa de herramientas | dueña | |
| 10 | Servicios simulados | dueña | Datos: oro operacional que leen |
| 11 | Identidad | dueña | Gobierno: qué acción exige qué nivel |
| 12 | Ficha de la transacción | la expone por servicio | Datos y Clientes: contenido |
| 13 | Redacción | ejecuta, filtra la salida y sirve las plantillas | IA: modelo y prompts; Clientes: texto de plantillas |
| 14 | Traspaso | cola, render y entrega | Clientes: contenido y operación humana |
| 15 | Vista del experto | plataforma y control de acceso | Clientes (Operaciones): uso y requisitos |
| 16 | Datos | consume oro operacional; exporta trazas a platino | Datos: capas, contratos, métricas oficiales |
| 17 | Evaluación | LLM simulado, inyección de fallas, API del motor para simuladores, corridas reproducibles | IA: arnés; Gobierno: retenido y corrida final |
| 18 | Observabilidad | dueña (SRE) | IA (Operación de agentes): la usa para deriva e incidentes |

### 1.3 Fuera de alcance

- El contenido de la política, del retenido, de los guiones y de los modelos.
- Las capas de datos (bronce a platino), salvo el consumo del oro operacional y la exportación de trazas.
- Operar un banco real: no hay movimiento de dinero, ni WhatsApp real, ni un core bancario real
  (enunciado, *Data and execution boundaries*). La telefonía real es opcional.
- Un entorno de producción: se **documenta** como referencia (arquitectura, costos, trabajo restante) pero
  no se construye.

### 1.4 Firmas y compuertas

| Compuerta | Qué firma Tecnología | Evidencia |
|---|---|---|
| F0 | instalación de un comando y entorno de la nube levantable | `just setup demo` en máquina limpia; `terraform plan` sin cambios |
| F3 | núcleo y chat de punta a punta | N1 a N6 por chat en ES; pyright estricto sin errores; trazas con la secuencia de estados |
| F3v | voz sobre el mismo núcleo | los mismos casos por voz en ES dentro del presupuesto de latencia |
| F5 (participa) | capacidad y degradación | reporte de punto de quiebre; simulacros de reversión y de caída segura |
| F6 (participa) | versión candidata congelada | digest de imagen con versiones de modelo, prompt, política y datos en el acta |
| F7 (participa) | reproducibilidad | prueba en máquina limpia con Auditoría |

### 1.5 Principios que más pesan aquí

P4 (el código decide), P5 (seguridad por construcción), P6 (solo lo verificado), P9 (lo simple primero),
P11 (privacidad y mínimo privilegio) y P13 (reproducible y trazable). En un choque, la regla de desempate del
[modelo operativo](00_Presidencia_Modelo_operativo.md) (sección 4.2) pone latencia y costo en el quinto
puesto: nunca se compra latencia con seguridad ni con honestidad de la medición.

---

## 2. Definiciones y estándares del dominio

### 2.1 Arquitectura de referencia en Google Cloud

```
      Cliente (navegador o teléfono)                          Personal del banco (agentes, supervisores, auditor)
               │ HTTPS, SSE y WebSocket                                          │ HTTPS con IAP
     ┌─────────┴───────────────────────┐                        ┌────────────────┴──────────────┐
     ▼                                 ▼                        ▼                               ▼
 [Cloud Run lb-chat]            [Cloud Run lb-voz]        [Cloud Run lb-staff]           [Cloud Run lb-phoenix]
 SPA y AG-UI por SSE            Pipecat en cascada        vista del experto,             trazas de LLM
 motor (biblioteca)             motor (biblioteca)        cola humana, panel             (Arize Phoenix)
     │     │                        │     │   └──────► Speech-to-Text y Text-to-Speech (o proveedor elegido en S1)
     │     └──────────┬─────────────┘     │   (Twilio Media Streams entra aquí por WebSocket, opcional)
     │                ▼                   │
     │   [Cloud Run lb-gateway, interno]  LiteLLM + Presidio + Model Armor ───► Vertex AI (Gemini y otros)
     ▼                                    ▼
 [Cloud Run lb-bian, interno]  servicios simulados BIAN e identidad (JWT firmado con Cloud KMS)
     │                 └──────► Cloud Storage: oro operacional en Parquet, montado en solo lectura
     ▼
 [Cloud SQL para PostgreSQL]  bases nucleo, bian, litellm y phoenix

 Transversal: Artifact Registry, Secret Manager, Cloud KMS, Cloud Logging, Cloud Trace, Cloud Monitoring,
 presupuesto de facturación con alertas. Borde opcional: balanceador externo con Cloud Armor.
 Trabajos (Cloud Run jobs): lb-migrar, lb-sembrar, lb-exportar-trazas.
```

**Unidades desplegables.** El sistema es un **monolito modular**: el paquete `latam_bank` contiene el
dominio, el motor, la política, las herramientas y los clientes de servicios; las unidades desplegables son
procesos que lo importan con distinto punto de entrada. Se separa en procesos solo donde hay una razón
(frontera de confianza, perfil de escala distinto o componente de terceros).

| Unidad | Qué corre | Imagen y comando | Ingreso | Escala en la demo [S] | Cuenta de servicio |
|---|---|---|---|---|---|
| `lb-chat` | SPA del cliente, endpoint AG-UI (SSE), motor como biblioteca | `app`, `python -m latam_bank.run chat` | público | 0 a 5 instancias; concurrencia 40; 1 vCPU y 1 GiB | `sa-chat` |
| `lb-voz` | Pipecat (WebSocket y telefonía), motor como biblioteca | `app`, `... run voz` | público | 1 a 5; 6 llamadas por instancia; 2 vCPU y 4 GiB; tiempo máximo de solicitud 3.600 s | `sa-voz` |
| `lb-bian` | servicios simulados con nombres BIAN e identidad | `app`, `... run bian` | interno, IAM | 0 a 3; concurrencia 80; 1 vCPU y 2 GiB | `sa-bian` |
| `lb-gateway` | LiteLLM con guardarraíles propios | `gateway` (base LiteLLM fijada por digest) | interno, IAM | 1 a 3; concurrencia 80; 1 vCPU y 2 GiB | `sa-gateway` |
| `lb-staff` | vista del experto, cola humana, panel de operación, dispositivo simulado de OTP | `app`, `... run staff` | IAP | 0 a 2 | `sa-staff` |
| `lb-phoenix` | Arize Phoenix con base en Postgres | imagen oficial fijada por digest | IAP | 1 | `sa-phoenix` |
| `lb-llm-simulado` (efímero, F5) | modelo simulado para pruebas de carga | `app`, `... run llm_simulado` | interno, IAM | según la prueba | `sa-carga` |
| `lb-migrar` (job) | migraciones Alembic | `app`, `... run migrar` | | una ejecución por despliegue | `sa-migrar` |
| `lb-sembrar` (job) | identidades de prueba, directorio de comercios del equipo, catálogo de plantillas | `app`, `... run sembrar` | | a demanda | `sa-migrar` |
| `lb-exportar-trazas` (job) | trazas de una corrida a `trazas_resumen` de platino | `app`, `... run exportar_trazas` | | a demanda | `sa-exportar` |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-01 | Un núcleo, varias superficies: `lb-chat` y `lb-voz` importan el mismo motor (`latam_bank.engine.api`); ninguna superficie contiene lógica de decisión, reglas de negocio ni llamadas a herramientas. | contrato de import-linter (R-TEC-33); prueba de paridad que corre el mismo caso por chat y por voz y compara la secuencia de estados (L1, V4) |
| R-TEC-02 | Las unidades desplegables son las de la tabla; agregar, quitar o fusionar una exige ADR aprobado por el Comité de Plataforma. | Terraform declara exactamente esas unidades; índice de ADR |
| R-TEC-03 | Una imagen de aplicación (`app`) y una del gateway, construidas **una vez por commit** y promovidas por digest a todos los entornos; nunca se reconstruye para promover. | el digest desplegado (`gcloud run services describe`) coincide con el registrado en la ejecución del CD |
| R-TEC-04 | Ninguna instancia guarda estado de conversación entre turnos: todo estado vive en Postgres y el oro es de solo lectura; la única excepción es el audio de una llamada viva en `lb-voz`. | prueba que termina una instancia a mitad de conversación y continúa en otra con el mismo resultado; revisión: sin cachés mutables de conversación a nivel de módulo |
| R-TEC-05 | `lb-bian`, `lb-gateway` y `lb-llm-simulado` tienen ingreso interno y exigen autenticación IAM; `lb-staff` y `lb-phoenix` están detrás de IAP; solo `lb-chat` y `lb-voz` son públicos. | `gcloud run services describe` (ingress y política IAM); una llamada externa sin identidad recibe 403 o 404 |
| R-TEC-06 | Solo `lb-gateway` habla con proveedores de modelos de lenguaje. | IAM: solo `sa-gateway` tiene `roles/aiplatform.user`; regla `banned-api` de ruff para clientes de proveedores fuera de `latam_bank.gateway`; conciliación de llamadas del gateway contra spans |
| R-TEC-07 | Ninguna llamada de red entre componentes existe sin *timeout* explícito (tabla de 2.12). | regla propia en CI que rechaza clientes HTTP o de base sin *timeout*; pruebas de la sección 2.12 |
| R-TEC-08 | Paridad entre local y nube: mismo código, misma imagen, misma versión mayor de Postgres; toda diferencia está en la tabla de entornos (2.2) y en configuración. | la suite de integración corre contra la pila de Docker Compose construida con la misma imagen que se despliega |

### 2.2 Entornos y configuración

| Aspecto | `local` (desarrollo y demo reproducible) | `ci` | `demo` (nube) | `produccion-referencia` (solo documentado) |
|---|---|---|---|---|
| Cómo se levanta | `just setup demo` (Docker Compose) | GitHub Actions con contenedores efímeros | Terraform y CD desde `main` | no se construye |
| Modelos | LLM simulado por defecto; proveedor real con clave; modelo abierto local como plan B | LLM simulado | Vertex AI por el gateway | Vertex AI con rendimiento aprovisionado |
| Datos | oro operacional local (organizador) y *fixture* | *fixture* y datos del equipo | datos del equipo; oro del organizador solo con autorización (R-TEC-13) | core bancario real |
| Identidad | propia, llave en archivo fuera del repositorio | propia, llave efímera | propia, llave en Cloud KMS; personal por IAP | proveedor de identidad del banco |
| Filtros | Presidio | Presidio | Presidio y Model Armor | Presidio, Model Armor y Apigee |
| Trazas | Phoenix local | archivo OTLP como artefacto del CI | Phoenix y Cloud Trace | Cloud Trace y plataforma de LLMOps |
| Voz | WebRTC entre pares (SmallWebRTC) | audio sintético por WebSocket | WebSocket a Cloud Run; teléfono opcional | WebRTC gestionado y troncal SIP |
| Postgres | contenedor `postgres:16` fijado por digest | contenedor | Cloud SQL 16, `db-g1-small` | Cloud SQL con alta disponibilidad y núcleos dedicados |
| Reloj | `RelojSimulado` desde `AS_OF` | `RelojCongelado` | `RelojSimulado` desde `AS_OF` | reloj del sistema |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-09 | Existen cuatro entornos con nombre (`local`, `ci`, `demo`, `produccion-referencia`) seleccionados por `LB_ENTORNO`; un valor desconocido impide arrancar. | prueba de la clase de configuración |
| R-TEC-10 | Configuración tipada con pydantic-settings; cada parámetro tiene un valor por defecto seguro; los secretos se leen por referencia (Secret Manager o archivo local ignorado), nunca desde el código ni la imagen. | prueba que falla si un campo marcado como secreto tiene valor por defecto; gitleaks sobre la imagen y el repositorio |
| R-TEC-11 | Banderas declaradas y registradas en cada traza raíz: `LB_FLAG_STREAMING_CHAT`, `LB_FLAG_MODEL_ARMOR`, `LB_FLAG_VOZ_NATIVA`, `LB_FLAG_TELEFONO`, `LB_FLAG_LLM_SIMULADO`, `LB_FLAG_TODO_A_HUMANO`. | atributo `latam.flags` en el span raíz de cada turno |
| R-TEC-12 | En `ci`, y por defecto en `local`, corre el LLM simulado: ninguna prueba automática depende de una API externa ni envía datos fuera de la máquina. | el CI no tiene secretos de proveedores; `pytest-socket` bloquea la red en pruebas unitarias |
| R-TEC-13 | La nube no carga filas del organizador (ni derivados como el oro operacional) sin autorización registrada en [Decisiones](../Diseno/Decisiones.md) (D-15); mientras tanto `demo` usa el conjunto de demostración generado por el equipo, marcado `origen: equipo`. | el manifiesto del bucket de oro declara `origen`; el despliegue se niega a montar `origen: organizador` si `LB_AUTORIZACION_DATOS_NUBE` no cita una decisión |
| R-TEC-14 | Todo el sistema lee el tiempo de un `Reloj` inyectado: `RelojSimulado(as_of=2026-06-17, t0)` avanza con el tiempo real desde `AS_OF` ([03](../Diseno/03_Datos_por_capas.md), sección 5.1); las pruebas usan `RelojCongelado` que se adelanta a mano. | atributo `latam.reloj.as_of` en cada traza; regla `banned-api` de R-TEC-32 |

### 2.3 Infraestructura como código

Terraform en `infra/terraform/`, con estos módulos: `proyecto` (APIs habilitadas), `identidades` (cuentas de
servicio e IAM), `registro` (Artifact Registry con política de limpieza), `datos` (Cloud SQL, bases,
usuarios, bucket de oro), `secretos` (Secret Manager y la llave de Cloud KMS), `servicios` (Cloud Run
services y jobs), `acceso` (IAP), `observabilidad` (buckets y retención de logs, paneles, alertas,
comprobaciones de disponibilidad), `presupuesto` (presupuesto de facturación y notificaciones), `wif`
(Workload Identity Federation para GitHub), `borde` (opcional: balanceador externo y Cloud Armor) y
`apigee` (opcional, solo para el *spike* S7).

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-15 | Todo recurso de la nube se declara en Terraform; lo único manual es el arranque (proyecto, cuenta de facturación, bucket de estado), documentado paso a paso en `infra/ARRANQUE.md`. | `terraform plan` sin cambios después de `apply`; revisión del inventario de recursos del proyecto contra el estado |
| R-TEC-16 | Estado remoto en un bucket de Cloud Storage con versionado y bloqueo; versión de Terraform y del proveedor `google` fijadas; `.terraform.lock.hcl` versionado. | archivos en el repositorio; `terraform init` reproducible en máquina limpia |
| R-TEC-17 | Las imágenes de Cloud Run las cambia el CD, no Terraform (`lifecycle.ignore_changes` sobre la imagen), para que no peleen. | `terraform plan` después de un despliegue no muestra deriva |
| R-TEC-18 | El presupuesto de facturación con alertas al 50, 80 y 100% se crea **antes** que cualquier recurso con costo. | el módulo `presupuesto` es dependencia de los demás; notificación de prueba recibida |
| R-TEC-19 | Etiquetas obligatorias en todo recurso: `mision=cargo-no-reconocido`, `entorno`, `componente`, `dueno=tecnologia`, para atribuir costo. | verificación en CI sobre el plan en JSON |
| R-TEC-20 | Desmontaje con un comando (`just destroy-demo`), que desactiva la protección de borrado de Cloud SQL y destruye todo salvo el bucket de estado y los artefactos de evidencia; se ejecuta al cerrar la calificación. | reporte de facturación con costo diario cercano a cero dos días después |

### 2.4 Integración continua, despliegue y reversión

**Flujos de GitHub Actions**

| Flujo | Cuándo | Qué hace |
|---|---|---|
| `ci.yml` | cada PR y cada push | formato, lint, pyright estricto, contratos de importación, pruebas `unit`, `propiedades` (perfil `ci`), `contrato` e `integracion` con Postgres en contenedor; gitleaks, pip-audit, OSV-Scanner y zizmor; construcción de imágenes sin publicar y SBOM |
| `cd.yml` | push a `main` | construir una vez, publicar en Artifact Registry por digest, correr `lb-migrar`, desplegar revisiones **sin tráfico** con etiqueta `c-<sha>`, humo contra la URL etiquetada, promover al 100%, registrar la versión |
| `nocturno.yml` | cada noche y a demanda | propiedades con perfil `nocturno`, prueba corta de carga con LLM simulado, escaneo completo del historial |
| `eval-dev.yml` | a demanda | corre el conjunto de **desarrollo** con el LLM configurado; nunca el retenido (lo corre Gobierno, 04, sección 10) |

**Pruebas de humo** (contra la revisión etiquetada, con LLM simulado): salud de cada servicio, N1 de punta a
punta por chat, apertura de una sesión de voz por WebSocket con audio sintético, reto de RFC 9470 ante `acr`
insuficiente y una acción rechazada por el punto de decisión.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-21 | GitHub Actions es el CI/CD; la autenticación a Google Cloud es por Workload Identity Federation, sin llaves de cuentas de servicio. | `gcloud iam service-accounts keys list --managed-by=user` vacío en todas las cuentas; el flujo usa la acción de autenticación con WIF |
| R-TEC-22 | Nada se fusiona a `main` con `ci.yml` en rojo; `main` está protegida y exige PR. | configuración de protección de rama con las comprobaciones requeridas |
| R-TEC-23 | `ci.yml` dura como máximo 12 minutos en el percentil 90 [S]; lo más lento va a `nocturno.yml`. | tiempos de ejecución de Actions |
| R-TEC-24 | Despliegue a `demo` solo desde `main`, en el orden: construir, publicar por digest, migrar, desplegar sin tráfico, humo, promover. | registro del flujo `cd.yml`; lista de revisiones con su etiqueta |
| R-TEC-25 | Migraciones con el patrón expandir y contraer: cada migración es compatible con la versión anterior del código, para poder revertir sin tocar la base. | prueba de compatibilidad en CI: el código de la versión anterior corre contra el esquema nuevo |
| R-TEC-26 | Reversión en dos minutos o menos con `just rollback-demo` (mueve el tráfico a la revisión anterior). Disparadores: humo fallido; errores por encima de 2% durante 5 minutos; p95 del turno por encima de 1,5 veces el presupuesto durante 10 minutos; alarma del filtro de salida (R-TEC-116). | simulacro en F5 con el tiempo medido y registrado en la bitácora |
| R-TEC-27 | La versión candidata de F6 es un digest de imagen más las versiones de modelo, prompt, política, tabla de precios y datos, registrados en el acta; la corrida del retenido se hace contra ese digest. | el acta contiene el digest; las trazas de la corrida tienen `service.version` igual a él |
| R-TEC-28 | Sin despliegues manuales a `demo`; una emergencia se registra en la bitácora con su motivo. | Cloud Audit Logs: el autor de cada despliegue es la cuenta del CD |

### 2.5 Estándares de ingeniería del repositorio

**Estructura.** Extiende la de [06](../Diseno/06_Arquitectura.md), sección 8. El repositorio vive fuera del
Drive, en `C:\Users\LaraJ\Projects\factored-hackathon-2026`, con remoto en GitHub (D-03).

```
factored-hackathon-2026/
├── .github/workflows/      ci.yml, cd.yml, nocturno.yml, eval-dev.yml
├── .claude/agents/         subagentes de Gobierno, Auditoría y voz del cliente
├── contracts/              odcs/ (Datos), openapi/ (servicios BIAN), agui/ (esquemas de componentes)
├── deploy/                 compose.yaml con perfiles, litellm/config.yaml, phoenix/
├── docs/adr/               NNNN-titulo.md en formato MADR
├── docs/runbooks/          proveedor caído, secreto filtrado, costo desbocado, inyección exitosa
├── finops/precios.yaml     tabla de precios versionada (sección 2.15)
├── infra/terraform/        módulos y el entorno demo; ARRANQUE.md
├── policy/v1/              (Gobierno) con su esquema JSON
├── src/latam_bank/         domain, engine, nlu, respond, tools, services, handoff, gateway,
│                           observability, channels/chat, channels/voice, reloj, run
├── web/                    chat, voz y staff (React y TypeScript)
├── eval/  pipeline/  dominios/  agentes/  tests/
└── pyproject.toml, uv.lock, .python-version, justfile, .pre-commit-config.yaml, .gitleaks.toml
```

**Recetas del `justfile`** (las que usa todo el equipo): `setup`, `check` (formato, lint, pyright,
contratos de importación), `test`, `test-all`, `demo` (levanta la pila local y siembra), `up`, `down`,
`carga`, `sbom`, `audit`, `deploy-demo`, `rollback-demo`, `demo-on` y `demo-off` (instancias mínimas en la
nube), `destroy-demo`. Datos e IA agregan las suyas (`data`, `data-test`, `eval`).

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-29 | Python 3.12 fijado (`.python-version` y `requires-python = "==3.12.*"`); uv es el único gestor; CI y Docker instalan con `uv sync --locked`. | CI falla si el lock no corresponde a `pyproject.toml` |
| R-TEC-30 | Enfriamiento de dependencias: la opción `exclude-newer` de uv se fija en una fecha al menos 7 días anterior a cada actualización del lock; una versión más reciente solo entra con excepción registrada. Motivo: las versiones maliciosas 1.82.7 y 1.82.8 de LiteLLM estuvieron unos 40 minutos en PyPI el 24 de marzo de 2026 [V]. | `pyproject.toml`; revisión de cada PR que toca el lock |
| R-TEC-31 | pyright en modo estricto sobre `src/` y `tests/`, con cero errores; cada `# type: ignore` lleva código y motivo, y hay un máximo de 10 en todo el repositorio [S]. | salida de pyright en CI; conteo automático |
| R-TEC-32 | ruff para lint y formato, con al menos las familias E, F, W, I, B, UP, S, ASYNC, DTZ, T20, PT, SIM, TID y RUF; `banned-api` prohíbe `datetime.now`, `date.today` y `time.time` fuera de `latam_bank.reloj`, y los clientes de proveedores de LLM (`openai`, `anthropic`, `google.genai`, `litellm`) fuera de `latam_bank.gateway`. | CI |
| R-TEC-33 | Contratos de arquitectura con import-linter: capas `channels`, `engine.api`, `engine` y `tools`, `services.clientes`, `domain`, en ese orden; `nlu` y `respond` no importan `tools` ni `services` (los trabajadores de lenguaje no tienen herramientas, P4); solo `services.identidad` construye `SesionAutenticada`. | `lint-imports` en CI |
| R-TEC-34 | pytest con marcadores obligatorios (`unit`, `propiedades`, `contrato`, `integracion`, `e2e`, `carga`) y `--strict-markers`; `just test` corre unit, propiedades, contrato e integración contra Postgres real en contenedor (definición de terminado, 07, sección 7). | configuración de pytest; ejecución de `just test` en CI |
| R-TEC-35 | Hypothesis con perfiles `dev` (100 ejemplos), `ci` (1.000) y `nocturno` (10.000), semilla registrada; los invariantes de Gobierno (GOB-5) se escriben como máquinas de estado (`RuleBasedStateMachine`). | perfiles en `conftest.py`; el reporte de propiedades cuenta ejemplos generados |
| R-TEC-36 | Cobertura de ramas de al menos 90% en `engine`, `tools`, `services.identidad` y `gateway.filtros`, y de 75% global [S]. | reporte de cobertura en CI |
| R-TEC-37 | Sin red ni reloj real en pruebas unitarias; sin datos del organizador en `tests/` (solo el *fixture* marcado y datos del equipo). | `pytest-socket`; gancho de pre-commit de R-TEC-38 |
| R-TEC-38 | pre-commit con: ruff, ruff-format, gitleaks, detect-private-key, check-added-large-files (500 KB), check-yaml, check-toml, check-json, `no-commit-to-branch` sobre `main`, validación de `policy/` contra su esquema y un gancho propio que bloquea `data/`, `*.parquet` y `*.csv` fuera de `tests/fixtures/`. | `.pre-commit-config.yaml`; CI corre `pre-commit run --all-files` |
| R-TEC-39 | Escaneo en cada PR: gitleaks, pip-audit sobre el lock exportado y OSV-Scanner; escaneo de la imagen publicada. Una vulnerabilidad crítica, o alta y explotable en nuestro uso, bloquea la fusión salvo excepción con fecha de vencimiento. | reportes del CI; registro de excepciones |
| R-TEC-40 | Commits de **una línea** en estilo convencional (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `ci:`, `build:`, `chore:`), en español, sin cuerpo ni remolques; una intención por commit; ramas cortas y PR a `main`. | comprobación en CI sobre los mensajes del PR (una línea, prefijo válido) |
| R-TEC-41 | ADR en `docs/adr/` con formato MADR (contexto, opciones, decisión, consecuencias, estado y principio que la guía); toda D-xx técnica y toda DP-TEC aprobada tiene su ADR; el Comité de Plataforma los aprueba con acta. | índice de ADR enlazado desde [Decisiones](../Diseno/Decisiones.md) |
| R-TEC-42 | Cada paquete de `src/latam_bank/` tiene un README corto (responsabilidad, contratos, límites); las APIs públicas llevan docstring en español; los tipos del dominio usan los nombres de [06](../Diseno/06_Arquitectura.md), sección 5. | lista de revisión del PR |
| R-TEC-43 | Frontend en TypeScript con `strict: true`, ESLint, Prettier, Vitest y Playwright; los tipos de los componentes se **generan** desde el JSON Schema de los modelos Pydantic, nunca se redefinen a mano. | CI de `web/`; el archivo generado no difiere del versionado |
| R-TEC-44 | La máquina limpia solo necesita git, Docker (con Compose), uv y just; `just setup demo` funciona en Linux y en Windows 11 con Docker Desktop y Git Bash, y el frontend se construye dentro de Docker. | prueba de Auditoría en F7 en ambos sistemas, con el tiempo registrado |

### 2.6 Especificación del núcleo: motor de flujo, estado durable, idempotencia y retoma

#### 2.6.1 Tipos del dominio

Precisan los contratos de [06](../Diseno/06_Arquitectura.md), sección 5. Todos son modelos Pydantic v2
inmutables (`frozen=True`), con validación estricta y sin `float` para dinero.

| Tipo | Campos principales | Invariantes | Lo construye |
|---|---|---|---|
| `CustomerRef` | valor opaco (token determinista de plata) | nunca el documento ni el número de cliente en claro | solo identidad, dentro de la sesión |
| `Dinero` | `monto: Decimal`, `moneda: Literal["COP", "MXN", "ARS", "USD", "BRL"]` | monto mayor o igual a 0, cuantizado a 2 decimales; la moneda es la del registro (D7) | cualquiera, validado |
| `SesionAutenticada` | `sid`, `cliente: CustomerRef`, `acr`, `amr`, `auth_time`, `exp`, `canal` | constructor privado; vigencia evaluada con el `Reloj` | solo `services.identidad` |
| `TurnoEntrante` | `turno_id` (UUIDv7), `conversacion_id`, `canal`, `texto`, `idioma_detectado`, `confianza_asr`, `dtmf`, `ref_sesion` | texto de 2.000 caracteres como máximo; `turno_id` único | superficies |
| `Interpretacion` | motivo, urgencia, entidades, confianza, idioma, `fuera_de_alcance` | no contiene acciones ni identificadores de cliente | comprensión |
| `HechoVerificado[T]` | `valor: T`, `fuente` (servicio y operación), `obtenido_en`, `id_consulta` | solo lo construye la capa de herramientas | herramientas |
| `ReglaDePolitica` | `id`, `version`, `norma`, `fecha_consulta`, `valor` | cargada de `policy/v1` validada | política |
| `Decision` | ruta, acción, `requiere_confirmacion`, motivo, `regla_id` | la produce `transicionar()` | motor |
| `SolicitudConfirmacion` | `nonce`, acción, monto leído de la base, transacción enmascarada, `expira_en`, canal, `sid` | se persiste antes de mostrarse | motor |
| `Confirmacion` | `nonce`, acción, monto, canal, evidencia (evento de aprobación, "sí" transcrito con su confianza, o DTMF) | coincide con una `SolicitudConfirmacion` viva de la misma sesión y canal; un solo uso | el motor, al validar la evidencia que envía la superficie (precisión sobre 06, sección 5) |
| `AccionVerificada` | acción, resultado releído (`HechoVerificado`), llave de idempotencia | solo existe después de la relectura | herramientas |
| `RespuestaTipada` | bloques (texto libre, plantilla con id y variables, componente), marcas para voz | cada cifra de un bloque libre está respaldada por un hecho o una regla del contexto | redacción y plantillas |
| `PaqueteTraspaso` | solicitud, hechos, interpretaciones, conflictos, acciones, evidencia (ids de traza), preguntas abiertas, motivo, idioma, prioridad | hechos e interpretaciones en listas de tipos distintos | motor |
| `EventoTraza` | nombre, atributos, momento | sin datos personales en claro | todos |

#### 2.6.2 Máquina de estados

Los estados son los de [01](../Diseno/01_Interacciones_y_criterios.md), sección 4. El motor sigue el
patrón **núcleo funcional y cáscara imperativa**: `transicionar()` es pura y decide; la cáscara ejecuta los
efectos, con sus llaves, y devuelve los resultados como eventos.

```python
class Estado(StrEnum):
    INICIO = "inicio"
    COMPRENDIENDO = "comprendiendo"
    ACLARANDO = "aclarando"
    AUTENTICANDO = "autenticando"
    IDENTIFICANDO_TRANSACCION = "identificando_transaccion"
    EXPLICANDO = "explicando"  # R1
    CLASIFICANDO_MOTIVO = "clasificando_motivo"
    CONTENIENDO = "conteniendo"  # bloqueo (R3)
    URGENTE = "urgente"  # R4
    CONFIRMANDO_ACCION = "confirmando_accion"
    EJECUTANDO = "ejecutando"
    VERIFICANDO = "verificando"
    INFORMANDO = "informando"
    CIERRE = "cierre"
    FALLA_SEGURA = "falla_segura"  # R8
    TRASPASO = "traspaso"  # R4 y R5
    ABSTENCION = "abstencion"  # R6
    NEGADO = "negado"  # R7


TRANSICIONES: Final[Mapping[Estado, frozenset[Estado]]] = {...}  # tabla explícita, revisada contra 01


@dataclass(frozen=True)
class Transicion:
    desde: Estado
    hacia: Estado
    evento: TipoEvento
    regla_id: str | None
    efectos: tuple[Efecto, ...]  # consultas, acciones, OTP, respuesta, traspaso


def transicionar(
    estado: EstadoConversacion, evento: Evento, politica: Politica, ahora: datetime
) -> Transicion:
    """Sin E/S y determinista: toda decisión de ruta, acción y escalamiento vive aquí (P4)."""
```

- **Eventos:** `TurnoRecibido` (con la `Interpretacion`), `ResultadoEfecto` (hecho, acción verificada o
  falla tipada), `ConfirmacionRecibida`, `SesionCambiada`, `PedidoHumano`, `FallaAutorizacion` y `Tick`
  (vencimientos, ventana de 24 horas del modo WhatsApp).
- **Efectos:** `Consultar`, `Ejecutar` (exige `Confirmacion`), `SolicitarOtp`, `EmitirRespuesta`,
  `EncolarTraspaso`.
- **Ciclo de un turno:** idempotencia del turno; carga del estado con su versión; comprensión (fuera del
  núcleo funcional; su salida entra como evento); `transicionar()` repetido mientras haya efectos
  síncronos, con un máximo de 8 pasos por turno [S]; persistencia en una sola transacción; respuesta a la
  superficie; cierre de la traza.

#### 2.6.3 Estado durable (Postgres 16)

```sql
-- esquema nucleo
conversaciones (id uuid pk, cliente_ref text null, estado text, version int, politica_version text,
                canal_origen text, idioma text, datos jsonb, creada_en timestamptz,
                actualizada_en timestamptz, cerrada_en timestamptz null, ruta_final text null)
turnos         (id uuid pk, conversacion_id uuid fk, canal text, recibido_en timestamptz,
                texto_redactado text, respuesta jsonb, estado_resultante text)
transiciones   (conversacion_id uuid, numero int, desde text, hacia text, evento text, regla_id text,
                en timestamptz, traza_id text, primary key (conversacion_id, numero))
efectos        (id uuid pk, conversacion_id uuid, numero_transicion int, tipo text,
                llave_idempotencia text unique, estado text,  -- pendiente, en_curso, hecho, fallido, incierto
                intentos int, resultado jsonb, actualizado_en timestamptz)
decisiones_autorizacion (id bigserial pk, conversacion_id uuid, sid text, accion text, recurso text,
                resultado text, motivo text, regla_id text, politica_version text,
                entrada_hash text, cadena_hash text, en timestamptz)
sesiones       (sid text pk, cliente_ref text, acr text, canal text, emitida_en timestamptz,
                expira_en timestamptz, revocada_en timestamptz null)
desafios_otp   (id uuid pk, sid text, codigo_hmac text, expira_en timestamptz, intentos int,
                consumido_en timestamptz null)
confirmaciones_pendientes (nonce text pk, conversacion_id uuid, sid text, canal text, accion text,
                monto numeric(18,2), moneda text, transaccion_ref text, expira_en timestamptz,
                usada_en timestamptz null)
traspasos      (id uuid pk, conversacion_id uuid, paquete jsonb, cola text, prioridad int, idioma text,
                creado_en timestamptz, tomado_en timestamptz null, tomado_por text null)
costos_turno   (turno_id uuid, componente text, unidades numeric, precios_version text, costo_usd numeric)

-- esquema bian (lo que "crea" el banco simulado; el oro no se escribe, D-08)
casos          (id text pk, cliente_ref text, transaccion_ref text, motivo text, monto numeric(18,2),
                moneda text, pais text, radicado_en timestamptz, plazo_regla_id text, estado text,
                tareas_back_office jsonb, llave_idempotencia text unique)
               -- índice único parcial (cliente_ref, transaccion_ref) where estado in ('abierto', 'en_proceso')
bloqueos_tarjeta (id text pk, cliente_ref text, tarjeta_ref text, bloqueado_en timestamptz, motivo text,
                llave_idempotencia text unique)
idempotencia_servicio (llave text pk, huella_solicitud text, respuesta jsonb, creada_en timestamptz)
```

Migraciones con Alembic; acceso con SQLAlchemy 2 asíncrono y asyncpg; particiones mensuales en `turnos`,
`transiciones` y `decisiones_autorizacion` cuando el volumen lo pida (producción).

#### 2.6.4 Idempotencia en tres niveles

| Nivel | Llave | Dónde se garantiza | Escenario |
|---|---|---|---|
| Turno | `turno_id` UUIDv7 que genera la superficie; en AG-UI es el `runId` | `turnos.id` único; un turno repetido devuelve la respuesta registrada | reintentos de red, doble clic |
| Efecto | SHA-256 de (conversación, número de transición, tipo de efecto, recurso), enviada como cabecera `Idempotency-Key` ([borrador del IETF](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)) | `efectos.llave_idempotencia` y `idempotencia_servicio` en el servicio | reintento acotado, caída entre la llamada y el commit, retoma (D5, D6, V6) |
| Negocio | (cliente, transacción) con caso abierto | índice único parcial en `bian.casos` | A5: reclamo ya abierto |

#### 2.6.5 Retoma entre canales

1. La continuidad se identifica por **cliente y conversación abierta**, no por canal: la conversación guarda el
   `cliente_ref` desde que hay sesión.
2. Al autenticarse en un canal nuevo (V6: empezó en chat, llama por voz), el motor busca conversaciones
   abiertas del cliente dentro de la ventana de retoma y ofrece continuar.
3. El resumen para el cliente se **renderiza desde el estado tipado** (qué se sabe, qué se hizo, qué falta),
   no lo escribe un modelo; las acciones hechas aparecen como hechos verificados y no se repiten.
4. La sesión es del canal: el canal nuevo exige su propia autenticación con el `acr` necesario, y toda
   `SolicitudConfirmacion` pendiente del canal anterior queda invalidada.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-45 | El estado de la conversación vive en `conversaciones.datos` como modelo Pydantic con `schema_version`; el historial de mensajes nunca es fuente de estado (P4). | propiedad: reconstruir el estado solo desde la base produce las mismas decisiones que el proceso vivo |
| R-TEC-46 | Solo `transicionar()` cambia el estado, contra la tabla `TRANSICIONES`; una transición no listada lleva a `FALLA_SEGURA` y queda registrada. | máquina de estados de Hypothesis con eventos aleatorios; prueba que compara la tabla con [01](../Diseno/01_Interacciones_y_criterios.md), sección 4 |
| R-TEC-47 | Pedir un humano lleva a `TRASPASO` en el mismo turno desde cualquier estado; quedar fuera de alcance lleva a `ABSTENCION`; una falla de autorización lleva a `NEGADO`. | propiedades para E4, V11, F1 a F5 y S1 a S10 |
| R-TEC-48 | Límites: 8 pasos por turno y, por conversación, 30 turnos del cliente, 12 llamadas al LLM, 60.000 tokens y 20 minutos de voz [S] (Gobierno confirma); al agotarse, traspaso con motivo "presupuesto" (OWASP LLM10). | pruebas; contadores en la traza raíz |
| R-TEC-49 | Cada turno es una transacción de base: carga con versión (bloqueo optimista), transiciones, efectos pendientes y avance de versión; un conflicto de versión obliga a releer y reprocesar, como máximo 2 veces. | prueba de concurrencia: dos turnos simultáneos por chat y por voz producen un solo efecto |
| R-TEC-50 | Un `turno_id` repetido devuelve la respuesta ya registrada, sin nuevas transiciones ni efectos. | prueba de repetición |
| R-TEC-51 | Todo efecto que escribe lleva su `Idempotency-Key`; el servicio guarda llave y huella de la solicitud durante 7 días y devuelve la misma respuesta; la misma llave con otra huella recibe 422. | pruebas de contrato; prueba que mata el proceso entre la llamada y el commit y verifica un solo caso |
| R-TEC-52 | Un caso abierto por cliente y transacción, garantizado por el índice único parcial (A5). | prueba de la restricción; escenario A5 |
| R-TEC-53 | Una escritura sin respuesta (tiempo agotado) queda en estado `incierto`; el motor reconsulta con la misma llave antes de afirmar nada y nunca informa éxito sin `AccionVerificada` (P6). | inyección de fallas D2 sobre radicar y bloquear |
| R-TEC-54 | Retoma entre canales por cliente y conversación abierta, con ventana de 72 horas [S] (Gobierno confirma); resumen renderizado desde el estado, sin preguntas repetidas ni acciones duplicadas (V6, D6). | escenario V6: cero preguntas repetidas y el mismo número de efectos |
| R-TEC-55 | La autenticación y las confirmaciones no viajan entre canales. | prueba: confirmación pendiente en chat y retoma por voz exigen nueva confirmación |
| R-TEC-56 | `policy/v1` se valida contra su JSON Schema al arrancar; su versión y huella quedan en cada traza y en cada `Decision`; una política inválida impide arrancar el servicio. | prueba de arranque con política inválida; atributo `latam.politica.version` |

### 2.7 Capa de herramientas, punto de decisión y servicios simulados BIAN

#### 2.7.1 Catálogo de herramientas

Los dominios BIAN salen de la [investigación 17](../Investigacion/17_VP_Tecnologia.md) y se confirman contra
el [repositorio público de BIAN](https://github.com/bian-official/public) en F3 [A].

| Herramienta | Firma (resumen) | Dominio BIAN [A] | Nivel `acr` | Confirmación | *Timeout* y reintentos | Verificación posterior |
|---|---|---|---|---|---|---|
| `consultar_transacciones` | `(sesion, filtro) -> HechoVerificado[list[TransaccionResumen]]` | Current Account, Credit Card | consulta | no | 1,5 s; 2 | no aplica |
| `obtener_ficha` | `(sesion, CargoPropio) -> HechoVerificado[Ficha]` | lectura de transacción más directorio de comercios del equipo | consulta | no | 1,5 s; 2 | no aplica |
| `consultar_estado_tarjeta` | `(sesion, TarjetaPropia) -> HechoVerificado[EstadoTarjeta]` | Issued Device Administration | consulta | no | 1,5 s; 2 | no aplica |
| `bloquear_tarjeta` | `(sesion, TarjetaPropia, Confirmacion) -> AccionVerificada` | Issued Device Administration | acción | sí | 3 s; 2 con la misma llave | relee el estado: bloqueada |
| `radicar_caso` | `(sesion, CargoPropio, MotivoDisputa, Confirmacion) -> AccionVerificada[CasoRadicado]` | Card Case | acción | sí | 3 s; 2 con la misma llave | relee el caso creado |
| `consultar_caso` | `(sesion, RefCaso \| None) -> HechoVerificado[EstadoCaso]` | Card Case, Customer Case Management | consulta | no | 1,5 s; 2 | no aplica |
| `puntaje_fraude` | `(sesion, CargoPropio) -> HechoVerificado[PuntajeFraude]` | Fraud Diagnosis | consulta | no | 1,5 s; 2 | no aplica |
| `consultar_tasa_cambio` | `(sesion, fecha, par) -> HechoVerificado[Tasa]` | datos de referencia | consulta | no | 1 s; 2 | no aplica |
| `solicitar_otp`, `verificar_otp` | `(sesion_o_desafio, ...)` | Party Authentication | ninguno o consulta | no | 1 s; 0 | no aplica |
| `encolar_traspaso` | `(PaqueteTraspaso) -> HechoVerificado[TicketTraspaso]` | Customer Case Management | ninguno (humano siempre disponible, P7) | no | 1 s; 2 | relee el ticket |

`CargoPropio` y `TarjetaPropia` solo se obtienen de un `HechoVerificado` producido con la misma sesión: no
hay forma de construir el tipo para un recurso de otro cliente ([investigación 8](../Investigacion/08_IA_con_tipos_seguros.md)).

#### 2.7.2 Punto de decisión (PDP) propio

Evalúa, en este orden, y se detiene en la primera negación: sesión vigente según el `Reloj`; sesión no
revocada; `acr` suficiente para la acción (tabla de `policy/v1`); dueño del recurso igual al cliente de la
sesión; confirmación válida si la acción la exige; límites de autonomía de la política (monto, estado de la
cuenta, D9); historial de la sesión (tres negaciones seguidas exigen humano, S8). Negación por defecto: una
acción que no está en la tabla se niega. El resultado es `Permitido` o `Denegado(motivo, regla_id,
reto_acr)`, y cada evaluación se registra (R-TEC-58).

#### 2.7.3 Servicios simulados

```
Party Authentication           POST /PartyAuthentication/Initiate          sesión de prueba confiable
                               POST /PartyAuthentication/{id}/Evaluate     verifica OTP y eleva acr
                               GET  /.well-known/jwks.json
Current Account, Credit Card   GET  /CurrentAccount/{cr}/Transactions/Retrieve?desde&hasta&monto&comercio
Issued Device Administration   GET  /IssuedDeviceAdministration/{cr}/Retrieve
                               PUT  /IssuedDeviceAdministration/{cr}/Update     bloqueo, con Idempotency-Key
Card Case                      POST /CardCase/Initiate                          radicar, con Idempotency-Key
                               GET  /CardCase/{cr}/Retrieve
Fraud Diagnosis                GET  /FraudDiagnosis/{transaccion}/Retrieve      fraud_score como dato
Customer Case Management       POST /CustomerCaseManagement/Initiate            traspaso a la cola humana
Plano de control (operador)    POST /_control/fallas                            solo con credencial de operador
```

Los servicios corren en `lb-bian` (FastAPI), leen el oro operacional con DuckDB en modo solo lectura
(Parquet montado desde Cloud Storage en la nube, carpeta local en `local`) y escriben casos y bloqueos en el
esquema `bian` de Postgres. Cada contrato declara su **limitación**: por ejemplo, que el bloqueo es un cambio
de estado simulado sin red de tarjetas, que el caso no llega a una red de contracargos y que el abono
provisional de México es una tarea pendiente del back office.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-57 | Las herramientas exigen `SesionAutenticada` en su firma y, si la acción tiene efecto, `Confirmacion`; el cliente sale de la sesión; ninguna herramienta recibe identificador de cliente, documento ni número de cuenta como texto. | pyright estricto; prueba que inspecciona las firmas del catálogo |
| R-TEC-58 | Toda llamada pasa por el PDP antes de ejecutarse; cada decisión, permitida o negada, se registra en `decisiones_autorizacion` con huella encadenada por conversación y como evento del span. | propiedades: S1 a S10 rechazados en la capa de herramientas; script que verifica la cadena de huellas |
| R-TEC-59 | Los servicios autorizan por su cuenta (defensa en profundidad y exigencia del enunciado de aplicar el acceso en la capa de servicio o de herramientas): verifican firma y vigencia del JWT, el `acr` y que el recurso pertenezca al `sub`; si el nivel no alcanza, responden 401 con el reto de RFC 9470. | pruebas de contrato: recurso ajeno da 403; `acr` bajo da 401 con `WWW-Authenticate` |
| R-TEC-60 | Contratos OpenAPI 3.1 versionados en `contracts/openapi/`; el CI compara el contrato generado con el versionado (un cambio incompatible exige versión mayor) y corre Schemathesis contra el servicio. | CI |
| R-TEC-61 | Cada contrato lleva `x-bian-service-domain` confirmado contra BIAN en F3 y `x-limitaciones` con lo que se simula y lo que no. | revisión del contrato |
| R-TEC-62 | El oro operacional se abre en solo lectura y toda consulta filtra por el cliente de la sesión en la consulta misma (nunca leer todo y filtrar después); las escrituras van solo al esquema `bian` (D-08). | DuckDB con `read_only`; pruebas del constructor de consultas |
| R-TEC-63 | La inyección de fallas (error, lentitud, tiempo agotado, datos corruptos) solo se activa por el plano de control con credencial de operador; en `demo` está apagada salvo durante la demostración de caída segura, y cada activación queda registrada. | llamada con sesión de cliente recibe 403; registro de auditoría |
| R-TEC-64 | Después de toda acción la herramienta relee el estado y solo construye `AccionVerificada` si coincide; si no coincide, el efecto queda `incierto` y el flujo va a R8. | prueba con escritura exitosa y relectura distinta |
| R-TEC-65 | Ningún movimiento de dinero: no existe herramienta de pagos; el abono provisional de México se registra como tarea pendiente dentro del caso, nunca como acción ejecutada ([05](../Diseno/05_Cobertura_del_enunciado.md), punto 12). | catálogo de herramientas; verificación del escenario N6 |

### 2.8 Identidad

| Parámetro | Valor | Quién lo fija |
|---|---|---|
| Formato | JWT firmado ES256 con `kid`; emisor `https://identidad.latambank.test`; audiencia `latam-bank-nucleo` | Tecnología |
| Reclamos | `iss`, `aud`, `sub` (`CustomerRef`), `sid`, `iat`, `auth_time`, `exp`, `acr`, `amr`, `canal` | Tecnología |
| Nivel `urn:latambank:acr:consulta` | sesión de prueba confiable del canal (inicio de sesión simulado en la web; OTP al dispositivo simulado en voz) | Gobierno aprueba |
| Nivel `urn:latambank:acr:accion` | OTP reciente: `amr` contiene `otp` y `auth_time` no tiene más de 300 s | Gobierno aprueba |
| Vigencia | 15 minutos por inactividad y 60 minutos absolutos [S] | Gobierno aprueba |
| OTP | 6 dígitos; vence en 300 s; 3 intentos; 3 envíos por cada 15 minutos; se guarda su HMAC | Gobierno aprueba |
| Reto insuficiente (RFC 9470) | `WWW-Authenticate: Bearer error="insufficient_user_authentication", acr_values="urn:latambank:acr:accion", max_age=300` | [RFC 9470](https://www.rfc-editor.org/rfc/rfc9470) |
| Llaves | local: EC P-256 en `~/.latam-bank/claves/`, creada por `just setup`; nube: llave asimétrica `EC_SIGN_P256_SHA256` de Cloud KMS, no exportable | Tecnología |
| JWKS | `/.well-known/jwks.json` en `lb-bian`; los verificadores lo guardan 5 minutos | Tecnología |
| Reloj | `Reloj` con `ahora()` en UTC con zona y `monotonico()`; implementaciones `RelojSistema`, `RelojSimulado`, `RelojCongelado` | Tecnología |

Las identidades de prueba de la sesión confiable se generan con `just identidades` desde la vista segura de
clientes y se guardan solo en local o en Secret Manager; ningún documento ni repositorio las contiene. El
OTP se entrega a un **dispositivo simulado** (una vista de `lb-staff` en la demo), nunca al modelo.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-66 | Solo el servicio de identidad emite sesiones; el núcleo verifica firma, `iss`, `aud` y `exp` y construye `SesionAutenticada` con un constructor privado. | import-linter; prueba que intenta construir la sesión desde otro módulo y falla |
| R-TEC-67 | Un documento o un número de cliente nunca autentica, y la voz tampoco; el factor para acciones es el OTP (enunciado; D-18). | escenarios S4 y V9 |
| R-TEC-68 | Los niveles `acr` y el `max_age` son los de la tabla; toda acción con efecto exige `accion`; la respuesta de nivel insuficiente tiene la forma de RFC 9470. | pruebas de contrato |
| R-TEC-69 | Vigencias y parámetros del OTP salen de la configuración y del `Reloj`; ninguna prueba duerme: adelanta el reloj. | pruebas con `RelojCongelado`; `banned-api` de R-TEC-32 |
| R-TEC-70 | El OTP en claro no se persiste, no aparece en trazas ni logs y no llega al LLM; se guarda su HMAC con una llave de Secret Manager. | prueba que siembra un OTP conocido y lo busca en logs, trazas y base |
| R-TEC-71 | En la nube la llave de firma vive en Cloud KMS y no se exporta; en local, en un archivo fuera del repositorio; la rotación publica dos versiones en el JWKS durante el traslape. | nivel de protección de la llave; gitleaks; JWKS con dos `kid` después de rotar |
| R-TEC-72 | Revocan la sesión: cerrar sesión, cambiar de canal con una acción pendiente y tres negaciones seguidas del PDP (S8). | propiedad para S8; `sesiones.revocada_en` |

### 2.9 Superficie de chat (AG-UI)

**Tecnología.** Frontend en React 19, TypeScript y Vite (`web/chat`), que habla con el servidor con el
cliente oficial de AG-UI (`@ag-ui/client`) sin un servidor intermedio de Node; servidor en FastAPI dentro de
`lb-chat`, que codifica los eventos con el SDK de Python de AG-UI (`ag-ui-protocol`) y los envía por SSE
([AG-UI](https://docs.ag-ui.com/introduction)). `threadId` es la conversación y `runId` es el `turno_id`
(idempotencia de turno).

| Lo que produce el motor | Evento AG-UI | Detalle |
|---|---|---|
| inicio del turno | `RUN_STARTED` | con `threadId` y `runId` |
| texto al cliente | `TEXT_MESSAGE_START`, un `TEXT_MESSAGE_CONTENT` por frase filtrada, `TEXT_MESSAGE_END` | nunca tokens sueltos del modelo |
| componente tipado | llamada a una herramienta **de interfaz** (`TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`) | la interfaz la dibuja; en el servidor no se ejecuta nada |
| confirmación | herramienta de interfaz `solicitar_confirmacion` con `nonce`, acción, monto de la base y vencimiento | la respuesta vuelve como mensaje de herramienta en el siguiente `RunAgentInput`; el motor valida el `nonce` |
| estado visible del caso | `STATE_SNAPSHOT` y `STATE_DELTA` (JSON Patch) | solo campos enmascarados |
| fin o error | `RUN_FINISHED` o `RUN_ERROR` | el error lleva un código, nunca el detalle interno |

| Componente | Contenido | Degradación a WhatsApp |
|---|---|---|
| `FichaTransaccion` | comercio (descriptor y marca del directorio del equipo), fecha y hora del evento, monto y moneda, estado, canal, compras previas | texto con la ficha y 2 botones ("La reconozco", "No la reconozco") |
| `OpcionesTransaccion` | hasta 10 transacciones enmascaradas (fecha, comercio, monto) | lista de hasta 10 filas |
| `SolicitudConfirmacion` | acción, monto leído de la base, transacción enmascarada, vencimiento | 2 botones ("Confirmo", "No") |
| `EstadoCaso` | número de caso, estado, plazo y norma | texto |
| `AvisoTraspaso` | motivo, cola, espera declarada (E7) | texto con 1 botón o plantilla fuera de la ventana |
| `SolicitudOtp` | canal de entrega simulado y vencimiento | plantilla de autenticación |

**Emisión por frases.** El texto libre de la redacción se acumula hasta un fin de frase (punto, signo de
interrogación o de exclamación, punto y coma o salto de línea, seguido de espacio o de fin), sin cortar
números (`1.234,56`), abreviaturas de una lista cerrada (`Sr.`, `Sra.`, `No.`, `núm.`, `aprox.`) ni
enumeraciones; si una frase pasa de 200 caracteres se corta en el último espacio. Cada frase pasa el filtro
de salida (R-TEC-75) y solo entonces se emite. Si una frase falla, se detiene la emisión de esa respuesta y
se envía la plantilla de respaldo del estado, con un evento `filtro_salida.bloqueo` en la traza.

**Modo WhatsApp simulado.** Un selector de la demo dibuja cada componente con su degradación y aplica la
ventana de 24 horas con el `Reloj`: fuera de la ventana solo salen plantillas del catálogo de Clientes.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-73 | La superficie de chat solo traduce: convierte la entrada en `TurnoEntrante` y la `Decision` o `RespuestaTipada` en eventos AG-UI; no llama herramientas ni modelos. | import-linter; revisión |
| R-TEC-74 | El texto llega al cliente por frases que ya pasaron el filtro de salida, nunca como tokens crudos del modelo. | prueba con un modelo simulado que inserta un dato sensible a mitad de frase: nunca llega al cliente |
| R-TEC-75 | Filtro de salida por frase, en este orden: enmascaramiento de datos sensibles; **anclaje de cifras** (cada monto, fecha, plazo o estado debe coincidir con un `HechoVerificado` o una `ReglaDePolitica` del contexto de redacción); afirmaciones prohibidas sin `AccionVerificada` ("radicado", "bloqueada", "reembolso", "abonado" y sus equivalentes en portugués); Model Armor en la nube si su p95 medido es de 250 ms o menos. | pruebas por verificación; métrica de bloqueos |
| R-TEC-76 | Montos, plazos, confirmaciones y el informe de acciones salen de **plantillas deterministas**, nunca del modelo. | la traza muestra el id de plantilla de esos bloques; prueba |
| R-TEC-77 | La aprobación se acepta solo si el `nonce` existe, está vigente (5 minutos [S]), pertenece a la misma sesión y canal y no se usó; el monto que se muestra es el de la base. | pruebas de repetición, de otra sesión y de vencimiento |
| R-TEC-78 | Cada componente tiene su degradación a WhatsApp probada (3 botones de 20 caracteres como máximo; listas de 10 filas como máximo) y el modo simulado respeta la ventana de 24 horas. | propiedades que generan componentes; prueba de interfaz del modo simulado |
| R-TEC-79 | Primer texto visible con p50 menor a 1 s; turno completo con p50 menor a 2 s y p95 menor a 5 s ([06](../Diseno/06_Arquitectura.md), sección 6), medidos en el servidor y en el navegador. | spans; tiempos de Playwright |
| R-TEC-80 | Seguridad del navegador: política de seguridad de contenido estricta sin scripts en línea, HSTS, token de sesión solo en memoria (nunca en `localStorage`), CORS limitado al origen propio, límite de 20 turnos por minuto por sesión y 60 solicitudes por minuto por IP [S]. | prueba de cabeceras; prueba de límite de tasa |

### 2.10 Superficie de voz (Pipecat en cascada)

```python
pipeline = Pipeline(
    [
        transporte.input(),  # WebSocket (nube), SmallWebRTC (local) o Twilio Media Streams
        stt,  # reconocimiento en streaming elegido en S1 (es-MX, es-CO, es-AR, pt-BR)
        agregador_turno,  # VAD de Silero y SmartTurn: deciden el fin del turno
        ProcesadorMotor(motor, reloj),  # arma TurnoEntrante con confianza y DTMF, llama al motor,
        # emite frases, plantillas y rellenos; no decide nada
        tts,  # síntesis en streaming, con marcas de tiempo por palabra si existen
        ObservadorHabla(registro),  # registra lo que el agente alcanzó a decir antes de una interrupción
        transporte.output(),
    ]
)
```

Los nombres exactos de clases dependen de la versión fijada de Pipecat [A]; la forma de la tubería no.

| Entorno | Transporte | Por qué |
|---|---|---|
| `local` | WebRTC entre pares (SmallWebRTC) desde el navegador | latencia mínima y sin servidores extra; cumple D-18 |
| `demo` | WebSocket del navegador a `lb-voz` (PCM de 16 kHz, mono, tramas de 20 ms, capturado con AudioWorklet y cancelación de eco del navegador); cliente web con el SDK de cliente de Pipecat | Cloud Run solo recibe HTTP, HTTP/2, WebSocket y gRPC; no recibe UDP, que es lo que usa WebRTC para el audio (documentación de Cloud Run; se reconfirma en S1). Tiempo máximo de solicitud: 60 minutos |
| `demo`, si S1 mide mala calidad por WebSocket | WebRTC gestionado (Daily o LiveKit Cloud) o un servidor TURN | cambia costo y dependencias; exige ADR |
| teléfono (opcional) | Twilio Media Streams por WebSocket hacia `lb-voz` (μ-law de 8 kHz, eventos DTMF) | Pipecat trae el serializador; no requiere UDP entrante |

**Detalles que deciden la calidad**

- Solo el resultado **final** del reconocimiento entra al motor; los parciales sirven para detectar que el
  cliente empezó a hablar (interrupción).
- La confianza del reconocimiento viaja en `TurnoEntrante.confianza_asr`; si el proveedor no la reporta,
  se trata como media.
- Rellenos honestos: si la herramienta que se va a llamar suele tardar más de 700 ms, se emite un relleno del
  catálogo de Clientes ("estoy revisando sus movimientos") **presintetizado** en caché, para no pagar la
  latencia de síntesis.
- Interrupciones: con marcas de tiempo por palabra del proveedor de síntesis, se registra el prefijo dicho;
  sin ellas, se estima por el audio efectivamente enviado. Una confirmación interrumpida no vale (V1).
- DTMF: el teclado de la página de voz envía mensajes de aplicación; Twilio envía sus eventos; ambos llegan
  como `TurnoEntrante.dtmf` (V8).
- Audio: se procesa en memoria; no se escribe en disco ni en trazas.

**Experimento nativo** (IA-8, primero en el orden de recorte). Gemini Live por Vertex AI con **una sola**
herramienta, `delegar_en_motor(texto_del_cliente)`, que devuelve el texto que el modelo debe decir; se mide
la desviación entre ese texto y la transcripción de lo que el modelo dijo. Precios de la Live API de Gemini
3.8 (endpoint regional): audio de entrada US$3,00 y audio de salida US$12,00 por millón de tokens, a 25 tokens
por segundo de audio; los tokens de turnos anteriores se vuelven a cobrar en cada turno [V]. Con una
ventana de contexto acotada, el costo ronda US$0,03 por minuto de llamada [S].

| Etapa de un turno de voz sin herramienta | p50 | p95 | Nota |
|---|---|---|---|
| Fin del turno (VAD con 200 ms de silencio y SmartTurn) | 250 ms | 400 ms | parámetros de IA (Voz) |
| Reconocimiento final después del fin del habla | 150 ms [P] | 350 ms [P] | depende del proveedor de S1 |
| Motor con plantilla | 30 ms | 80 ms | |
| Motor con LLM hasta la primera frase | 450 ms [P] | 1.000 ms [P] | |
| Síntesis hasta el primer audio | 150 ms [P] | 350 ms [P] | depende del proveedor de S1 |
| Transporte navegador y Cloud Run, ida y vuelta | 60 ms [A] | 150 ms [A] | medir desde Bogotá en S1 |
| **Total con plantilla** | **≈ 640 ms** | **≈ 1.330 ms** | cumple 06, sección 6 |
| **Total con LLM** | **≈ 1.060 ms** | **≈ 2.250 ms** | no cumple: la suma de percentiles 95 es una cota pesimista, pero la mediana ya excede 1,0 s |

**Consecuencia de diseño:** en voz, lo frecuente se responde con plantillas (que además son obligatorias
para lo crítico, D-18) y la redacción libre usa el modelo más rápido y se sintetiza desde la primera frase.
S1 confirma o corrige estas cifras.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-81 | La voz usa la misma API del motor que el chat; la tubería de voz no decide nada. | import-linter; prueba de paridad |
| R-TEC-82 | Transporte según la tabla: en Cloud Run solo WebSocket; cualquier WebRTC en la nube pasa por un proveedor gestionado o un TURN aprobado por ADR. | configuración; ADR |
| R-TEC-83 | Solo el resultado final del reconocimiento entra al motor. | prueba con parciales contradictorios |
| R-TEC-84 | Si la confianza del reconocimiento en un dato crítico (monto, fecha, dígitos) está bajo el umbral de la política, el motor lee de vuelta y exige "sí" explícito o DTMF; sin confianza reportada, se asume media. | escenario V2 |
| R-TEC-85 | Se registra lo que el agente alcanzó a decir antes de cada interrupción (`latam.voz.dicho_hasta`); una confirmación interrumpida no vale. | escenario V1 |
| R-TEC-86 | Relleno en 1,0 s o menos cuando una herramienta tarda más de 700 ms, tomado de un catálogo aprobado por Clientes y presintetizado; ningún relleno afirma una acción. | tiempos en la traza; revisión del catálogo |
| R-TEC-87 | Presupuesto de voz a voz: p50 de 1,0 s o menos y p95 de 2,0 s o menos sin herramienta, medido desde el fin del habla del cliente hasta el primer audio del agente, por acento e idioma. | spans por etapa; reportes de S1 y F5 |
| R-TEC-88 | El audio crudo no se persiste en operación: ni en disco, ni en trazas, ni en logs. Las grabaciones de evaluación, con consentimiento, viven fuera de la plataforma. | inspección del sistema de archivos del contenedor; búsqueda en logs |
| R-TEC-89 | Los webhooks de telefonía validan la firma del proveedor y rechazan lo que no está firmado. | prueba con firma inválida: 403 |
| R-TEC-90 | El experimento nativo corre detrás de `LB_FLAG_VOZ_NATIVA`, con una sola herramienta y medido contra la cascada sobre el mismo retenido de voz; no está en la ruta crítica. | bandera; lista de herramientas del experimento; reporte de 5.9 |

### 2.11 Gateway de IA

**Forma.** LiteLLM Proxy en `lb-gateway`, fijado por digest, con los guardarraíles escritos por el equipo
en `latam_bank.gateway.filtros` (código propio, tipado y probado, que LiteLLM invoca antes y después de cada
llamada). Esquema ilustrativo; las claves exactas dependen de la versión fijada [A]:

```yaml
model_list:
  - model_name: comprension          # comparado LLM de D-14 y respaldo; modelo ligero que elige IA
    litellm_params: {model: vertex_ai/<modelo-ligero-con-version>, vertex_location: us-central1, timeout: 2.5}
  - model_name: redaccion            # texto abierto; modelo rápido que elige IA
    litellm_params: {model: vertex_ai/<modelo-rapido-con-version>, vertex_location: us-central1, timeout: 8}
  - model_name: juez                 # familia distinta del sistema (D-20); la elige IA
  - model_name: simulador            # usuario simulado, familia distinta; la elige IA
  - model_name: generador            # conversaciones sintéticas (IA-1)
  - model_name: simulado             # LLM simulado para CI, local y carga
    litellm_params: {model: openai/simulado, api_base: "http://llm-simulado:8080/v1"}
router_settings: {num_retries: 1}
litellm_settings: {callbacks: ["otel"]}
guardrails:                          # implementados en latam_bank.gateway.filtros
  - redaccion_pii        # pre_call: Presidio y reconocedores propios
  - limite_prompt        # pre_call: tokens máximos por alias
  - model_armor_entrada  # pre_call, solo en demo
  - model_armor_salida   # post_call, solo en demo, para respuestas completas
```

**Endpoint regional o global.** El endpoint regional (`us-central1`) cuesta 10% más que el global en los
modelos Gemini de 2026 (por ejemplo, Gemini 3.8 Flash: US$0,825 frente a US$0,75 por millón de tokens de
entrada) [V]; el global no garantiza dónde se procesa. Se usa el **regional** por defecto [S] y Gobierno
decide si acepta el global.

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-91 | Toda llamada a un modelo de lenguaje pasa por el gateway con la **clave virtual del trabajador** que la hace (comprensión, redacción, juez, simulador, generador); nada llama al proveedor directo. | IAM y `banned-api` (R-TEC-06, R-TEC-32); conciliación de los registros de gasto del gateway con los spans |
| R-TEC-92 | El gateway redacta datos personales antes de cualquier modelo con Presidio y reconocedores propios para CURP, CC, DNI, CPF, número de tarjeta (con Luhn), CBU, CLABE, correo y teléfono; precisión y recuperación se miden sobre un conjunto etiquetado del equipo y Gobierno fija el umbral. | reporte de la prueba en CI |
| R-TEC-93 | Model Armor en la nube es una capa **adicional** de entrada y salida, con su plantilla versionada en Terraform; como su filtro de inyección analiza hasta 512 tokens ([investigación 10](../Investigacion/10_Gobernanza_y_gateway.md)), se le envía el mensaje del cliente y las frases de salida, no el prompt completo. Su aporte se mide aparte: detectados, falsos positivos sobre casos legítimos y ataques no detectados que la arquitectura igual contuvo. | tabla de la investigación 10 en el reporte de seguridad |
| R-TEC-94 | Límites por alias (tokens de prompt), presupuesto diario por clave virtual y tasa por minuto; excederlos devuelve un error tipado que el motor convierte en degradación (2.12). | configuración; prueba que agota el presupuesto |
| R-TEC-95 | Sin caché semántica de respuestas (riesgo de entregar a un cliente la respuesta de otro, investigación 10); solo la caché de prompt del proveedor para el prefijo estable. | configuración; revisión |
| R-TEC-96 | Los reintentos de modelo ocurren solo en el gateway (uno, ante 429 o 503, con espera exponencial y variación aleatoria); el cliente no reintenta, para no multiplicar la carga. | configuración; prueba que cuenta llamadas |
| R-TEC-97 | Cada alias apunta a una versión fija del modelo, registrada en cada traza (`gen_ai.response.model`) y en cada corrida; cambiarla es un cambio de configuración con ADR corto y revalidación ([04](../Diseno/04_Organizacion_y_roles.md), sección 11). | atributo de la traza contra la configuración |
| R-TEC-98 | El contenido de prompts y respuestas no se guarda en trazas por defecto; en `local` y `ci`, con datos del equipo, se puede activar ya redactado. | configuración por entorno; inspección de trazas de `demo` |

### 2.12 Confiabilidad

| Dependencia | *Timeout* | Reintentos | Interruptor de circuito | Si falla |
|---|---|---|---|---|
| Postgres | 1,5 s por sentencia; 2 s de conexión | 1, solo errores de conexión | 5 fallas en 30 s; abierto 15 s | N5 |
| Servicios BIAN de lectura | 1,5 s | 2 | 5 en 30 s; 15 s | "no pude consultar", nunca "no existe"; R8 u oferta de traspaso |
| Servicios BIAN de escritura | 3 s | 2, con la misma llave | 3 en 60 s; 30 s | N4; efecto `incierto` y reconsulta |
| Identidad y OTP | 1 s | 0 (los intentos de OTP cuentan) | 5 en 30 s; 15 s | pedir de nuevo o traspaso |
| Gateway, alias `comprension` | 2,5 s | 1, en el gateway | 5 en 60 s; 30 s | N3 |
| Gateway, alias `redaccion` | 3 s al primer token; 8 s en total | 1, en el gateway | 5 en 60 s; 30 s | N2 |
| Model Armor | 0,8 s | 0 | 5 en 60 s; 60 s | N1 |
| Reconocimiento de voz | 5 s sin transcripción después del fin del habla | 1 reconexión | 3 en 60 s | proveedor alterno si existe; menú DTMF; oferta de chat o traspaso |
| Síntesis de voz | 1,5 s al primer audio | 1 | 3 en 60 s | audios pregrabados de frases críticas; proveedor alterno |
| Cola humana | 1 s | 2 | 5 en 30 s | R8 con aviso honesto |

| Nivel | Disparador | Qué hace el sistema | Ruta típica |
|---|---|---|---|
| N0 | ninguno | todo disponible | la del caso |
| N1 sin Model Armor | interruptor abierto o bandera | sigue con filtros locales y lo registra (`latam.filtro_externo = no_disponible`) | la del caso |
| N2 sin redacción por LLM | interruptor de `redaccion` o presupuesto agotado | solo plantillas deterministas por idioma y registro | la del caso, con tono más rígido |
| N3 sin LLM | interruptores de todos los alias | comprensión solo con el clasificador aprendido; con baja confianza, opciones con botones (chat) o menú DTMF (voz) | la del caso o R5 |
| N4 sin escrituras BIAN | interruptor de escritura | informa, no ejecuta y ofrece traspaso con el paquete completo; nunca dice "radicado" | R8 o R5 |
| N5 sin base operativa | Postgres no disponible | no ejecuta ni afirma estado; mensaje de falla con la vía alterna (volver más tarde o línea humana) | R8 |
| N6 todo a humano | `LB_FLAG_TODO_A_HUMANO` (Gobierno, ante un incidente) | todo caso nuevo va a traspaso con paquete; el agente recoge y encola | R5 |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-99 | Los *timeouts* son los de la tabla, viven en configuración y su suma en la ruta de un turno cabe en el presupuesto del canal. | prueba que suma los *timeouts* de la ruta crítica contra el presupuesto |
| R-TEC-100 | Reintentos acotados: como máximo 2, solo ante fallas transitorias (conexión, 429, 502, 503, 504) y solo en operaciones idempotentes (lecturas y escrituras con llave); **nunca por lentitud** ([investigación 11](../Investigacion/11_Latencia_y_costo.md)); espera exponencial con variación aleatoria completa (base 100 ms, tope 1 s). | pruebas unitarias; escenario D1 con 2 reintentos como máximo en la traza |
| R-TEC-101 | Interruptor de circuito por dependencia con los parámetros de la tabla; su estado se ve en métricas y en la traza. | prueba de caos; métrica de interruptores abiertos |
| R-TEC-102 | Escalera de degradación N0 a N6; ante la duda se baja un nivel y nunca se inventa (P6). | una prueba de inyección de fallas por nivel; demostración de uno en la demo |
| R-TEC-103 | Caída segura (R8): ninguna afirmación falsa, reintento acotado, oferta de traspaso o de continuar después y estado persistido; la tasa de caída segura sobre fallas inyectadas es 100% ([01](../Diseno/01_Interacciones_y_criterios.md), sección 5.6). | métrica del arnés de evaluación |
| R-TEC-104 | El interruptor "todo a humano" se activa sin desplegar (variable del servicio o fila de configuración leída cada 30 s) y lo usa Gobierno ante un incidente ([04](../Diseno/04_Organizacion_y_roles.md), sección 11). | simulacro en F5 |
| R-TEC-105 | Sondas de arranque y de vida en cada servicio (`/salud/viva`; `/salud/lista` comprueba Postgres y dependencias críticas con 500 ms); apagado ordenado ante SIGTERM: termina los turnos en curso en 8 s o menos y, en voz, avisa al cliente y persiste el estado. | configuración de Cloud Run; prueba de SIGTERM |
| R-TEC-106 | La suma de instancias máximas por el tamaño máximo del pool de cada servicio no pasa del 80% de `max_connections` de Cloud SQL; LiteLLM y Phoenix cuentan. | validación en las variables de Terraform |

### 2.13 Capacidad

**Herramientas.** Locust para chat: usuarios virtuales que recorren guiones del **conjunto de desarrollo**
(nunca del retenido) contra el endpoint AG-UI. Un generador propio para voz: clientes de Pipecat que
transmiten audio sintetizado por WebSocket y miden el tiempo de voz a voz. Código en `tests/carga/`.

**Modos.** *Plataforma*: el alias apunta al LLM simulado, con una distribución de latencia ajustada a los
spans reales (lognormal), para hallar el punto de quiebre de la plataforma sin gastar tokens. *Real*: el
proveedor real, a baja escala, para medir la cola de latencia y los 429 del proveedor. Ambos se reportan
separados y etiquetados como **simulación** (P3).

**Protocolo.** Línea base con 1 conversación; rampa escalonada de 1, 2, 4, 8, 16, 32 y 64 conversaciones
concurrentes, 3 minutos por escalón; remojo de 30 minutos al 70% del quiebre; pico súbito. **Punto de
quiebre** = primer escalón con p95 fuera del presupuesto o con errores por encima de 1%. El **cuello de
botella** se identifica por el span que más crece.

**Modelo de capacidad.** Por la ley de Little, conversaciones concurrentes = llegadas por segundo por
duración. Con 50.000 llamadas al mes de 3 minutos y demanda plana en las 24 horas (así la trae el dataset,
[05](../Diseno/05_Cobertura_del_enunciado.md), sección 3.1), hay unas 3,5 llamadas simultáneas en promedio y
unas 7 en un pico de dos veces [S]: dos instancias de `lb-voz`. El límite real lo ponen las cuotas de los
proveedores y el costo, no el cómputo.

| Servicio | Límite que importa | Valor | Cómo se confirma en F0 |
|---|---|---|---|
| Vertex AI (Gemini) | cuota compartida dinámica: sin tope fijo por proyecto; responde 429 en congestión; el rendimiento aprovisionado da garantías | [A] | consola de cuotas y documentación de cuota compartida dinámica |
| Speech-to-Text V2 | sesiones de streaming concurrentes por región y duración máxima de un stream | [A] | página de cuotas de Speech-to-Text |
| Text-to-Speech | solicitudes por minuto | [A] | consola de cuotas |
| Model Armor | solicitudes por minuto | [A] | consola de cuotas |
| Cloud Run | instancias máximas por servicio; concurrencia por instancia | [A] | documentación de límites de Cloud Run |
| Cloud SQL `db-g1-small` | `max_connections` por defecto | [A] | `SHOW max_connections;` |
| Twilio | llamadas por segundo de la cuenta en pago por uso | [A] | página de precios de Twilio |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-107 | La prueba de capacidad usa Locust (chat) y el generador de voz propio, con guiones del conjunto de desarrollo. | scripts en `tests/carga/`; revisión de que no leen `eval/cases/holdout/` |
| R-TEC-108 | Se corren los dos modos (plataforma y real) y se reportan separados y etiquetados como simulación. | reporte de capacidad |
| R-TEC-109 | El reporte trae punto de quiebre, cuello de botella por span, costo por hora en el quiebre y la tabla de cuotas llena. | reporte de TEC-9 con consultas sobre platino |
| R-TEC-110 | La tabla de cuotas se llena en F0 con valores leídos en la consola y la forma de pedir aumento; ninguna cifra de cuota se supone. | tabla sin celdas [A] al cerrar F0 |

### 2.14 Observabilidad

| Span | Tipo | Atributos clave |
|---|---|---|
| `turno` (raíz, uno por turno) | SERVER | `gen_ai.conversation.id`, `latam.canal`, `latam.idioma`, `latam.estado.origen`, `latam.estado.destino`, `latam.ruta`, `latam.politica.version`, `service.version` (digest), `latam.flags`, `latam.reloj.as_of` |
| `chat {modelo}` (cada llamada al LLM) | CLIENT | `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `latam.trabajador`, `latam.costo.usd` |
| `politica.evaluar` | INTERNAL | `latam.regla.id`, `latam.decision` |
| `pdp.autorizar` | INTERNAL | `latam.pdp.resultado`, `latam.pdp.motivo`, `latam.pdp.regla` |
| `execute_tool {herramienta}` | CLIENT | `gen_ai.tool.name`, huella de la llave de idempotencia, `latam.reintentos`, `http.response.status_code` |
| `redaccion` o `plantilla` | INTERNAL | `latam.plantilla.id`, `latam.frases`, `latam.primer_texto_ms` |
| `filtro_entrada` y `filtro_salida` | INTERNAL | `latam.filtro.detectados`, `latam.filtro.bloqueos`, `latam.filtro_externo` |
| `voz.fin_turno`, `voz.stt`, `voz.tts`, `voz.transporte` | INTERNAL | `latam.voz.proveedor`, `latam.voz.confianza`, `latam.voz.dicho_hasta`, `latam.voz.primer_audio_ms` |

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-111 | Una traza por turno, enlazada a la conversación por `gen_ai.conversation.id`, con un span por cada etapa ejecutada; el 100% de los turnos está completo. | consulta de completitud sobre las trazas exportadas |
| R-TEC-112 | Se usan las convenciones semánticas GenAI de OpenTelemetry con la versión del paquete fijada, más atributos propios con prefijo `latam.`, catalogados en `latam_bank/observability/atributos.py` ([OpenTelemetry GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)). | pruebas que verifican atributos por span |
| R-TEC-113 | Exportación dual en la nube desde el SDK: OTLP hacia Phoenix (vista de LLM) y exportador de Cloud Trace (vista de infraestructura); en local, solo Phoenix. Un colector aparte solo si hace falta muestreo central. | la misma traza aparece en ambos |
| R-TEC-114 | Logs estructurados en JSON con los campos de correlación de Cloud Logging (`trace` y `spanId`), sin datos personales (procesador de redacción) y sin contenido de prompts. | prueba que busca patrones de documento, tarjeta, correo y OTP en los logs |
| R-TEC-115 | Métricas: tasa, errores y duración por servicio; latencia por etapa; rutas; traspasos; bloqueos de filtros; reintentos; interruptores abiertos; costo por hora. Paneles en Cloud Monitoring (versionados en Terraform) y en Phoenix y `lb-staff` en local. | JSON de los paneles en el repositorio |
| R-TEC-116 | Alertas de la nube: errores por encima de 2% durante 5 minutos; p95 del turno fuera del presupuesto durante 10 minutos; 429 del proveedor por encima de 5% durante 5 minutos; interruptor abierto; más de 3 bloqueos del filtro de salida en 10 minutos; gasto diario por encima del 20% del presupuesto. Destino: correo del equipo. | políticas de alerta en Terraform; alerta de prueba |
| R-TEC-117 | Retención propuesta (Gobierno aprueba, S-TEC-03): trazas y logs 30 días; estado de conversaciones 90 días; desafíos OTP 24 horas; llaves de idempotencia 7 días; audio 0. | retención de los buckets de logs; trabajos de purga con prueba |
| R-TEC-118 | Exportación a platino: `lb-exportar-trazas` convierte las trazas de cada corrida de evaluación en `trazas_resumen` (Parquet), sin contenido y con huella encadenada por conversación ([investigación 19](../Investigacion/19_Auditoria.md)); el reporte solo cita trazas exportadas. | script de verificación de la cadena; aceptación de Datos |

### 2.15 FinOps: costo por caso

```
costo por caso = Σ llamadas al LLM (tokens de entrada no cacheados × precio
                                    + tokens cacheados × precio de caché
                                    + tokens de salida × precio de salida)
               + minutos de reconocimiento × precio + caracteres (o tokens de audio) de síntesis × precio
               + tokens revisados por Model Armor × precio + minutos de telefonía × precio
               + (si hay traspaso) minutos humanos del traspaso × costo del minuto humano [S]
costo por resolución segura = costo total de los casos intentados / resoluciones seguras   ("no definido" si son 0)
infraestructura fija (Cloud SQL, instancias mínimas, balanceador) = se reporta aparte, prorrateada con su supuesto
```

La tabla `finops/precios.yaml` guarda cada precio con unidad, fuente, fecha de consulta y vigencia:

```yaml
version: "2026-09-27"
moneda: USD
modelos:
  gemini-3.8-flash:           # introductorio hasta el 31 de diciembre de 2026; luego 1,50 y 7,50
    entrada: 0.75
    entrada_cache: 0.075
    salida: 3.75
    unidad: millon_tokens
    endpoint: global          # el regional cuesta 10% más
    vigente_hasta: "2026-12-31"
    fuente: https://cloud.google.com/vertex-ai/generative-ai/pricing
voz:
  stt_google_v2_estandar: {precio: 0.016, unidad: minuto}
  tts_chirp3_hd: {precio: 30.0, unidad: millon_caracteres, gratis_mes: 1000000}
filtros:
  model_armor: {precio: 0.10, unidad: millon_tokens, gratis_mes: 2000000}
telefonia:
  twilio_us_entrante: {precio: 0.0085, unidad: minuto}
  twilio_media_streams: {precio: 0.0044, unidad: minuto}
humano:
  minuto_agente: {precio: null, supuesto: "se fija con Clientes y Datos desde la duración del dataset"}
```

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-119 | El costo por caso y por resolución segura se calcula con la fórmula de arriba, en consultas sobre platino; "no definido" cuando no hay resoluciones seguras (enunciado). | pruebas de las consultas con un *fixture* de costos |
| R-TEC-120 | Todo precio vive en `finops/precios.yaml` con fuente, fecha y vigencia; cada corrida registra la versión de la tabla. | archivo; atributo `latam.precios.version` |
| R-TEC-121 | El uso se toma de lo que reporta el proveedor en la traza (tokens, segundos de audio, caracteres); se estima solo si el proveedor no lo reporta, y se marca. | presencia de atributos de uso; marca `latam.uso.estimado` |
| R-TEC-122 | Conciliación al cierre: exportación de facturación a BigQuery y comparación entre lo estimado y lo facturado por servicio; una diferencia de más de 15% se explica en el reporte. | tabla de conciliación |
| R-TEC-123 | La proyección de producción va en su propia sección, etiquetada como **proyección** y con supuestos de volumen, mezcla y precios vigentes a la fecha de operación (no los introductorios). | revisión de Auditoría |

### 2.16 Términos nuevos para el glosario común

| Término | Significado |
|---|---|
| Unidad desplegable | proceso con su imagen, comando, cuenta de servicio y escala (sección 2.1) |
| Efecto | operación que el motor pide a la cáscara (consultar, ejecutar, encolar); lleva llave de idempotencia |
| Llave de idempotencia | huella que hace que repetir un efecto no lo duplique (sección 2.6.4) |
| Escalera de degradación | niveles N0 a N6 de funcionamiento reducido y seguro (sección 2.12) |
| Punto de quiebre | primera carga con p95 fuera de presupuesto o errores por encima de 1% (sección 2.13) |
| LLM simulado | modelo falso, determinista y con latencia configurable, para pruebas y carga |
| Clave virtual | credencial del gateway por trabajador, con presupuesto y límites propios |
| Relleno honesto | frase que cubre la espera de una herramienta sin afirmar ninguna acción |

---

## 3. Decisiones de tecnología del dominio

### 3.1 Gateway de IA: LiteLLM frente a Apigee

| Criterio | Apigee con Model Armor | LiteLLM con Presidio y Model Armor |
|---|---|---|
| Políticas de IA | `LLMTokenQuota`, `PromptTokenLimit`, `SanitizeUserPrompt`, `SanitizeModelResponse`, caché semántica; **todas son políticas "Extensible"** [V] | presupuestos y límites por clave virtual, alias de modelos, guardarraíles propios antes y después de cada llamada, registro de gasto |
| Entorno mínimo que las permite | Intermediate (el entorno Base solo admite proxies Standard) [V] | cualquier contenedor |
| Costo de pago por uso | Intermediate US$1.460 por mes y región; Comprehensive US$3.431; llamadas Extensible US$100 por millón (hasta 50 millones) [V]; red aparte | US$0 de licencia; cabe en el nivel gratuito de Cloud Run en la demo |
| Costo en 10 días | ≈ US$480 más llamadas y red | ≈ US$3 de instancia mínima (sección 7) |
| Evaluación gratuita | 60 días sin costo y sin SLA [V]; exige aprovisionar la organización de Apigee y su red [A: tiempo de aprovisionamiento] | no aplica |
| Reproducibilidad local (P13) | no corre en la máquina del jurado | corre en Docker Compose igual que en la nube |
| Riesgo principal | costo y tiempo de montaje | cadena de suministro: versiones maliciosas en PyPI el 24 de marzo de 2026 [V] |

**Decisión (DP-TEC-02):** se mantiene LiteLLM en todos los entornos, como dice D-20, con Presidio siempre y
Model Armor en la nube. Apigee queda como **ruta a producción documentada**, con el mapeo política por
política de abajo, y un *spike* opcional (S7) con la evaluación gratuita solo si sobra tiempo; no está en la
ruta crítica. El riesgo de LiteLLM se mitiga con imagen fijada por digest, enfriamiento de 7 días
(R-TEC-30), salida de red restringida y credenciales de modelos solo en `sa-gateway`; si Gobierno veta
LiteLLM, el **plan B** es un gateway mínimo propio en `latam_bank.gateway` con la misma interfaz (alias,
claves, presupuestos, guardarraíles), que llama a Vertex AI con su SDK.

| Política de Apigee | Equivalente en la hackatón | Dónde vive |
|---|---|---|
| `LLMTokenQuota` | presupuesto diario y límite de tokens por minuto de cada clave virtual; presupuesto por conversación del motor (R-TEC-48) | gateway y motor |
| `PromptTokenLimit` | guardarraíl `limite_prompt` por alias | gateway |
| `SanitizeUserPrompt` | guardarraíl `redaccion_pii` (Presidio) y `model_armor_entrada` | gateway |
| `SanitizeModelResponse` | filtro de salida por frases (R-TEC-75) y `model_armor_salida` | motor y gateway |
| `SemanticCacheLookup` y `SemanticCachePopulate` | no se usan (R-TEC-95) | |
| enrutamiento por alias | `model_list` con alias por trabajador | gateway |
| analítica y costo | registro de gasto del gateway, trazas y platino | gateway y observabilidad |
| `SpikeArrest` y cuotas por consumidor | límites de tasa en las superficies (R-TEC-80); Cloud Armor en producción | superficies y borde |

### 3.2 Identidad: propia frente a Identity Platform

**Decisión (DP-TEC-04):** se mantiene la identidad propia de D-20 para clientes. Identity Platform gestiona
usuarios reales con correo, teléfono y segundo factor [A: precio por usuario activo y por SMS en su página],
pero no da por sí mismo el reto de RFC 9470 con `acr` y `max_age` sobre el recurso, no permite inyectar el
reloj para probar vencimientos (D5) y obligaría a crear usuarios sintéticos del banco en un tercero. Se
agregan dos piezas de Google Cloud que no cambian D-20: la llave de firma en **Cloud KMS** (US$0,06 por
versión al mes y US$0,03 por cada 10.000 firmas [V]) y **IAP** para las superficies internas (`lb-staff` y
`lb-phoenix`) con identidades de Google, lo que cubre el control de acceso del personal que pide el enunciado
[A: costo de IAP y su activación directa en Cloud Run sin balanceador, a confirmar en F0].

### 3.3 Observabilidad: Phoenix más la suite de Google Cloud

**Decisión (DP-TEC-03):** en la nube se exporta a Phoenix (vista de conversaciones y llamadas al modelo,
código abierto, OpenTelemetry nativo) **y** a Cloud Trace, Cloud Logging y Cloud Monitoring (latencia de
infraestructura, correlación con logs, alertas y paneles). En local se queda Phoenix (D-20). Costo en la
demo: Trace gratis hasta 2,5 millones de spans al mes por cuenta y luego US$0,20 por millón; Logging gratis
hasta 50 GiB por proyecto y luego US$0,50 por GiB con 30 días de retención incluidos; Monitoring sin costo
para métricas de Google Cloud y 150 MiB gratis de métricas cobrables [V]. Alternativas: Langfuse (equivalente
a Phoenix), Logfire y plataformas comerciales como Datadog (costo por host y por span sin necesidad aquí).

### 3.4 Región

**Decisión (DP-TEC-01):** la demo vive en `us-central1`: es región de nivel 1 y el nivel gratuito de Cloud
Run se calcula con sus precios [V]. La latencia desde Bogotá, Ciudad de México y Buenos Aires se mide en S1
[A]. Para producción existen regiones en México (`northamerica-south1`), São Paulo (`southamerica-east1`) y
Santiago (`southamerica-west1`) [V]; la disponibilidad de Vertex AI, Speech-to-Text y Model Armor en ellas se
confirma antes de elegir [A], y la residencia de los datos la decide Gobierno por país.

### 3.5 Proveedores de voz: candidatos para S1

D-18 manda elegir por medición. Criterios: error por acento (es-MX, es-CO, es-AR, pt-BR), tiempo hasta el
resultado final y hasta el primer audio, confianza reportada, marcas de tiempo por palabra en la síntesis,
streaming real, condiciones de retención de datos del proveedor y precio.

| Candidato | Precio | Etiqueta |
|---|---|---|
| Google Speech-to-Text V2 (modelos estándar, incluido Chirp) | US$0,016 por minuto hasta 500.000 minutos al mes; lote dinámico US$0,003 | [V] |
| Google Text-to-Speech Chirp 3 HD | US$30 por millón de caracteres; primer millón gratis al mes | [V] |
| Google Text-to-Speech Neural2 | US$16 por millón de caracteres; primer millón gratis | [V] |
| Gemini 2.5 Flash TTS | US$0,50 por millón de tokens de texto y US$10 por millón de tokens de audio | [V] |
| Deepgram, AssemblyAI, ElevenLabs, Cartesia, Soniox | exactitud según la [investigación 20](../Investigacion/20_Canales_voz_y_chat.md) (cifras de proveedor) | [P]; precios [A] en sus páginas antes de S1 |

Si un proveedor externo gana, su credencial va a Secret Manager, su llamada sale de `sa-voz` y su contrato de
retención de datos pasa por Gobierno (riesgo de terceros).

### 3.6 Resto de decisiones

| Tema | Decisión | Estado del arte y fuente | Alternativas y por qué no | Estado |
|---|---|---|---|---|
| Cómputo | Cloud Run (servicios y jobs) | contenedores sin servidores, escala a cero, WebSocket de hasta 60 minutos | GKE Autopilot (más operación para diez días); Compute Engine (solo si S1 exige WebRTC con UDP propio) | DP-TEC-09 |
| Base operativa | Cloud SQL para PostgreSQL 16, `db-g1-small` en la demo (US$0,035 por hora; SSD US$0,17 por GiB al mes) [V] | Postgres es el estándar para estado transaccional; DuckDB admite un solo escritor ([05](../Diseno/05_Cobertura_del_enunciado.md), punto 8) | `db-f1-micro` (0,6 GB de memoria, estrecho para cuatro bases, US$0,0105 por hora) [V]; AlloyDB (prueba de 30 días, desproporcionado) [V]; Postgres en una VM (más operación). Los núcleos compartidos no tienen SLA [V] | D-20 |
| Durabilidad del flujo | persistencia propia con *outbox* y llaves (sección 2.6) | PydanticAI integra DBOS y Temporal ([investigación 17](../Investigacion/17_VP_Tecnologia.md)) | DBOS si sobra tiempo (D-11); Temporal, demasiada infraestructura | D-11 |
| Infraestructura como código | Terraform con estado en Cloud Storage | estándar de facto con proveedor oficial de Google | OpenTofu (equivalente, menos documentación de Google); Pulumi; scripts de `gcloud` (no declarativos) | DP-TEC-08 |
| CI/CD | GitHub Actions con WIF | el repositorio ya vive en GitHub (D-03); federación sin llaves | Cloud Build (otra consola y otro formato; no aporta aquí) | DP-TEC-08 |
| Frontend | React, TypeScript y Vite con `@ag-ui/client` | AG-UI es el protocolo abierto de 2026 para agentes e interfaces (D-19) | CopilotKit (suma un servidor de Node); Chainlit o Streamlit (sin componentes tipados ni aprobaciones como eventos) | DP-TEC-11 |
| Pruebas de API | Schemathesis contra OpenAPI | pruebas basadas en propiedades sobre contratos, en la misma línea que Hypothesis | pruebas escritas a mano (menos cobertura) | R-TEC-60 |
| Carga | Locust y generador propio de voz | Python como el resto; admite clientes a medida (SSE, WebSocket) | k6 (otro lenguaje); Gatling | DP-TEC-14 |
| Modelos | Vertex AI detrás del gateway; Gemini 3.8 Flash a US$0,75 y US$3,75 por millón (introductorio hasta el 31 de diciembre de 2026), Gemini 3.1 Flash-Lite a US$0,25 y US$1,50, Gemini 3.1 Pro Preview a US$2 y US$12, Gemma 4 26B a US$0,15 y US$0,60 [V] | la página de precios de 2026 presenta Vertex AI como Agent Platform [V] | APIs directas de cada proveedor (más secretos y más facturas) | D-20; la elección es de IA |
| Plan B de modelos (D-15) | modelo abierto propio: Ollama en local; en la nube, Cloud Run con GPU L4 a US$0,0001867 por segundo (≈ US$0,67 por hora) más CPU y memoria [V] | un modelo propio en infraestructura propia no es una "solicitud a un modelo externo" | modelo abierto solo en CPU (lento) | D-15 |

### 3.7 Ruta a producción: trabajo restante

El enunciado pide "*the remaining deployment work*". Lo que falta para operar de verdad, por dominio técnico:

| Frente | Trabajo restante |
|---|---|
| Identidad | federar con el proveedor de identidad del banco (OIDC con autenticación reforzada real); OTP por canal real con proveedor certificado |
| Integración | adaptadores a los sistemas reales con las APIs BIAN confirmadas; red de tarjetas para bloqueos; red de contracargos para casos |
| Canales | WhatsApp Business real con plantillas aprobadas; troncal SIP o proveedor de telefonía con números por país; WebRTC gestionado |
| Seguridad | Apigee con Model Armor, Cloud Armor Enterprise, VPC Service Controls (exige organización de Google Cloud [A]), llaves CMEK, IP privada para Cloud SQL, pruebas de penetración y equipo rojo externo |
| Confiabilidad | Cloud SQL con alta disponibilidad, recuperación a un punto en el tiempo y plan de continuidad; SLO con guardia y gestión de incidentes; rendimiento aprovisionado de modelos |
| Datos y privacidad | residencia por país, evaluación de impacto de privacidad, retención aprobada por el regulador, consentimiento de grabaciones |
| Capacidad | prueba de carga a volumen de producción con cuotas aumentadas y costos reales |
| Gobierno de modelos | validación independiente, monitoreo de deriva por acento e idioma, proceso de cambio de modelo con revalidación |

---

## 4. Seguridad, privacidad y gobierno del dominio

Tecnología implementa y prueba; Gobierno (Seguridad y equipo rojo; Cumplimiento y privacidad) define,
desafía y puede vetar. La numeración continúa la de la sección 2.

### 4.1 Identidades y accesos

| Cuenta | Roles | Alcance |
|---|---|---|
| `sa-chat` | `roles/cloudsql.client`, `roles/cloudsql.instanceUser`, `roles/run.invoker` (sobre `lb-bian` y `lb-gateway`), `roles/cloudtrace.agent`, `roles/logging.logWriter`, `roles/monitoring.metricWriter` | recurso cuando se puede |
| `sa-voz` | los de `sa-chat`; el rol de Speech-to-Text si el proveedor es Google [A: nombre exacto]; `roles/secretmanager.secretAccessor` sobre los secretos de voz y de Twilio | recurso |
| `sa-bian` | `roles/cloudsql.client`, `roles/cloudsql.instanceUser`, `roles/storage.objectViewer` sobre el bucket de oro, `roles/cloudkms.signerVerifier` sobre la llave de identidad, `roles/secretmanager.secretAccessor` sobre `otp-hmac` | recurso |
| `sa-gateway` | `roles/aiplatform.user` (la única cuenta con este rol), el rol de usuario de Model Armor [A: nombre exacto], `roles/cloudsql.client` para su base, `roles/secretmanager.secretAccessor` sobre sus secretos | recurso |
| `sa-staff` | `roles/cloudsql.client`, `roles/cloudsql.instanceUser` con vistas de solo lectura, `roles/run.invoker` sobre `lb-bian` | recurso |
| `sa-phoenix` | `roles/cloudsql.client` y el secreto de su base | recurso |
| `sa-migrar`, `sa-exportar`, `sa-carga` | lo mínimo de su trabajo | recurso |
| `sa-despliegue` (CI por WIF) | `roles/run.developer`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser` solo sobre las cuentas de ejecución | proyecto y recurso |
| Personas | una sola persona dueña del proyecto; el resto `roles/viewer`; el personal simulado entra a `lb-staff` y `lb-phoenix` por IAP (`roles/iap.httpsResourceAccessor`) | proyecto y recurso |

### 4.2 Secretos

| Secreto | Uso | Local | Nube | Accede | Rotación |
|---|---|---|---|---|---|
| Llave de firma de sesiones | JWT de identidad | archivo PEM fuera del repositorio | Cloud KMS, no exportable | `sa-bian` | por entorno y ante sospecha |
| `otp-hmac` | HMAC de los OTP | `.env` ignorado por git | Secret Manager | `sa-bian` | por versión mayor |
| Llave maestra y claves virtuales del gateway | administración y uso de LiteLLM | `.env` | Secret Manager | `sa-gateway`; cada clave virtual, su trabajador | al cierre |
| Contraseñas de las bases de terceros (`litellm`, `phoenix`) | conexión | `.env` | Secret Manager | la cuenta del componente | al cierre |
| Credencial del proveedor de voz externo y token de Twilio | API y firma de webhooks | `.env` | Secret Manager | `sa-voz` | al cierre |
| Llave HMAC de tokenización de datos personales | plata (Datos) | `.env` de Datos | no sube a la nube | Datos | Datos |
| Llave de AWS de solo lectura del organizador | descarga del bucket | `~/.aws/credentials` | nunca | quien corre el pipeline | según los organizadores |

`.env.example` versionado lista los nombres, nunca los valores.

### 4.3 Reglas de seguridad técnica

| ID | Regla | Cómo se verifica |
|---|---|---|
| R-TEC-124 | Una cuenta de servicio por unidad desplegable, con los roles de la tabla 4.1 y nada más; ninguna cuenta de servicio tiene roles básicos (Owner, Editor, Viewer). | script en CI que compara la política IAM exportada con la tabla |
| R-TEC-125 | No existen llaves de cuentas de servicio; el CI entra por WIF con condición de atributo limitada al repositorio y a la rama `main`. | `gcloud iam service-accounts keys list --managed-by=user`; condición del proveedor de identidad |
| R-TEC-126 | Acceso humano: una persona dueña; el resto lectores; el personal simulado entra por IAP con lista de correos y tiene roles de aplicación en `lb-staff` (`agente_fraude`, `supervisor`, `auditor_lectura`); cada acción en la vista del experto queda registrada con el usuario. | política de IAP; prueba de interfaz: sin identidad hay redirección; registro de acciones |
| R-TEC-127 | Conexión a Cloud SQL por la conexión integrada de Cloud Run, sin redes autorizadas; nuestros servicios usan autenticación IAM de base de datos (sin contraseñas); LiteLLM y Phoenix usan contraseña en Secret Manager limitada a su base; privilegios mínimos por esquema; `lb-staff` solo lee vistas. | prueba de permisos SQL; configuración de la instancia |
| R-TEC-128 | Los secretos se montan desde Secret Manager (no como texto en la definición del servicio) y cada secreto tiene acceso solo para la cuenta que lo usa. | Terraform; `gcloud run services describe` muestra referencias a secretos |
| R-TEC-129 | La llave de AWS del organizador nunca llega a la nube, a una imagen ni a un contenedor desplegado (P11). | regla de gitleaks para llaves de AWS sobre repositorio e imágenes |
| R-TEC-130 | Cifrado: TLS en todo salto (Cloud Run y la conexión de Cloud SQL lo dan); en reposo, el cifrado por defecto de Google; CMEK con Cloud KMS para Cloud SQL y el bucket de oro como control de producción (US$0,06 por versión de llave al mes [V]). | configuración |
| R-TEC-131 | Red: ingreso interno para servicios internos (R-TEC-05); salida de `lb-gateway` solo hacia APIs de Google y proveedores aprobados en una lista; VPC Service Controls en producción (sección 3.7). | configuración; ADR de la lista de salida |
| R-TEC-132 | Borde: en la demo, límites de tasa en las superficies y en el gateway; en producción, balanceador externo con Cloud Armor (reglas WAF preconfiguradas y límite por IP). Cloud Armor Standard cuesta US$5 por política y US$1 por regla al mes más US$0,75 por millón de solicitudes; Enterprise, US$200 al mes con 2 recursos protegidos [V]. Se puede activar en la demo por unos US$10 [S]. | configuración |
| R-TEC-133 | Cadena de suministro: imágenes base por digest; acciones de GitHub por SHA completo; `permissions` mínimos en cada flujo; zizmor sin hallazgos altos; imagen de LiteLLM por digest de una versión con más de 7 días y firma verificada si el proyecto la publica [A]; SBOM CycloneDX por versión; escaneo de imagen; Dependabot con enfriamiento. Contexto: en marzo de 2026 una misma campaña comprometió el escáner Trivy (19 de marzo) y paquetes de PyPI de LiteLLM (24 de marzo) y de Telnyx [V]. | verificaciones del CI |
| R-TEC-134 | Contenedores sin usuario root, con sistema de archivos de solo lectura donde se pueda y construcción en varias etapas sin herramientas de depuración en la imagen final. | hadolint; inspección de la imagen |
| R-TEC-135 | Datos a modelos externos: solo hechos mínimos y enmascarados, y solo con la autorización de D-15; en la nube, si Gobierno exige retención cero, se desactiva la caché de datos de Vertex AI a nivel de proyecto [A: procedimiento vigente en la documentación de Vertex AI]; el plan B es un modelo abierto propio (sección 3.6). | configuración; visto bueno de Gobierno |
| R-TEC-136 | Registro de auditoría: Cloud Audit Logs de actividad administrativa (siempre activos) y de acceso a datos para Secret Manager y Cloud KMS; el registro del PDP es la auditoría de negocio; ambos se conservan al menos 30 días. | configuración |
| R-TEC-137 | Runbooks en `docs/runbooks/` para proveedor de modelos caído, secreto filtrado (rotación en 30 minutos o menos), costo desbocado, inyección exitosa y voz sintética; un simulacro en F5. | archivos; bitácora del simulacro |

### 4.4 Lo que necesita visto bueno de Gobierno

- Fallas abiertas o cerradas de cada filtro: la propuesta es que el nivel N1 (sin Model Armor) siga con
  filtros locales, porque la garantía es la arquitectura (P5), y que el filtro de salida local falle cerrado
  (si falla, se responde con plantilla).
- Umbral de recuperación de datos personales del gateway y plantilla de Model Armor.
- Retención por clase de dato, ventana de retoma, presupuesto por conversación, vigencias de sesión y OTP,
  nivel `acr` por acción y umbral de confianza de voz para datos críticos.
- Endpoint regional o global de Vertex AI, y si Vertex AI cuenta como modelo externo para D-15.
- Aceptación de LiteLLM con los controles de R-TEC-30 y R-TEC-133, o el plan B de gateway propio.

---

## 5. Interfaces

### 5.1 Lo que Tecnología entrega

| A quién | Qué | Día | Aceptación |
|---|---|---|---|
| Todas las caras | repositorio con esqueleto, `just setup demo`, CI, ADR de D-11, D-12 y D-17 a D-20 | D0 | la máquina limpia levanta la pila |
| IA | LLM simulado detrás del gateway | D1 | `ci` corre sin claves externas |
| IA | gateway con alias y claves virtuales por trabajador; costo y latencia por trabajador en las trazas | D3 | cada llamada aparece con su trabajador y su costo |
| IA | API del motor para los simuladores de texto y voz | D3 | el arnés corre el conjunto de desarrollo por la API |
| IA | plataforma del experimento nativo detrás de su bandera | D7 | una llamada de prueba delega en el motor |
| Clientes | tiempo de ejecución de componentes AG-UI y modo WhatsApp simulado | D4 | los seis componentes con su degradación |
| Clientes | puntos de enganche de voz: plantillas, rellenos, lectura de vuelta, DTMF | D5 | V1, V2 y V8 en desarrollo |
| Clientes (Operaciones) | vista del experto, cola humana y dispositivo simulado de OTP | D5 | E1 a E7 muestran el paquete completo |
| Datos | consumo del oro operacional con su contrato; exportación de trazas y costos a platino | D3 y D6 | las consultas de platino reproducen las cifras |
| Gobierno | registro del PDP, arnés de propiedades, inyección de fallas, interruptor "todo a humano" | D3 a D5 | S1 a S10 rechazados en la capa de herramientas; simulacro del interruptor |
| Gobierno | evidencia de controles: IAM, secretos, SBOM, escaneos, medición del filtro | D7 | tabla de controles con su evidencia |
| Auditoría | digests y SBOM por versión; cadena de huellas de trazas; prueba en máquina limpia | D8 y D9 | verificación de la cadena sin errores |
| Presidencia y Oficina de Entrega | reporte de costos y presupuesto; reporte de capacidad; sección de ruta a producción | D0, semanal, D7 y D9 | cifras con fuente y etiqueta |

### 5.2 Lo que Tecnología necesita

```
Solicitud S-TEC-01
De: VP Tecnología   Para: VP Gobierno (Cumplimiento)
Qué: policy/v1 en YAML que valide contra el JSON Schema que entrega Tecnología (acciones, acr por acción,
     umbrales de autonomía, qué exige confirmación, plazos por país con norma y fecha)
Para qué: TEC-2 (cargador de política) y TEC-4 (punto de decisión)
Para cuándo: D2
Aceptación: valida contra el esquema; cada regla tiene norma y fecha de consulta
Estado: abierta
```

```
Solicitud S-TEC-02
De: VP Tecnología   Para: VP Gobierno (Seguridad y equipo rojo)
Qué: matriz de fallas abiertas o cerradas por filtro y nivel de degradación (2.12); umbral de recuperación
     de datos personales; plantilla de Model Armor; aceptación de LiteLLM con sus controles o plan B
Para qué: TEC-7, R-TEC-102 y DP-TEC-02
Para cuándo: D3
Aceptación: acta del Comité de Confianza con la matriz firmada
Estado: abierta
```

```
Solicitud S-TEC-03
De: VP Tecnología   Para: VP Gobierno (Cumplimiento y privacidad)
Qué: retención por clase de dato (R-TEC-117), ventana de retoma (R-TEC-54), presupuesto por conversación
     (R-TEC-48), vigencias de sesión y OTP (2.8), endpoint regional o global de Vertex AI (2.11)
Para qué: parámetros de Terraform, de los trabajos de purga y de la identidad
Para cuándo: D2
Aceptación: valores con su norma o criterio, registrados en policy/v1 o en acta
Estado: abierta
```

```
Solicitud S-TEC-04
De: VP Tecnología   Para: VP Datos
Qué: contrato ODCS y exportación en Parquet del oro operacional (transacciones recientes, estado de
     productos, vista segura de clientes, candidatos de disputa) con manifiesto, huella y origen; y un
     conjunto de demostración generado por el equipo con el mismo contrato, para la nube (R-TEC-13)
Para qué: TEC-3 (servicios simulados) y DP-TEC-07
Para cuándo: D3
Aceptación: lb-bian lee ambos conjuntos sin cambios de código y las pruebas de contrato pasan
Estado: abierta
```

```
Solicitud S-TEC-05
De: VP Tecnología   Para: VP Datos y VP Clientes
Qué: directorio de comercios del equipo (razón social, descriptor, marca) y contrato de la ficha
Para qué: herramienta obtener_ficha (2.7) y componente FichaTransaccion (2.9)
Para cuándo: D3
Aceptación: N1 muestra un descriptor confuso resuelto con la marca
Estado: abierta
```

```
Solicitud S-TEC-06
De: VP Tecnología   Para: VP Datos
Qué: esquema de trazas_resumen y de costos en platino, y definición oficial de latencia y costo por caso
Para qué: TEC-8 y TEC-14 (que la plataforma y platino calculen igual)
Para cuándo: D3
Aceptación: la misma corrida da las mismas cifras en el panel y en la consulta de platino
Estado: abierta
```

```
Solicitud S-TEC-07
De: VP Tecnología   Para: VP Inteligencia Artificial
Qué: esquema de salida de Interpretacion; modelo con versión por alias; presupuesto de tokens por
     trabajador y por conversación; familias del juez, del simulador y del generador
Para qué: TEC-7 (gateway) y la estimación de costos de 7.3
Para cuándo: D2
Aceptación: la configuración del gateway se genera desde ese registro (agentes/registro.yaml)
Estado: abierta
```

```
Solicitud S-TEC-08
De: VP Tecnología   Para: VP Inteligencia Artificial (Voz)
Qué: resultado de S1: proveedores de reconocimiento y síntesis con error por acento, tiempo al resultado
     final y al primer audio, confianza reportada, marcas de tiempo por palabra; parámetros de VAD y SmartTurn
Para qué: TEC-6 y R-TEC-84 a R-TEC-87
Para cuándo: D0 (F0)
Aceptación: tabla por proveedor y acento con intervalos; decisión registrada
Estado: abierta
```

```
Solicitud S-TEC-09
De: VP Tecnología   Para: VP Clientes (Diseño conversacional)
Qué: guiones por estado en ES y PT como plantillas con variables tipadas; catálogo de rellenos; catálogo de
     plantillas de WhatsApp; textos de componentes y de su degradación
Para qué: TEC-5 y TEC-6 (plantillas deterministas, R-TEC-76)
Para cuándo: D3 para chat y D4 para voz
Aceptación: cada estado del motor tiene plantilla en ambos idiomas; revisado por voz-del-cliente
Estado: abierta
```

```
Solicitud S-TEC-10
De: VP Tecnología   Para: VP Clientes (Operaciones de fraude y disputas)
Qué: modelo de colas (idioma, turno, especialidad, capacidad por hora desde el dataset, espera declarada)
     y requisitos de la vista del experto con sus roles
Para qué: TEC-15
Para cuándo: D3
Aceptación: E7 encola en portugués de noche con espera declarada
Estado: abierta
```

```
Solicitud S-TEC-11
De: VP Tecnología   Para: Presidencia
Qué: aprobar el gasto (cuenta de facturación con medio de pago, techo de DP-TEC-12, opcionales de 7.2) y
     enviar a los organizadores las preguntas técnicas de la sección 10.2
Para qué: F0 y DP-TEC-12
Para cuándo: D0
Aceptación: decisión registrada con el techo y los opcionales aprobados
Estado: abierta
```

```
Solicitud S-TEC-12
De: VP Tecnología   Para: Auditoría
Qué: criterio de la prueba en máquina limpia (sistemas, tiempo máximo, evidencia) y formato de
     verificación de la cadena de huellas de trazas
Para qué: TEC-10 y R-TEC-118
Para cuándo: D7
Aceptación: criterio escrito y aceptado antes de F7
Estado: abierta
```

```
Solicitud S-TEC-13
De: VP Tecnología   Para: VP Gobierno (Riesgo y riesgo de modelo)
Qué: protocolo de la corrida del retenido contra el digest congelado (quién la corre, dónde y qué se registra)
Para qué: R-TEC-27
Para cuándo: D8
Aceptación: acta de F6 con digest, versiones y huella de resultados
Estado: abierta
```

```
Solicitud S-TEC-14
De: VP Tecnología   Para: VP Inteligencia Artificial (Evaluación y simulación)
Qué: perfiles de carga derivados del conjunto de desarrollo (mezcla de rutas, turnos, pausas) y distribución
     de latencia medida por alias para el LLM simulado
Para qué: TEC-9 (capacidad)
Para cuándo: D5
Aceptación: Locust y el generador de voz reproducen la mezcla declarada
Estado: abierta
```

---

## 6. Métricas y criterios de aceptación del dominio

| Métrica | Definición | Meta | Fuente |
|---|---|---|---|
| Latencia de chat | primer texto visible; turno completo p50 y p95 | menos de 1 s; menos de 2 s; menos de 5 s (06, sección 6) | spans |
| Latencia de voz | voz a voz sin herramienta p50 y p95; relleno cuando hay herramienta | 1,0 s o menos; 2,0 s o menos; 1,0 s o menos | spans por etapa |
| Desglose por etapa | p50 y p95 de cada span del turno | reportar | spans |
| Caída segura | fallas inyectadas que terminan en R8 correcto | 100% (01, sección 5.6) | arnés |
| Reintentos | llamadas reintentadas sobre llamadas; máximo por llamada | tasa reportada; nunca más de 2 | spans |
| Disponibilidad en ventanas de demo | comprobaciones exitosas de disponibilidad | 99% [S] | Cloud Monitoring |
| Punto de quiebre | concurrencia en que el p95 sale del presupuesto o los errores pasan de 1% | reportar con cuello de botella y costo | prueba de capacidad |
| Costo | por caso intentado y por resolución segura, por idioma y canal | reportar; "no definido" si no hay resoluciones | platino |
| Conciliación de costo | estimado frente a facturado | diferencia de 15% o menos, o explicada | exportación de facturación |
| Completitud de trazas | turnos con todos sus spans | 100% | platino |
| Invariantes | ejemplos generados sin violación | 1.000 o más en CI; 10.000 o más cada noche | Hypothesis |
| Tipado | errores de pyright estricto | 0 | CI |
| Secretos | hallazgos de gitleaks en repositorio e imágenes | 0 | CI |
| Vulnerabilidades | críticas o altas explotables sin excepción vigente | 0 | CI |
| Reproducibilidad | `just setup demo` en máquina limpia | éxito en 30 minutos o menos [S], sin pasos fuera del README | Auditoría |
| Reversión | tiempo desde la decisión hasta el tráfico en la revisión anterior | 2 minutos o menos | simulacro |
| Aporte del filtro externo | detectados, falsos positivos en legítimos y ataques contenidos por la arquitectura | reportar ([investigación 10](../Investigacion/10_Gobernanza_y_gateway.md)) | conjunto de estrés |

| Compuerta | Criterio de aceptación de Tecnología |
|---|---|
| F0 | `just setup demo` funciona en máquina limpia; CI en verde; `terraform plan` sin cambios; presupuesto con alertas; *spikes* S3 y S4 cerrados y S1 con Voz; ADR iniciales aprobados |
| F3 | N1 a N6 por chat en español de punta a punta; S1 a S10 rechazados en la capa de herramientas; pyright sin errores; cada traza muestra la secuencia de estados |
| F3v | los mismos casos por voz en español dentro del presupuesto; V1, V2 y V8 sin resultado inseguro; V6 (chat a voz) sin repetir preguntas ni acciones |
| F5 | reporte de capacidad; simulacros de reversión, de degradación por nivel y del interruptor "todo a humano"; medición del filtro externo |
| F7 | prueba en máquina limpia aprobada por Auditoría; SBOM y digests de la versión entregada; conciliación de costos |

---

## 7. Compras y costos

### 7.1 Qué hay que pagar sí o sí

1. **Cuenta de facturación de Google Cloud con medio de pago**, aunque se use el crédito de prueba: Cloud KMS
   y Text-to-Speech exigen facturación habilitada [V].
2. **Consumo de modelos de lenguaje** (sistema, simulador de usuario, generador de conversaciones y juez): es
   el rubro mayor. Alternativa gratuita: modelo abierto local, con menor calidad y costo de hardware propio.
3. **Reconocimiento y síntesis de voz** por encima de los niveles gratuitos, para evaluar la voz (D-17,
   D-18). Alternativa gratuita: modelos locales (por ejemplo, Whisper y Piper) [A: calidad y latencia por
   acento, a medir en S1].
4. **Cloud SQL**, solo si hay demo en la nube (no tiene nivel gratuito). Alternativa gratuita: demo solo
   local.

Todo lo demás de la plataforma cabe en niveles gratuitos o es opcional.

### 7.2 Lista de materiales de la hackatón (10 días)

Precios [V] del 27 de septiembre de 2026 en `us-central1`; usos [S].

| Rubro | Precio | Uso supuesto | Costo en 10 días | Tipo | Alternativa gratuita |
|---|---|---|---|---|---|
| Cloud Run | CPU activa US$0,000024 por vCPU-s; memoria US$0,0000025 por GiB-s; instancia mínima inactiva US$0,0000025 por vCPU-s; US$0,40 por millón de solicitudes; gratis al mes 180.000 vCPU-s, 360.000 GiB-s y 2 millones de solicitudes | 60 horas activas de 1 vCPU y 1 GiB; `lb-voz` (2 vCPU, 4 GiB) y `lb-gateway` (1 vCPU, 2 GiB) con una instancia mínima durante 5 días | ≈ US$11 | indispensable para la nube | local |
| Cloud SQL `db-g1-small` | US$0,035 por hora; SSD US$0,000232877 por GiB-hora; respaldos US$0,000109589 por GiB-hora | 240 horas; 10 GiB | ≈ US$9 | indispensable para la nube | local |
| Artifact Registry | 0,5 GB gratis y luego cerca de US$0,10 por GB al mes [A] | 3 GB con limpieza | menos de US$1 | indispensable para la nube | local |
| Secret Manager | 6 versiones y 10.000 accesos gratis; luego US$0,06 por versión al mes y US$0,03 por 10.000 accesos | 10 versiones | ≈ US$0,10 | indispensable para la nube | `.env` local |
| Cloud KMS | US$0,06 por versión al mes; US$0,03 por 10.000 operaciones | 1 llave; 50.000 firmas | ≈ US$0,20 | indispensable para la nube | archivo local |
| Cloud Logging | 50 GiB por proyecto al mes gratis; US$0,50 por GiB | menos de 20 GiB | US$0 | incluido | |
| Cloud Trace | 2,5 millones de spans al mes gratis; US$0,20 por millón | 3 millones (la evaluación exporta solo a Phoenix local) | ≈ US$0,10 | incluido | Phoenix |
| Cloud Monitoring | métricas de Google Cloud sin costo; 150 MiB cobrables gratis | pocas métricas propias | US$0 | incluido | |
| Model Armor | 2 millones de tokens al mes gratis; US$0,10 por millón | 20 millones (medición del filtro y demo) | ≈ US$2 | indispensable en la nube | Presidio |
| Vertex AI (modelos) | ver 7.3 | ver 7.3 | ≈ US$230 a 400 | **indispensable** | modelo abierto local |
| Speech-to-Text V2 | US$0,016 por minuto | 4.000 minutos (S1, evaluación de voz y demo) | ≈ US$64 | **indispensable** | modelo local [A] |
| Text-to-Speech | Chirp 3 HD US$30 y Neural2 US$16 por millón de caracteres; 1 millón gratis de cada uno al mes | 3 millones (agente y clientes simulados) | ≈ US$23 a 60 | **indispensable** | modelo local [A] |
| **Subtotal indispensable** | | | **≈ US$340 a 550** | | |
| Gemini Live (experimento, recortable) | audio de entrada US$3 y de salida US$12 por millón de tokens; 25 tokens por segundo; el contexto se cobra en cada turno | 600 minutos | ≈ US$20 a 40 [S] | opcional | no hacer el experimento |
| Telefonía Twilio con número de EE. UU. | número US$1,15 al mes; entrante US$0,0085 por minuto; Media Streams US$0,0044 por minuto; US$15 de prueba | 1 número; 300 minutos | ≈ US$5 (lo cubre la prueba) | opcional | voz por navegador |
| Telefonía Twilio con número de Colombia | número US$14 al mes; entrante US$0,0945 por minuto | 1 número; 300 minutos | ≈ US$44 [A: requisitos regulatorios del número] | opcional | número de EE. UU. |
| Balanceador y Cloud Armor | política US$5 y regla US$1 al mes; US$0,75 por millón de solicitudes; regla de reenvío del balanceador cerca de US$0,025 por hora [A] | 10 días; 5 reglas | ≈ US$10 | opcional | límites de tasa en la aplicación |
| Dominio propio | cerca de US$12 al año [A] | 1 dominio | ≈ US$12 | opcional | URL `run.app` con TLS gestionado sin costo |
| Apigee (evaluación) | sin costo por 60 días; red aparte [A] | *spike* S7 | ≈ US$0 a 10 | opcional | LiteLLM |
| GPU L4 para el plan B | US$0,0001867 por segundo más 4 vCPU y 16 GiB [A: configuración mínima] | 20 horas | ≈ US$25 | opcional | modelo abierto en el portátil |
| **Total con todos los opcionales** | | | **hasta ≈ US$700** | | |

Con el crédito de la prueba gratuita (US$300 por 90 días para cuentas nuevas [V]), el desembolso de lo
indispensable queda en ≈ US$40 a 250. El crédito puede no cubrir algunos productos (la prueba limita el acceso
a ciertos servicios para evitar abuso [V]; GPU y modelos de socios en Vertex AI [A]).

### 7.3 Consumo de modelos en la hackatón

Supuestos [S], a confirmar con IA (S-TEC-07):

- Una conversación del sistema tiene 8 turnos y 13 llamadas al LLM (8 de comprensión cuando se usa el
  comparado LLM o el respaldo, 5 de redacción), con 18.000 tokens de entrada (60% en caché) y 1.400 de salida.
- Volumen: 12.000 conversaciones del sistema (desarrollo 6.000; retenido de texto 3.000, que son 500 casos por
  k = 3 por sistema y línea base LLM; voz 1.500; equipo rojo 500; carga con proveedor real 1.000).
- Simulador de usuario: 12.000 conversaciones de 10.000 tokens de entrada y 800 de salida.
- Generador de conversaciones (IA-1): 3.000 conversaciones de 2.000 tokens de entrada y 2.500 de salida.
- Juez: 3.000 casos de 3.000 tokens de entrada y 300 de salida.

| Trabajador | Modelo de referencia (precio [V]) | Costo por unidad | Total |
|---|---|---|---|
| Sistema | Gemini 3.1 Flash-Lite (US$0,25 y US$1,50) a Gemini 3.8 Flash (US$0,75 y US$3,75, introductorio) | US$0,004 a 0,011 por conversación | US$50 a 138 |
| Simulador de usuario | familia distinta con precio entre Flash-Lite y Flash [S] | US$0,004 a 0,011 | US$44 a 126 |
| Generador | Gemini 3.1 Pro Preview (US$2 y US$12) o equivalente | US$0,034 | ≈ US$102 |
| Juez | Gemini 3.1 Pro Preview o equivalente de otra familia | US$0,010 | ≈ US$29 |
| **Total** | | | **≈ US$230 a 400** |

El precio introductorio de Gemini 3.8 Flash vence el 31 de diciembre de 2026 y pasa a US$1,50 y US$7,50 [V]:
la proyección de producción usa ese precio.

### 7.4 Proyección de producción (mensual)

**Etiqueta: proyección** (P3). Supuestos [S]: 60% de voz telefónica y 40% de chat; llamada de 3 minutos; chat
de 8 turnos; Gemini 3.8 Flash a precio estándar de 2027 con 60% de caché; Chirp 3 HD; telefonía con número
local de Colombia de Twilio como referencia; Model Armor en todo; sin costo de mensajes de WhatsApp [A: tarifa
por mensaje desde octubre de 2026, investigación 14].

| Costo unitario | Chat | Voz telefónica |
|---|---|---|
| Modelos | US$0,023 | US$0,023 |
| Reconocimiento (3 minutos) | | US$0,048 |
| Síntesis (1.300 caracteres) | | US$0,039 |
| Model Armor | US$0,0001 | US$0,0001 |
| Telefonía (3 minutos entrantes más Media Streams) | | US$0,297 |
| **Total por caso** | **≈ US$0,023** | **≈ US$0,41** (≈ US$0,11 sin telefonía) |

Costo fijo mensual [S] en una región y sin Apigee: Cloud SQL con alta disponibilidad, 2 vCPU y 8 GiB
(US$202 [V]), 100 GiB de SSD con alta disponibilidad y respaldos (≈ US$42); instancias mínimas de Cloud Run
(≈ US$160); balanceador (≈ US$18 [A]); Cloud Armor Enterprise (US$200 [V]); observabilidad (≈ US$30);
secretos, llaves y registro (≈ US$5). Total ≈ **US$660**.

| Casos al mes | Variable | Fijo | Total | Por caso | Total con Apigee Intermediate | Por caso con Apigee |
|---|---|---|---|---|---|---|
| 10.000 | US$2.530 | US$660 | US$3.190 | US$0,32 | US$4.663 | US$0,47 |
| 50.000 | US$12.650 | US$660 | US$13.310 | US$0,27 | US$14.835 | US$0,30 |
| 200.000 | US$50.600 | US$660 | US$51.260 | US$0,26 | US$52.980 | US$0,26 |

Lectura honesta: la telefonía es la línea mayor del costo automatizado (una troncal SIP propia la reduciría
[A]); Apigee pesa a bajo volumen y se diluye a alto volumen. Y el costo que decide no es el de la plataforma:
si el 30% de los casos pasa a un humano a US$7 a 14 por contacto de voz ([investigación 11](../Investigacion/11_Latencia_y_costo.md),
cifra de industria [P]), el traspaso suma US$2,1 a 4,2 por caso en promedio, entre 8 y 16 veces el costo de la
plataforma. La palanca económica es la resolución segura y la calidad del traspaso, no la infraestructura.

### 7.5 Créditos y gratuidades disponibles

| Qué | Cuánto | Etiqueta |
|---|---|---|
| Prueba gratuita de Google Cloud | US$300 por 90 días para cuentas nuevas | [V] |
| Niveles gratuitos mensuales | Cloud Run, Logging, Trace, Monitoring, Secret Manager, Model Armor y Text-to-Speech (sección 7.2); Speech-to-Text da 60 minutos al mes en V1 | [V]; en V2 [A] |
| Evaluación de Apigee | 60 días sin costo | [V] |
| Prueba de AlloyDB | 30 días (no se usa) | [V] |
| Prueba de Twilio | US$15 | [V] |
| Créditos de los organizadores | a preguntar (pregunta 8 de [05](../Diseno/05_Cobertura_del_enunciado.md)) | [A] |

### 7.6 Controles de gasto

- Presupuesto con alertas al 50, 80 y 100% antes de crear recursos (R-TEC-18).
- Presupuesto diario por clave virtual del gateway (R-TEC-94): un error del simulador no quema el mes.
- Instancias mínimas solo en ventanas de demo (`just demo-on` y `just demo-off`); instancias máximas
  acotadas por servicio.
- Limpieza de Artifact Registry (se conservan las 10 imágenes más recientes); exclusión de logs ruidosos.
- Las corridas de evaluación exportan trazas solo a Phoenix local; Cloud Trace se usa para la demo y la carga.
- Desmontaje al cerrar (R-TEC-20) y conciliación con la factura (R-TEC-122).
- Opcional [S]: una notificación del presupuesto por Pub/Sub que apaga las instancias mínimas y las claves
  del gateway al llegar al 100%.

---

## 8. Backlog propuesto

Las épicas TEC-1 a TEC-10 son las de la [hoja de ruta](../Diseno/07_Hoja_de_ruta.md), sección 3; TEC-0 y TEC-11 a
TEC-17 son nuevas. Los días siguen el calendario de 07, sección 5. Una historia está terminada cuando cumple
su criterio, está tipada, probada, con trazas y en `just test` (modelo operativo, sección 8).

| ID | Historia | Criterio de aceptación | Depende de | Día |
|---|---|---|---|---|
| **TEC-0** | **Arranque y *spikes*** | | | |
| TEC-0.1 | repositorio con el esqueleto de 2.5, pre-commit, `justfile` y CI mínimo | `just check` y `ci.yml` en verde; gitleaks sin hallazgos | | D0 |
| TEC-0.2 | ADR de D-11, D-12, D-17, D-18, D-19 y D-20, y de las DP-TEC aprobadas | formato MADR con principio; acta del Comité de Plataforma | TEC-0.1 | D0 |
| TEC-0.3 | *spike* S3: texto por frases, un componente y una aprobación por AG-UI a una web mínima | aprobación con `nonce` de ida y vuelta; primer texto medido | TEC-0.1 | D0 |
| TEC-0.4 | *spike* S4: caso en Postgres retomado de chat a voz sin repetir la acción | un solo efecto con la misma llave; guion reproducible | TEC-0.1 | D0 |
| TEC-0.5 | *spike* S1 con IA (Voz): Pipecat con proveedores intercambiables, medición de voz a voz y WebSocket en Cloud Run | tabla de p50 y p95 por par de proveedores y por transporte; decisión registrada | TEC-0.6 | D0 |
| TEC-0.6 | arranque de Google Cloud: proyecto, facturación, presupuesto con alertas, bucket de estado, WIF | `terraform plan` limpio; alerta de prueba recibida | S-TEC-11 | D0 |
| TEC-0.7 | LLM simulado con salidas tipadas y latencia configurable | el CI corre sin claves de proveedores | TEC-0.1 | D1 |
| **TEC-1** | **Tipos del dominio** | | | |
| TEC-1.1 | tipos de 2.6.1 con sus invariantes | pyright estricto; propiedades de `Dinero` (sin `float`, cuantización) | TEC-0.1 | D1 |
| TEC-1.2 | constructores privados y contratos de import-linter | construir `SesionAutenticada` fuera de identidad falla en prueba | TEC-1.1 | D1 |
| TEC-1.3 | JSON Schema de los modelos y tipos TypeScript generados | diferencia vacía en CI (R-TEC-43) | TEC-1.1 | D1 |
| TEC-1.4 | `Reloj` y reglas `banned-api` | el CI rechaza `datetime.now` fuera de `reloj` | TEC-1.1 | D1 |
| **TEC-2** | **Motor de flujo y estado durable** | | | |
| TEC-2.1 | estados, tabla de transiciones y `transicionar()` pura | propiedades de R-TEC-46 y R-TEC-47 | TEC-1 | D3 |
| TEC-2.2 | esquema de 2.6.3 y migraciones con prueba de compatibilidad | R-TEC-25 | TEC-1 | D3 |
| TEC-2.3 | cáscara: ciclo de turno, efectos pendientes y bloqueo optimista | prueba de concurrencia de R-TEC-49 | TEC-2.1, TEC-2.2 | D3 |
| TEC-2.4 | idempotencia de turno, efecto y negocio | R-TEC-50 a R-TEC-52; A5 | TEC-2.3 | D3 |
| TEC-2.5 | retoma entre canales | V6 y D6 | TEC-2.4, TEC-6.2 | D5 |
| TEC-2.6 | límites por turno y por conversación | R-TEC-48 | TEC-2.3 | D3 |
| TEC-2.7 | cargador de `policy/v1` con esquema y versión en cada decisión | R-TEC-56 | S-TEC-01 | D3 |
| **TEC-3** | **Servicios simulados BIAN e identidad** | | | |
| TEC-3.1 | contratos OpenAPI con nombres BIAN confirmados y limitaciones | R-TEC-60 y R-TEC-61 | S-TEC-04 | D3 |
| TEC-3.2 | servicios de lectura sobre el oro con filtro por cliente | S3 y S10 rechazados también en el servicio | DAT-4 | D3 |
| TEC-3.3 | servicios de escritura (bloqueo y caso) con `Idempotency-Key` | N4, N8, D1 y D2 | TEC-3.1 | D3 |
| TEC-3.4 | identidad: sesión de prueba, JWT ES256, `acr`, OTP, reto de RFC 9470, JWKS, reloj | D5, S4 y V9 | TEC-1.4 | D3 |
| TEC-3.5 | firma con Cloud KMS en la nube | el JWKS publica la llave de KMS; R-TEC-71 | TEC-3.4, TEC-11.1 | D4 |
| TEC-3.6 | plano de control de inyección de fallas | R-TEC-63 | TEC-3.1 | D3 |
| TEC-3.7 | Schemathesis en CI | sin fallas | TEC-3.1 | D3 |
| **TEC-4** | **Capa de herramientas y punto de decisión** | | | |
| TEC-4.1 | catálogo de 2.7.1 con firmas de capacidades | R-TEC-57 | TEC-1, TEC-3 | D3 |
| TEC-4.2 | PDP con negación por defecto y registro encadenado | R-TEC-58; verificación de la cadena | TEC-4.1, TEC-2.7 | D3 |
| TEC-4.3 | *timeouts*, reintentos e interruptores por herramienta | R-TEC-99 a R-TEC-101 | TEC-4.1 | D3 |
| TEC-4.4 | verificación posterior y efectos inciertos | R-TEC-53 y R-TEC-64 | TEC-4.1 | D3 |
| TEC-4.5 | arnés de propiedades para los invariantes de Gobierno | GOB-5 corre 1.000 ejemplos en CI | TEC-4.2 | D4 |
| **TEC-5** | **Superficie de chat** | | | |
| TEC-5.1 | endpoint AG-UI por SSE con el mapeo de 2.9 | eventos validados con el SDK | TEC-0.3, TEC-2 | D4 |
| TEC-5.2 | SPA con los seis componentes | Playwright por componente | S-TEC-09, TEC-1.3 | D4 |
| TEC-5.3 | confirmación por `nonce` | R-TEC-77 | TEC-5.1 | D4 |
| TEC-5.4 | emisión por frases y filtro de salida | R-TEC-74 y R-TEC-75 | TEC-5.1 | D4 |
| TEC-5.5 | modo WhatsApp simulado con ventana de 24 horas | R-TEC-78 | TEC-5.2 | D5 |
| TEC-5.6 | dispositivo simulado de OTP | el OTP no aparece en logs ni trazas | TEC-3.4 | D4 |
| TEC-5.7 | N1 a N6 de punta a punta en ES con Playwright | compuerta F3 | TEC-5.1 a TEC-5.4 | D4 |
| **TEC-6** | **Superficie de voz** | | | |
| TEC-6.1 | tubería Pipecat con VAD, SmartTurn y los proveedores de S1 | voz a voz medido por etapa | TEC-0.5, S-TEC-08 | D5 |
| TEC-6.2 | `ProcesadorMotor` con plantillas por frase | paridad con chat (R-TEC-81) | TEC-6.1, TEC-2 | D5 |
| TEC-6.3 | registro de lo dicho hasta la interrupción | V1 | TEC-6.2 | D5 |
| TEC-6.4 | rellenos presintetizados | R-TEC-86 | S-TEC-09 | D5 |
| TEC-6.5 | DTMF en el navegador | V8 | TEC-6.2 | D5 |
| TEC-6.6 | regla de confianza para datos críticos | V2 | TEC-6.2 | D5 |
| TEC-6.7 | cliente web de voz: WebRTC en local, WebSocket en la nube | R-TEC-82; latencia medida en ambos | TEC-6.1 | D5 |
| TEC-6.8 | punta a punta con audio sintético | los casos del chat por voz en ES (F3v) | TEC-6.2 a TEC-6.7 | D5 |
| **TEC-7** | **Gateway** | | | |
| TEC-7.1 | LiteLLM con alias, claves virtuales y presupuestos desde `agentes/registro.yaml` | cada llamada con su trabajador | S-TEC-07 | D3 |
| TEC-7.2 | redacción con Presidio y reconocedores propios | R-TEC-92 con precisión y recuperación reportadas | TEC-7.1 | D5 |
| TEC-7.3 | Model Armor en la nube con latencia medida | R-TEC-93; decide su uso por frase | TEC-7.1, TEC-11 | D6 |
| TEC-7.4 | costo por llamada en los spans | R-TEC-120 y R-TEC-121 | TEC-7.1, TEC-8.1 | D4 |
| TEC-7.5 | medición del aporte del filtro | tabla de la investigación 10 | TEC-7.3, GOB-4 | D7 |
| TEC-7.6 | salida exclusiva del gateway hacia modelos | R-TEC-06 | TEC-7.1, TEC-13.1 | D3 |
| **TEC-8** | **Trazas y panel** | | | |
| TEC-8.1 | OpenTelemetry con convenciones GenAI y atributos `latam.` | R-TEC-111 y R-TEC-112 | TEC-2.3 | D3 |
| TEC-8.2 | Phoenix en local y en la nube detrás de IAP | trazas visibles en ambos | TEC-8.1 | D3 y D6 |
| TEC-8.3 | Cloud Trace y logs correlacionados sin datos personales | R-TEC-113 y R-TEC-114 | TEC-8.1, TEC-11 | D6 |
| TEC-8.4 | paneles y alertas en Terraform | R-TEC-115 y R-TEC-116 | TEC-8.3 | D7 |
| TEC-8.5 | exportación a platino con huella encadenada | R-TEC-118 | S-TEC-06 | D8 |
| **TEC-9** | **Capacidad** | | | |
| TEC-9.1 | escenarios de Locust para chat | mezcla declarada reproducida | S-TEC-14 | D7 |
| TEC-9.2 | generador de carga de voz | voz a voz medido bajo carga | TEC-6.8 | D7 |
| TEC-9.3 | perfiles de latencia del LLM simulado ajustados a spans reales | distribución documentada | TEC-8.1 | D7 |
| TEC-9.4 | tabla de cuotas llena | R-TEC-110 | TEC-0.6 | D0 y D7 |
| TEC-9.5 | reporte de capacidad | R-TEC-109 | TEC-9.1 a TEC-9.3 | D7 |
| **TEC-10** | **Instalación de un comando** | | | |
| TEC-10.1 | perfiles de Compose (`nucleo`, `voz`, `llm-local`, `observabilidad`) | `just demo` levanta cada perfil | TEC-0.1 | D0 |
| TEC-10.2 | siembra de identidades de prueba, directorio de comercios y plantillas | `just demo` deja la demo lista | TEC-3, S-TEC-05 | D3 |
| TEC-10.3 | README de un comando con solución de problemas | Auditoría lo sigue sin preguntar | todas | D9 |
| TEC-10.4 | prueba en máquina limpia en Linux y Windows | R-TEC-44 | S-TEC-12 | D9 |
| **TEC-11** | **Infraestructura en Google Cloud** | | | |
| TEC-11.1 | módulos de Terraform de 2.3 | R-TEC-15 a R-TEC-19 | TEC-0.6 | D0 a D3 |
| TEC-11.2 | Cloud SQL con autenticación IAM y usuarios por esquema | R-TEC-127 | TEC-11.1 | D3 |
| TEC-11.3 | servicios y jobs de Cloud Run con sondas y límites | R-TEC-105 y R-TEC-106 | TEC-11.2 | D4 |
| TEC-11.4 | IAP para `lb-staff` y `lb-phoenix` | R-TEC-126 | TEC-11.3 | D5 |
| TEC-11.5 | bucket de oro en solo lectura con `origen` | R-TEC-13 | S-TEC-04, autorización D-15 | D4 |
| TEC-11.6 | desmontaje verificado | R-TEC-20 | todas | D10 |
| **TEC-12** | **CI/CD y cadena de suministro** | | | |
| TEC-12.1 | `ci.yml` completo | R-TEC-22 | TEC-0.1 | D1 |
| TEC-12.2 | `cd.yml` con despliegue sin tráfico, humo, promoción y reversión | R-TEC-24; simulacro de R-TEC-26 en F5 | TEC-11.3 | D4 |
| TEC-12.3 | WIF sin llaves | R-TEC-21 y R-TEC-125 | TEC-0.6 | D0 |
| TEC-12.4 | SBOM, escaneos y zizmor | R-TEC-39 y R-TEC-133 | TEC-12.1 | D2 |
| TEC-12.5 | enfriamiento de dependencias y Dependabot | R-TEC-30 | TEC-0.1 | D1 |
| **TEC-13** | **Seguridad de plataforma** | | | |
| TEC-13.1 | cuentas de servicio y roles de 4.1 con verificación en CI | R-TEC-124 | TEC-11.1 | D3 |
| TEC-13.2 | inventario de secretos en Secret Manager | R-TEC-128 | TEC-11.1 | D3 |
| TEC-13.3 | seguridad del navegador y límites de tasa | R-TEC-80 | TEC-5.1 | D4 |
| TEC-13.4 | interruptor "todo a humano" | R-TEC-104 | TEC-2 | D5 |
| TEC-13.5 | registros de auditoría de acceso a datos | R-TEC-136 | TEC-11.1 | D3 |
| TEC-13.6 | runbooks y simulacro | R-TEC-137 | TEC-8.4 | D7 |
| TEC-13.7 | borde con Cloud Armor (opcional) | R-TEC-132 | TEC-11.3 | D7 |
| **TEC-14** | **FinOps** | | | |
| TEC-14.1 | `finops/precios.yaml` | R-TEC-120 | | D2 |
| TEC-14.2 | consultas de costo por caso y por resolución segura | R-TEC-119 | S-TEC-06, TEC-7.4 | D6 |
| TEC-14.3 | exportación de facturación y conciliación | R-TEC-122 | TEC-0.6 | D9 |
| TEC-14.4 | sección de costos del reporte con la proyección etiquetada | R-TEC-123 | TEC-14.2 | D9 |
| **TEC-15** | **Traspaso y vista del experto (con Clientes)** | | | |
| TEC-15.1 | render del paquete desde el objeto tipado, con hechos, interpretaciones y conflictos separados | E1 a E7 | TEC-2 | D5 |
| TEC-15.2 | cola por idioma, turno y especialidad con espera declarada | E7 | S-TEC-10 | D5 |
| TEC-15.3 | vista del experto con roles y registro de acciones | R-TEC-126 | TEC-11.4 | D5 |
| TEC-15.4 | reclasificación del motivo como etiqueta para IA | evento de etiqueta en platino | TEC-15.3 | D6 |
| **TEC-16** | **Experimento nativo (recortable)** | | | |
| TEC-16.1 | Gemini Live con una sola herramienta detrás de la bandera | R-TEC-90 | S2, TEC-6.2 | D7 |
| TEC-16.2 | métricas de 5.9 y costo por minuto medido | tabla comparada con la cascada | TEC-16.1 | D8 |
| **TEC-17** | **Telefonía (recortable)** | | | |
| TEC-17.1 | número de Twilio, Media Streams y serializador | llamada real de punta a punta | TEC-6.8 | D7 |
| TEC-17.2 | validación de firma de webhooks | R-TEC-89 | TEC-17.1 | D7 |
| TEC-17.3 | prueba con degradación telefónica G.711 | V3 y V4 por teléfono | TEC-17.1 | D7 |

**Orden de recorte de Tecnología** (coherente con 07, sección 6): TEC-16, TEC-17, TEC-13.7, el modo de
streaming (TEC-5.4 pasa a respuesta completa filtrada), TEC-11.5 (demo en la nube con datos del equipo) y, por
último, la demo en la nube completa (queda la local). **Nunca se recortan:** TEC-1 a TEC-4, TEC-8.1, TEC-10 y la
parte de seguridad de TEC-13.

---

## 9. Riesgos y mitigaciones

| Riesgo | Señal | Probabilidad | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| WebRTC no funciona en Cloud Run por falta de UDP | S1 | media | medio | WebSocket en la nube; WebRTC gestionado por ADR; la demo local conserva WebRTC | Canales |
| La mediana de voz con LLM pasa de 1,0 s | S1 y F3v | alta | medio | plantillas para lo frecuente, modelo más rápido, síntesis desde la primera frase; se reporta con honestidad | Canales e IA (Voz) |
| 429 del proveedor durante las corridas | tasa de 429 | media | alto | corridas escalonadas; un reintento en el gateway; reservar tiempo en F6; LLM simulado para carga | SRE |
| Paquete comprometido en la cadena de suministro | avisos de seguridad | media | alto | R-TEC-30 y R-TEC-133; plan B de gateway propio | Plataforma |
| No se autorizan datos en la nube ni modelos externos (D-15) | respuesta de los organizadores | media | alto | datos del equipo en la nube; modelo abierto propio; demo con datos reales solo en local | Arquitectura |
| Gasto desbocado (por ejemplo, un bucle del simulador) | alerta de presupuesto | media | medio | presupuesto por clave virtual; alertas; techo de DP-TEC-12 | SRE |
| Deriva entre local y nube | humo falla en la nube | media | medio | misma imagen; Postgres real en pruebas (DP-TEC-06); humo en cada despliegue | Plataforma |
| Model Armor agrega mucha latencia por frase | medición de TEC-7.3 | media | bajo | usarlo solo en la entrada y en respuestas completas si su p95 pasa de 250 ms | Canales |
| Conexiones de Cloud SQL agotadas | errores de conexión | media | alto | R-TEC-106; pools pequeños; instancias máximas | SRE |
| Arranque en frío en la demo | primer turno lento | alta | medio | instancias mínimas en ventanas de demo; aceleración de CPU al arrancar | SRE |
| Errores de zona horaria o de reloj en plazos | pruebas de borde | media | alto | `Reloj` inyectable, reglas DTZ, casos del desfase de fechas (D8) | Plataforma |
| Fuga de un secreto | gitleaks o aviso | baja | alto | pre-commit, Secret Manager, runbook con rotación en 30 minutos | Plataforma y Gobierno |
| Capacidad del equipo (una persona en la primera línea) | backlog atrasado en la revisión diaria | alta | alto | orden de recorte; P9; LLM simulado para iterar barato | Oficina de Entrega |
| IAP directo en Cloud Run no disponible en un proyecto sin organización | F0 | media | bajo | balanceador con IAP, o autenticación de aplicación con lista de correos | Plataforma |
| El crédito de prueba no cubre algún producto | F0 | media | bajo | confirmarlo al arrancar; tarjeta con límite | Presidencia |
| Cambio de modelo o de precio a mitad del evento (fin del precio introductorio, retiro de versiones *preview*) | notas de versión | media | medio | versiones fijadas; tabla de precios con vigencia; *preview* solo en generador y juez | IA y SRE |
| Cambios de API de Pipecat entre versiones | actualización | media | medio | versión fijada; capa propia delgada sobre la tubería | Canales |
| El proveedor de voz no da confianza ni marcas de tiempo | S1 | media | medio | criterio de selección de S1; estimación por audio enviado; confianza media por defecto | IA (Voz) |
| Dependencia de un proveedor de nube | | baja | bajo | gateway compatible con OpenAI, OpenTelemetry, Terraform y contenedores estándar | Arquitectura |

---

## 10. Decisiones propuestas y preguntas abiertas

### 10.1 Decisiones propuestas

| ID | Propuesta | Relación con decisiones firmes | Principio | Consulta obligatoria |
|---|---|---|---|---|
| DP-TEC-01 | Google Cloud como plataforma de referencia, con entorno `demo` en `us-central1`; el entorno local es la vía reproducible oficial; la región de producción la fija la residencia de datos | nueva | P13, P9 | Datos, IA; Gobierno puede objetar |
| DP-TEC-02 | LiteLLM como gateway en todos los entornos, con Presidio siempre y Model Armor en la nube; Apigee como ruta a producción con mapeo política por política; evaluación gratuita de Apigee solo como *spike* opcional S7; controles de cadena de suministro y plan B de gateway propio | confirma y precisa D-20 | P9, P13, P5 | Gobierno (Seguridad), IA |
| DP-TEC-03 | Observabilidad dual en la nube: Phoenix más Cloud Trace, Logging y Monitoring | amplía D-20 (Phoenix local) | P13 | IA (Operación de agentes) |
| DP-TEC-04 | Identidad propia para clientes con llave de firma en Cloud KMS; IAP para superficies internas; Identity Platform descartado para clientes | precisa D-20 | P5, P11 | Gobierno |
| DP-TEC-05 | Transporte de voz: WebRTC entre pares en local; WebSocket del navegador a Cloud Run en la nube; WebRTC gestionado solo si S1 lo exige; telefonía opcional con Twilio y número de EE. UU. para la demo | modifica D-18 ("navegador con WebRTC") solo en la nube | P9, P13 | IA (Voz), Clientes |
| DP-TEC-06 | Pruebas de persistencia contra Postgres real en contenedor; SQLite solo en pruebas unitarias sin SQL | modifica D-20 ("SQLite en pruebas") | P13 | Datos |
| DP-TEC-07 | Oro operacional en la nube como Parquet versionado en Cloud Storage, montado en solo lectura en `lb-bian`, solo con autorización registrada; sin ella, datos generados por el equipo | aplica D-15 y D-08 | P11 | Datos, Gobierno |
| DP-TEC-08 | Terraform para la infraestructura y GitHub Actions con WIF para CI/CD; Cloud Build no se usa | nueva | P13 | |
| DP-TEC-09 | Monolito modular con seis servicios y tres trabajos (sección 2.1); el núcleo es una biblioteca | precisa 06 y D-18 (Pipecat en proceso con el motor) | P4, P9 | IA, Datos |
| DP-TEC-10 | Autorización también en la capa de servicio (JWT con `acr` y dueño), además de tipos y PDP | amplía D-05 y D-20 | P5 | Gobierno |
| DP-TEC-11 | Frontend React, TypeScript y Vite con `@ag-ui/client`; componentes como herramientas de interfaz; confirmación por `nonce` | precisa D-19 | P5, P6 | Clientes |
| DP-TEC-12 | Techo de gasto total de US$600 para la hackatón (antes de créditos), con alertas al 50, 80 y 100%; opcionales solo con aprobación | nueva; decide Presidencia | P9 | Presidencia decide; Gobierno por riesgo de terceros |
| DP-TEC-13 | Enfriamiento de 7 días para dependencias y controles de cadena de suministro de R-TEC-133 | nueva | P5, P13 | Gobierno (Seguridad) |
| DP-TEC-14 | Capacidad con Locust y generador propio de voz, en modos plataforma y real, con reporte de punto de quiebre | nueva | P2, P3 | IA (Evaluación) |

### 10.2 Preguntas abiertas

**Para los organizadores** (las envía la Presidencia, S-TEC-11):

1. ¿Se permite alojar derivados del dataset (el oro operacional) en un proyecto de nube privado del equipo?
2. ¿Una API de modelos en el proyecto propio del equipo (Vertex AI) cuenta como "*external model request*"?
3. ¿Hay créditos de nube o de APIs de modelos y de voz?
4. ¿La demo debe estar desplegada y accesible para el jurado, o bastan el video y el repositorio?
5. ¿Se permite una línea telefónica real en la demo?
6. ¿El repositorio de la entrega debe ser público? Cambia el alcance gratuito de GitHub Actions y del escaneo
   de secretos.

**Para Gobierno:** matriz de fallas abiertas o cerradas; retención por clase de dato; ventana de retoma;
presupuesto por conversación; `acr` por acción; umbral de confianza de voz; endpoint regional o global;
aceptación de LiteLLM (S-TEC-02 y S-TEC-03).

**Para IA:** modelos con versión por alias, presupuestos de tokens y familias del juez y del simulador
(S-TEC-07); resultado de S1 (S-TEC-08).

**Para Clientes:** catálogo de plantillas, rellenos y plantillas de WhatsApp (S-TEC-09); modelo de colas
(S-TEC-10).

**Para Datos:** tamaño y formato del oro operacional y del conjunto del equipo (S-TEC-04); esquemas de platino
(S-TEC-06).

**Internas de Tecnología (se cierran en F0):** latencia real desde Bogotá, Ciudad de México y Buenos Aires a
`us-central1`; disponibilidad de IAP directo en Cloud Run en nuestro tipo de proyecto; soporte de Model Armor
como guardarraíl nativo en la versión fijada de LiteLLM; versión de Pipecat y de SmartTurn; `max_connections`
de `db-g1-small`; rol exacto de IAM para Speech-to-Text y Model Armor; costo de la regla de reenvío del
balanceador.

---

## 11. Fuentes

**Consultadas para este documento el 27 de septiembre de 2026** (precios y hechos marcados [V]):

- [Precios de Cloud Run](https://cloud.google.com/run/pricing)
- [Precios de Cloud SQL](https://cloud.google.com/sql/pricing)
- [Precios de Apigee](https://cloud.google.com/apigee/pricing)
- [Política SanitizeUserPrompt de Apigee (política Extensible)](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-user-prompt-policy)
- [Model Armor, producto y precios](https://cloud.google.com/security/products/model-armor)
- [Prueba gratuita y nivel gratuito de Google Cloud](https://cloud.google.com/free/docs/free-cloud-features)
- [Precios de Cloud Logging, Cloud Monitoring y Cloud Trace](https://cloud.google.com/stackdriver/pricing)
- [Precios de Secret Manager](https://cloud.google.com/secret-manager/pricing)
- [Precios de Cloud KMS](https://cloud.google.com/kms/pricing)
- [Precios de Cloud Armor](https://cloud.google.com/armor/pricing)
- [Precios de modelos generativos en Vertex AI (Agent Platform)](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Precios de Speech-to-Text](https://cloud.google.com/speech-to-text/pricing)
- [Precios de Text-to-Speech](https://cloud.google.com/text-to-speech/pricing)
- [Precios de voz de Twilio en EE. UU.](https://www.twilio.com/en-us/voice/pricing/us) y [en Colombia](https://www.twilio.com/en-us/voice/pricing/co)
- [Aviso de seguridad de LiteLLM, marzo de 2026](https://docs.litellm.ai/blog/security-update-march-2026)
- [Datadog Security Labs: LiteLLM y Telnyx comprometidos en PyPI, campaña TeamPCP](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)

**Referencias técnicas** (estándares y documentación de herramientas):

- [AG-UI](https://docs.ag-ui.com/introduction)
- [Convenciones semánticas GenAI de OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [RFC 9470, autenticación reforzada en OAuth 2.0](https://www.rfc-editor.org/rfc/rfc9470)
- [Borrador del IETF sobre la cabecera Idempotency-Key](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
- [APIs semánticas de BIAN](https://github.com/bian-official/public)
- [WebSockets en Cloud Run](https://cloud.google.com/run/docs/triggering/websockets)
- [Microsoft Presidio](https://microsoft.github.io/presidio/)
- [Configuración `exclude-newer` de uv](https://docs.astral.sh/uv/reference/settings/#exclude-newer)
- [import-linter](https://import-linter.readthedocs.io/), [Schemathesis](https://schemathesis.readthedocs.io/), [Locust](https://locust.io/), [MADR](https://adr.github.io/madr/)

**Documentos internos:** [investigación 2](../Investigacion/02_Arquitectura_y_control.md),
[8](../Investigacion/08_IA_con_tipos_seguros.md), [10](../Investigacion/10_Gobernanza_y_gateway.md),
[11](../Investigacion/11_Latencia_y_costo.md), [17](../Investigacion/17_VP_Tecnologia.md),
[19](../Investigacion/19_Auditoria.md) y [20](../Investigacion/20_Canales_voz_y_chat.md); diseño
[00](../Diseno/00_Principios.md) a [07](../Diseno/07_Hoja_de_ruta.md) y [Decisiones](../Diseno/Decisiones.md);
[enunciado](../Documentos/Enunciado_Factored_Hackathon_2026.pdf).
