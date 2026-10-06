# Video pitch, 3 minutes maximum

Recording setup: one browser window with two tabs already open and warm, the banking demo (`/banca/`) and the expert console (`/operador/`, already logged in with the code). Open a third tab with the slides. Speak over the screen; do not read the slides. Target 2:50. If a step is slow, keep talking: do not wait in silence.

Before recording: send "Hola" once to Lía to wake the agent, then reset the demo state (command in `presidencia/reporte/demo/guion.md`).

| Time | On screen | Say |
|---|---|---|
| 0:00 to 0:20 | Slide 2 (problem) | "LATAM Bank is a fictional bank on the hackathon's synthetic data. In 686 thousand contacts, unrecognized card charges are the largest complaint: 18 percent, with a median first response of 37 hours. Fraud is contained in minutes, so we built one workflow: dispute intake, AI first." |
| 0:20 to 0:55 | `/banca/`: pick Colombia, enter, open a posted purchase, click "No reconozco este cargo", type "No reconozco este cargo, yo no compré ahí", approve on screen | "The customer starts from a transaction. The server pins it, not the model. The agent reads the data and proposes; nothing happens until I approve on screen. Our rule is simple: the model understands and writes, code decides. Policy, permissions and approvals live outside the prompt." |
| 0:55 to 1:20 | In the assistant type "Antes de reclamar, ¿el banco me abona algo mientras revisa?" then "¿Me pueden subir el cupo?" | "Policy questions are answered only from a retrieved source, with the rule cited. That retriever is a learned component: 90 percent against 52 for a BM25 baseline on held-out questions. Out of scope, like a credit limit, it abstains and never invents eligibility." |
| 1:20 to 1:55 | Click "Hablar con una persona". Switch to `/operador/`, open the handoff, take it, click "Sugerir borrador con IA", edit a word, send. Switch back: the message is in the same thread | "A human is always one click away. The expert receives a 19 field package: the request, verified facts with their source, actions done and not done, open questions and the rule that triggered the handoff. A copilot drafts the reply; the human edits and sends." |
| 1:55 to 2:15 | Back in `/banca/`, choose Brasil, open a charge, type "Não reconheço essa cobrança" | "The same flow in Portuguese. The data has no Brazilian accounts, so this is service in Portuguese for regional customers, and we say so." |
| 2:15 to 2:45 | Slide 5 (evaluation) | "We measured it on held-out cases, including expired sessions, unauthorized access, prompt injection and outages: zero unsafe outcomes in 96 runs, which bounds the risk at 4 percent, it does not prove zero. And the honest headline: a rules baseline follows policy as well as the agent. The agent adds language and conversation. The evaluation found four real defects; we fixed them in the tool layer and froze a new held-out set for a clean measurement." |
| 2:45 to 2:58 | Slide 6 (operation) | "It runs on Google Cloud with tracing, retention, alerts and Terraform. Data pipelines, three models with baselines, one of them a negative result we report. Everything, including what is still missing, is in the repository. Thank you." |

If the model is slow or fails live: click "Hablar con una persona" and continue with the console. The handoff does not depend on the model, and that is itself a demonstration of safe fallback.

Spanish is fine too if you prefer it: the content matters more than the language. Keep the same order and timings.
