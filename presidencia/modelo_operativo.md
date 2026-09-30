# Modelo operativo de LATAM Bank: roles, cómo se hablan y cómo se resuelven las cosas

**Cara:** Presidencia y Oficina de Entrega. **Versión:** 1 (26 de septiembre de 2026).
**Propósito:** fijar las reglas del juego entre las caras de LATAM Bank antes de que cada una escriba sus
definiciones: quién decide qué, por dónde se comunican, cómo se resuelve un desacuerdo y qué forma tiene
cada documento. Se apoya en la [organización v2](../docs/diseno/04_Organizacion_y_roles.md), la
[arquitectura](../docs/diseno/06_Arquitectura.md), la [hoja de ruta](hoja_de_ruta.md) y los
[principios](../docs/diseno/00_Principios.md).

---

## 1. Roles

| Rol | Misión | Decide | Rinde cuentas a | Entrega |
|---|---|---|---|---|
| **Junta directiva** (el jurado) | calificar la entrega | la nota | | |
| **Presidencia** | que exista una entrega coherente con una sola historia | alcance, calendario, desempates, qué se recorta | la junta | la entrega |
| **Oficina de Entrega** | que el trabajo avance en orden y sin huecos | el orden del backlog y la agenda de compuertas (no el diseño) | Presidencia | backlog, bitácora diaria, integración del reporte y la demo |
| **Misión "cargo no reconocido"** | el resultado de punta a punta en chat y voz | cómo se combinan las capacidades para el resultado | VP Clientes (dueña) | el sistema funcionando |
| **VP Clientes** | que el cliente resuelva y el humano reciba el caso listo | experiencia, guiones, operación humana, resultados de servicio | Presidencia | definiciones de servicio y de conversación |
| **VP Inteligencia Artificial** | agentes y modelos que aportan contra su línea base | modelos, prompts, componente aprendido, voz, arnés de evaluación | Presidencia | trabajadores digitales con hoja de vida |
| **VP Datos** | una sola verdad certificada | capas, contratos, calidad, métricas oficiales, inventario de insumos | Presidencia | productos de datos y cifras oficiales |
| **VP Tecnología** | un sistema correcto por construcción, observable, reproducible y barato | arquitectura, plataforma, canales, infraestructura, costo técnico | Presidencia | la plataforma y el sistema desplegable |
| **VP Gobierno** | que nada llegue al cliente sin validación independiente | política, umbrales, controles de seguridad, privacidad, equidad; **veto de salida** | Presidencia (y la junta, por su veto) | política como código, retenido, controles, actas |
| **Auditoría** | que lo afirmado sea verdad y reproducible | si la evidencia alcanza; **puede devolver la entrega** | la junta | dictamen, matriz de trazabilidad |
| **Subagentes** | ejercer una cara con independencia de contexto | solo dentro del mandato de su cara | la cara que representan | documentos con formato fijo |

## 2. Derechos de decisión

Cada tipo de decisión tiene un **dueño que decide**, caras que **deben ser consultadas** y un
**revisor que puede objetar**. Nadie decide fuera de su fila.

| Tipo de decisión | Decide | Consulta obligatoria | Puede objetar |
|---|---|---|---|
| Alcance, calendario, recortes | Presidencia | Oficina de Entrega, todas las VP | Gobierno (si el recorte toca un principio) |
| Experiencia, guiones, contenido al cliente | VP Clientes | IA, Gobierno (Protección al consumidor) | Gobierno |
| Modelos, prompts, componente aprendido, voz | VP IA | Datos, Tecnología | Gobierno (Riesgo de modelo) |
| Datos: capas, contratos, calidad, métricas oficiales | VP Datos | IA, Tecnología | Gobierno (Privacidad) |
| Arquitectura, plataforma, proveedores técnicos | VP Tecnología (Comité de Plataforma) | Datos, IA | Gobierno (Seguridad) |
| Política de negocio, umbrales, controles, privacidad | VP Gobierno (Comité de Confianza) | Clientes, IA, Datos, Tecnología | Auditoría |
| Liberar una versión candidata | VP Gobierno | todas | Auditoría |
| Qué cuenta como evidencia en el reporte | Auditoría | Datos | |
| Gasto (qué se compra o se paga) | Presidencia | Tecnología (costo técnico), Gobierno (riesgo de terceros) | Gobierno |

## 3. Cómo se hablan

Las caras **se hablan por artefactos**, no por conversación suelta. Un acuerdo que no queda en un
artefacto no existe.

| Artefacto | Para qué | Dónde vive | Quién lo escribe |
|---|---|---|---|
| **Definición de cara** | las reglas, estándares e interfaces de un dominio | `Definiciones/` en el Drive | cada cara |
| **Solicitud entre caras** | pedir algo a otra cara | sección "Interfaces" de la definición y, en desarrollo, un *issue* | quien pide |
| **ADR** | registrar una decisión técnica con alternativas | `docs/adr/` en el repositorio | Tecnología, con el Comité de Plataforma |
| **Decisión** | registrar cualquier decisión del proyecto | [Decisiones.md](decisiones.md) | la cara dueña de la decisión |
| **Contrato** | fijar una interfaz: datos (ODCS), API (OpenAPI), tipos (Pydantic) | `contracts/` y `src/latam_bank/domain/` | el dueño del dato o del servicio |
| **Acta** | registrar una sesión de comité con sus desafíos | `Diseno/Actas/` | quien preside |
| **Informe de revisión** | lo que devuelve un revisor (subagente o persona) | junto a lo revisado | el revisor |
| **Bitácora diaria** | qué se cerró, qué bloquea, qué se recortó | `Diseno/Bitacora.md` | Oficina de Entrega |

### 3.1 Una solicitud entre caras

Formato fijo, para que no haya ambigüedad:

```
Solicitud S-<CARA>-<nn>
De: <cara que pide>   Para: <cara que entrega>
Qué: <artefacto o dato concreto>
Para qué: <épica o decisión que lo necesita>
Para cuándo: <día del calendario>
Aceptación: <cómo se sabe que está bien>
Estado: abierta | aceptada | entregada | rechazada (con motivo)
```

La cara que recibe responde el **mismo día**: acepta, rechaza con motivo o propone otra fecha. Una
solicitud sin respuesta pasa a la revisión diaria.

### 3.2 Una propuesta que afecta a otras caras

1. La cara dueña escribe la propuesta en su definición (o un ADR) con alternativas.
2. Las caras con consulta obligatoria (sección 2) comentan en su propio informe.
3. Gobierno desafía si toca riesgo, seguridad, privacidad o equidad.
4. El dueño decide y lo registra como decisión; si hay objeción sostenida, escala (sección 4).

### 3.3 Lenguaje común

Se usan siempre los mismos nombres: rutas **R1 a R8**, escenarios de
[01](../docs/diseno/01_Interacciones_y_criterios.md) (N, A, E, F, D, S, L, V), tipos del dominio de
[06](../docs/diseno/06_Arquitectura.md), sección 5, métricas de 01, sección 5, principios **P1 a P13**,
decisiones **D-xx**. Un término nuevo se define en la definición de la cara que lo introduce y se suma
al glosario de la sección 9.

## 4. Cómo se resuelven las cosas

### 4.1 Escalera de resolución

| Nivel | Quién | Plazo máximo en la hackatón | Qué sale |
|---|---|---|---|
| 1. Entre pares | las dos caras en conflicto | 2 horas | acuerdo escrito en ambas definiciones |
| 2. Comité | Plataforma (técnico) o Confianza (riesgo) | la siguiente sesión, mismo día | acta con desafíos y decisión |
| 3. Presidencia | desempate | 1 hora desde el acta | decisión registrada |

### 4.2 Reglas de desempate

Cuando dos objetivos chocan, gana el de arriba:

1. **Seguridad del cliente** (P5, P6, P11): ninguna acción ni dato indebido.
2. **Honestidad de la medición** (P1, P2, P3).
3. **Cumplimiento de la norma** del país del cliente.
4. **Resultado del cliente** (resolución segura, traspaso útil).
5. **Latencia y costo.**
6. **Alcance y fecha.** Si falta tiempo se recorta alcance según el orden de
   [07](hoja_de_ruta.md), sección 6, nunca un principio.

### 4.3 El veto de Gobierno

- Gobierno puede vetar una versión candidata, una política o un control. El veto va por escrito, con el
  riesgo concreto y lo que lo levantaría.
- La Presidencia **no** levanta un veto por decreto: solo con un acta del Comité de Confianza que registre
  la mitigación aceptada.

### 4.4 Cambios después de congelar

Una vez congelado el retenido (compuerta de F2), cambiar política, métricas, umbrales o casos exige acta
del Comité de Confianza y se reporta en el informe final (P1).

## 5. Cadencia

| Qué | Cuándo | Quién | Sale |
|---|---|---|---|
| Revisión diaria | cada mañana, 15 minutos | Oficina de Entrega con las VP | bitácora: cerrado, bloqueado, recortado |
| Comité de Plataforma | cuando hay ADR o contrato nuevo | Tecnología preside | acta |
| Comité de Confianza | en cada compuerta de Gobierno (F2, F4, F5, F6) | Gobierno preside | acta |
| Retrospectiva | al cerrar cada fase | todas | una mejora concreta al proceso |

## 6. Las definiciones de cada cara

### 6.1 Plantilla obligatoria

Cada cara escribe `Definiciones/<nn>_<Cara>.md` con estas secciones, en este orden:

1. **Mandato y alcance** en la misión.
2. **Definiciones y estándares del dominio:** las reglas del juego, numeradas `R-<CARA>-<nn>`, cada una
   verificable (cómo se sabe si se cumple).
3. **Decisiones de tecnología** del dominio, con estado del arte citado, la opción en Google Cloud cuando
   aplique y sus alternativas.
4. **Seguridad, privacidad y gobierno** del dominio: controles concretos.
5. **Interfaces:** qué entrega a cada cara y qué necesita de cada cara (solicitudes `S-<CARA>-<nn>`).
6. **Métricas y criterios de aceptación** del dominio.
7. **Compras y costos:** qué hay que comprar o pagar, para qué, costo estimado en la hackatón y en
   producción, supuestos y alternativa gratuita.
8. **Backlog propuesto:** épicas e historias `<CARA>-<épica>.<n>` con criterio de aceptación y
   dependencias.
9. **Riesgos y mitigaciones.**
10. **Decisiones propuestas** `DP-<CARA>-<nn>` y **preguntas abiertas.**
11. **Fuentes.**

Prefijos: `CLI` Clientes, `IA` Inteligencia Artificial, `DAT` Datos, `TEC` Tecnología, `GOB` Gobierno,
`AUD` Auditoría, `PRE` Presidencia.

### 6.2 Estilo

Español; sin guiones, rayas ni puntos medios como puntuación en prosa; sin emojis; tablas donde
ordenen; cada cifra con su fuente; lo verificado, lo supuesto y lo proyectado separados (P3).

### 6.3 Plataforma

Google Cloud es la plataforma de referencia mencionada por la presidencia; cada cara la usa por defecto
cuando aporta (gobierno de datos, seguridad, modelos, voz) y propone alternativas cuando otra opción es
mejor, con la razón. La reproducibilidad local se conserva (P13).

## 7. Cómo se iteran las definiciones hasta cerrarlas

1. **Primera versión:** cada cara escribe su definición (subagentes en paralelo).
2. **Desafío de Gobierno:** revisa las definiciones de la primera línea (Clientes, IA, Datos, Tecnología).
3. **Auditoría de completitud:** revisa todas contra el enunciado, entre sí (contradicciones, huecos,
   solicitudes sin dueño) y contra las decisiones.
4. **Resolución:** la Oficina de Entrega consolida hallazgos, aplica la escalera de la sección 4 y
   registra decisiones.
5. **Segunda versión:** cada cara corrige lo que le toca.
6. **Cierre:** Auditoría confirma que no quedan hallazgos bloqueantes. Entonces las reglas del juego
   están dadas y empieza el backlog de desarrollo.

Un hallazgo es **bloqueante** si deja una exigencia del enunciado sin dueño, contradice un principio o
una decisión firme, o deja una interfaz sin quien la entregue.

## 8. Definición de listo y de terminado

| | Una historia está lista cuando | Una historia está terminada cuando |
|---|---|---|
| Todas | tiene dueño, criterio de aceptación, dependencias resueltas y referencia a su regla o escenario | cumple su criterio y está enlazada desde el backlog |
| Código | el contrato de la interfaz existe | tipado estricto, pruebas, trazas, en `just test` |
| Componente con IA | hay línea base y conjunto de desarrollo | hoja de vida y evaluación reportada |
| Datos | el contrato de datos está aprobado | contrato validado y huella reproducible |
| Artefacto de Gobierno | la norma está identificada | acta y firma |

## 9. Glosario común (se amplía con cada definición)

| Término | Significado |
|---|---|
| Misión | el equipo orientado al resultado "cargo no reconocido" |
| Ruta R1 a R8 | los finales posibles de una conversación ([01](../docs/diseno/01_Interacciones_y_criterios.md), sección 2) |
| Retenido | conjunto de evaluación congelado, representativo y de estrés (D-16) |
| Hecho verificado | dato producido por una herramienta, con fuente y hora |
| Superficie | canal de entrada y salida (chat o voz) sin poder de decisión |
| Núcleo | motor de flujo, política, herramientas y estado |
| Compuerta | punto de control al final de una fase, con firma |
