# Guía de estilo de LATAM Bank (CLI-1.2)

Versión 1. Fuente: [definición de Clientes](../definicion.md), secciones 2.3.1 a 2.3.8. Lo que una máquina puede
verificar vive en [estilo.yaml](estilo.yaml): el linter de contenido (`uv run python -m latam_clientes.linter`,
también en pytest) y la biblioteca de prompts de IA leen ese archivo. Esta guía explica el porqué.
Pendiente: visto bueno de Gobierno (S-CLI-02).

## Voz de marca

LATAM Bank habla como una persona experta y serena del equipo de fraude: clara, cálida sin exageración, concreta
y honesta sobre lo que no sabe.

- **Claro:** una idea por frase; 20 palabras o menos en chat y WhatsApp, 15 o menos en voz. Sin jerga
  ("contracargo", "chargeback").
- **Cálido:** un solo reconocimiento al inicio; otro solo si hay un hecho nuevo.
- **Sereno:** sin signos de exclamación, sin mayúsculas de énfasis, sin emojis en ningún canal.
- **Concreto:** montos, fechas y plazos salen de la base y de `policy/v1`, nunca de una estimación.
- **Honesto:** se dice lo que no se hizo y lo que no se sabe.
- **Respetuoso:** tratamiento del país de la cuenta; sin diminutivos ni apodos; sin el nombre del cliente en la IA.

## Registro y vocabulario por país

El país sale de la sesión autenticada, nunca del acento. Antes de autenticar se usa usted neutro.

| País | Tratamiento | El cargo se llama | Documento mensual |
|---|---|---|---|
| México | usted | cargo | estado de cuenta |
| Colombia | usted | cobro | extracto |
| Argentina | vos | consumo | resumen |
| Neutro | usted | cargo | estado de cuenta |

Las plantillas no escriben esos términos: usan `{cargo}` y `{documento_mensual}`, y el motor los rellena según el
país. El linter rechaza un término de país escrito a mano.

- **Usted:** "¿Lo confirma?", "marque uno", "su tarjeta". Nunca "tú" ni "tu".
- **Vos:** "confirmás", "podés", "marcá", "decí", "tu tarjeta". Nunca mezclar "tú" y "vos".
- **Portugués (voce):** la matriz lo reserva y queda pendiente hasta CLI-1.5; sin formas de Portugal.
- Las etiquetas de botón van en infinitivo para servir a todos los registros.

## Cifras, plazos y montos

Ninguna plantilla lleva una cifra, una fecha, un símbolo ni un código de moneda escritos. Todo entra por un
marcador `{nombre}` del catálogo de `estilo.yaml`. Un plazo exige cinco datos: norma, número, unidad, evento y
fecha; un monto exige `{monto}` y `{moneda}` en chat y WhatsApp, y `{monto_en_palabras}` en voz.

## Frases prohibidas y obligatorias

La lista completa, con su motivo y su alternativa, está en `frases_prohibidas` de `estilo.yaml`; es la única del
repositorio (los prompts de IA la reutilizan con `frases_prohibidas(estilo, "prompt")`). En resumen: nada de
promesas de devolución, de "listo" sin verificar, de diagnósticos ("esto es fraude"), de acusaciones al cliente, de
plazos sin regla, de certezas indebidas, de "caso cerrado" con el reclamo abierto, de pedir la clave o el código,
de decir que es una persona, de revelar reglas internas ni de normas de otro país.

Obligatorias: aviso de IA y opción de persona al abrir; "no hicimos ningún cambio en su cuenta" cuando no hubo
acción (falla segura, negado, cierre sin cambios); la frase de seguridad (el banco nunca pide la clave ni que se
mueva dinero; dónde se digita el código de verificación).

## Por canal

| Canal | Frase | Largo | No se dice |
|---|---|---|---|
| Chat | 20 palabras | 420 caracteres | "marque", "diga" (hay botones) |
| WhatsApp | 20 palabras | 480 caracteres | "botón", "toque" (no hay botones) |
| Voz | 15 palabras | 320 caracteres | "botón", "pantalla", "enlace", "escriba" |

## Cómo se cambia

Se edita `estilo.yaml` o las plantillas y se corre el linter. Una frase prohibida nueva sin `alcance: [prompt]` no
afecta a la biblioteca de IA; con él, sus pruebas la exigen también en los prompts.
