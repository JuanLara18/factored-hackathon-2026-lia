// Consola del experto (CLI-4.4 a CLI-4.6). Sin compilación ni scripts en línea.
// API: window.LATAM_API_BASE + /api/operador/* (tecnologia/web/API_BANCA.md). Con ?demo=local usa operador/fixtures/.
// Todo el texto se coloca con textContent: nada de lo que llega de la red se interpreta como HTML.
"use strict";

const DEMO = new URLSearchParams(window.location.search).get("demo") === "local";
const BASE = String(window.LATAM_API_BASE || "").replace(/\/+$/, "");
const SLA_S = { P1: 60, P2: 300, P3: 1200, P4: 86400 };
const NOMBRE_PAIS = { MX: "México", CO: "Colombia", AR: "Argentina" };
const IDIOMA = { es: "Español", pt: "Portugués" };
const CANAL = { chat: "Chat", voz: "Voz", whatsapp: "WhatsApp simulado" };
const AREA = { "back office": "Back office", cliente: "Cliente", red: "Red" };
const MOTIVOS_VERDADEROS = [
  ["fraude", "Fraude"], ["error_procesamiento", "Error de procesamiento"], ["disputa_comercial", "Disputa comercial"],
  ["es_mia", "Es mía pero no la reconocía"], ["no_es_disputa", "No es disputa"], ["fuera_de_alcance", "Fuera de alcance"],
];
const RUTAS = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"];
const RESULTADOS = [["resuelto", "Resuelto"], ["radicado", "Reclamo radicado"], ["escalado", "Pasado a especialista o back office"], ["sin_accion", "Sin acción necesaria"]];
const RE_PII = /\b\d{13,19}\b/;

const $ = (id) => document.getElementById(id);
const est = { sesion: null, cola: [], actual: null, paquete: null, ultimoMensaje: 0, cargaGen: 0, mock: null };
let relojes = null;
let sondeoCola = null;
let sondeoHilo = null;

// ---------- utilidades ----------
function el(tag, clase, texto, attrs) {
  const n = document.createElement(tag);
  if (clase) n.className = clase;
  if (texto !== undefined && texto !== null) n.textContent = texto;
  if (attrs) for (const k of Object.keys(attrs)) n.setAttribute(k, attrs[k]);
  return n;
}
function anunciar(t) {
  $("op-anuncio").textContent = "";
  window.setTimeout(() => { $("op-anuncio").textContent = t; }, 50);
}
// Enmascara cualquier número largo que se cuele: la vista nunca muestra una tarjeta completa.
function limpio(t) {
  return String(t == null ? "" : t).replace(/\b\d{13,19}\b/g, (m) => "•••• " + m.slice(-4));
}
function fmtDur(s) {
  const neg = s < 0;
  let a = Math.abs(Math.round(s));
  const d = Math.floor(a / 86400); a -= d * 86400;
  const h = Math.floor(a / 3600); a -= h * 3600;
  const m = Math.floor(a / 60); const seg = a - m * 60;
  const p2 = (x) => String(x).padStart(2, "0");
  let t;
  if (d > 0) t = d + " d " + p2(h) + " h";
  else if (h > 0) t = h + ":" + p2(m) + ":" + p2(seg);
  else t = m + ":" + p2(seg);
  return (neg ? "-" : "") + t;
}
const ahoraS = () => Date.now() / 1000;
const instante = (n, campoIso, campoRel) => {
  if (n[campoIso]) return Date.parse(n[campoIso]) / 1000;
  if (typeof n[campoRel] === "number") return ahoraS() - n[campoRel];
  return ahoraS();
};

// ---------- API y modo local ----------
class ErrorApi extends Error {
  constructor(msg, estado) { super(msg); this.estado = estado; }
}
async function api(metodo, ruta, cuerpo) {
  if (DEMO) return mock(metodo, ruta, cuerpo);
  const cab = { Accept: "application/json" };
  if (cuerpo !== undefined) cab["Content-Type"] = "application/json";
  if (est.sesion) cab["X-Operador"] = est.sesion;
  let r;
  try {
    r = await fetch(BASE + ruta, { method: metodo, headers: cab, body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) });
  } catch (e) {
    throw new ErrorApi("No hay conexión con el servicio.", 0);
  }
  if (r.status === 404 || r.status === 501) throw new ErrorApi("Este servicio todavía no está disponible.", r.status);
  if (r.status === 401 || r.status === 403) {
    if (ruta === "/api/operador/ingresar") throw new ErrorApi("El código no es correcto.", r.status);
    if (est.sesion) { salir(); $("op-error-ingreso").textContent = "Su sesión venció. Ingrese de nuevo."; }
    throw new ErrorApi("La sesión no es válida. Ingrese de nuevo.", r.status);
  }
  if (!r.ok) throw new ErrorApi("El servicio respondió con un error (" + r.status + ").", r.status);
  try { return await r.json(); } catch (e) { return {}; }
}
async function fixture(nombre) {
  const r = await fetch("/operador/fixtures/" + nombre);
  if (!r.ok) throw new ErrorApi("Falta la muestra " + nombre + ".", r.status);
  return r.json();
}
async function mock(metodo, ruta, cuerpo) {
  if (!est.mock) {
    est.mock = { cola: await fixture("cola.json"), paquetes: {}, t0: ahoraS() };
    for (const c of est.mock.cola) c.creado_en = new Date((est.mock.t0 - c.creado_hace_s) * 1000).toISOString();
  }
  const m = est.mock;
  if (ruta === "/api/operador/ingresar") {
    if (!cuerpo || !String(cuerpo.codigo || "").trim()) throw new ErrorApi("Código inválido.", 401);
    return { sesion_operador: "demo-local" };
  }
  if (ruta === "/api/operador/cola") return m.cola.map((c) => Object.assign({}, c));
  const g = ruta.match(/^\/api\/operador\/traspasos\/([\w-]+)(?:\/(\w+))?$/);
  if (!g) throw new ErrorApi("Ruta desconocida.", 404);
  const item = m.cola.find((c) => c.id_traspaso === g[1]);
  if (!item) throw new ErrorApi("No existe ese traspaso.", 404);
  if (!m.paquetes[g[1]]) {
    const p = await fixture("traspaso_" + g[1] + ".json");
    p.creado_en = item.creado_en;
    for (const pl of p.plazos_en_curso || []) if (typeof pl.vence_en_s === "number") pl.vence = new Date((m.t0 + pl.vence_en_s) * 1000).toISOString();
    m.paquetes[g[1]] = p;
  }
  const p = m.paquetes[g[1]];
  if (metodo === "GET" && !g[2]) return JSON.parse(JSON.stringify(p));
  if (g[2] === "tomar") { item.estado = p.estado = "tomado"; item.tomado_por = p.tomado_por = "Usted"; return { estado: "tomado" }; }
  if (g[2] === "mensaje") {
    const id = p.mensajes.length + 1;
    p.mensajes.push({ id, autor: "persona", texto: cuerpo.texto, en: new Date().toTimeString().slice(0, 5) });
    return { id };
  }
  if (g[2] === "resolver") { item.estado = p.estado = "resuelto"; p.correccion = cuerpo; return { estado: "resuelto" }; }
  if (g[2] === "sugerencia") {
    return {
      resumen: "El cliente no reconoce un cargo y pidió una persona. El cargo está verificado y no se ha abierto reclamo. Falta confirmar si quiere bloquear la tarjeta.",
      respuesta: "Hola, soy del equipo de LATAM Bank. Ya leí lo que le contó al asistente y no tiene que repetirlo. Voy a revisar el cargo con usted y le cuento el siguiente paso por este mismo chat.",
      fuentes: ["TRA-04", "A-13"], origen: "modelo", aviso: null,
    };
  }
  throw new ErrorApi("Ruta desconocida.", 404);
}

// ---------- ingreso ----------
async function ingresar(ev) {
  ev.preventDefault();
  const codigo = $("op-codigo").value.trim();
  const err = $("op-error-ingreso");
  err.textContent = "";
  if (!codigo) { err.textContent = "Escriba el código de demostración."; $("op-codigo").focus(); return; }
  try {
    const r = await api("POST", "/api/operador/ingresar", { codigo });
    est.sesion = r.sesion_operador || "sesion";
    $("op-codigo").value = "";
    mostrarApp();
  } catch (e) {
    err.textContent = e.message;
    $("op-codigo").focus();
  }
}
function mostrarApp() {
  $("op-ingreso").classList.add("oculto");
  $("op-app").classList.remove("oculto");
  $("op-salir").classList.remove("oculto");
  cargarCola(true);
  sondeoCola = window.setInterval(() => cargarCola(false), 15000);
  relojes = window.setInterval(tic, 1000);
}
function salir() {
  window.clearInterval(sondeoCola); window.clearInterval(sondeoHilo); window.clearInterval(relojes);
  est.sesion = null; est.actual = null; est.paquete = null;
  $("op-app").classList.add("oculto");
  $("op-salir").classList.add("oculto");
  $("op-caso").classList.add("oculto");
  $("op-vacio").classList.remove("oculto");
  $("op-ingreso").classList.remove("oculto");
  $("op-codigo").focus();
}

// ---------- cola ----------
const ordenPrio = (p) => Number(String(p).replace(/\D/g, "")) || 9;
async function cargarCola(primera) {
  const err = $("op-error-cola");
  try {
    const datos = await api("GET", "/api/operador/cola");
    err.textContent = "";
    est.cola = (Array.isArray(datos) ? datos : []).slice().sort((a, b) => ordenPrio(a.prioridad) - ordenPrio(b.prioridad) || instante(a, "creado_en", "creado_hace_s") - instante(b, "creado_en", "creado_hace_s"));
    pintarCola(primera);
  } catch (e) {
    err.textContent = e.message + " Se reintenta cada 15 segundos.";
    if (primera) pintarCola(false);
  }
}
function pintarCola(primera) {
  const ul = $("op-lista");
  const foco = document.activeElement && document.activeElement.closest ? document.activeElement.closest("li") : null;
  const idFoco = foco && ul.contains(foco) ? foco.dataset.id : null;
  ul.textContent = "";
  const abiertos = est.cola.filter((c) => c.estado !== "resuelto");
  $("op-estado-cola").textContent = abiertos.length + (abiertos.length === 1 ? " traspaso abierto" : " traspasos abiertos");
  if (!est.cola.length) { ul.appendChild(el("li", "op-suave op-vacio-cola", "No hay traspasos en cola.")); return; }
  for (const c of est.cola) {
    const li = el("li", "op-item op-i-" + String(c.prioridad).toLowerCase() + (est.actual === c.id_traspaso ? " op-activo" : "") + (c.estado === "resuelto" ? " op-resuelto" : ""));
    li.dataset.id = c.id_traspaso;
    const b = el("button", "op-item-boton", null, { type: "button", "aria-current": est.actual === c.id_traspaso ? "true" : "false" });
    const fila1 = el("span", "op-fila");
    fila1.appendChild(insignia(c.prioridad));
    fila1.appendChild(el("span", "op-motivo", c.motivo_texto || c.motivo));
    const fila2 = el("span", "op-fila op-suave op-meta");
    const pais = NOMBRE_PAIS[c.pais] || c.pais;
    fila2.appendChild(el("span", null, [pais, IDIOMA[c.idioma] || c.idioma, c.registro].filter(Boolean).join(" · ")));
    fila2.appendChild(el("span", null, CANAL[c.canal] || c.canal));
    const fila3 = el("span", "op-fila op-meta");
    const t = el("span", "op-sla");
    t.dataset.creado = String(instante(c, "creado_en", "creado_hace_s"));
    t.dataset.prio = c.prioridad;
    fila3.appendChild(t);
    fila3.appendChild(el("span", "op-suave", estadoTexto(c)));
    b.append(fila1, fila2, fila3);
    b.setAttribute("aria-label", c.prioridad + ", " + (c.motivo_texto || c.motivo) + ", " + pais + ", " + estadoTexto(c));
    b.addEventListener("click", () => abrir(c.id_traspaso, true));
    li.appendChild(b);
    ul.appendChild(li);
  }
  if (idFoco) { const b = ul.querySelector('li[data-id="' + idFoco + '"] button'); if (b) b.focus(); }
  tic();
}
function estadoTexto(c) {
  if (c.estado === "tomado") return "Tomado" + (c.tomado_por ? " por " + c.tomado_por : "");
  if (c.estado === "resuelto") return "Resuelto";
  return "En cola";
}
function insignia(p) {
  const s = el("span", "op-prio op-" + String(p).toLowerCase(), p);
  s.setAttribute("aria-label", "Prioridad " + p);
  return s;
}
function colaTeclado(ev) {
  const botones = Array.from($("op-lista").querySelectorAll(".op-item-boton"));
  const i = botones.indexOf(document.activeElement);
  if (i < 0) return;
  let j = null;
  if (ev.key === "ArrowDown") j = Math.min(botones.length - 1, i + 1);
  else if (ev.key === "ArrowUp") j = Math.max(0, i - 1);
  else if (ev.key === "Home") j = 0;
  else if (ev.key === "End") j = botones.length - 1;
  if (j !== null) { ev.preventDefault(); botones[j].focus(); }
}

// ---------- relojes ----------
function tic() {
  const ahora = ahoraS();
  for (const n of document.querySelectorAll(".op-sla")) {
    const en = ahora - Number(n.dataset.creado);
    const lim = SLA_S[n.dataset.prio] || 86400;
    const rest = lim - en;
    n.textContent = "En cola " + fmtDur(en) + " · SLA " + (rest >= 0 ? fmtDur(rest) : "vencido " + fmtDur(-rest));
    n.classList.toggle("op-vencido", rest < 0);
    n.classList.toggle("op-por-vencer", rest >= 0 && rest < lim * 0.25);
  }
  for (const n of document.querySelectorAll(".op-cuenta")) {
    const rest = Number(n.dataset.vence) - ahora;
    n.textContent = rest >= 0 ? "vence en " + fmtDur(rest) : "vencido hace " + fmtDur(-rest);
    n.classList.toggle("op-vencido", rest < 0);
  }
}

// ---------- detalle ----------
async function abrir(id, mover) {
  est.actual = id;
  const gen = ++est.cargaGen;
  window.clearInterval(sondeoHilo);
  pintarCola(false);
  const caso = $("op-caso");
  $("op-vacio").classList.add("oculto");
  caso.classList.remove("oculto");
  caso.textContent = "";
  caso.appendChild(el("p", "op-suave", "Cargando el paquete..."));
  try {
    const p = await api("GET", "/api/operador/traspasos/" + encodeURIComponent(id));
    if (gen !== est.cargaGen) return;
    est.paquete = p;
    est.ultimoMensaje = 0;
    pintarCaso();
    if (mover) { $("op-caso-titulo").focus(); anunciar("Caso " + id + ", prioridad " + p.prioridad + ", abierto."); }
    sondeoHilo = window.setInterval(refrescarHilo, 4000);
  } catch (e) {
    caso.textContent = "";
    caso.appendChild(el("p", "op-error", e.message, { role: "alert" }));
  }
}
async function refrescarHilo() {
  if (!est.actual) return;
  try {
    const p = await api("GET", "/api/operador/traspasos/" + encodeURIComponent(est.actual));
    if (est.actual !== p.id_traspaso) return;
    const previo = est.paquete;
    est.paquete = p;
    if ((p.mensajes || []).length !== ((previo && previo.mensajes) || []).length) pintarMensajes(true);
    if (previo && previo.estado !== p.estado) pintarCaso();
  } catch (e) { /* el siguiente sondeo lo reintenta */ }
}

function seccion(num, titulo, id) {
  const s = el("section", "op-sec", null, { "aria-labelledby": "op-h-" + id });
  s.id = "op-s-" + id;
  const h = el("h3", null, null, { id: "op-h-" + id });
  h.appendChild(el("span", "op-num", String(num)));
  h.appendChild(document.createTextNode(titulo));
  s.appendChild(h);
  return s;
}
function proc(tipo, texto) {
  const clases = { verificado: "op-proc-v", cliente: "op-proc-c", ia: "op-proc-i" };
  return el("span", "op-proc " + clases[tipo], texto);
}
function vacio(t) { return el("p", "op-suave op-vacio-sec", t); }
function fuenteHora(x) { return [x.fuente, x.hora].filter(Boolean).join(", "); }

function pintarCaso() {
  const p = est.paquete;
  const caso = $("op-caso");
  caso.textContent = "";
  const tomado = p.estado === "tomado";
  const resuelto = p.estado === "resuelto";
  const motivo = p.motivo || {};

  // 1. barra superior
  const cab = el("header", "op-caso-cab");
  const fila = el("div", "op-fila");
  fila.appendChild(insignia(p.prioridad));
  const h = el("h2", null, motivo.texto || motivo.codigo || "Traspaso", { id: "op-caso-titulo", tabindex: "-1" });
  fila.appendChild(h);
  cab.appendChild(fila);
  const meta = el("dl", "op-datos");
  const dato = (k, v, extra) => { const d = el("div"); d.appendChild(el("dt", null, k)); const dd = el("dd", extra || null, v); d.appendChild(dd); meta.appendChild(d); return dd; };
  const c0 = (est.cola.find((c) => c.id_traspaso === p.id_traspaso)) || {};
  const creado = instante(p, "creado_en", "creado_hace_s") || instante(c0, "creado_en", "creado_hace_s");
  const sla = dato("Tiempo en cola y SLA", "", "op-sla"); sla.dataset.creado = String(creado); sla.dataset.prio = p.prioridad;
  dato("Idioma y registro", [IDIOMA[p.idioma] || p.idioma, p.registro].filter(Boolean).join(", "));
  dato("País de la cuenta", NOMBRE_PAIS[p.pais_cuenta] || p.pais_cuenta);
  dato("Canal actual", CANAL[p.canal_actual] || p.canal_actual);
  if (p.cola_destino) dato("Cola", [p.cola_destino.especialidad, p.cola_destino.franja].filter(Boolean).join(", "));
  dato("Identidad", p.identidad ? "Verificada (" + p.identidad.nivel + ", " + p.identidad.metodo + ", " + p.identidad.hora + ")" : "No verificada");
  dato("Estado", estadoTexto(p));
  if (p.caso_id) dato("Caso", p.caso_id);
  cab.appendChild(meta);
  const bar = el("div", "op-fila op-acciones-cab");
  if (!tomado && !resuelto) {
    const b = el("button", "op-boton", "Tomar caso", { type: "button", id: "op-tomar" });
    b.addEventListener("click", tomar);
    bar.appendChild(b);
  }
  if (tomado) {
    const r = el("button", "op-boton op-secundario", "Responder", { type: "button", id: "op-ir-responder" });
    r.addEventListener("click", () => { const t = $("op-texto"); if (t) { t.scrollIntoView({ block: "center" }); t.focus(); } });
    const v = el("button", "op-boton op-secundario", "Resolver", { type: "button", id: "op-ir-resolver" });
    v.addEventListener("click", () => { const t = $("op-resultado"); if (t) { t.scrollIntoView({ block: "center" }); t.focus(); } });
    bar.append(r, v);
  }
  if (motivo.regla) bar.appendChild(el("span", "op-suave", "Regla " + motivo.regla.id + " (" + motivo.regla.version + ")"));
  if (bar.children.length) bar.classList.add("op-barra-acc");
  cab.appendChild(el("p", "op-error", "", { id: "op-error-caso", role: "alert" }));
  caso.appendChild(cab);

  // 2. qué hacer primero
  let s = seccion(2, "Qué hacer primero", "primero");
  s.appendChild(proc("ia", "Sugerencia de política"));
  const ol = el("ol", "op-lista-simple");
  for (const x of p.que_hacer_primero || []) {
    const li = el("li", null, limpio(x.paso));
    if (x.regla) li.appendChild(el("span", "op-suave", " (" + x.regla + ")"));
    ol.appendChild(li);
  }
  s.appendChild((p.que_hacer_primero || []).length ? ol : vacio("La política no sugiere pasos para este motivo."));
  caso.appendChild(s);

  // 3. compromisos comunicados
  s = seccion(3, "Compromisos ya comunicados al cliente", "compromisos");
  const ulc = el("ul", "op-lista-simple");
  for (const x of p.compromisos_comunicados || []) {
    const li = el("li", null, "“" + limpio(x.texto) + "”");
    li.appendChild(el("span", "op-suave", " dicho a las " + x.hora));
    ulc.appendChild(li);
  }
  s.appendChild((p.compromisos_comunicados || []).length ? ulc : vacio("No hay compromisos registrados."));
  caso.appendChild(s);

  // 4. solicitud e interpretación
  s = seccion(4, "Solicitud e interpretación", "solicitud");
  const dos = el("div", "op-dos");
  const izq = el("div"); izq.appendChild(proc("cliente", "Dicho por el cliente"));
  izq.appendChild(el("blockquote", null, limpio(p.solicitud && p.solicitud.cita), p.solicitud && p.solicitud.idioma ? { lang: p.solicitud.idioma } : null));
  const der = el("div"); der.appendChild(proc("ia", "Interpretación de la IA"));
  const i = p.interpretacion || {};
  const conf = typeof i.confianza === "number" ? Math.round(i.confianza * 100) + "% de confianza" : "confianza no disponible";
  der.appendChild(el("p", null, [i.motivo, i.urgencia ? "urgencia " + i.urgencia : ""].filter(Boolean).join(", ")));
  if ((i.entidades || []).length) der.appendChild(el("p", "op-suave", "Entidades: " + i.entidades.map(limpio).join(", ")));
  der.appendChild(el("p", "op-suave", conf));
  dos.append(izq, der);
  s.appendChild(dos);
  caso.appendChild(s);

  // 5. hechos verificados
  s = seccion(5, "Hechos verificados", "hechos");
  const ulh = el("ul", "op-lista-simple");
  for (const x of p.hechos_verificados || []) {
    const li = el("li");
    li.appendChild(proc("verificado", "Verificado"));
    li.appendChild(document.createTextNode(" " + limpio(x.texto) + " "));
    li.appendChild(el("span", "op-suave", "(" + fuenteHora(x) + ")"));
    ulh.appendChild(li);
  }
  s.appendChild((p.hechos_verificados || []).length ? ulh : vacio("No hay hechos verificados. El motivo consta en el encabezado."));
  caso.appendChild(s);

  // 6. acciones
  s = seccion(6, "Acciones realizadas y no realizadas", "acciones");
  const dosA = el("div", "op-dos");
  const a1 = el("div"); a1.appendChild(el("h4", null, "Realizadas"));
  const u1 = el("ul", "op-lista-simple");
  for (const x of p.acciones_realizadas || []) {
    const li = el("li"); li.appendChild(proc("verificado", "Verificado"));
    li.appendChild(document.createTextNode(" " + limpio(x.accion) + ": " + limpio(x.resultado) + " "));
    li.appendChild(el("span", "op-suave", "(" + x.hora + ")"));
    u1.appendChild(li);
  }
  a1.appendChild((p.acciones_realizadas || []).length ? u1 : vacio("Ninguna."));
  const a2 = el("div"); a2.appendChild(el("h4", null, "No realizadas"));
  const u2 = el("ul", "op-lista-simple");
  for (const x of p.acciones_no_realizadas || []) u2.appendChild(el("li", null, limpio(x.accion) + ". Motivo: " + limpio(x.motivo) + "."));
  a2.appendChild((p.acciones_no_realizadas || []).length ? u2 : vacio("Ninguna."));
  dosA.append(a1, a2); s.appendChild(dosA);
  caso.appendChild(s);

  // 7. conflictos
  s = seccion(7, "Conflictos entre lo declarado y el registro", "conflictos");
  if ((p.conflictos || []).length) {
    const t = el("table", "op-tabla");
    t.appendChild(el("caption", "visualmente-oculto", "Conflictos en dos columnas"));
    const tr = el("tr");
    for (const k of ["Tema", "Declarado", "Registro"]) tr.appendChild(el("th", null, k, { scope: "col" }));
    const th = el("thead"); th.appendChild(tr); t.appendChild(th);
    const tb = el("tbody");
    for (const x of p.conflictos) {
      const r = el("tr");
      r.appendChild(el("th", null, limpio(x.tipo), { scope: "row" }));
      const d = el("td"); d.appendChild(proc("cliente", "Dicho por el cliente")); d.appendChild(el("div", null, "“" + limpio(x.declarado) + "”"));
      const g = el("td"); g.appendChild(proc("verificado", "Verificado")); g.appendChild(el("div", null, limpio(x.registro)));
      r.append(d, g); tb.appendChild(r);
    }
    t.appendChild(tb); s.appendChild(t);
  } else s.appendChild(vacio("Sin conflictos."));
  caso.appendChild(s);

  // 8. preguntas abiertas
  s = seccion(8, "Preguntas abiertas", "preguntas");
  const ulp = el("ul", "op-lista-simple");
  for (const x of p.preguntas_abiertas || []) {
    const li = el("li", null, limpio(x.pregunta) + " ");
    li.appendChild(el("span", "op-etiqueta", "Le toca a: " + (AREA[x.a_quien] || x.a_quien)));
    li.appendChild(document.createTextNode(" "));
    li.appendChild(el("span", "op-etiqueta" + (x.bloquea ? " op-bloquea" : ""), x.bloquea ? "Bloquea la resolución" : "No bloquea"));
    ulp.appendChild(li);
  }
  s.appendChild((p.preguntas_abiertas || []).length ? ulp : vacio("No hay preguntas abiertas."));
  caso.appendChild(s);

  // 9. plazos
  s = seccion(9, "Plazos en curso", "plazos");
  const ulz = el("ul", "op-lista-simple");
  for (const x of p.plazos_en_curso || []) {
    const li = el("li", null, limpio(x.regla) + ", desde " + x.inicio + ": ");
    const c = el("strong", "op-cuenta");
    c.dataset.vence = String(x.vence ? Date.parse(x.vence) / 1000 : ahoraS() + (x.vence_en_s || 0));
    li.appendChild(c); ulz.appendChild(li);
  }
  s.appendChild((p.plazos_en_curso || []).length ? ulz : vacio("No hay plazos en curso."));
  caso.appendChild(s);

  // 10. evidencia
  s = seccion(10, "Evidencia", "evidencia");
  const ev = p.evidencia || {};
  const pe = el("p");
  if (ev.traza_url && /^https:\/\//.test(ev.traza_url)) {
    pe.appendChild(el("a", null, "Abrir la traza del caso", { href: ev.traza_url, target: "_blank", rel: "noopener noreferrer" }));
  } else pe.textContent = "Traza no disponible.";
  s.appendChild(pe);
  if ((ev.reglas || []).length) s.appendChild(el("p", "op-suave", "Reglas aplicadas: " + ev.reglas.join(", ")));
  if ((ev.plantillas || []).length) s.appendChild(el("p", "op-suave", "Plantillas enviadas: " + ev.plantillas.join(", ")));
  caso.appendChild(s);

  // 11. transcripción plegada
  s = seccion(11, "Transcripción enmascarada", "transcripcion");
  const det = el("details");
  det.appendChild(el("summary", null, "Ver la conversación (" + (p.transcripcion || []).length + " mensajes)"));
  const tr = el("ul", "op-hilo");
  for (const m of p.transcripcion || []) tr.appendChild(burbuja(m));
  det.appendChild(tr); s.appendChild(det);
  caso.appendChild(s);

  // 12. panel de acciones
  s = seccion(12, "Panel de acciones", "panel");
  if (!tomado && !resuelto) s.appendChild(vacio("Tome el caso para escribir al cliente y resolverlo."));
  if (tomado) {
    s.appendChild(el("p", "op-suave", "Ahora le atiende una persona del equipo. El asistente queda en modo asistente y no escribe al cliente."));
    s.appendChild(el("h4", null, "Hilo con el cliente"));
    s.appendChild(el("ul", "op-hilo", null, { id: "op-mensajes", "aria-label": "Mensajes del hilo" }));
    const f = el("form", "op-form", null, { id: "op-form-msg" });
    f.appendChild(el("label", null, "Respuesta al cliente", { for: "op-texto" }));
    const ta = el("textarea", null, "Hola, soy del equipo de " + (p.cola_destino ? p.cola_destino.especialidad : "servicio") + " de LATAM Bank. Ya leí lo que le contó al asistente. No tiene que repetirlo.", { id: "op-texto", rows: "3" });
    f.appendChild(ta);
    const bs = el("button", "op-boton", "Enviar", { type: "submit" });
    f.appendChild(bs); f.addEventListener("submit", enviarMensaje);
    // Copiloto: el borrador llega al cuadro de texto y la persona lo revisa; nada se envía solo.
    const bb = el("button", "op-boton op-secundario", "Sugerir borrador con IA", { type: "button", id: "op-sugerir" });
    bb.addEventListener("click", sugerirBorrador);
    f.appendChild(bb);
    f.appendChild(el("div", "op-borrador", null, { id: "op-borrador", "aria-live": "polite" }));
    s.appendChild(f);
    s.appendChild(formularioResolver());
  }
  if (resuelto) {
    s.appendChild(el("p", null, "Caso resuelto. La corrección quedó registrada como etiqueta del equipo."));
    s.appendChild(el("ul", "op-hilo", null, { id: "op-mensajes", "aria-label": "Mensajes del hilo" }));
  }
  caso.appendChild(s);
  if (bar.children.length) caso.appendChild(bar);
  pintarMensajes(false);
  tic();
}

function burbuja(m) {
  const li = el("li", "op-msg op-msg-" + m.autor);
  const rol = { cliente: "Cliente", asistente: "Asistente de IA", persona: "Usted" }[m.autor] || m.autor;
  li.appendChild(el("span", "op-msg-autor", rol + (m.en ? ", " + m.en : "")));
  li.appendChild(el("span", "op-msg-texto", limpio(m.texto)));
  return li;
}
function pintarMensajes(anuncia) {
  const ul = $("op-mensajes");
  if (!ul) return;
  ul.textContent = "";
  const ms = (est.paquete && est.paquete.mensajes) || [];
  if (!ms.length) ul.appendChild(el("li", "op-suave", "Aún no hay mensajes en el hilo."));
  for (const m of ms) ul.appendChild(burbuja(m));
  ul.scrollTop = ul.scrollHeight;
  const ultimo = ms.length ? ms[ms.length - 1] : null;
  if (anuncia && ultimo && ultimo.autor === "cliente") anunciar("Nuevo mensaje del cliente.");
}

function campoSelect(id, etiqueta, opciones, vacioTxt) {
  const d = el("div", "op-campo");
  d.appendChild(el("label", null, etiqueta, { for: id }));
  const s = el("select", null, null, { id });
  if (vacioTxt) s.appendChild(el("option", null, vacioTxt, { value: "" }));
  for (const o of opciones) s.appendChild(el("option", null, o[1], { value: o[0] }));
  d.appendChild(s);
  return d;
}
function campoSiNo(id, etiqueta) {
  return campoSelect(id, etiqueta, [["si", "Sí"], ["no", "No"]], "Sin indicar");
}
function formularioResolver() {
  const f = el("form", "op-form op-resolver", null, { id: "op-form-resolver", novalidate: "" });
  f.appendChild(el("h4", null, "Resolver y corregir"));
  f.appendChild(el("p", "op-suave", "La corrección es una etiqueta del equipo. No lleva datos del cliente."));
  const g = el("div", "op-grid");
  g.appendChild(campoSelect("op-resultado", "Resultado", RESULTADOS, "Elija un resultado"));
  g.appendChild(campoSelect("op-motivo-verdadero", "Motivo verdadero", MOTIVOS_VERDADEROS, "Sin indicar"));
  g.appendChild(campoSiNo("op-urgencia"  , "Urgencia verdadera"));
  g.appendChild(campoSelect("op-ruta", "Ruta correcta", RUTAS.map((r) => [r, r]), "Sin indicar"));
  g.appendChild(campoSiNo("op-traspaso-necesario", "Traspaso necesario"));
  g.appendChild(campoSiNo("op-motivo-correcto", "Motivo del traspaso correcto"));
  g.appendChild(campoSelect("op-utilidad", "Utilidad del paquete (5: resolví sin preguntar nada de lo que ya traía)", [1, 2, 3, 4, 5].map((n) => [String(n), String(n)]), "Sin indicar"));
  f.appendChild(g);
  const r1 = el("div", "op-campo");
  r1.appendChild(el("label", null, "Datos del paquete que tuvo que volver a pedir", { for: "op-repetidas" }));
  r1.appendChild(el("input", null, null, { id: "op-repetidas", type: "text", autocomplete: "off" }));
  f.appendChild(r1);
  const r2 = el("div", "op-campo");
  r2.appendChild(el("label", null, "Nota de cierre (sin nombres, documentos ni tarjetas)", { for: "op-nota" }));
  r2.appendChild(el("textarea", null, null, { id: "op-nota", rows: "3" }));
  f.appendChild(r2);
  f.appendChild(el("p", "op-error", "", { id: "op-error-resolver", role: "alert" }));
  f.appendChild(el("button", "op-boton", "Resolver caso", { type: "submit" }));
  f.addEventListener("submit", resolver);
  return f;
}

// ---------- acciones ----------
async function tomar() {
  const b = $("op-tomar");
  b.disabled = true;
  try {
    await api("POST", "/api/operador/traspasos/" + encodeURIComponent(est.actual) + "/tomar");
    est.paquete.estado = "tomado"; est.paquete.tomado_por = "Usted";
    const c = est.cola.find((x) => x.id_traspaso === est.actual);
    if (c) { c.estado = "tomado"; c.tomado_por = "Usted"; }
    pintarCola(false); pintarCaso();
    const ta = $("op-texto"); if (ta) ta.focus();
    anunciar("Caso tomado. Puede escribir al cliente.");
  } catch (e) {
    b.disabled = false;
    $("op-error-caso").textContent = e.message;
  }
}
async function sugerirBorrador() {
  const b = $("op-sugerir"), caja = $("op-borrador"), ta = $("op-texto");
  b.disabled = true; caja.replaceChildren(el("p", "op-suave", "Preparando el borrador."));
  try {
    const r = await api("POST", "/api/operador/traspasos/" + encodeURIComponent(est.actual) + "/sugerencia", {});
    caja.replaceChildren();
    caja.appendChild(el("p", "op-borrador-aviso", r.origen === "modelo"
      ? "Borrador de inteligencia artificial. Revíselo y edítelo antes de enviar: usted responde por el mensaje."
      : (r.aviso || "Texto de plantilla.")));
    caja.appendChild(el("h5", null, "Resumen para usted"));
    caja.appendChild(el("p", null, r.resumen));
    if ((r.fuentes || []).length) caja.appendChild(el("p", "op-suave", "Fuente: política del banco, regla " + r.fuentes.join(", ")));
    ta.value = r.respuesta;
    est.borrador = { caso: est.actual, texto: r.respuesta, origen: r.origen };
    ta.focus();
    anunciar("Borrador listo para revisar.");
  } catch (e) {
    caja.replaceChildren(el("p", "op-error", e.message));
  }
  b.disabled = false;
}
// Qué hizo la persona con el borrador: queda en la etiqueta de corrección como medida de supervisión humana.
function usoDelBorrador(texto) {
  const d = est.borrador;
  if (!d || d.caso !== est.actual) return null;
  return texto === d.texto.trim() ? "enviado_sin_cambios" : "editado";
}
async function enviarMensaje(ev) {
  ev.preventDefault();
  const ta = $("op-texto");
  const texto = ta.value.trim();
  if (!texto) { ta.focus(); return; }
  const uso = usoDelBorrador(texto);
  // cuenta el primer mensaje tras el borrador; los siguientes ya son de la persona
  if (uso && !(est.borradorUso && est.borradorUso.caso === est.actual)) est.borradorUso = { caso: est.actual, uso, origen: est.borrador.origen };
  if (RE_PII.test(texto)) { $("op-error-caso").textContent = "El mensaje parece traer un número de tarjeta completo. Quítelo antes de enviar."; ta.focus(); return; }
  const b = ev.target.querySelector("button"); b.disabled = true;
  try {
    await api("POST", "/api/operador/traspasos/" + encodeURIComponent(est.actual) + "/mensaje", { texto });
    $("op-error-caso").textContent = "";
    ta.value = "";
    await refrescarHilo();
    pintarMensajes(false);
    ta.focus();
  } catch (e) {
    $("op-error-caso").textContent = e.message;
  }
  b.disabled = false;
}
async function resolver(ev) {
  ev.preventDefault();
  const err = $("op-error-resolver");
  const v = (id) => $(id).value;
  if (!v("op-resultado")) { err.textContent = "Elija un resultado antes de cerrar."; $("op-resultado").focus(); return; }
  const nota = $("op-nota").value.trim();
  if (RE_PII.test(nota) || RE_PII.test($("op-repetidas").value)) { err.textContent = "La nota parece traer un número de tarjeta completo. Quítelo."; $("op-nota").focus(); return; }
  const corr = {
    motivo_verdadero: v("op-motivo-verdadero") || null,
    urgencia_verdadera: v("op-urgencia") || null,
    ruta_correcta: v("op-ruta") || null,
    traspaso_necesario: v("op-traspaso-necesario") || null,
    motivo_traspaso_correcto: v("op-motivo-correcto") || null,
    utilidad_paquete: v("op-utilidad") ? Number(v("op-utilidad")) : null,
    preguntas_repetidas: $("op-repetidas").value.trim() || null,
    comentario: nota || null,
    borrador_ia: est.borradorUso && est.borradorUso.caso === est.actual
      ? est.borradorUso.uso + ":" + est.borradorUso.origen
      : (est.borrador && est.borrador.caso === est.actual ? "pedido_y_descartado" : "no_pedido"),
  };
  const b = ev.target.querySelector("button[type=submit]"); b.disabled = true;
  try {
    await api("POST", "/api/operador/traspasos/" + encodeURIComponent(est.actual) + "/resolver", { resultado: v("op-resultado"), etiqueta_correccion: corr, nota });
    est.paquete.estado = "resuelto";
    const c = est.cola.find((x) => x.id_traspaso === est.actual);
    if (c) c.estado = "resuelto";
    pintarCola(false); pintarCaso();
    $("op-caso-titulo").focus();
    anunciar("Caso resuelto.");
  } catch (e) {
    err.textContent = e.message; b.disabled = false;
  }
}

// ---------- arranque ----------
document.addEventListener("DOMContentLoaded", () => {
  if (DEMO) $("op-modo").classList.remove("oculto");
  $("op-form-ingreso").addEventListener("submit", ingresar);
  $("op-salir").addEventListener("click", salir);
  $("op-refrescar").addEventListener("click", () => cargarCola(false));
  $("op-lista").addEventListener("keydown", colaTeclado);
  $("op-codigo").focus();
  // Atajo de la demostración local: ?demo=local&caso=TR-1002 entra y abre ese traspaso.
  const caso = new URLSearchParams(window.location.search).get("caso");
  if (DEMO && caso) {
    api("POST", "/api/operador/ingresar", { codigo: "demo" }).then(async (r) => {
      est.sesion = r.sesion_operador; mostrarApp(); await cargarCola(true); abrir(caso, false);
    });
  }
});
