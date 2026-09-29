# LATAM Bank: atención AI-first para cargos no reconocidos

Solución para la **Factored AI & Data Hackathon 2026**: un banco inventado, LATAM Bank, que atiende por
**chat, WhatsApp y voz** (navegador y teléfono) en **español y portugués** la recepción de disputas por
cargos no reconocidos, con un núcleo determinista que decide y modelos que entienden y redactan.

**¿Sesión nueva?** Empieza por [`presidencia/ESTADO.md`](presidencia/ESTADO.md): dónde estamos y qué sigue.

## El repositorio es el organigrama

Cada carpeta de primer nivel es una cara de LATAM Bank y su dueña está en `.github/CODEOWNERS`.

| Carpeta | Cara | Qué vive ahí |
|---|---|---|
| [`presidencia/`](presidencia/README.md) | Presidencia y Oficina de Entrega | modelo operativo, decisiones, backlog, hoja de ruta, bitácora, reporte final |
| [`comun/`](comun/README.md) | Comité de Plataforma | contratos compartidos: los tipos del dominio que conectan a todas las caras |
| [`clientes/`](clientes/README.md) | VP Clientes | guiones, plantillas, operación humana, demo |
| [`ia/`](ia/README.md) | VP Inteligencia Artificial | comprensión, redacción, voz, registro de agentes, arnés de evaluación |
| [`datos/`](datos/README.md) | VP Datos | ingesta, capas bronce a platino, contratos de datos, *fixture* |
| [`tecnologia/`](tecnologia/README.md) | VP Tecnología | motor, herramientas, servicios, canales, gateway, sitio web, infraestructura, ADR |
| [`gobierno/`](gobierno/README.md) | VP Gobierno | política como código, amenazas, adversariales, privacidad, equidad, actas |
| [`auditoria/`](auditoria/README.md) | Auditoría | matriz de trazabilidad, fuentes, dictamen |
| [`docs/`](docs/README.md) | todas | investigación, diseño y enunciado |
| `.claude/agents/` | Gobierno y Auditoría | subagentes revisores en frío |

## Empezar

```bash
uv sync --all-packages --all-groups   # dependencias de todas las caras
just check         # formato, tipos y pruebas
```

Las reglas de trabajo (ramas, commits, revisiones y compuertas) están en [CONTRIBUTING.md](CONTRIBUTING.md).
