# Cómo se trabaja en este repositorio

## Ramas

| Rama | Qué es | Cómo se llega |
|---|---|---|
| `main` | **producción**: lo que está desplegado y lo que se entrega | solo desde `release/*` o `hotfix/*`, con la compuerta firmada (acta en `gobierno/actas/`) y una etiqueta `vX.Y.Z` |
| `develop` | **integración**: lo que ya pasó revisión y CI | *pull request* desde `feature/*` |
| `feature/<cara>-<historia>-<tema>` | trabajo de una historia del backlog | se crea desde `develop`; ejemplo `feature/tec-0.1-esqueleto` |
| `release/vX.Y.Z` | candidata a producción | desde `develop` al cerrar una fase; aquí corre Gobierno |
| `hotfix/<tema>` | corrección urgente de producción | desde `main`; vuelve a `main` y a `develop` |

Prefijos de cara: `pre`, `cli`, `ia`, `dat`, `tec`, `gob`, `aud`.

## Commits

Una línea, en español, con prefijo convencional: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`,
`chore: ...`, `refactor: ...`. Un commit por intención. El detalle vive en el *pull request* y en la bitácora.

## Pull requests

- Uno por historia, con su ID (`TEC-0.1`) en el título y la plantilla completa.
- CI en verde: formato, tipos estrictos, pruebas y escaneo de secretos.
- Revisión de la cara dueña de cada carpeta tocada (`.github/CODEOWNERS`).
- Si toca `gobierno/politica/`, contratos o herramientas, revisión del subagente de Gobierno.

## Compuertas

Pasar de `develop` a `main` es una compuerta de fase (F0 a F7,
[hoja de ruta](presidencia/hoja_de_ruta.md)). Sin acta firmada no hay *release*.

## Lo que nunca entra al repositorio

Datos del organizador, credenciales, el diccionario del dataset (trae credenciales), audio de
voluntarios, tokens de Meta o Twilio. Todo eso vive fuera de git y los secretos en Secret Manager.
