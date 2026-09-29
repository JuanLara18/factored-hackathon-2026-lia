// Cliente mínimo AG-UI: lee el SSE, dibuja texto por frases, la ficha y la aprobación.
// No usa @ag-ui/client a propósito: el spike solo prueba el contrato de eventos (ver ADR 0010).
"use strict";

const FICHA_TOOL = {
  name: "FichaTransaccion",
  description: "Dibuja la ficha de una transacción",
  parameters: { type: "object", properties: { comercio: { type: "string" } } },
};
const threadId = crypto.randomUUID();
let historial = [];
const chat = document.getElementById("chat");
const metricas = document.getElementById("metricas");

function nodo(clase, texto) {
  const d = document.createElement("div");
  if (clase) d.className = clase;
  if (texto !== undefined) d.textContent = texto;
  chat.appendChild(d);
  return d;
}

async function correr(resume) {
  const t0 = performance.now();
  let primero = null;
  const cuerpo = {
    threadId, runId: crypto.randomUUID(), state: {}, messages: historial,
    tools: [FICHA_TOOL], context: [], forwardedProps: {},
  };
  if (resume) cuerpo.resume = resume;
  const resp = await fetch("/agui", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(cuerpo),
  });
  const lector = resp.body.getReader();
  const dec = new TextDecoder();
  let resto = "";
  const textos = {};
  const asistentes = [];
  const llamadas = {};
  let interrupciones = [];
  for (;;) {
    const { done, value } = await lector.read();
    if (done) break;
    resto += dec.decode(value, { stream: true });
    const bloques = resto.split("\n\n");
    resto = bloques.pop();
    for (const b of bloques) {
      const linea = b.split("\n").find((l) => l.startsWith("data: "));
      if (!linea) continue;
      const e = JSON.parse(linea.slice(6));
      if (e.type === "TEXT_MESSAGE_START") {
        textos[e.messageId] = nodo("texto");
        asistentes.push({ id: e.messageId, role: "assistant", content: "" });
      } else if (e.type === "TEXT_MESSAGE_CONTENT") {
        if (primero === null) primero = performance.now() - t0;
        textos[e.messageId].textContent += e.delta;
        asistentes.find((a) => a.id === e.messageId).content += e.delta;
      } else if (e.type === "TOOL_CALL_START") {
        llamadas[e.toolCallId] = { parent: e.parentMessageId, name: e.toolCallName, args: "" };
      } else if (e.type === "TOOL_CALL_ARGS") {
        llamadas[e.toolCallId].args += e.delta;
      } else if (e.type === "TOOL_CALL_RESULT") {
        llamadas[e.toolCallId].resultado = { id: e.messageId, content: e.content };
      } else if (e.type === "RUN_FINISHED") {
        interrupciones = (e.outcome && e.outcome.interrupts) || [];
      } else if (e.type === "RUN_ERROR") {
        nodo("error", "Error: " + e.message);
      }
    }
  }
  // reconstruir el historial como lo espera el servidor
  for (const a of asistentes) {
    historial.push(a);
    const propias = Object.entries(llamadas).filter(([, c]) => c.parent === a.id);
    if (propias.length) {
      a.toolCalls = propias.map(([id, c]) => ({ id, type: "function", function: { name: c.name, arguments: c.args } }));
    }
    for (const [id, c] of propias) {
      if (c.resultado) historial.push({ id: c.resultado.id, role: "tool", toolCallId: id, content: c.resultado.content });
    }
  }
  for (const [id, c] of Object.entries(llamadas)) {
    if (c.name === "FichaTransaccion") dibujarFicha(id, JSON.parse(c.args));
  }
  for (const i of interrupciones) dibujarAprobacion(i, llamadas[i.toolCallId]);
  const total = performance.now() - t0;
  metricas.textContent = `primer texto: ${primero === null ? "n/d" : primero.toFixed(0)} ms; turno completo: ${total.toFixed(0)} ms`;
}

function dibujarFicha(id, datos) {
  const d = nodo("ficha");
  d.textContent = `${datos.comercio}: ${datos.monto} ${datos.moneda} (${datos.estado})`;
  historial.push({ id: "tool-" + id, role: "tool", toolCallId: id, content: JSON.stringify("dibujada") });
}

function dibujarAprobacion(interrupcion, llamada) {
  const args = JSON.parse(llamada.args);
  const d = nodo("aprobacion");
  d.append(`Confirmas ${args.accion} por ${args.monto}? (nonce ${args.nonce}) `);
  for (const [etiqueta, aprobado] of [["Confirmo", true], ["No", false]]) {
    const b = document.createElement("button");
    b.textContent = etiqueta;
    b.addEventListener("click", () => {
      d.querySelectorAll("button").forEach((x) => (x.disabled = true));
      correr([{ interruptId: interrupcion.id, status: "resolved", payload: { approved: aprobado } }]);
    });
    d.appendChild(b);
  }
}

document.getElementById("iniciar").addEventListener("click", () => {
  historial = [{ id: crypto.randomUUID(), role: "user", content: "No reconozco un cargo" }];
  chat.textContent = "";
  correr(null);
});
