// Asistente flotante de la banca en línea. Reutilizable en cualquier página de banca (requiere banca.js).
// Misma lógica que chat.js: AG-UI con texto por frases, FichaTransaccion, aprobación con vencimiento accesible,
// aviso de IA fijo y "Hablar con una persona" siempre visible. Tras un traspaso muestra los mensajes de la persona.
"use strict";

(function () {
  const B = window.Banca;
  if (!B) return;
  const { h } = B;
  const FICHA_TOOL = {
    name: "FichaTransaccion",
    description: "Dibuja la ficha de una transacción del cliente",
    parameters: { type: "object", properties: { comercio: { type: "string" } } },
  };
  const RE_PERSONA = /\b(persona|humano|asesor)\b/i;
  const AVISO_S = 60;
  const SONDEO_MS = 4000;
  const ahora = () => (typeof window.relojChat === "function" ? window.relojChat() : Date.now());

  // Textos de respaldo por si /api/textos no responde (plantillas de clientes/, registro usted).
  const RESPALDO = {
    etiquetas: { ia: "Asistente de inteligencia artificial", persona: "Hablar con una persona", escribir: "Escriba su mensaje", enviar: "Enviar",
      confirmo: "Confirmo", no: "No, gracias", renovar: "Renovar la confirmación", vence: "Vence en", vence_pronto: "La confirmación vence en un minuto.",
      vencida: "La confirmación venció.", reconozco: "Reconozco este cargo", no_reconozco: "No reconozco este cargo", tarjeta: "Tarjeta", monto: "Monto",
      sesion_vencida: "Su sesión venció. Vuelva a ingresar para continuar." },
    textos: { aviso: "Hola. Soy el asistente virtual de LATAM Bank, un sistema de inteligencia artificial. Si prefiere hablar con una persona, puede pedirlo en cualquier momento.",
      procesando: "El asistente está escribiendo", falla: "No pude completar la solicitud. Puede intentarlo de nuevo o hablar con una persona.",
      sin_cambios: "No se hizo ningún cambio." },
  };

  const est = { conversacion: null, historial: [], ocupado: false, textos: RESPALDO, traspaso: false, ultimoMensaje: null, sondeo: null, abierto: false };
  const el = {};
  let reloj = null;

  const et = (k) => est.textos.etiquetas[k] || RESPALDO.etiquetas[k] || "";
  const tx = (k) => est.textos.textos[k] || RESPALDO.textos[k] || "";

  function construir() {
    el.lanzador = h("button", { type: "button", id: "asistente-lanzador", clase: "bw-lanzador", "aria-expanded": "false", "aria-controls": "asistente-panel", texto: "Asistente" });
    el.ia = h("p", { id: "asistente-ia", clase: "bw-ia", role: "note", texto: RESPALDO.etiquetas.ia });
    el.persona = h("button", { type: "button", clase: "bw-persona", texto: RESPALDO.etiquetas.persona });
    el.cerrar = h("button", { type: "button", clase: "bw-cerrar", "aria-label": "Cerrar el asistente", texto: "Cerrar" });
    el.titulo = h("h2", { id: "asistente-titulo", tabindex: "-1", texto: "Asistente de LATAM Bank" });
    el.log = h("div", { id: "asistente-log", clase: "bw-log", role: "log", "aria-live": "polite", "aria-relevant": "additions", tabindex: "0", "aria-label": "Conversación" });
    el.estado = h("p", { clase: "nota bw-estado", role: "status" });
    el.entrada = h("input", { id: "asistente-mensaje", type: "text", maxlength: "500", required: true, autocomplete: "off" });
    el.etiquetaEntrada = h("label", { for: "asistente-mensaje", clase: "visualmente-oculto", texto: RESPALDO.etiquetas.escribir });
    el.enviar = h("button", { type: "submit", clase: "primario", texto: RESPALDO.etiquetas.enviar });
    el.form = h("form", { clase: "bw-form" }, el.etiquetaEntrada, el.entrada, el.enviar);
    el.panel = h("section", { id: "asistente-panel", clase: "bw-panel oculto", role: "dialog", "aria-modal": "false", "aria-labelledby": "asistente-titulo" },
      h("div", { clase: "bw-cab" }, el.titulo, el.cerrar), h("div", { clase: "bw-sub" }, el.ia, el.persona),
      el.log, el.estado, el.form);
    el.anuncio = h("p", { id: "asistente-anuncio", clase: "visualmente-oculto", role: "status", "aria-live": "assertive" });
    el.apTexto = h("p", { id: "ap-texto" });
    el.apVence = h("p", { id: "ap-vence", clase: "nota" });
    el.apSi = h("button", { type: "button", clase: "primario" });
    el.apNo = h("button", { type: "button" });
    el.apRenovar = h("button", { type: "button", clase: "oculto" });
    el.dialogo = h("dialog", { id: "aprobacion", "aria-labelledby": "ap-texto", "aria-describedby": "ap-vence" },
      el.apTexto, el.apVence, h("div", { clase: "acciones" }, el.apSi, el.apNo, el.apRenovar));
    document.body.append(el.lanzador, el.panel, el.dialogo, el.anuncio);

    el.lanzador.addEventListener("click", () => (est.abierto ? cerrar() : abrir({})));
    el.cerrar.addEventListener("click", cerrar);
    el.panel.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && !el.dialogo.open) cerrar(); });
    el.persona.addEventListener("click", () => pedirPersona(null));
    el.form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const t = el.entrada.value.trim();
      if (!t) return;
      el.entrada.value = "";
      enviar(t);
    });
    aplicarTextos();
  }

  function anunciar(texto) {
    el.anuncio.textContent = "";
    window.setTimeout(() => { el.anuncio.textContent = texto; }, 50);
  }

  function aplicarTextos() {
    el.ia.textContent = et("ia");
    el.persona.textContent = et("persona");
    el.etiquetaEntrada.textContent = et("escribir");
    el.entrada.placeholder = et("escribir");
    el.enviar.textContent = et("enviar");
    el.apSi.textContent = et("confirmo");
    el.apNo.textContent = et("no");
    el.apRenovar.textContent = et("renovar");
  }

  async function cargarTextos() {
    try {
      const d = await B.llamar("/api/textos?registro=usted");
      if (d && d.etiquetas && d.textos) est.textos = d;
    } catch (e) { est.textos = RESPALDO; }
    aplicarTextos();
  }

  function burbuja(clase, texto) {
    const d = h("div", { clase: "bw-msg " + clase });
    if (texto !== undefined) d.textContent = texto;
    el.log.append(d);
    d.scrollIntoView({ block: "end" });
    return d;
  }
  function etiquetaAutor(autor) { return h("span", { clase: "bw-autor", texto: autor }); }

  // Apertura ---------------------------------------------------------------------------------------------------

  async function abrir(op) {
    const o = op || {};
    est.abierto = true;
    el.panel.classList.remove("oculto");
    el.lanzador.setAttribute("aria-expanded", "true");
    if (o.conversacion && o.conversacion !== est.conversacion) await empezar(o.conversacion, o.contexto);
    else if (!est.conversacion && !o.conversacion) mostrarSinContexto();
    el.titulo.focus();
  }
  function cerrar() {
    est.abierto = false;
    el.panel.classList.add("oculto");
    el.lanzador.setAttribute("aria-expanded", "false");
    el.lanzador.focus();
  }

  function mostrarSinContexto() {
    if (el.log.childElementCount) return;
    cargarTextos().then(() => {
      burbuja("asistente", tx("aviso"));
      burbuja("asistente", "Para revisar un cargo, ábralo desde sus movimientos y elija No reconozco este cargo. También puede pedir hablar con una persona.");
    });
  }

  async function empezar(conversacion, contexto) {
    detenerSondeo();
    est.conversacion = conversacion;
    est.historial = [];
    est.traspaso = false;
    est.ultimoMensaje = null;
    el.log.textContent = "";
    await cargarTextos();
    burbuja("asistente", tx("aviso")); // aviso de IA en el primer turno (R-CLI-13)
    // El servidor ya fijó la transacción; el primer mensaje del cliente arranca la revisión.
    await enviar(et("no_reconozco"));
  }

  // Traspaso a una persona ------------------------------------------------------------------------------------

  async function pedirPersona(textoUsuario) {
    if (est.traspaso) { el.entrada.focus(); return; }
    if (textoUsuario) burbuja("usuario", textoUsuario);
    let texto;
    try {
      const r = await B.llamar("/api/traspaso", { metodo: "POST", cuerpo: { conversacion: est.conversacion } });
      texto = r.texto || "Ya avisamos a una persona. Le responderá en esta misma conversación.";
      est.traspaso = true;
    } catch (e) {
      texto = e.status === 401 ? et("sesion_vencida") : "No pudimos avisar a una persona en este momento. Puede intentarlo de nuevo.";
    }
    burbuja("asistente", texto);
    anunciar(texto);
    if (est.traspaso) { el.estado.textContent = "Esperando a una persona"; iniciarSondeo(); }
  }

  function iniciarSondeo() {
    detenerSondeo();
    est.sondeo = window.setInterval(sondear, SONDEO_MS);
    sondear();
  }
  function detenerSondeo() { if (est.sondeo) window.clearInterval(est.sondeo); est.sondeo = null; }

  async function sondear() {
    if (!est.conversacion) return;
    try {
      const q = est.ultimoMensaje ? "?desde=" + encodeURIComponent(est.ultimoMensaje) : "";
      const lista = await B.llamar(`/api/banca/conversaciones/${encodeURIComponent(est.conversacion)}/mensajes${q}`);
      for (const m of lista) {
        est.ultimoMensaje = m.id;
        if (m.autor !== "persona") continue;
        const b = burbuja("persona");
        b.append(etiquetaAutor("Persona de LATAM Bank"), h("span", { texto: m.texto }));
        anunciar("Nueva respuesta de una persona de LATAM Bank");
        el.estado.textContent = "";
      }
    } catch (e) {
      if (e.status === 404) { detenerSondeo(); el.estado.textContent = "Por ahora no podemos mostrar las respuestas de la persona. Vuelva a abrir el asistente en unos minutos."; }
    }
  }

  async function responderAPersona(texto) {
    const b = burbuja("usuario", texto);
    try {
      await B.llamar(`/api/banca/conversaciones/${encodeURIComponent(est.conversacion)}/mensajes`, { metodo: "POST", cuerpo: { texto } });
    } catch (e) {
      b.classList.add("error");
      burbuja("asistente error", e.status === 409 || e.status === 404 ? "Todavía no hay una persona en este caso. Su mensaje no se envió." : "No pudimos enviar su mensaje. Inténtelo de nuevo.");
    }
  }

  // Turnos con el asistente -----------------------------------------------------------------------------------

  async function enviar(texto) {
    if (est.ocupado) return;
    if (est.traspaso) { await responderAPersona(texto); return; }
    if (RE_PERSONA.test(texto)) { await pedirPersona(texto); return; }
    if (!est.conversacion) { burbuja("usuario", texto); burbuja("asistente", "Para hablar con el asistente, abra primero un movimiento y elija No reconozco este cargo."); return; }
    burbuja("usuario", texto);
    est.historial.push({ id: crypto.randomUUID(), role: "user", content: texto });
    await correr(null);
  }

  async function correr(resume) {
    est.ocupado = true;
    el.estado.textContent = tx("procesando");
    const s = B.sesion();
    const cuerpo = {
      threadId: est.conversacion, runId: crypto.randomUUID(), state: {}, messages: est.historial,
      tools: [FICHA_TOOL], context: [], forwardedProps: {},
    };
    if (resume) cuerpo.resume = resume;
    try {
      let eventos;
      if (B.MOCK) {
        eventos = eventosLocales(resume);
      } else {
        const resp = await fetch(B.BASE + "/api/agui", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Sesion": (s && s.sesion) || "", "X-Registro": "usted", Accept: "text/event-stream" },
          body: JSON.stringify(cuerpo),
        });
        if (resp.status === 401) { burbuja("asistente error", et("sesion_vencida")); return; }
        if (resp.status === 409) {
          const t = et("vencida") + " " + tx("sin_cambios");
          burbuja("asistente error", t);
          anunciar(t);
          return;
        }
        if (!resp.ok) throw new Error("http " + resp.status);
        eventos = leerSse(resp);
      }
      await procesar(eventos);
    } catch (e) {
      burbuja("asistente error", tx("falla"));
    } finally {
      est.ocupado = false;
      el.estado.textContent = est.traspaso ? "Esperando a una persona" : "";
    }
  }

  async function* leerSse(resp) {
    const lector = resp.body.getReader();
    const dec = new TextDecoder();
    let resto = "";
    for (;;) {
      const { done, value } = await lector.read();
      if (done) break;
      resto += dec.decode(value, { stream: true });
      const bloques = resto.split("\n\n");
      resto = bloques.pop();
      for (const b of bloques) {
        const linea = b.split("\n").find((l) => l.startsWith("data: "));
        if (linea) yield JSON.parse(linea.slice(6));
      }
    }
  }

  async function procesar(eventos) {
    const nodos = {};
    const asistentes = [];
    const llamadas = {};
    let interrupciones = [];
    for await (const e of eventos) {
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
        else est.historial.push({ id: e.messageId, role: "tool", toolCallId: e.toolCallId, content: e.content });
      } else if (e.type === "RUN_FINISHED") {
        interrupciones = (e.outcome && e.outcome.interrupts) || [];
      } else if (e.type === "RUN_ERROR") {
        burbuja("asistente error", tx("falla"));
      }
    }
    for (const a of asistentes) {
      est.historial.push(a);
      const propias = Object.entries(llamadas).filter(([, c]) => c.parent === a.id);
      if (propias.length) a.toolCalls = propias.map(([id, c]) => ({ id, type: "function", function: { name: c.name, arguments: c.args } }));
      for (const [id, c] of propias) {
        if (c.resultado) est.historial.push({ id: c.resultado.id, role: "tool", toolCallId: id, content: c.resultado.content });
      }
    }
    for (const [id, c] of Object.entries(llamadas)) if (c.name === "FichaTransaccion") dibujarFicha(id, JSON.parse(c.args));
    for (const i of interrupciones) dibujarAprobacion(i);
  }

  // Componente de transacción: solo campos conocidos, tarjeta siempre enmascarada (R-CLI-30).
  function dibujarFicha(id, datos) {
    est.historial.push({ id: "tool-" + id, role: "tool", toolCallId: id, content: JSON.stringify("dibujada") });
    const filas = [];
    const monto = `${datos.monto || ""} ${datos.moneda || ""}`.trim();
    if (monto) filas.push(h("dt", { texto: et("monto") }), h("dd", { clase: "bn-num", texto: monto }));
    if (datos.fecha) filas.push(h("dt", { texto: "Fecha" }), h("dd", { texto: String(datos.fecha) }));
    if (datos.estado) filas.push(h("dt", { texto: "Estado" }), h("dd", { texto: String(datos.estado) }));
    if (datos.tarjeta_final) filas.push(h("dt", { texto: et("tarjeta") }), h("dd", { clase: "bn-num", texto: "···· " + String(datos.tarjeta_final).replace(/\D/g, "").slice(-4) }));
    const acciones = h("div", { clase: "acciones" });
    for (const clave of ["reconozco", "no_reconozco"]) {
      const b = h("button", { type: "button", texto: et(clave) });
      b.addEventListener("click", () => {
        acciones.querySelectorAll("button").forEach((x) => { x.disabled = true; });
        enviar(et(clave));
      });
      acciones.append(b);
    }
    const caja = h("section", { clase: "bw-ficha", "aria-label": "Transacción" }, h("h3", { texto: String(datos.comercio || "") }), h("dl", {}, filas), acciones);
    el.log.append(caja);
    caja.scrollIntoView({ block: "end" });
  }

  // Aprobación con vencimiento accesible (R-CLI-44, R-CLI-46).
  function dibujarAprobacion(interrupcion) {
    const dlg = el.dialogo;
    const expira = Date.parse(interrupcion.expiresAt || "") || ahora() + 300000;
    let avisado = false;
    el.apTexto.textContent = interrupcion.message || "";
    el.apSi.disabled = false;
    el.apNo.disabled = false;
    el.apRenovar.classList.add("oculto");
    el.apSi.classList.remove("oculto");
    el.apNo.classList.remove("oculto");
    const pintar = () => {
      const resta = Math.max(0, Math.round((expira - ahora()) / 1000));
      el.apVence.textContent = `${et("vence")} ${Math.floor(resta / 60)}:${String(resta % 60).padStart(2, "0")}`;
      if (resta <= AVISO_S && !avisado) { avisado = true; anunciar(et("vence_pronto")); }
      if (resta === 0) vencer();
    };
    const cerrarDlg = () => { window.clearInterval(reloj); if (dlg.open) dlg.close(); };
    const vencer = () => {
      window.clearInterval(reloj);
      el.apSi.disabled = true; el.apNo.disabled = true;
      el.apSi.classList.add("oculto"); el.apNo.classList.add("oculto");
      el.apVence.textContent = et("vencida");
      el.apRenovar.classList.remove("oculto");
      el.apRenovar.focus();
      anunciar(et("vencida"));
      est.historial.push({ id: crypto.randomUUID(), role: "tool", toolCallId: interrupcion.toolCallId, content: "vencida" });
    };
    const decidir = (aprobado) => {
      if (ahora() >= expira) return;
      cerrarDlg();
      correr([{ interruptId: interrupcion.id, status: "resolved", payload: { approved: aprobado } }]);
    };
    el.apSi.onclick = () => decidir(true);
    el.apNo.onclick = () => decidir(false);
    el.apRenovar.onclick = () => { cerrarDlg(); enviar(et("no_reconozco")); };
    dlg.oncancel = (ev) => { ev.preventDefault(); }; // Escape no equivale a decidir
    window.clearInterval(reloj);
    pintar();
    reloj = window.setInterval(pintar, 1000);
    if (!dlg.open) dlg.showModal();
    el.apSi.focus();
  }

  // Modo local: guion de un turno de asistente con ficha y aprobación --------------------------------------------

  async function* eventosLocales(resume) {
    const pausaMs = (ms) => new Promise((r) => window.setTimeout(r, ms));
    const contexto = B.estadoLocal().contexto || {};
    const id = "m-" + crypto.randomUUID();
    const texto = async function* (frases) {
      yield { type: "TEXT_MESSAGE_START", messageId: id };
      for (const f of frases) { await pausaMs(350); yield { type: "TEXT_MESSAGE_CONTENT", messageId: id, delta: f }; }
    };
    if (resume) {
      const ok = resume[0].payload.approved;
      yield* texto(ok ? ["Listo. Bloqueé la tarjeta y abrí su reclamo. ", "Le devolvimos el monto de forma provisional y le avisaremos cuando haya respuesta."] : ["Entendido. No hice ningún cambio. ", "Si quiere, puede hablar con una persona."]);
      yield { type: "RUN_FINISHED" };
      return;
    }
    const usuarios = est.historial.filter((m) => m.role === "user").length;
    if (usuarios <= 1) {
      yield* texto(["Revisé sus movimientos recientes. ", "Encontré este cargo. ¿Es este?"]);
      yield { type: "TOOL_CALL_START", toolCallId: "tc1", toolCallName: "FichaTransaccion", parentMessageId: id };
      yield { type: "TOOL_CALL_ARGS", toolCallId: "tc1", delta: JSON.stringify({ comercio: contexto.descripcion || "Comercio", fecha: contexto.fecha, monto: contexto.monto, moneda: contexto.moneda, estado: contexto.estado, tarjeta_final: contexto.tarjeta_final }) };
      yield { type: "RUN_FINISHED" };
      return;
    }
    yield* texto(["Para proteger su cuenta le propongo bloquear la tarjeta y abrir el reclamo. ", "Necesito su confirmación."]);
    yield { type: "RUN_FINISHED", outcome: { interrupts: [{ id: "i1", toolCallId: "tc2", expiresAt: new Date(ahora() + 300000).toISOString(),
      message: `Voy a bloquear la tarjeta terminada en ${String(contexto.tarjeta_final || "").slice(-4)} y a reclamar ${contexto.monto || ""} ${contexto.moneda || ""} en ${contexto.descripcion || "el comercio"}. Podrá pedir una tarjeta nueva. Si elige No, gracias, no se hará ningún cambio.` }] } };
  }

  if (!B.sesion()) return; // sin ingreso no hay asistente
  construir();
  window.BancaWidget = { abrir, cerrar };
  const q = new URLSearchParams(window.location.search);
  if (B.MOCK && q.get("asistente")) {
    B.llamar("/api/banca/movimientos/t1/reclamar", { metodo: "POST", cuerpo: {} }).then((r) => B.fixture("movimientos").then((d) => abrir({ conversacion: r.conversacion, contexto: d.movimientos[0] })));
  }
})();
