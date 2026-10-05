// Chat de disputas sobre AG-UI (TEC-3). Sin compilación ni scripts en línea.
// Los textos vienen de /api/textos (plantillas de clientes/); aquí solo se colocan y se enmascaran.
"use strict";

const FICHA_TOOL = {
  name: "FichaTransaccion",
  description: "Dibuja la ficha de una transacción del cliente",
  parameters: { type: "object", properties: { comercio: { type: "string" } } },
};
const CAMPOS_FICHA = ["comercio", "fecha", "monto", "moneda", "estado", "tarjeta_final"];
const RE_PERSONA = /\b(persona|humano|asesor)\b/i;
const AVISO_S = 60;

// Reloj inyectable para probar el vencimiento (R-CLI-46).
const ahora = () => (typeof window.relojChat === "function" ? window.relojChat() : Date.now());
const $ = (id) => document.getElementById(id);

const est = { sesion: null, conversacion: null, registro: "usted", textos: null, historial: [], ocupado: false };
let temporizador = null;

function etiqueta(clave) {
  return est.textos ? est.textos.etiquetas[clave] : "";
}

function anunciar(texto) {
  $("anuncio").textContent = "";
  window.setTimeout(() => { $("anuncio").textContent = texto; }, 50);
}

async function cargarTextos() {
  const r = await fetch("/api/textos?registro=" + encodeURIComponent(est.registro));
  est.textos = await r.json();
  const e = est.textos.etiquetas;
  $("aviso-ia").textContent = e.ia;
  $("persona").textContent = e.persona;
  $("lbl-cliente").textContent = e.cliente;
  $("lbl-registro").textContent = e.registro;
  $("iniciar").textContent = e.iniciar;
  $("inicio-titulo").textContent = e.demo;
  $("conversacion").setAttribute("aria-label", e.conversacion);
  document.querySelector(".salto").textContent = e.ir_mensaje;
  $("lbl-mensaje").textContent = e.escribir;
  $("mensaje").placeholder = e.escribir;
  $("enviar").textContent = e.enviar;
  $("ap-si").textContent = e.confirmo;
  $("ap-no").textContent = e.no;
  $("ap-renovar").textContent = e.renovar;
}

function burbuja(clase, texto) {
  const d = document.createElement("div");
  d.className = "msg " + clase;
  if (texto !== undefined) d.textContent = texto;
  $("chat").appendChild(d);
  d.scrollIntoView({ block: "end" });
  return d;
}

function cabeceras() {
  return { "Content-Type": "application/json", "X-Sesion": est.sesion || "", "X-Registro": est.registro };
}

async function iniciar() {
  const registro = document.querySelector('input[name="registro"]:checked').value;
  est.registro = registro;
  const r = await fetch("/api/sesion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cliente: Number($("cliente").value), registro }),
  });
  const s = await r.json();
  est.sesion = s.sesion;
  est.conversacion = s.conversacion;
  est.historial = [];
  $("chat").textContent = "";
  $("inicio").classList.add("oculto");
  $("conversacion").classList.remove("oculto");
  await cargarTextos();
  burbuja("asistente", est.textos.textos.aviso); // aviso de IA en el primer turno (R-CLI-13)
  $("mensaje").focus();
}

async function pedirPersona(textoUsuario) {
  if (!est.sesion) return;
  if (textoUsuario) burbuja("usuario", textoUsuario);
  const r = await fetch("/api/traspaso", { method: "POST", headers: cabeceras() });
  const d = await r.json();
  const texto = d.texto || etiqueta("sesion_vencida");
  burbuja("asistente", texto);
  anunciar(texto);
}

async function enviar(texto) {
  if (est.ocupado) return;
  if (RE_PERSONA.test(texto)) {
    await pedirPersona(texto);
    return;
  }
  burbuja("usuario", texto);
  est.historial.push({ id: crypto.randomUUID(), role: "user", content: texto });
  await correr(null);
}

// Lee el SSE de AG-UI y dibuja texto por frases, la ficha y la aprobación.
async function correr(resume) {
  est.ocupado = true;
  $("estado").textContent = est.textos.textos.procesando;
  const cuerpo = {
    threadId: est.conversacion, runId: crypto.randomUUID(), state: {}, messages: est.historial,
    tools: [FICHA_TOOL], context: [], forwardedProps: {},
  };
  if (resume) cuerpo.resume = resume;
  try {
    const resp = await fetch("/api/agui", {
      method: "POST", headers: { ...cabeceras(), Accept: "text/event-stream" }, body: JSON.stringify(cuerpo),
    });
    if (resp.status === 401) { burbuja("asistente error", etiqueta("sesion_vencida")); return; }
    if (resp.status === 409) {
      const t = etiqueta("vencida") + " " + est.textos.textos.sin_cambios;
      burbuja("asistente error", t);
      anunciar(t);
      return;
    }
    if (!resp.ok) throw new Error("http " + resp.status);
    await leer(resp);
  } catch (e) {
    burbuja("asistente error", est.textos.textos.falla);
  } finally {
    est.ocupado = false;
    $("estado").textContent = "";
  }
}

async function leer(resp) {
  const lector = resp.body.getReader();
  const dec = new TextDecoder();
  let resto = "";
  const nodos = {};
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
        asistentes.push({ id: e.messageId, role: "assistant", content: "" });
      } else if (e.type === "TEXT_MESSAGE_CONTENT") {
        if (!nodos[e.messageId]) nodos[e.messageId] = burbuja("asistente");
        nodos[e.messageId].textContent += e.delta;
        asistentes.find((a) => a.id === e.messageId).content += e.delta;
      } else if (e.type === "TOOL_CALL_START") {
        llamadas[e.toolCallId] = { parent: e.parentMessageId, name: e.toolCallName, args: "" };
      } else if (e.type === "TOOL_CALL_ARGS") {
        llamadas[e.toolCallId].args += e.delta;
      } else if (e.type === "TOOL_CALL_RESULT") {
        if (llamadas[e.toolCallId]) llamadas[e.toolCallId].resultado = { id: e.messageId, content: e.content };
        else est.historial.push({ id: e.messageId, role: "tool", toolCallId: e.toolCallId, content: e.content }); // llamada de una corrida anterior (reanudación)
      } else if (e.type === "RUN_FINISHED") {
        interrupciones = (e.outcome && e.outcome.interrupts) || [];
      } else if (e.type === "RUN_ERROR") {
        // El servidor ya dijo la falla con la plantilla en este turno: no se repite en otra burbuja.
        if (!Object.keys(nodos).length) burbuja("asistente error", est.textos.textos.falla);
      }
    }
  }
  // El historial vuelve al servidor como lo espera el adaptador: asistente, sus llamadas y sus resultados.
  for (const a of asistentes) {
    est.historial.push(a);
    const propias = Object.entries(llamadas).filter(([, c]) => c.parent === a.id);
    if (propias.length) {
      a.toolCalls = propias.map(([id, c]) => ({ id, type: "function", function: { name: c.name, arguments: c.args } }));
    }
    for (const [id, c] of propias) {
      if (c.resultado) est.historial.push({ id: c.resultado.id, role: "tool", toolCallId: id, content: c.resultado.content });
    }
  }
  for (const [id, c] of Object.entries(llamadas)) {
    if (c.name === "FichaTransaccion") dibujarFicha(id, JSON.parse(c.args));
  }
  for (const i of interrupciones) dibujarAprobacion(i);
}

// Componente de transacción: solo campos conocidos, con la tarjeta siempre enmascarada (R-CLI-30).
function dibujarFicha(id, datos) {
  est.historial.push({ id: "tool-" + id, role: "tool", toolCallId: id, content: JSON.stringify("dibujada") });
  const caja = document.createElement("section");
  caja.className = "ficha";
  const h = document.createElement("h3");
  h.textContent = String(datos.comercio || "");
  caja.appendChild(h);
  const dl = document.createElement("dl");
  const filas = [
    [etiqueta("monto") || "", `${datos.monto || ""} ${datos.moneda || ""}`.trim()],
    ["", String(datos.fecha || "")],
    ["", String(datos.estado || "")],
    [etiqueta("tarjeta"), "···· " + String(datos.tarjeta_final || "").replace(/\D/g, "").slice(-4)],
  ];
  for (const [k, v] of filas) {
    if (!v) continue;
    if (k) { const dt = document.createElement("dt"); dt.textContent = k; dl.appendChild(dt); }
    const dd = document.createElement("dd");
    if (!k) dd.style.gridColumn = "1 / -1";
    dd.textContent = v;
    dl.appendChild(dd);
  }
  caja.appendChild(dl);
  const acciones = document.createElement("div");
  acciones.className = "acciones";
  for (const clave of ["reconozco", "no_reconozco"]) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = etiqueta(clave);
    b.addEventListener("click", () => {
      acciones.querySelectorAll("button").forEach((x) => { x.disabled = true; });
      enviar(etiqueta(clave));
    });
    acciones.appendChild(b);
  }
  caja.appendChild(acciones);
  $("chat").appendChild(caja);
  caja.scrollIntoView({ block: "end" });
}

// Diálogo de aprobación con vencimiento accesible (R-CLI-44, R-CLI-46).
function dibujarAprobacion(interrupcion) {
  const dlg = $("aprobacion");
  const expira = Date.parse(interrupcion.expiresAt || "") || ahora() + 300000;
  let avisado = false;
  $("ap-texto").textContent = interrupcion.message || "";
  $("ap-si").disabled = false;
  $("ap-no").disabled = false;
  $("ap-renovar").classList.add("oculto");
  $("ap-si").classList.remove("oculto");
  $("ap-no").classList.remove("oculto");

  const pintar = () => {
    const resta = Math.max(0, Math.round((expira - ahora()) / 1000));
    const mm = String(Math.floor(resta / 60)).padStart(1, "0");
    const ss = String(resta % 60).padStart(2, "0");
    $("ap-vence").textContent = `${etiqueta("vence")} ${mm}:${ss}`;
    if (resta <= AVISO_S && !avisado) { avisado = true; anunciar(etiqueta("vence_pronto")); }
    if (resta === 0) vencer();
  };
  const cerrar = () => { window.clearInterval(temporizador); if (dlg.open) dlg.close(); };
  const vencer = () => {
    window.clearInterval(temporizador);
    $("ap-si").disabled = true;
    $("ap-no").disabled = true;
    $("ap-si").classList.add("oculto");
    $("ap-no").classList.add("oculto");
    $("ap-vence").textContent = etiqueta("vencida");
    $("ap-renovar").classList.remove("oculto");
    $("ap-renovar").focus();
    anunciar(etiqueta("vencida"));
    // La llamada quedó sin resultado: se cierra en el historial para que el modelo pueda volver a proponerla.
    est.historial.push({ id: crypto.randomUUID(), role: "tool", toolCallId: interrupcion.toolCallId, content: "vencida" });
  };
  const decidir = (aprobado) => {
    if (ahora() >= expira) return;
    cerrar();
    correr([{ interruptId: interrupcion.id, status: "resolved", payload: { approved: aprobado } }]);
  };
  $("ap-si").onclick = () => decidir(true);
  $("ap-no").onclick = () => decidir(false);
  $("ap-renovar").onclick = () => { cerrar(); enviar(etiqueta("no_reconozco")); };
  dlg.oncancel = (ev) => { ev.preventDefault(); }; // Escape no equivale a decidir
  window.clearInterval(temporizador);
  pintar();
  temporizador = window.setInterval(pintar, 1000);
  if (!dlg.open) dlg.showModal();
  $("ap-si").focus();
}

async function arrancar() {
  await cargarTextos();
  const e = await (await fetch("/api/estado")).json();
  const sel = $("cliente");
  e.clientes.forEach((nombre, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = nombre;
    sel.appendChild(o);
  });
  $("origen").textContent = `${e.origen} · ${e.modelo}`;
  $("iniciar").addEventListener("click", iniciar);
  $("persona").addEventListener("click", () => pedirPersona(null));
  $("formulario").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const t = $("mensaje").value.trim();
    if (!t) return;
    $("mensaje").value = "";
    enviar(t);
  });
  document.querySelectorAll('input[name="registro"]').forEach((r) =>
    r.addEventListener("change", async () => {
      est.registro = r.value;
      await cargarTextos();
    }));
}

arrancar();
