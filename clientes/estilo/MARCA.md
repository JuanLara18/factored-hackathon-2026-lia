# Marca de LATAM Bank

Guía corta de la identidad del banco ficticio. Todo lo que aparece aquí está aplicado en `tecnologia/web/sitio/`.

## Idea

Un banco que habla claro y que siempre deja una persona cerca. El símbolo lo dice: la L es el banco que sostiene y el punto es la persona.

**Lema:** Banca clara, con una persona cerca. En portugués: Banco claro, com uma pessoa por perto.

## Símbolo y logotipo

| Pieza | Dónde está | Uso |
|---|---|---|
| Símbolo | `assets/icon.svg` y en línea en la cabecera de cada página | cuadrado redondeado azul con una onda más clara, la L blanca y el punto menta |
| Logotipo | símbolo más "LATAM" en peso 800 y "Bank" en peso 500 y color de acento | cabeceras, pie, consola del experto |
| Tarjeta para compartir | `assets/og.png` (1200 por 630) | vista previa del enlace en chats y redes |

Reglas: el símbolo no se recolorea ni se gira; lleva siempre sus cuatro colores fijos, también en modo oscuro. Alrededor se deja un margen libre de al menos un cuarto de su ancho. El nombre se escribe LATAM Bank, con LATAM en mayúsculas.

## Color

| Nombre | Valor | Uso |
|---|---|---|
| Azul LATAM | `#0a5a7a` | color principal, botones, enlaces (`--acento`) |
| Azul claro | `#0f7ea8` | onda del símbolo, ilustraciones (`--acento-2`) |
| Marino | `#0b2a3f` | fondos oscuros de bandas y tarjetas (`--marino`) |
| Menta | `#5eead4` | el punto de la persona y detalles pequeños (`--menta`); nunca como color de texto sobre blanco |
| Ámbar | `#f59e0b` | avisos dentro de ilustraciones |

Los colores de estado (aprobado, rechazado, aviso) son los tokens de `site.css` y no forman parte de la marca.

## Tipografía

Títulos, logotipo y botones usan Plus Jakarta Sans (variable, pesos 200 a 800), servida desde el propio sitio en `assets/fuentes/jakarta-latin.woff2`; el texto corrido usa la fuente del sistema. La fuente es de Tokotype y se distribuye con la licencia SIL Open Font License 1.1. No se cargan fuentes de terceros en tiempo de ejecución porque la política de seguridad del sitio solo permite recursos propios.

## Ilustraciones

`assets/arte-*.svg`: objetos planos (teléfono, tarjetas, escudo, fichas) sobre un círculo tenue, con la paleta de arriba, sin texto y sin estilos internos. Una por página interior.

## Voz

La voz ya está definida en esta carpeta (`estilo.yaml` y los léxicos): frases cortas, trato de usted, vos o você según el cliente, sin promesas y sin signos de exclamación. La marca visual sigue la misma idea: poco texto, un paso a la vez y la persona siempre a la vista.
