# Tabla de cuotas (TEC-9.4, R-TEC-110)

La definición no trae valores: cada celda se lee en la consola durante F0 y ninguna cifra se supone. Las
filas están listas para llenar; el estado `[A]` significa pendiente de confirmar.

| Servicio | Límite que importa | Valor | Cómo se confirma | Cómo pedir aumento | Estado |
|---|---|---|---|---|---|
| Vertex AI (Gemini) | cuota compartida dinámica; responde 429 en congestión | pendiente | consola de cuotas | solicitud de aumento en la consola de cuotas | [A] |
| Speech-to-Text V2 | sesiones de streaming concurrentes por región y duración máxima | pendiente | página de cuotas de Speech-to-Text | solicitud de aumento en la consola de cuotas | [A] |
| Text-to-Speech | solicitudes por minuto | pendiente | consola de cuotas | solicitud de aumento en la consola de cuotas | [A] |
| Model Armor | solicitudes por minuto | pendiente | consola de cuotas | solicitud de aumento en la consola de cuotas | [A] |
| Cloud Run | instancias máximas por servicio; concurrencia por instancia | pendiente | documentación de límites de Cloud Run | solicitud de aumento en la consola de cuotas | [A] |
| Cloud SQL | `max_connections` por defecto de la instancia | pendiente | `SHOW max_connections;` | bandera de base de datos | [A] |
| Twilio | llamadas por segundo de la cuenta en pago por uso | pendiente | página de precios de Twilio | soporte de Twilio | [A] |

Nota: la cuenta de prueba puede tener cuotas más bajas que las de una cuenta completa; anotar aquí la
diferencia al leer cada valor.
