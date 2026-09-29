# Estado del proyecto

Traspaso entre sesiones. Se reescribe al cerrar cada jornada; el historial está en [bitacora.md](bitacora.md).

**Actualizado:** 29 de septiembre de 2026.

## Dónde estamos

| Frente | Estado | Dónde |
|---|---|---|
| Plataforma | Todo en Google Cloud (D-30). Proyecto `latam-bank-hackaton-2026` en **sandbox de BigQuery**, sin facturación: la cuenta de facturación está cerrada | [decisiones.md](decisiones.md) |
| Datos | Bronce, plata, oro y platino en BigQuery; manifiesto encadenado; reglas Q-BRZ; dbt con 56 pruebas en verde; siete fichas de oro operacional y 12 dominios canónicos | [datos/README.md](../datos/README.md), [LIMITACIONES](../datos/LIMITACIONES.md) |
| Gobierno | Guardas contra datos y credenciales en pre-commit y CI; gitleaks configurado; `policy/v1` con huella (escalamiento, crédito provisional, riesgo, ACR por acción, traspaso) que el motor lee | `gobierno/src/latam_gobierno/guardas.py` |
| Auditoría | `fuentes.yaml` con 66 fuentes; plantillas del paquete de independencia y del informe sellado | `auditoria/` |
| Tecnología | ADR 0001 a 0010; perfiles de Compose; spike S4 (retoma idempotente de chat a voz) y spike S3 (chat AG-UI) funcionan; motor del caso de disputa y herramientas del agente (lectura de oro por cliente, efectos idempotentes con aprobación); Terraform escrito y **sin validar ni aplicar** | `tecnologia/adr/`, `tecnologia/infra/` |
| IA | IA-7.1 (registro de agentes y config del gateway) e IA-9.1 (biblioteca de prompts) sobre Gemini gratuito; fábrica de modelos con `TestModel` sin llave | [ia/README.md](../ia/README.md) |
| Clientes | CLI-1.1 a CLI-1.3 y CLI-1.6: matriz de 10 estados x 3 canales x usted y vos, guía de estilo, plantillas críticas y linter en pytest; la lista de frases prohibidas la comparte la IA | [clientes/README.md](../clientes/README.md) |

## BigQuery

Dataset `latam_bank`, con la capa como prefijo de tabla (7,2 GB de 10 GB; las tablas vencen el **28 de noviembre de 2026**):

| Capa | Tablas | Contenido |
|---|---|---|
| `bronce_` | 13 | crudo, todo texto; cuadra con los CSV (`platino_manifiesto_tablas`) |
| `plata_` | 14 | tipado, deduplicado, PII seudonimizada; `plata_digital_events` es vista |
| `oro_` | 8 | siete operacionales para el agente, sin PII; línea base de reclamos |
| `platino_` | 8 | manifiesto, calidad, conversiones fallidas, huérfanos, respaldo, inventario |

`latam_seguridad` guarda la llave de seudonimización; `latam_pruebas`, los fallos de las pruebas de dbt (7 días).
`AS_OF` = 2026-06-17. Copia local del bucket (fuera de git) en `C:\Users\LaraJ\Projects\fh-datos\data\`
(`espejo/` 5,0 GB y `respaldo_20260831/` 4,5 GB; el respaldo del organizador está incompleto de origen).

## Pendientes del usuario

1. Decidir si se reabre la facturación (tope real US$20). Sin ella no hay Cloud Run, Vertex AI, Cloud SQL ni
   buckets; los modelos irían por el nivel gratuito de la API de Gemini (llave de AI Studio).
2. Instalar Terraform y correr `terraform fmt -recursive` y `terraform validate` en `tecnologia/infra/terraform/envs/dev`.
3. Instalar `just` (las recetas del `justfile` se usan en la documentación).
4. Las llaves del organizador quedaron en el perfil `default` de AWS; revisar si había credenciales propias ahí.
5. Meta (WhatsApp) y Twilio en modo de prueba; preguntas a los organizadores.
6. Crear una llave de AI Studio (https://aistudio.google.com/apikey) y exportarla como `GEMINI_API_KEY`; sin ella la IA corre con `TestModel`.

## Siguientes historias, en orden

1. **IA-3.1 e IA-7.2:** redacción y renderizador por locale; hojas de vida generadas.
2. **IA-5.1:** arnés de evaluación con verificadores deterministas sobre el agente de disputas (en curso).
3. **Clientes:** CLI-1.4 (catálogo completo de chat), CLI-1.5 (portugués) y visto bueno de Gobierno a la guía (S-CLI-02).
4. **Tecnología:** web del chat sobre el spike S3 conectada al agente de disputas.

## Cómo se trabaja

Ramas `feature/<cara>-<historia>-<tema>` desde `develop`, una por subagente en su propio worktree (`../fh-<tema>`);
se fusionan a `develop` con `just check` en verde. Commits de una línea.
