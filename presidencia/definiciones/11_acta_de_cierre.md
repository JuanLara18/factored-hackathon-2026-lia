# Acta de cierre de las reglas del juego (versión 1)

**Cara:** Presidencia y Oficina de Entrega. **Fecha:** 27 de septiembre de 2026.
**Objeto:** dar por cerradas las reglas del juego de LATAM Bank sin una segunda ronda de subagentes. La
segunda versión se cortó tres veces por el límite de uso de la sesión y ninguna cara alcanzó a
aplicarla; en lugar de reescribir seis documentos de 1.100 a 2.200 líneas, se cierra con reglas de
precedencia que hacen el conjunto consistente.

---

## 1. Cómo se leen las definiciones a partir de hoy

1. **Precedencia.** Si dos textos se contradicen, gana el de más arriba: [Decisiones](../Diseno/Decisiones.md)
   (D-01 a D-28), luego la [resolución 10](10_Resolucion_Presidencia.md), luego los hallazgos aceptados
   de [08](08_Desafio_Gobierno.md) y [09](09_Auditoria_de_definiciones.md), y al final las definiciones
   `01` a `06`. Una regla R-xxx contradicha por un texto superior queda sin efecto en ese punto.
2. **Aceptación tácita.** Toda solicitud S-xxx sin respuesta escrita queda **aceptada** por la cara que la
   recibe, con la fecha pedida, salvo que 08, 09 o 10 digan otra cosa. Quien no pueda cumplirla lo
   levanta en la revisión diaria. Esto cierra H-AUD-01.
3. **Correcciones pendientes como historias.** Lo que cada cara debía cambiar en su segunda versión pasa
   al backlog como historia de primer día de su épica (sección 3), en vez de reescribir el documento.

## 2. Estado de los hallazgos

| Hallazgo | Estado |
|---|---|
| H-AUD-01 (solicitudes sin respuesta) | cerrado por la regla 2 |
| H-AUD-02 (solicitudes a la Presidencia) | cerrado en la resolución 10, sección 3 |
| H-AUD-04 (familias de modelos en costos) | cerrado por D-24 y la regla 1; la tabla 7.3 de Tecnología queda sin efecto |
| H-AUD-19 ("AI-first" y trabajo restante) | cerrado con PRE-3.4 y PRE-3.5 |
| Choques 1 a 12 y H-GOB-01 a 04 | cerrados en D-22 a D-28 |
| Mayores y menores restantes | pasan al backlog (sección 3) |

**Veredicto de la Oficina:** no quedan bloqueantes abiertos. Queda pendiente la pasada fría de
Auditoría (R-AUD-54) sobre versiones con huella, que se hace al arrancar F0 con el repositorio creado.

## 3. Correcciones que pasan al backlog (primer día de cada épica)

| Historia | Cara | Qué |
|---|---|---|
| TEC-0.8 | Tecnología | tabla única de costos con D-24, D-25 y los tamaños de R-GOB-53; costo humano de Latinoamérica y WhatsApp [P] en la proyección |
| DAT-1.0 | Datos | quitar estado civil y educación de `plata_restringida`; M-07 por tipo U1 a U13; marcadores sin valores hacia modelos |
| IA-1.0 | IA | tabla de familias de D-24; k de D-26; fichas de términos antes de usar proveedores de prueba |
| CLI-1.0 | Clientes | F5 siempre en R5 sin afirmar el vencimiento; bloqueo sin OTP |
| GOB-1.0 | Gobierno | sus cuatro menores; banda de edad para auditar; tabla de retención con dos filas |
| AUD-1.0 | Auditoría | huellas de las versiones; verificar primero C-2 y C-4 y las 28 referencias pendientes |

## 4. Lo que hay que pagar (D-25)

| Qué | Para qué | Estimado 10 días | Obligatorio |
|---|---|---|---|
| Modelos en Vertex AI (Gemini, Claude) y abiertos | comprensión, redacción, generador, juez, evaluación con k repeticiones | US$300 (escenario austero) | sí |
| Reconocimiento y síntesis de voz (Chirp 3 o el ganador de S1) | canal de voz y retenido de voz | incluido arriba; ≈US$0,03 por minuto | sí |
| Plataforma Google Cloud (Cloud Run, Cloud SQL, KMS, Secret Manager, Logging) | despliegue gobernado de la demo | ≈US$25 | sí, si se despliega |
| Datos en la nube (BigQuery, Storage) | perfil de nube de datos | hasta US$50 | solo con autorización de organizadores |
| Gobierno (Model Armor, SCC, SDP) | filtros y controles | hasta US$30 | Model Armor sí |
| Auditoría (segunda opinión, reejecución) | verificación | hasta US$60 | sí |
| Revisión nativa de portugués | calidad del PT | hasta US$150 | solo sin voluntario al D2 |
| Telefonía (Twilio, número de EE. UU.) | demo por teléfono | a confirmar | no |
| Apigee | gateway de producción | US$1.460 al mes | no (ruta a producción) |

**Total indispensable:** US$340 a 460, dentro del techo de US$600. El crédito de prueba de Google Cloud
(US$300, cuentas nuevas) baja el desembolso. **Nada se compra sin la aprobación de la presidencia
humana.**

## 5. Pendientes que no puede cerrar el equipo

1. Enviar las doce preguntas de [Preguntas_organizadores.md](../Diseno/Preguntas_organizadores.md).
2. Aprobar el gasto y abrir la facturación de Google Cloud.
3. Conseguir voluntarios con consentimiento (idealmente un hablante nativo de portugués).
4. Confirmar si el código se puede preparar antes del inicio oficial.

## 6. Qué sigue

Con las reglas cerradas, el desarrollo arranca por el [backlog consolidado](../Diseno/08_Backlog.md) en el
orden de la [hoja de ruta](../Diseno/07_Hoja_de_ruta.md): D0 empieza por TEC-0.1 (repositorio con esqueleto,
pre-commit, `justfile` y CI), AUD-4.1 y los subagentes de Gobierno, DAT-1.1 (espejo del bucket) y los
*spikes* S1 a S5 en local.
