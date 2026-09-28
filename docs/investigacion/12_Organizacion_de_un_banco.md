# Investigación 12: cómo se organiza un banco para operar IA

**Pregunta:** si vamos a trabajar el reto "con varias caras", como si fuéramos las vicepresidencias
de un banco, ¿qué caras tiene de verdad un banco regulado en México, Colombia y Argentina, cómo se
reparten la responsabilidad sobre un sistema de IA y qué funciona cuando esos roles los ejercen
personas o agentes durante un desarrollo corto?

**Hallazgo central:** la organización de un banco frente a la IA no se diseña por áreas de
conocimiento (datos, IA, TI) sino por **quién construye, quién desafía y quién certifica**: las
**tres líneas de defensa**. Las áreas técnicas se pueden agrupar de varias formas; lo que no se
negocia es que quien evalúa y aprueba sea independiente de quien construye, y que cada comité deje
**decisiones y desafíos registrados**, no solo nombres.

---

## 1. ¿Hay un banco? Sí: LATAM Bank

El dataset ya define el banco: **LATAM Bank**, regional, con 150 mil clientes, 400 mil productos,
350 sucursales, 1.200 agentes de servicio y operación en México, Colombia y Argentina entre junio de
2023 y junio de 2026. No hace falta inventarlo; hace falta **completarlo** (estructura, políticas,
apetito de riesgo) y declarar qué parte es supuesto del equipo.

**Advertencia de escala:** 800 mil interacciones en 1.097 días son unas 730 al día para 1.200
agentes, es decir **0,6 contactos por agente al día**, y hay 430 clientes por sucursal. Un banco
real tiene órdenes de magnitud más clientes por agente. El dataset es una **muestra**, no el banco
completo: cualquier proyección de ahorro o de capacidad se hace con supuestos explícitos y se
etiqueta como proyección (P3).

**Hilo narrativo disponible:** el enunciado pide portugués y los datos traen transacciones en Brasil
(cerca del 1% en la muestra). Un supuesto honesto es que LATAM Bank atiende clientes que viajan u
operan en Brasil y prepara su entrada a ese mercado; eso justifica el portugués sin fingir datos que
no existen.

## 2. Las caras de un banco

### Alta dirección típica

En los bancos grandes el presidente tiene como reportes directos a los negocios más los dueños de
funciones: finanzas (CFO), riesgos (CRO), tecnología (CIO o CTO), operaciones (COO), jurídica,
talento y, cada vez más, **datos y analítica (CDAO)**. JPMorgan tiene al CDAO en ese primer nivel
([Creately](https://creately.com/org-chart/fortune-500/jpmorgan-chase/)); Bank of America agrupa
tecnología e información en una sola cabeza ([Databahn](https://www.databahn.com/pages/bank-of-america-org-chart-report)).
En Colombia, Bancolombia definió en 2016 ocho vicepresidencias corporativas: Empresas y Gobierno,
Personas y Pymes, Estrategia y Finanzas, **Riesgos**, Jurídica, Innovación, **Auditoría** y Gestión
Humana ([Grupo Bancolombia](https://www.grupobancolombia.com/corporativo/gobierno-corporativo/estructura)).

### Datos e IA: juntos y arriba

| Evidencia | Qué dice |
|---|---|
| **BBVA, mayo de 2026** | crea el área global **AI Transformation** en el primer nivel de la organización, que **integra el área de Datos** con las capacidades para desarrollar, desplegar y gestionar **agentes de IA**; el objetivo es "industrializar" agentes con plataformas comunes ([Noticias Bancarias](https://noticiasbancarias.com/bancos/29/05/2026/bbva-situa-la-inteligencia-artificial-en-el-primer-nivel-de-su-organizacion-con-una-nueva-area-global/287970.html), [Deia](https://www.deia.eus/actualidad/sociedad/2026/05/29/bbva-crea-nueva-area-global-inteligencia-artificial-11132249.html)) |
| **Gartner 2025** | el 70% de los CDAO ya es responsable de la estrategia y el modelo operativo de IA; el 36% reporta al CEO ([EWSolutions](https://www.ewsolutions.com/chief-data-officer-vs-cio-vs-cdao/)) |
| **McKinsey** | en IA generativa, los bancos con modelo **centralizado** son los que más capturan valor; sin supervisión central los pilotos se quedan en silos. Los centros de excelencia mantienen la arquitectura, las plataformas y los guardarraíles ([McKinsey](https://www.mckinsey.com/industries/financial-services/our-insights/scaling-gen-ai-in-banking-choosing-the-best-operating-model)) |
| **Nubank** | ciencia de datos con dos roles distintos, científico de datos (análisis y negocio) e ingeniero de ML (ingeniería e infraestructura), repartidos en todas las unidades; la IA como parte de todo y no como departamento aislado; el soporte (*Customer Excellence*, agentes "Xpeers") fue la primera plataforma priorizada ([Building Nubank](https://building.nu.com/with-ai-nubank-is-pioneering-a-future-of-inclusive-personalized-financial-services/), [Precog](https://building.nu.com/presenting-precog-nubanks-real-time-event-ai/)) |

### El problema del Chief AI Officer

En el primer trimestre de 2026 se nombraron 47 CAIO, entre ellos el de HSBC, más del doble del ritmo
de 2025, y el diagnóstico repetido es **responsabilidad sin autoridad**: si el cargo no tiene
presupuesto ni capacidad de frenar a las unidades de negocio, se vuelve decorativo
([Product Impact](https://productimpactpod.com/news/hsbc-chief-ai-officer-wave-prediction/),
[Digital Chiefs](https://www.digital-chiefs.de/en/chief-ai-officer-2026/)). **Lección para
nosotros:** un rol que no puede bloquear una compuerta ni es dueño de un artefacto no existe.

## 3. Las tres líneas de defensa aplicadas a la IA

| Línea | Quién | Qué hace con un sistema de IA |
|---|---|---|
| **Primera** | el negocio dueño del caso de uso y quienes desarrollan, operan y usan el modelo | evalúa el riesgo inicial, implementa controles (validación de entradas, monitoreo de salidas, pruebas de sesgo), documenta, opera dentro de parámetros aprobados |
| **Segunda** | riesgos (con **riesgo de modelo**), cumplimiento, seguridad de la información | **validación independiente**: revisa código, documentación y decisiones metodológicas; desafía; monitorea |
| **Tercera** | auditoría interna | asegura ante la junta que el marco se cumplió |

([Yields](https://www.yields.io/insights/the-three-lines-of-defence-in-model-risk-management),
[Backbase](https://www.backbase.com/blog/ai-governance-in-banking),
[arXiv 2212.08364](https://arxiv.org/pdf/2212.08364))

- El **BIS** recomienda **adaptar** las tres líneas existentes a los riesgos de IA, no crear una
  estructura paralela ([Libertify, marco BIS](https://www.libertify.com/interactive-library/ai-governance-banking-bis-framework/)).
- **SR 26-2** (Fed, OCC y FDIC, 17 de abril de 2026) **reemplazó a SR 11-7** como guía de riesgo de
  modelo: enfoque por materialidad, riesgo agregado y supervisión independiente más fuerte. Deja
  **fuera de su alcance la IA generativa y agéntica**, que cada institución gobierna con sus
  prácticas de riesgo existentes mientras la Fed recoge comentarios para una guía propia
  ([OCC, Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html),
  [Sullivan & Cromwell](https://www.sullcrom.com/insights/memo/2026/April/OCC-Fed-FDIC-Issue-Revised-Guidance-Model-Risk-Management),
  [CRA](https://www.crai.com/insights-events/publications/model-risk-management-guidance-sr-26-2-in-the-era-of-ai/)).
  **Consecuencia para nosotros:** no hay un estándar regulatorio cerrado para validar un agente de
  lenguaje; hay que **proponer** uno y defenderlo, y un componente cuantitativo como el puntaje de
  riesgo sí cae en la lógica clásica de validación, desafío efectivo y monitoreo. Hay propuestas
  académicas compatibles con SR 26-2 para IA generativa ([arXiv 2607.04103](https://arxiv.org/html/2607.04103v1)).
- El **BCE** (febrero de 2026) señala brechas de responsabilidad y pide evaluación previa a la
  implementación, **participación de la segunda línea** y monitoreo posterior, y advierte que **los
  nombres de comités son evidencia débil sin decisiones aprobadas y registros de desafío**
  ([KLA](https://kla.digital/blog/ai-governance-banking-2026-guide)).
- El **AI Act** de la UE exige, desde agosto de 2026, estructuras de responsabilidad para IA de
  alto riesgo (entre ellas la evaluación crediticia) ([BankingNewsAI](https://www.bankingnewsai.com/ai-governance)).
- ¿Dónde va seguridad? Hay dos escuelas: el CISO bajo tecnología (cerca de quien construye) o bajo
  riesgos (**independencia**, separación entre dueño del riesgo y supervisor del riesgo)
  ([EY](https://www.ey.com/en_ch/insights/cybersecurity/where-should-your-ciso-sit-in-the-three-lines-of-defense-model),
  [SideChannel](https://sidechannel.com/blog/ciso-reporting-structure-options/)).

## 4. Funciones que la regulación obliga a tener, por país

Esto no es opcional: un banco en estos tres países **debe** tener estas caras. Es la base más
defendible para decidir qué vicepresidencias existen.

| Función | Colombia (SFC) | México (CNBV, CONDUSEF) | Argentina (BCRA) |
|---|---|---|---|
| Gestión integral de riesgos | **SIAR**: integra crédito, mercado, operacional, liquidez y otros, con agregación de datos de riesgo; revisión anual ([SFC, proyecto 2026](https://www.ambitojuridico.com/sites/default/files/2026-03/PROY-SUPERFINANCIERA-SARCO.pdf)) | **Unidad para la Administración Integral de Riesgos (UAIR)** designada por la institución ([Circular Única de Bancos](https://www.cnbv.gob.mx/Normatividad/Disposiciones%20de%20car%C3%A1cter%20general%20aplicables%20a%20las%20instituciones%20de%20cr%C3%A9dito.pdf)) | gestión de riesgos con participación de directorio |
| Cumplimiento normativo | cumplimiento y control interno | **Contralor normativo**, que reporta al consejo o al comité de auditoría ([CNBV](https://www.cnbv.gob.mx/Normatividad/Reglas%20generales%20para%20la%20integraci%C3%B3n%20de%20expedientes%20que%20contengan%20la%20informaci%C3%B3n%20que%20acredite%20el%20cumplimiento%20de%20los.pdf)) | cumplimiento |
| Lavado de activos | **SARLAFT** con funcionario responsable ([SFC](https://www.superfinanciera.gov.co/loader.php?lServicio=Tools2&lTipo=descargas&lFuncion=descargar&idFile=1070337)) | oficial de cumplimiento PLD | oficial de cumplimiento (UIF) |
| Consumidor financiero | **Defensor del Consumidor Financiero**: atiende y resuelve quejas, concilia y es vocero del consumidor ante la entidad ([SFC](https://www.superfinanciera.gov.co/preguntas-frecuentes/5/5-defensor-del-consumidor-financiero/)) | **Unidad Especializada de Atención a Usuarios (UNE)** ante CONDUSEF, verificada en la [investigación 18](18_VP_Gobierno.md) | **responsable de atención al usuario de servicios financieros**, obligatorio según el BCRA, verificado en la [investigación 18](18_VP_Gobierno.md) |
| Datos personales | **Ley 1581 de 2012**, supervisa la SIC ([Función Pública](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981)) | **nueva LFPDPPP** del 20 de marzo de 2025; desaparece el INAI y la autoridad pasa a la Secretaría Anticorrupción y Buen Gobierno ([Garrigues](https://www.garrigues.com/es_ES/noticia/mexico-nueva-ley-federal-proteccion-datos-personales-posesion-particulares-introduce)) | Ley 25.326 |
| Tecnología y seguridad | riesgo operacional y ciberseguridad | riesgo tecnológico en la Circular Única | **Comunicación A 7724** (marzo de 2023): gobierno de tecnología y seguridad con **participación activa del directorio**, continuidad y tercerización ([Segu-Info](https://blog.segu-info.com.ar/2023/03/nueva-bcra-comunicacion-7724-requisitos.html), [Grant Thornton](https://www.grantthornton.com.ar/en/insights/articles/2023/communication-a7724-bcra/)) |
| Auditoría | auditoría interna y revisoría fiscal | comité de auditoría del consejo | auditoría interna |

**Lectura:** el **defensor del consumidor** (y sus pares en México y Argentina) es la cara que casi
ningún equipo de hackatón piensa, y es justo la que pregunta por equidad, por explicaciones y por el
derecho a un humano: los criterios que el jurado revisa en el punto 5 y en la comparación por
segmento.

## 5. El servicio al cliente como organización

- McKinsey: el contact center suele ser **el primer dominio** de inversión en IA del banco porque
  concentra datos; el valor aparece cuando se **recablea el dominio completo** (operación,
  tecnología, ciencia de datos y riesgo juntos), no cuando la IA se pega encima
  ([McKinsey, customer care](https://www.mckinsey.com/industries/financial-services/our-insights/the-ai-powered-bank-rewiring-for-excellence-in-customer-care),
  [McKinsey, rewiring](https://www.mckinsey.com/industries/financial-services/our-insights/extracting-value-from-ai-in-banking-rewiring-the-enterprise)).
- Al crecer, el contact center separa la jefatura de primera línea de **planeación de capacidad**
  (*workforce management*), **calidad** y **formación** ([Nextiva](https://www.nextiva.com/blog/contact-center-staffing.html)).
- Aparecen roles nuevos: **diseñador conversacional** y **entrenador de IA conversacional**, que
  cuidan que las respuestas del agente virtual sean correctas y pertinentes
  ([GoodCall](https://www.goodcall.com/bpo/how-ai-will-transform-call-center-agent-roles),
  [Cresta](https://job-boards.greenhouse.io/cresta/jobs/4782039008)).

## 6. Roles ejercidos por agentes durante el desarrollo

Si las caras las ejercen agentes de IA (o una persona que se pone distintos sombreros), la
literatura de desarrollo con varios agentes dice qué funciona:

- **MetaGPT** organiza agentes como una empresa de software (producto, arquitecto, jefe de proyecto,
  ingeniero, QA) que siguen **procedimientos operativos estándar** y producen **documentos
  estructurados**, no conversación libre; con eso supera a ChatDev y a un solo agente
  ([arXiv 2308.00352](https://arxiv.org/html/2308.00352v6)).
- **ChatDev** encadena conversaciones de a dos entre roles (CEO, CPO, CTO, programador, revisor,
  probador) ([IBM](https://www.ibm.com/think/topics/chatdev)).

**Lección:** una cara vale por **el artefacto que produce, el que revisa y la compuerta que firma**.
Personajes que opinan sin entregables producen ruido. Y la regla bancaria coincide: la revisión
independiente solo sirve si **quien revisa no es quien construyó** (P1).

## 7. Lo que se desprende para el proyecto

1. El banco existe (LATAM Bank); lo completamos con supuestos declarados y lo usamos como marco de
   todas las decisiones.
2. Las caras salen de tres fuentes, en este orden: **las funciones obligatorias por regulación**,
   **las tres líneas de defensa** y **los seis criterios del enunciado**. Una cara que no cubre
   ninguna de las tres sobra.
3. Datos e IA van **juntos y centralizados** (BBVA 2026, McKinsey) salvo que haya razón para
   separarlos.
4. La evaluación del sistema es **segunda línea**: la ejerce riesgo de modelo, no quien construye.
5. Cada cara tiene mandato, artefactos, compuerta y **poder de veto**; los comités dejan decisión y
   desafío por escrito.
6. La organización tiene **dos usos**: cómo nos repartimos el desarrollo y cómo operaría LATAM Bank el
   sistema en producción (quién aprueba un cambio de prompt, quién responde a un incidente). El
   segundo es parte del entregable (criterio 6).

## Fuentes principales

- [BBVA, área AI Transformation (2026)](https://noticiasbancarias.com/bancos/29/05/2026/bbva-situa-la-inteligencia-artificial-en-el-primer-nivel-de-su-organizacion-con-una-nueva-area-global/287970.html)
- [McKinsey, modelo operativo de IA generativa en banca](https://www.mckinsey.com/industries/financial-services/our-insights/scaling-gen-ai-in-banking-choosing-the-best-operating-model)
- [Tres líneas de defensa en riesgo de modelo, Yields](https://www.yields.io/insights/the-three-lines-of-defence-in-model-risk-management)
- [SR 26-2, OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html)
- [Gobierno de IA en banca 2026, KLA](https://kla.digital/blog/ai-governance-banking-2026-guide)
- [El problema del Chief AI Officer, Product Impact](https://productimpactpod.com/news/hsbc-chief-ai-officer-wave-prediction/)
- [Defensor del Consumidor Financiero, SFC](https://www.superfinanciera.gov.co/preguntas-frecuentes/5/5-defensor-del-consumidor-financiero/)
- [BCRA, Comunicación A 7724](https://blog.segu-info.com.ar/2023/03/nueva-bcra-comunicacion-7724-requisitos.html)
- [Nueva LFPDPPP, Garrigues](https://www.garrigues.com/es_ES/noticia/mexico-nueva-ley-federal-proteccion-datos-personales-posesion-particulares-introduce)
- [MetaGPT](https://arxiv.org/html/2308.00352v6)
