// Banca en línea de demostración (D-33). Sin compilación ni scripts en línea.
// Contrato: tecnologia/web/API_BANCA.md. Con ?demo=local todo sale de banca/fixtures/ (sin backend).
"use strict";

(function () {
  const BASE = String(window.LATAM_API_BASE || "").replace(/\/+$/, "");
  const $ = (id) => document.getElementById(id);

  // Almacenamiento de sesión con respaldo en memoria (puede estar bloqueado).
  const memoria = {};
  const guardar = {
    leer(k) { try { return window.sessionStorage.getItem(k); } catch (e) { return memoria[k] || null; } },
    escribir(k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { memoria[k] = v; } },
    borrar(k) { try { window.sessionStorage.removeItem(k); } catch (e) { delete memoria[k]; } },
  };

  const params = new URLSearchParams(window.location.search);
  if (params.get("demo") === "local") guardar.escribir("banca_mock", "1");
  if (params.get("demo") === "off") { guardar.borrar("banca_mock"); guardar.borrar("banca_mock_estado"); }
  const MOCK = guardar.leer("banca_mock") === "1";

  // Idioma y trato (idioma.js): sin él la banca queda en español de usted.
  const T = (texto, valores) => (window.Idioma ? window.Idioma.t(texto, valores) : String(texto));
  const registro = () => (window.Idioma ? window.Idioma.modo() : "usted");
  const locale = () => (window.Idioma ? window.Idioma.locale() : "es");

  const pausa = (ms) => new Promise((r) => window.setTimeout(r, ms));

  // Construye nodos con nodos del DOM: todo texto entra por textContent.
  function h(tag, attrs, ...hijos) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "clase") n.className = v;
      else if (k === "texto") n.textContent = v;
      else n.setAttribute(k, v === true ? "" : v);
    }
    for (const c of hijos.flat()) {
      if (c === null || c === undefined || c === false) continue;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return n;
  }

  // Cliente de la API ------------------------------------------------------------------------------------------

  class ErrorApi extends Error {
    constructor(status, mensaje, codigo) { super(mensaje || "http " + status); this.status = status; this.codigo = codigo || ""; }
  }

  function sesion() {
    try { return JSON.parse(guardar.leer("banca_sesion") || "null"); } catch (e) { return null; }
  }
  function guardarSesion(s) { guardar.escribir("banca_sesion", JSON.stringify(s)); }
  function salir() { guardar.borrar("banca_sesion"); guardar.borrar("banca_mock_estado"); guardar.borrar("banca_conv"); }

  async function llamar(ruta, opciones) {
    const o = opciones || {};
    const metodo = o.metodo || "GET";
    if (MOCK) return mock(ruta, metodo, o.cuerpo);
    const s = sesion();
    let r;
    try {
      r = await fetch(BASE + ruta, {
        method: metodo,
        headers: { "Content-Type": "application/json", "X-Sesion": (s && s.sesion) || "", "X-Registro": registro() },
        body: o.cuerpo === undefined ? undefined : JSON.stringify(o.cuerpo),
      });
    } catch (e) {
      throw new ErrorApi(0, "sin conexión");
    }
    if (!r.ok) {
      let codigo = "";
      try { codigo = String((await r.json()).error || ""); } catch (e) { /* sin cuerpo */ }
      throw new ErrorApi(r.status, "", codigo);
    }
    return r.json();
  }

  // Modo local -------------------------------------------------------------------------------------------------

  const cacheFx = {};
  async function fixture(nombre) {
    if (!cacheFx[nombre]) {
      const r = await fetch("/banca/fixtures/" + nombre + ".json");
      if (!r.ok) throw new ErrorApi(404);
      cacheFx[nombre] = await r.json();
    }
    return JSON.parse(JSON.stringify(cacheFx[nombre]));
  }
  function estadoLocal() {
    try { return JSON.parse(guardar.leer("banca_mock_estado") || "{}"); } catch (e) { return {}; }
  }
  function guardarLocal(e) { guardar.escribir("banca_mock_estado", JSON.stringify(e)); }

  // Las fixtures están en pesos colombianos: se llevan al país y la moneda del cliente para que sean coherentes.
  const MONEDAS = { MX: "MXN", CO: "COP", AR: "ARS" };
  const FACTOR = { COP: 1, MXN: 1 / 215, ARS: 0.34 };
  function leerMonto(t) {
    const x = String(t);
    if (/,\d{1,2}$/.test(x) || (x.includes(".") && x.includes(","))) return Number(x.replace(/\./g, "").replace(",", "."));
    return Number(x.replace(/[^\d.-]/g, ""));
  }
  function escribirMonto(n) { return n.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function localizar(datos, cliente) {
    const pais = (cliente && cliente.pais) || "CO";
    const moneda = MONEDAS[pais] || "COP";
    const f = FACTOR[moneda] || 1;
    const conv = (v) => (v === null || v === undefined || v === "" ? v : escribirMonto(Math.round(leerMonto(v) * f / (f < 1 ? 10 : 1)) * (f < 1 ? 10 : 1)));
    const signo = (v) => (typeof v === "string" && /^[+-]/.test(v) ? v[0] + conv(v.slice(1)) : conv(v));
    const lista = Array.isArray(datos) ? datos : datos.productos || datos.movimientos || [];
    lista.forEach((x) => {
      if (x.moneda) x.moneda = moneda;
      ["saldo", "limite", "monto", "credito_provisional"].forEach((k) => { if (k in x) x[k] = conv(x[k]); });
      if ("monto_con_signo" in x) x.monto_con_signo = signo(x.monto_con_signo);
      if (x.pais === "CO" && pais !== "CO") x.pais = pais;
      else if (x.pais === pais && pais !== "CO" && x.es_extranjera) x.pais = "CO";
    });
    return datos;
  }

  async function mock(ruta, metodo, cuerpo) {
    await pausa(280);
    const [camino, consulta] = ruta.split("?");
    const q = new URLSearchParams(consulta || "");
    const loc = estadoLocal();
    loc.bloqueadas = loc.bloqueadas || [];
    loc.reclamadas = loc.reclamadas || {};
    let m;
    if (camino === "/api/banca/clientes-demo") return fixture("clientes-demo");
    if (camino === "/api/banca/ingresar") {
      const lista = await fixture("clientes-demo");
      const c = lista.find((x) => x.indice === (cuerpo && cuerpo.indice)) || lista[0];
      return { sesion: "demo-local", cliente: { alias: c.alias, nombre: c.nombre, indice: c.indice, pais: c.pais, moneda: MONEDAS[c.pais] || "USD", registro: registro() } };
    }
    if (camino === "/api/banca/resumen") {
      const r = await fixture("resumen");
      const s = sesion();
      if (s && s.cliente) r.cliente = s.cliente;
      localizar(r, r.cliente);
      r.productos.forEach((p) => { if (loc.bloqueadas.includes(p.producto_ref)) p.estado = "bloqueada"; });
      return r;
    }
    if (camino === "/api/banca/movimientos") {
      const d = await fixture("movimientos");
      const res = await fixture("resumen");
      localizar(d, (sesion() || {}).cliente);
      const prod = res.productos.find((p) => p.producto_ref === q.get("producto_ref"));
      if (prod) d.movimientos = d.movimientos.filter((t) => t.tarjeta_final === prod.final);
      d.movimientos.forEach((t) => { if (loc.reclamadas[t.tx_ref]) t.caso_ref = loc.reclamadas[t.tx_ref]; });
      return d;
    }
    if ((m = camino.match(/^\/api\/banca\/movimientos\/([^/]+)\/reclamar$/))) {
      const d = await fixture("movimientos");
      localizar(d, (sesion() || {}).cliente);
      const t = d.movimientos.find((x) => x.tx_ref === m[1]);
      if (!t) throw new ErrorApi(404);
      loc.reclamadas[t.tx_ref] = loc.reclamadas[t.tx_ref] || "c-" + t.tx_ref;
      loc.contexto = t;
      guardarLocal(loc);
      return { conversacion: "demo-" + t.tx_ref };
    }
    if ((m = camino.match(/^\/api\/banca\/movimientos\/([^/]+)$/))) {
      const d = await fixture("movimientos");
      localizar(d, (sesion() || {}).cliente);
      const t = d.movimientos.find((x) => x.tx_ref === m[1]);
      if (!t) throw new ErrorApi(404);
      return t;
    }
    if (camino === "/api/banca/reclamos") {
      const lista = await fixture("reclamos");
      const d = await fixture("movimientos");
      localizar(lista, (sesion() || {}).cliente);
      localizar(d, (sesion() || {}).cliente);
      for (const [tx, ref] of Object.entries(loc.reclamadas)) {
        if (lista.some((c) => c.caso_ref === ref)) continue;
        const t = d.movimientos.find((x) => x.tx_ref === tx);
        if (!t) continue;
        const hoy = new Date().toISOString().slice(0, 10);
        lista.unshift({ caso_ref: ref, tx_ref: tx, descripcion: t.descripcion, monto: t.monto, moneda: t.moneda, estado: "abierto", abierto_en: hoy, credito_provisional: null, plazo: null, historial: [{ fecha: hoy, evento: "Recibimos su reclamo" }] });
      }
      return lista;
    }
    if ((m = camino.match(/^\/api\/banca\/tarjetas\/([^/]+)\/bloqueo$/))) {
      const ya = loc.bloqueadas.includes(m[1]);
      if (!ya) loc.bloqueadas.push(m[1]);
      guardarLocal(loc);
      return { estado: "bloqueada", ya_estaba: ya };
    }
    if (camino === "/api/textos") return fixture("textos");
    if (camino === "/api/traspaso") { loc.traspaso = Date.now(); guardarLocal(loc); return { texto: "Ya avisamos a una persona. Le responderá en esta misma conversación." }; }
    if ((m = camino.match(/^\/api\/banca\/conversaciones\/([^/]+)\/mensajes$/))) {
      if (metodo === "POST") return { id: "u-" + Date.now() };
      const listo = loc.traspaso && Date.now() - loc.traspaso > 6000 && !q.get("desde");
      return listo ? [{ id: "p1", autor: "persona", texto: "Hola, soy Camila, de LATAM Bank. Ya revisé su caso y veo el cargo. ¿Prefiere que le reponga la tarjeta hoy?", en: new Date().toISOString() }] : [];
    }
    throw new ErrorApi(404);
  }


  // Formato ----------------------------------------------------------------------------------------------------

  const hoyIso = () => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
  function fechaLarga(iso) {
    const d = new Date(String(iso) + "T12:00:00");
    if (Number.isNaN(d.getTime())) return String(iso || "");
    const dia = Math.round((new Date(hoyIso() + "T12:00:00") - d) / 86400000);
    if (dia === 0) return T("Hoy");
    if (dia === 1) return T("Ayer");
    return d.toLocaleDateString(locale(), { weekday: "long", day: "numeric", month: "long" });
  }
  function fechaCorta(iso) {
    const d = new Date(String(iso) + "T12:00:00");
    if (Number.isNaN(d.getTime())) return String(iso || "");
    return d.toLocaleDateString(locale(), { day: "numeric", month: "short", year: "numeric" });
  }
  const limpio = (monto) => String(monto).replace(/,00$/, "");
  const dinero = (monto, moneda) => (monto === null || monto === undefined ? "" : limpio(monto) + " " + String(moneda || ""));
  // Cifra con el código de moneda en pequeño: nunca se muestra un monto sin su moneda.
  function cifra(monto, moneda, clase) {
    return h("span", { clase: "bn-cifra bn-num " + (clase || "") }, h("span", { texto: limpio(monto) }), h("small", { texto: " " + String(moneda || "") }));
  }
  const enmascarar = (final) => "···· " + String(final || "").replace(/\D/g, "").slice(-4);
  const minuscula = (t) => String(t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  // El backend manda el tipo como texto ("Tarjeta Crédito"), no como código: se normaliza antes de comparar.
  const esTarjeta = (p) => /tarjeta|card/.test(minuscula(p.tipo) + " " + minuscula(p.etiqueta));
  const esCredito = (p) => /credit/.test(minuscula(p.tipo) + " " + minuscula(p.etiqueta));
  const esCuenta = (p) => !esTarjeta(p);

  const ESTADOS = {
    aprobada: ["Aprobada", "ok"], pendiente: ["Pendiente", "aviso"], rechazada: ["Rechazada", "mal"], reversada: ["Reversada", "neutro"],
    activa: ["Activa", "ok"], bloqueada: ["Bloqueada", "mal"],
    abierto: ["Abierto", "aviso"], en_revision: ["En revisión", "aviso"], resuelto: ["Resuelto", "ok"], cerrado: ["Cerrado", "neutro"],
  };
  // Respaldo: el backend puede mandar códigos en inglés ("Approved", "Entertainment"...); se pasan a español aquí.
  const ESTADO_EN = { approved: "aprobada", declined: "rechazada", rejected: "rechazada", pending: "pendiente", reversed: "reversada", refunded: "reversada" };
  const CATEGORIA_EN = {
    entertainment: "Entretenimiento", services: "Servicios", food: "Comida", purchase: "Compras", purchases: "Compras", withdrawal: "Retiro",
    deposit: "Abono", transfer: "Transferencia", transport: "Transporte", travel: "Viajes", health: "Salud", shopping: "Compras", cash: "Efectivo",
    groceries: "Supermercado", restaurants: "Restaurantes", subscriptions: "Suscripciones", payment: "Pago", income: "Ingresos",
  };
  const TIPO_EN = { purchase: "Compra", withdrawal: "Retiro", deposit: "Abono", transfer: "Transferencia", payment: "Pago", compra: "Compra", retiro: "Retiro en cajero", deposito: "Abono recibido", pago: "Pago", transferencia: "Transferencia" };
  const ICONO_DE = [
    [/supermerc|restaur|comida|food|grocer|caf[eé]/, "comida"], [/compra|purchase|shopping|tienda|retail/, "compras"],
    [/transporte|taxi|transport|uber|gasolina/, "transporte"], [/entreten|suscrip|stream|cine|entertain|subscri/, "entretenimiento"],
    [/servicio|service|energ|agua|luz|internet/, "servicios"], [/salud|farmacia|health|clinic/, "salud"],
    [/efectivo|retiro|cajero|withdraw|cash/, "efectivo"], [/transfer/, "transferencia"], [/pago|payment/, "pago"],
    [/ingreso|deposit|abono|n[oó]mina|income/, "deposito"], [/viaje|hotel|travel|vuelo/, "viajes"],
  ];
  const clave = (v) => minuscula(v).trim();

  // Normaliza un movimiento: prefiere los campos en español del backend y rellena lo que falte.
  function norm(m) {
    if (m.__n) return m;
    const ek = clave(m.estado);
    m.estado = ESTADO_EN[ek] || ek.replace(/\s+/g, "_");
    const cat = String(m.categoria || "");
    m.categoria_es = m.categoria_texto || CATEGORIA_EN[clave(cat)] || cat;
    m.tipo_es = m.tipo_texto || TIPO_EN[clave(m.tipo)] || String(m.tipo || "");
    m.estado_es = m.estado_texto || (ESTADOS[m.estado] ? ESTADOS[m.estado][0] : m.estado);
    m.canal_es = m.canal_texto || String(m.canal || "");
    const texto = clave(cat + " " + m.tipo);
    m.sentido = m.sentido || (/deposit|abono|ingreso|income|nomina|reembolso|refund/.test(texto) ? "abono" : "cargo");
    let icono = m.icono;
    if (!icono || !ICONOS[icono]) {
      icono = "otro";
      for (const [re, slug] of ICONO_DE) if (re.test(texto)) { icono = slug; break; }
    }
    m.icono = icono;
    m.__n = true;
    return m;
  }
  const esAbono = (m) => m.sentido === "abono";
  function textoMonto(m) {
    return (esAbono(m) ? "+" : "−") + limpio(String(m.monto).replace(/^[+-]/, "")) + " " + String(m.moneda || "");
  }
  function chip(texto, tono, clase) {
    return h("span", { clase: "bn-insignia bn-" + (tono || "neutro") + (clase ? " " + clase : ""), texto });
  }
  function insignia(estado) {
    const [texto, tono] = ESTADOS[estado] || [String(estado || "").replace(/_/g, " "), "neutro"];
    return chip(T(texto), tono);
  }

  // Personas de demostración: nombres ficticios por índice, sin relación con personas reales.
  const NOMBRES = ["Valentina", "Mateo", "Sofía", "Santiago", "Luciana", "Andrés"];
  const PAISES = { MX: "México", CO: "Colombia", AR: "Argentina", BR: "Brasil", US: "Estados Unidos", CL: "Chile", PE: "Perú", UY: "Uruguay", ES: "España" };
  const indiceDe = (c) => {
    if (c && typeof c.indice === "number") return c.indice;
    const n = /(\d+)/.exec((c && c.alias) || "");
    return n ? Number(n[1]) - 1 : 0;
  };
  const nombreDe = (c) => (c && c.nombre) || NOMBRES[indiceDe(c) % NOMBRES.length];
  const iniciales = (n) => String(n).trim().split(/\s+/).slice(0, 2).map((p) => p.charAt(0)).join("").toUpperCase();
  const pais = (c) => T(PAISES[c] || c || "");

  // Iconos en línea (SVG de trazo, sin dependencias) ------------------------------------------------------------

  const SVGNS = "http://www.w3.org/2000/svg";
  const ICONOS = {
    compras: ["M6 8h12l1 12H5L6 8z", "M9 8a3 3 0 0 1 6 0"],
    comida: ["M7 3v7", "M4.5 3v4.5a2.5 2.5 0 0 0 5 0V3", "M7 11v10", "M17 3c-2.2 1.4-3 3.8-3 6.5h3V21"],
    transporte: ["M5 17V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v9", "M5 17h14", "M7 17v2.5", "M17 17v2.5", "M8 12h.01", "M16 12h.01"],
    entretenimiento: ["M4 5h16v14H4z", "M10 9l5 3-5 3V9z"],
    servicios: ["M13 2 5 14h6l-1 8 8-12h-6l1-8z"],
    salud: ["M9 3h6v6h6v6h-6v6H9v-6H3V9h6V3z"],
    efectivo: ["M3 7h18v10H3z", "M12 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z", "M6.5 10v.01", "M17.5 14v.01"],
    transferencia: ["M4 8h15", "M15 4l4 4-4 4", "M20 16H5", "M9 12l-4 4 4 4"],
    pago: ["M3 6h18v12H3z", "M3 10h18", "M7 15h3"],
    deposito: ["M12 4v11", "M7 10.5l5 5 5-5", "M4 20h16"],
    viajes: ["M21 3 3 10l7 3 3 7 8-17z", "M10 13l11-10"],
    otro: ["M5 12h.01", "M12 12h.01", "M19 12h.01"],
    persona: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M4.5 20a7.5 7.5 0 0 1 15 0"],
    alerta: ["M12 3 2.5 20h19L12 3z", "M12 10v4", "M12 17.2v.01"],
    candado: ["M6 11h12v9H6z", "M8.5 11V8a3.5 3.5 0 0 1 7 0v3"],
    reclamos: ["M6 3h9l4 4v14H6z", "M14 3v5h5", "M9 13h7", "M9 17h5"],
    chat: ["M4 5h16v11H9l-5 4V5z"],
    cuenta: ["M3 10 12 4l9 6", "M5 10v8", "M10 10v8", "M14 10v8", "M19 10v8", "M3 20h18"],
    cerrar: ["M6 6l12 12", "M18 6 6 18"],
    enviar: ["M12 19V6", "M6 12l6-6 6 6"],
    buscar: ["M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z", "M15.5 15.5 20 20"],
    escudo: ["M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3z", "M9 12l2 2 4-4"],
    mundo: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M3 12h18", "M12 3c2.6 2.6 3.6 5.6 3.6 9S14.6 18.4 12 21c-2.6-2.6-3.6-5.6-3.6-9S9.4 5.6 12 3z"],
    chip: ["M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z", "M3 11h18", "M9 5v14"],
  };
  function icono(slug, clase) {
    const s = document.createElementNS(SVGNS, "svg");
    s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", "none");
    s.setAttribute("stroke", "currentColor");
    s.setAttribute("stroke-width", "1.8");
    s.setAttribute("stroke-linecap", "round");
    s.setAttribute("stroke-linejoin", "round");
    s.setAttribute("aria-hidden", "true");
    s.setAttribute("focusable", "false");
    if (clase) s.setAttribute("class", clase);
    (ICONOS[slug] || ICONOS.otro).forEach((d) => {
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("d", d);
      s.appendChild(p);
    });
    return s;
  }
  const avatar = (nombre, clase) => h("span", { clase: "bn-avatar " + (clase || ""), "aria-hidden": "true", texto: iniciales(nombre) });
  const IC = (slug) => icono(slug, "bn-ico");

  // Piezas comunes ---------------------------------------------------------------------------------------------

  function anunciar(texto) {
    const n = $("anuncio");
    if (!n) return;
    n.textContent = "";
    window.setTimeout(() => { n.textContent = texto; }, 50);
  }
  let temporizadorAviso = null;
  function aviso(texto) {
    anunciar(texto);
    const t = $("toast");
    if (!t) return;
    t.textContent = texto;
    t.classList.remove("oculto");
    window.clearTimeout(temporizadorAviso);
    temporizadorAviso = window.setTimeout(() => t.classList.add("oculto"), 6000);
  }
  function esqueleto(clase, n) {
    return Array.from({ length: n }, () => h("div", { clase: "bn-esq " + clase, "aria-hidden": "true" }));
  }
  function estadoVacio(titulo, texto, accion) {
    return h("div", { clase: "bn-vacio" }, h("h3", { texto: titulo }), texto ? h("p", { texto }) : null, accion || null);
  }
  function estadoError(mensaje, reintentar) {
    const b = h("button", { type: "button", texto: T("Intentar de nuevo") });
    b.addEventListener("click", reintentar);
    return h("div", { clase: "bn-error", role: "alert" }, h("h3", { texto: T("No pudimos cargar esta información") }), h("p", { texto: mensaje }), b);
  }
  function mensajeDeError(e) {
    if (e && e.status === 401) return T("Su sesión venció. Vuelva a ingresar para continuar.");
    if (e && (e.status === 404 || e.status === 0 || e.status === 501 || e.status === 503)) {
      return T("El servicio de la banca en línea no está disponible en este momento. En la demostración local puede usar la vista de ejemplo.");
    }
    return T("Ocurrió un problema. Puede intentarlo de nuevo en unos minutos.");
  }

  // Con la sesión vencida no hay nada que mostrar: se limpia y se vuelve al ingreso con un aviso.
  function sesionVencida(e) {
    if (!e || e.status !== 401) return false;
    salir();
    guardar.escribir("banca_aviso", T("Su sesión venció. Vuelva a ingresar para continuar."));
    window.location.href = "/banca/index.html" + (MOCK ? "?demo=local" : "");
    return true;
  }

  function cabeceraSesion() {
    const s = sesion();
    const zona = $("zona-sesion");
    if (!zona) return;
    zona.textContent = "";
    if (!s) return;
    const nombre = nombreDe(s.cliente);
    const b = h("button", { type: "button", clase: "bn-enlace", texto: T("Salir") });
    b.addEventListener("click", () => { salir(); window.location.href = "/banca/index.html"; });
    zona.append(
      h("span", { clase: "bn-segura" }, IC("candado"), h("span", { texto: T("Sesión segura") })),
      h("span", { clase: "bn-quien", title: s.cliente.alias }, avatar(nombre), h("span", { clase: "bn-quien-nombre", texto: nombre })),
      b);
  }

  // Abre el widget ya dentro de la conversación de un reclamo.
  function abrirAsistente(conversacion, contexto) {
    if (window.BancaWidget) window.BancaWidget.abrir({ conversacion, contexto });
  }
  function hablarConPersona() {
    if (window.BancaWidget) window.BancaWidget.abrir({ persona: true });
  }
  const urlBanca = (ruta) => ruta + (MOCK ? "?demo=local" : "");

  // Ingreso ----------------------------------------------------------------------------------------------------

  async function pintarIngreso() {
    const cont = $("ingreso-cuerpo");
    // El selector de idioma vive dentro de la tarjeta de ingreso mientras no hay sesión.
    const sitioIdioma = $("ingreso-idioma");
    const selIdioma = $("selector-idioma");
    if (sitioIdioma && selIdioma && !sitioIdioma.contains(selIdioma)) sitioIdioma.append(selIdioma);
    cont.textContent = "";
    cont.append(...esqueleto("bn-esq-linea", 3));
    let lista;
    try { lista = await llamar("/api/banca/clientes-demo"); } catch (e) {
      cont.textContent = "";
      cont.append(estadoError(mensajeDeError(e), pintarIngreso));
      return;
    }
    cont.textContent = "";
    const tarjetas = lista.map((c, i) => {
      const nombre = nombreDe(c);
      const n = typeof c.productos === "number" ? c.productos : (typeof c.num_productos === "number" ? c.num_productos : null);
      const detalle = pais(c.pais) + (n ? " · " + T(n === 1 ? "{n} producto" : "{n} productos", { n }) : "");
      const radio = h("input", { type: "radio", name: "cliente", value: String(c.indice), id: "cliente-" + c.indice, checked: i === 0 });
      return h("label", { clase: "bn-persona", for: "cliente-" + c.indice },
        radio,
        h("span", { clase: "bn-persona-cuerpo" },
          avatar(nombre, "bn-avatar-g"),
          h("span", { clase: "bn-persona-txt" }, h("span", { clase: "bn-persona-nombre", texto: nombre }), h("span", { clase: "bn-persona-meta", texto: detalle })),
          h("span", { clase: "bn-persona-marca", "aria-hidden": "true" })));
    });
    const btn = h("button", { type: "submit", clase: "primario bn-grande", texto: T("Ingresar a la demostración") });
    const aviso = guardar.leer("banca_aviso") || "";
    guardar.borrar("banca_aviso");
    const err = h("p", { id: "ingreso-error", clase: "bn-msg-error", role: "alert", texto: aviso });
    const form = h("form", { id: "form-ingreso" },
      h("fieldset", { clase: "bn-personas" }, h("legend", { texto: T("Cliente de demostración") }), h("div", { clase: "bn-personas-lista" }, tarjetas)),
      btn, err,
      h("p", { clase: "nota bn-ficticio", texto: T("Personas ficticias. No se usa ningún dato real.") }));
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      btn.disabled = true;
      err.textContent = "";
      const elegido = form.querySelector("input[name=cliente]:checked");
      const indice = Number(elegido ? elegido.value : 0);
      try {
        const r = await llamar("/api/banca/ingresar", { metodo: "POST", cuerpo: { indice, registro: registro() } });
        const base = lista.find((c) => c.indice === indice) || {};
        guardarSesion({ sesion: r.sesion, conversacion: r.conversacion, cliente: Object.assign({ indice, nombre: base.nombre }, r.cliente) });
        window.location.href = "/banca/index.html" + (MOCK ? "?demo=local" : "");
      } catch (e) {
        err.textContent = mensajeDeError(e);
        btn.disabled = false;
      }
    });
    cont.append(form);
  }

  // Tablero ----------------------------------------------------------------------------------------------------

  const tablero = { productos: [], movimientos: [], siguiente: null, producto: "", estado: "", texto: "", resumen: null };

  const mesDe = (iso) => { const d = new Date(String(iso) + "T12:00:00"); return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString(locale(), { month: "long" }); };

  // Resumen: usa el bloque del backend si existe y, si no, lo calcula con lo que ya se cargó.
  function sumar(lista, moneda) {
    return lista.filter((p) => p.moneda === moneda).reduce((a, p) => a + leerMonto(p.saldo), 0);
  }
  function datosResumen() {
    const r = tablero.resumen || {};
    const b = r.panorama || r.totales || r.resumen || {};
    const cuentas = tablero.productos.filter((p) => esCuenta(p) && p.saldo !== null && p.saldo !== undefined);
    const monedaPrincipal = (r.cliente && r.cliente.moneda) || (cuentas[0] && cuentas[0].moneda) || "";
    let saldo = null;
    const bs = b.saldo_disponible;
    if (bs && typeof bs === "object" && !Array.isArray(bs)) {
      const m = bs[monedaPrincipal] !== undefined ? monedaPrincipal : Object.keys(bs)[0];
      if (m) saldo = { monto: String(bs[m]), moneda: m };
    } else if (Array.isArray(bs) && bs.length) {
      const x = bs.find((e) => e.moneda === monedaPrincipal) || bs[0];
      saldo = { monto: String(x.saldo !== undefined ? x.saldo : x.monto), moneda: x.moneda };
    } else if (bs !== undefined && bs !== null) {
      saldo = { monto: String(bs), moneda: monedaPrincipal };
    } else if (cuentas.length) {
      saldo = { monto: escribirMonto(sumar(cuentas, monedaPrincipal)), moneda: monedaPrincipal };
    }
    const tarjetas = tablero.productos.filter(esTarjeta).map((p) => p.final);
    const cargos = tablero.movimientos.filter((m) => !esAbono(m) && m.estado === "aprobada" && tarjetas.includes(m.tarjeta_final));
    const ultimo = cargos.map((m) => m.fecha).sort().pop() || "";
    const mes = ultimo ? ultimo.slice(0, 7) : "";
    const delMes = cargos.filter((m) => m.fecha.slice(0, 7) === mes);
    let gasto = null;
    const bg = b.gasto_mes_tarjetas !== undefined ? b.gasto_mes_tarjetas : b.gasto_tarjetas_mes;
    if (Array.isArray(bg) && bg.length) {
      const x = bg.find((e) => e.moneda === monedaPrincipal) || bg[0];
      gasto = { monto: String(x.monto), moneda: x.moneda, mes: T("este mes") };
    } else if (bg !== undefined && bg !== null && !Array.isArray(bg)) gasto = { monto: String(bg), moneda: monedaPrincipal, mes: T("este mes") };
    else if (tablero.movimientos.length) gasto = { monto: escribirMonto(delMes.reduce((a, m) => a + leerMonto(m.monto), 0)), moneda: (delMes[0] || {}).moneda || monedaPrincipal, mes: mes ? mesDe(ultimo) : "" };
    const abiertos = b.reclamos_abiertos !== undefined && b.reclamos_abiertos !== null ? Number(b.reclamos_abiertos) : tablero.movimientos.filter((m) => m.caso_ref).length;
    return { saldo, gasto, abiertos };
  }

  function pintarResumen() {
    const cont = $("resumen");
    if (!cont) return;
    const d = datosResumen();
    cont.textContent = "";
    const kpi = (titulo, valor, pie, extra) => h("div", { clase: "bn-kpi " + (extra || "") },
      h("p", { clase: "bn-kpi-titulo", texto: titulo }), valor, pie ? h("p", { clase: "bn-kpi-pie", texto: pie }) : null);
    cont.append(
      kpi(T("Saldo disponible"), d.saldo ? cifra(d.saldo.monto, d.saldo.moneda, "bn-kpi-valor") : h("span", { clase: "bn-kpi-valor", texto: "—" }),
        T("Suma de sus cuentas"), "bn-kpi-principal"),
      kpi(d.gasto && d.gasto.mes && d.gasto.mes !== T("este mes") ? T("Gasto con tarjetas en {mes}", { mes: d.gasto.mes }) : T("Gasto con tarjetas este mes"),
        d.gasto ? cifra(d.gasto.monto, d.gasto.moneda, "bn-kpi-valor") : h("span", { clase: "bn-kpi-valor", texto: "—" }), T("Compras aprobadas")),
      kpi(T("Reclamos abiertos"), h("span", { clase: "bn-kpi-valor bn-num", texto: String(d.abiertos) }),
        d.abiertos ? T("Ver cómo van") : T("Ninguno por ahora")));
    const ult = cont.lastElementChild;
    if (d.abiertos) {
      const a = h("a", { clase: "bn-kpi-enlace", href: urlBanca("/banca/reclamos.html"), texto: T("Ver mis reclamos") });
      ult.append(a);
    }
  }

  // Lo que se puede hacer con cada producto, en el propio producto: todo son funciones que ya existen.
  function verMovimientosDe(p) {
    const sel = $("f-producto");
    sel.value = p.producto_ref;
    tablero.producto = p.producto_ref;
    cargarMovimientos(false);
    $("t-mov").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }
  function accionProducto(ic, texto, fn, apagado) {
    const b = h("button", { type: "button", clase: "bn-prod-accion" }, IC(ic), h("span", { texto: T(texto) }));
    if (apagado) b.disabled = true; else b.addEventListener("click", fn);
    return b;
  }
  function accionesDe(p, bloq) {
    const lista = [accionProducto("buscar", "Movimientos", () => verMovimientosDe(p))];
    if (esTarjeta(p)) {
      lista.push(accionProducto("candado", bloq ? "Bloqueada" : "Bloquear", () => confirmarBloqueo([p], null), bloq));
      lista.push(accionProducto("alerta", "Reportar un cargo", () => { verMovimientosDe(p); reportarCargo(); }));
    } else {
      lista.push(accionProducto("chat", "Preguntar a Lía", () => { if (window.BancaWidget) window.BancaWidget.abrir({}); }));
    }
    return h("div", { clase: "bn-prod-acciones", role: "group", "aria-label": T("Acciones de este producto") }, lista);
  }

  function tarjetaProducto(p) {
    const bloq = p.estado === "bloqueada";
    if (esTarjeta(p)) {
      const barra = [];
      let uso = null;
      if (p.saldo !== null && p.saldo !== undefined && p.limite) {
        const pct = Math.min(100, Math.max(0, (leerMonto(p.saldo) / leerMonto(p.limite)) * 100));
        const rel = h("span", { clase: "bn-barra-relleno" });
        rel.style.width = pct.toFixed(0) + "%";
        barra.push(h("div", { clase: "bn-barra", role: "img", "aria-label": T("Usa el {n}% de su cupo", { n: pct.toFixed(0) }) }, rel));
        uso = h("div", { clase: "bn-tarjeta-cifras" },
          h("div", {}, h("p", { clase: "bn-tarjeta-rot", texto: T(esCredito(p) ? "Saldo utilizado" : "Saldo") }), cifra(p.saldo, p.moneda, "bn-tarjeta-cifra")),
          h("div", {}, h("p", { clase: "bn-tarjeta-rot", texto: T("Cupo") }), cifra(p.limite, p.moneda, "bn-tarjeta-cifra")));
      } else if (p.saldo !== null && p.saldo !== undefined) {
        uso = h("div", { clase: "bn-tarjeta-cifras" }, h("div", {}, h("p", { clase: "bn-tarjeta-rot", texto: T("Saldo") }), cifra(p.saldo, p.moneda, "bn-tarjeta-cifra")));
      } else {
        uso = h("p", { clase: "bn-tarjeta-nota", texto: T(bloq ? "Bloqueada. No se puede usar." : "Se paga con el saldo de su cuenta.") });
      }
      return h("li", { clase: "bn-producto bn-plastico" + (bloq ? " bn-bloqueado" : "") },
        h("div", { clase: "bn-plastico-cab" },
          h("div", {}, h("p", { clase: "bn-plastico-marca", texto: "LATAM Bank" }), h("h3", { texto: p.etiqueta })),
          h("span", { clase: "bn-plastico-estado " + (bloq ? "bn-mal" : "bn-ok"), texto: T(bloq ? "Bloqueada" : "Activa") })),
        h("div", { clase: "bn-plastico-medio" }, icono("chip", "bn-plastico-chip"), h("p", { clase: "bn-final bn-num", "aria-label": T("Tarjeta terminada en {n}", { n: String(p.final).slice(-4) }), texto: enmascarar(p.final) })),
        uso, barra, accionesDe(p, bloq));
    }
    return h("li", { clase: "bn-producto bn-cuenta-tile" + (bloq ? " bn-bloqueado" : "") },
      h("div", { clase: "bn-tile-cab" },
        h("span", { clase: "bn-ico-caja" }, IC("cuenta")),
        h("div", { clase: "bn-tile-txt" }, h("h3", { texto: p.etiqueta }), h("p", { clase: "bn-final bn-num", texto: enmascarar(p.final) })),
        bloq ? insignia(p.estado) : null),
      p.saldo !== null && p.saldo !== undefined
        ? h("div", {}, h("p", { clase: "bn-tarjeta-rot", texto: T("Saldo disponible") }), cifra(p.saldo, p.moneda, "bn-tile-cifra"))
        : h("p", { clase: "nota", texto: T("Sin saldo para mostrar.") }),
      accionesDe(p, bloq));
  }

  function pintarProductos() {
    const cont = $("productos");
    cont.textContent = "";
    if (!tablero.productos.length) { cont.append(estadoVacio(T("No tiene productos en esta demostración"), "", null)); return; }
    const orden = [...tablero.productos].sort((a, b) => Number(esTarjeta(b)) - Number(esTarjeta(a)));
    cont.append(...orden.map(tarjetaProducto));
  }

  const SEGMENTOS = [["", "Todos"], ["aprobada", "Aprobados"], ["pendiente", "Pendientes"], ["rechazada", "Rechazados"], ["reclamo", "En reclamo"]];
  function pintarSegmentos() {
    const cont = $("f-estado");
    cont.textContent = "";
    SEGMENTOS.forEach(([valor, texto]) => {
      const b = h("button", { type: "button", clase: "bn-segmento", "data-estado": valor, "aria-pressed": String(tablero.estado === valor), texto: T(texto) });
      b.addEventListener("click", () => {
        tablero.estado = valor;
        cont.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        pintarMovimientos();
      });
      cont.append(b);
    });
  }

  function filtrados() {
    const t = minuscula(tablero.texto).trim();
    return tablero.movimientos.filter((m) =>
      (!tablero.estado || (tablero.estado === "reclamo" ? Boolean(m.caso_ref) : m.estado === tablero.estado)) &&
      (!t || [m.descripcion, m.categoria_es, m.categoria, m.monto, m.tipo_es].some((x) => minuscula(x).includes(t))));
  }

  const RAPIDAS = [
    ["alerta", "Reportar un cargo", () => reportarCargo()],
    ["candado", "Bloquear tarjeta", () => bloquearDesdeInicio()],
    ["reclamos", "Mis reclamos", null],
    ["chat", "Preguntar a Lía", () => { if (window.BancaWidget) window.BancaWidget.abrir({}); }],
    ["persona", "Hablar con una persona", () => hablarConPersona()],
  ];
  function pintarRapidas() {
    const cont = $("rapidas");
    cont.textContent = "";
    RAPIDAS.forEach(([ic, texto, fn]) => {
      const cuerpo = [h("span", { clase: "bn-ico-caja" }, IC(ic)), h("span", { texto: T(texto) })];
      let el;
      if (fn) { el = h("button", { type: "button", clase: "bn-rapida" }, cuerpo); el.addEventListener("click", fn); }
      else el = h("a", { clase: "bn-rapida", href: urlBanca("/banca/reclamos.html") }, cuerpo);
      cont.append(h("li", {}, el));
    });
  }
  function reportarCargo() {
    $("pista-reporte").classList.remove("oculto");
    $("t-mov").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    const primera = document.querySelector("#movimientos .bn-fila");
    if (primera) primera.focus({ preventScroll: true });
    anunciar(T("Toque el cargo que no reconoce y elija No reconozco este cargo."));
  }
  function bloquearDesdeInicio() {
    const activas = tablero.productos.filter((p) => esTarjeta(p) && p.estado !== "bloqueada");
    if (!activas.length) { aviso(T("No tiene tarjetas activas para bloquear.")); return; }
    confirmarBloqueo(activas, null);
  }

  function marcasMovimiento(m, sinEstado) {
    const marcas = [];
    if (!sinEstado && (m.estado === "rechazada" || m.estado === "pendiente" || m.estado === "reversada")) marcas.push(chip(T(m.estado_es), (ESTADOS[m.estado] || [])[1]));
    if (m.caso_ref) marcas.push(chip(T("En reclamo"), "aviso"));
    if (m.es_extranjera) marcas.push(chip(T("Exterior"), "neutro"));
    return marcas;
  }

  function filaMovimiento(m) {
    const abono = esAbono(m);
    const a11y = T("{desc}, {monto}, {estado}. Ver detalle", {
      desc: m.descripcion,
      monto: (abono ? T("abono de ") : T("cargo de ")) + dinero(String(m.monto).replace(/^[+-]/, ""), m.moneda),
      estado: m.estado_es,
    });
    const b = h("button", { type: "button", clase: "bn-fila" + (m.estado === "rechazada" ? " bn-fila-rechazada" : ""), "aria-label": a11y },
      h("span", { clase: "bn-ico-caja " + (abono ? "bn-ico-abono" : "") }, IC(m.icono)),
      h("span", { clase: "bn-fila-txt" },
        h("span", { clase: "bn-fila-desc", texto: m.descripcion }),
        h("span", { clase: "bn-fila-meta", texto: `${T(m.categoria_es || m.tipo_es)} · ${m.hora} · ${enmascarar(m.tarjeta_final)}` }),
        (() => { const x = marcasMovimiento(m); return x.length ? h("span", { clase: "bn-fila-marcas" }, x) : null; })()),
      h("span", { clase: "bn-monto bn-num " + (abono ? "bn-abono" : "") },
        h("span", { clase: "bn-monto-num", texto: (abono ? "+" : "−") + limpio(String(m.monto).replace(/^[+-]/, "")) }),
        h("small", { texto: String(m.moneda || "") })));
    b.addEventListener("click", () => abrirDetalle(m, b));
    return h("li", {}, b);
  }

  function pintarMovimientos() {
    const cont = $("movimientos");
    cont.textContent = "";
    const lista = filtrados();
    $("cuenta-resultados").textContent = T(lista.length === 1 ? "{n} movimiento" : "{n} movimientos", { n: lista.length });
    if (!lista.length) {
      const hay = tablero.movimientos.length > 0;
      cont.append(estadoVacio(T(hay ? "No hay movimientos con esos filtros" : "Todavía no hay movimientos"),
        T(hay ? "Pruebe con otra búsqueda o quite algún filtro." : "Cuando haga una compra la verá aquí."), null));
      return;
    }
    const grupos = new Map();
    lista.forEach((m) => { if (!grupos.has(m.fecha)) grupos.set(m.fecha, []); grupos.get(m.fecha).push(m); });
    const ul = h("ul", { clase: "bn-lista" });
    for (const [fecha, filas] of grupos) {
      ul.append(h("li", { clase: "bn-dia" }, h("h3", { texto: fechaLarga(fecha) })), ...filas.map(filaMovimiento));
    }
    cont.append(ul);
  }

  async function cargarMovimientos(mas) {
    const cont = $("movimientos");
    if (!mas) { cont.textContent = ""; cont.append(...esqueleto("bn-esq-fila", 5)); tablero.movimientos = []; }
    const q = new URLSearchParams({ limite: "50" });
    if (tablero.producto) q.set("producto_ref", tablero.producto);
    if (mas && tablero.siguiente) q.set("antes_de", tablero.siguiente);
    try {
      const d = await llamar("/api/banca/movimientos?" + q.toString());
      tablero.movimientos = tablero.movimientos.concat((d.movimientos || []).map(norm));
      tablero.siguiente = d.siguiente || null;
      pintarMovimientos();
      pintarResumen();
      $("mas").classList.toggle("oculto", !tablero.siguiente);
    } catch (e) {
      if (sesionVencida(e)) return;
      cont.textContent = "";
      cont.append(estadoError(mensajeDeError(e), () => cargarMovimientos(false)));
    }
  }

  async function cargarResumen() {
    const cont = $("productos");
    cont.textContent = "";
    cont.append(...esqueleto("bn-esq-tarjeta", 3));
    const kp = $("resumen");
    kp.textContent = "";
    kp.append(...esqueleto("bn-esq-kpi", 3));
    try {
      const r = await llamar("/api/banca/resumen");
      tablero.resumen = r;
      tablero.productos = r.productos || [];
      const s = sesion();
      const cliente = Object.assign({}, (s && s.cliente) || {}, r.cliente || {});
      $("saludo").textContent = T("Hola, {nombre}", { nombre: nombreDe(cliente) });
      pintarProductos();
      pintarResumen();
      const sel = $("f-producto");
      sel.textContent = "";
      sel.append(h("option", { value: "", texto: T("Todos los productos") }));
      tablero.productos.forEach((p) => sel.append(h("option", { value: p.producto_ref, texto: `${p.etiqueta} ${enmascarar(p.final)}` })));
    } catch (e) {
      cont.textContent = "";
      kp.textContent = "";
      cont.append(estadoError(mensajeDeError(e), cargarResumen));
      sesionVencida(e);
    }
  }

  // Detalle y acciones ----------------------------------------------------------------------------------------

  let disparador = null;

  function filaDetalle(k, v) { return h("div", {}, h("dt", { texto: k }), h("dd", { clase: "bn-num", texto: v })); }

  // Una explicación breve y serena, sin prometer lo que el banco no decide aquí.
  function explicacion(m, propio) {
    const lugar = m.es_extranjera ? T("Se hizo desde {pais}, fuera de su país.", { pais: pais(m.pais) }) : "";
    if (m.estado === "rechazada") return T("Este intento fue rechazado, por eso no se descontó de su dinero. Si no lo reconoce, puede reportarlo igual.") + " " + lugar;
    if (m.estado === "pendiente") return T("Este cargo todavía no es definitivo. Puede cambiar de monto o caer cuando el comercio lo confirme.") + " " + lugar;
    if (esAbono(m)) return T("Este dinero ya está en su cuenta.");
    if (m.estado === "reversada") return T("Este cargo fue reversado y el dinero volvió a su producto.");
    return (m.es_extranjera ? lugar + " " : "") + T("Si reconoce este cargo, no tiene que hacer nada. Si no, puede reportarlo y lo revisamos.");
  }

  function abrirDetalle(m, origen) {
    disparador = origen;
    const dlg = $("detalle");
    const cuerpo = $("detalle-cuerpo");
    cuerpo.textContent = "";
    const abono = esAbono(m);
    const producto = tablero.productos.find((p) => p.final === m.tarjeta_final);
    $("detalle-titulo").textContent = m.descripcion;
    const marcas = marcasMovimiento(m, true);
    if (!m.es_extranjera) marcas.push(chip(T("País: {pais}", { pais: pais(m.pais) }), "neutro"));
    cuerpo.append(
      h("div", { clase: "bn-hero" },
        h("span", { clase: "bn-ico-caja bn-ico-g " + (abono ? "bn-ico-abono" : "") }, IC(m.icono)),
        h("p", { clase: "bn-hero-comercio", texto: m.descripcion }),
        h("p", { clase: "bn-detalle-monto bn-num " + (abono ? "bn-abono" : ""), "aria-label": textoMonto(m) },
          h("span", { texto: (abono ? "+" : "−") + limpio(String(m.monto).replace(/^[+-]/, "")) }), h("small", { texto: " " + String(m.moneda || "") })),
        h("p", { clase: "bn-fila-marcas bn-centro" }, chip(T(m.estado_es), (ESTADOS[m.estado] || [])[1]), marcas)),
      h("p", { clase: "bn-explica", texto: explicacion(m, producto).trim() }),
      h("dl", { clase: "bn-datos" },
        filaDetalle(T("Fecha"), fechaCorta(m.fecha)), filaDetalle(T("Hora"), m.hora),
        filaDetalle(T(producto && esTarjeta(producto) ? "Tarjeta" : "Producto"), enmascarar(m.tarjeta_final)), filaDetalle(T("Categoría"), T(m.categoria_es || m.tipo_es)),
        filaDetalle(T("Canal"), T(m.canal_es))));
    const res = h("p", { id: "detalle-resultado", clase: "bn-resultado", role: "status" });
    const acciones = h("div", { clase: "bn-acciones-detalle" });
    if (m.caso_ref) {
      cuerpo.append(h("div", { clase: "bn-callout" }, IC("reclamos"),
        h("div", {}, h("p", { clase: "bn-callout-t", texto: T("Ya tiene un reclamo por este cargo") }),
          h("a", { href: urlBanca("/banca/reclamos.html"), texto: T("Ver mi reclamo") }))));
    } else if (m.reclamable) {
      const b = h("button", { type: "button", clase: "primario bn-grande", texto: T("No reconozco este cargo") });
      b.addEventListener("click", () => reclamar(m, b, res));
      acciones.append(b);
    } else {
      acciones.append(h("p", { clase: "nota", texto: T("Este movimiento no admite reclamos.") }));
    }
    if (producto && esTarjeta(producto) && producto.estado !== "bloqueada") {
      const b = h("button", { type: "button", texto: T("Bloquear tarjeta") });
      b.addEventListener("click", () => confirmarBloqueo([producto], res));
      acciones.append(b);
    } else if (producto && esTarjeta(producto)) {
      acciones.append(h("p", { clase: "nota", texto: T("La tarjeta {t} está bloqueada.", { t: enmascarar(producto.final) }) }));
    }
    cuerpo.append(acciones, res);
    dlg.showModal();
    $("detalle-cerrar").focus();
  }

  async function reclamar(m, boton, res) {
    boton.disabled = true;
    res.textContent = T("Abriendo su reclamo...");
    try {
      const r = await llamar(`/api/banca/movimientos/${encodeURIComponent(m.tx_ref)}/reclamar`, { metodo: "POST", cuerpo: { registro: registro() } });
      m.caso_ref = m.caso_ref || "abierto";
      $("detalle").close();
      pintarMovimientos();
      pintarResumen();
      abrirAsistente(r.conversacion, m);
    } catch (e) {
      boton.disabled = false;
      res.textContent = e.status === 409 ? T("Este cargo ya tiene un reclamo abierto.") : mensajeDeError(e);
    }
  }

  // Confirmación previa al bloqueo: con varias tarjetas se elige cuál; Cancelar no cambia nada.
  function confirmarBloqueo(tarjetas, res) {
    const dlg = $("confirmar");
    const ops = $("confirmar-opciones");
    const si = $("confirmar-si");
    const no = $("confirmar-no");
    let elegida = tarjetas[0];
    const texto = (p) => T("Va a bloquear la tarjeta {t}. No podrá usarla para compras ni retiros hasta que se reponga. Si no quiere bloquearla, elija Cancelar y no se hará ningún cambio.", { t: `${p.etiqueta} ${enmascarar(p.final)}` });
    ops.querySelectorAll("label").forEach((x) => x.remove());
    ops.classList.toggle("oculto", tarjetas.length < 2);
    if (tarjetas.length > 1) {
      tarjetas.forEach((p, i) => {
        const r = h("input", { type: "radio", name: "tarjeta-bloq", value: p.producto_ref, checked: i === 0 });
        r.addEventListener("change", () => { elegida = p; $("confirmar-texto").textContent = texto(p); });
        ops.append(h("label", { clase: "bn-opcion" }, r, h("span", { texto: `${p.etiqueta} ${enmascarar(p.final)}` })));
      });
    }
    $("confirmar-texto").textContent = texto(elegida);
    si.disabled = false;
    si.onclick = async () => {
      si.disabled = true;
      const p = elegida;
      try {
        const r = await llamar(`/api/banca/tarjetas/${encodeURIComponent(p.producto_ref)}/bloqueo`, { metodo: "POST", cuerpo: { confirmo: true } });
        p.estado = "bloqueada";
        dlg.close();
        const t = r.ya_estaba ? T("La tarjeta {t} ya estaba bloqueada. No hicimos ningún cambio.", { t: enmascarar(p.final) }) : T("Bloqueamos la tarjeta {t}.", { t: enmascarar(p.final) });
        if (res) res.textContent = t;
        aviso(t);
        pintarProductos();
      } catch (e) {
        si.disabled = false;
        dlg.close();
        const t = e.status === 400 || e.status === 404
          ? T("No pudimos bloquear esta tarjeta desde aquí. Puede pedir ayuda a una persona desde el asistente.")
          : mensajeDeError(e);
        if (res) res.textContent = t;
        aviso(t);
      }
    };
    no.onclick = () => dlg.close();
    dlg.showModal();
    no.focus();
  }

  function iniciarTablero() {
    $("ingreso").classList.add("oculto");
    $("tablero").classList.remove("oculto");
    pintarRapidas();
    pintarSegmentos();
    cargarResumen();
    cargarMovimientos(false);
    $("f-producto").addEventListener("change", (ev) => { tablero.producto = ev.target.value; cargarMovimientos(false); });
    $("f-texto").addEventListener("input", (ev) => { tablero.texto = ev.target.value; pintarMovimientos(); });
    $("mas").addEventListener("click", () => cargarMovimientos(true));
    $("detalle-cerrar").addEventListener("click", () => $("detalle").close());
    $("detalle").addEventListener("close", () => { if (disparador && document.contains(disparador)) disparador.focus(); });
    // Se cierra el panel al pulsar el velo (fuera del contenido).
    ["detalle", "confirmar"].forEach((id) => $(id).addEventListener("click", (ev) => { if (ev.target === ev.currentTarget) ev.currentTarget.close(); }));
    // Revisión visual en modo local: ?abrir=t1 abre el detalle y ?asistente=1 abre el asistente.
    if (MOCK && params.get("abrir")) {
      const timer = window.setInterval(() => {
        const m = tablero.movimientos.find((x) => x.tx_ref === params.get("abrir"));
        if (m && tablero.productos.length) { window.clearInterval(timer); abrirDetalle(m, null); }
      }, 200);
    }
  }

  // Reclamos ---------------------------------------------------------------------------------------------------

  const ETAPAS = [["abierto", "Recibido"], ["en_revision", "En revisión"], ["resuelto", "Resuelto"]];
  function etapaDe(estado) { return estado === "cerrado" ? 2 : Math.max(0, ETAPAS.findIndex((e) => e[0] === estado)); }

  function plazoTexto(c) {
    if (!c.plazo) return T("Se lo informaremos pronto");
    const dias = Math.round((new Date(c.plazo + "T12:00:00") - new Date(hoyIso() + "T12:00:00")) / 86400000);
    const cierre = c.estado === "resuelto" || c.estado === "cerrado";
    let extra = "";
    if (!cierre) extra = dias > 1 ? " · " + T("quedan {n} días", { n: dias }) : dias === 1 ? " · " + T("queda 1 día") : dias === 0 ? " · " + T("vence hoy") : " · " + T("el plazo ya pasó");
    return fechaCorta(c.plazo) + extra;
  }

  function tarjetaReclamo(c) {
    const etapa = etapaDe(c.estado);
    const eventos = (c.historial || []).map((e) => h("li", {}, h("span", { clase: "bn-punto", "aria-hidden": "true" }),
      h("div", {}, h("p", { clase: "bn-evento", texto: T(e.evento) }), h("p", { clase: "nota", texto: fechaCorta(e.fecha) }))));
    const pasos = h("ol", { clase: "bn-pasos", "aria-label": T("Etapas del reclamo") },
      ETAPAS.map(([k, t], i) => h("li", { clase: "bn-paso" + (i < etapa ? " hecho" : "") + (i === etapa ? " actual" : ""), "aria-current": i === etapa ? "step" : null },
        h("span", { clase: "bn-paso-bola", "aria-hidden": "true", texto: i < etapa ? "✓" : String(i + 1) }), h("span", { texto: T(t) }))));
    const prov = c.credito_provisional;
    return h("li", { clase: "bn-reclamo" },
      h("div", { clase: "bn-reclamo-cab" },
        h("span", { clase: "bn-ico-caja" }, IC("reclamos")),
        h("div", { clase: "bn-reclamo-tit" }, h("h2", { texto: c.descripcion || T("Cargo reclamado") }), h("p", { clase: "nota", texto: T("Abierto el {fecha}", { fecha: fechaCorta(c.abierto_en) }) })),
        insignia(c.estado)),
      pasos,
      c.traspaso ? h("p", { clase: "bn-persona-aviso" }, IC("persona"), h("span", { texto: T("Una persona del equipo tiene su caso y le responderá en la conversación.") })) : null,
      h("dl", { clase: "bn-datos bn-datos-rec" },
        h("div", {}, h("dt", { texto: T("Monto reclamado") }), h("dd", {}, cifra(c.monto, c.moneda))),
        h("div", { clase: prov ? "bn-prov" : "" }, h("dt", { texto: T("Devolución provisional") }), h("dd", {}, prov ? cifra(prov, c.moneda) : T("Todavía no aplica"))),
        h("div", {}, h("dt", { texto: T("Plazo de respuesta") }), h("dd", { texto: plazoTexto(c) }))),
      h("h3", { texto: T("Historial") }),
      h("ol", { clase: "bn-linea", "aria-label": T("Historial del reclamo") }, eventos));
  }

  async function iniciarReclamos() {
    const cont = $("reclamos");
    const cargar = async () => {
      cont.textContent = "";
      cont.append(...esqueleto("bn-esq-tarjeta", 2));
      try {
        const lista = await llamar("/api/banca/reclamos");
        cont.textContent = "";
        if (!lista.length) {
          cont.append(estadoVacio(T("No tiene reclamos"), T("Si no reconoce un cargo, ábralo desde sus movimientos y le ayudamos."),
            h("a", { clase: "boton", href: urlBanca("/banca/index.html"), texto: T("Ver mis movimientos") })));
          return;
        }
        cont.append(...lista.map(tarjetaReclamo));
      } catch (e) {
        if (sesionVencida(e)) return;
        cont.textContent = "";
        cont.append(estadoError(mensajeDeError(e), cargar));
      }
    };
    await cargar();
  }

  // Arranque ---------------------------------------------------------------------------------------------------

  async function arrancar() {
    const pagina = document.body.dataset.pagina;
    // Revisión visual en modo local: ?cliente=1 entra sin pasar por el formulario.
    if (MOCK && !sesion() && params.get("cliente")) {
      const r = await llamar("/api/banca/ingresar", { metodo: "POST", cuerpo: { indice: Number(params.get("cliente")) - 1 } });
      guardarSesion({ sesion: r.sesion, conversacion: r.conversacion, cliente: r.cliente });
    }
    const s = sesion();
    cabeceraSesion();
    if (MOCK) $("modo-local") && $("modo-local").classList.remove("oculto");
    if (pagina === "inicio") {
      if (!s) { $("ingreso").classList.remove("oculto"); $("tablero").classList.add("oculto"); pintarIngreso(); } else iniciarTablero();
    } else if (pagina === "reclamos") {
      if (!s) { $("sin-sesion").classList.remove("oculto"); $("reclamos-zona").classList.add("oculto"); } else iniciarReclamos();
    }
  }

  window.Banca = { llamar, h, sesion, MOCK, BASE, guardar, ErrorApi, pausa, anunciar, fixture, estadoLocal, T, registro, icono, avatar, nombreDe, iniciales };
  arrancar();
})();
