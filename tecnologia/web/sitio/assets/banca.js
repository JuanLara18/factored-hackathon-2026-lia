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
      const moneda = { MX: "MXN", CO: "COP", AR: "ARS" }[c.pais] || "USD";
      return { sesion: "demo-local", cliente: { alias: c.alias, pais: c.pais, moneda, registro: registro() } };
    }
    if (camino === "/api/banca/resumen") {
      const r = await fixture("resumen");
      const s = sesion();
      if (s && s.cliente) r.cliente = s.cliente;
      r.productos.forEach((p) => { if (loc.bloqueadas.includes(p.producto_ref)) p.estado = "bloqueada"; });
      return r;
    }
    if (camino === "/api/banca/movimientos") {
      const d = await fixture("movimientos");
      const res = await fixture("resumen");
      const prod = res.productos.find((p) => p.producto_ref === q.get("producto_ref"));
      if (prod) d.movimientos = d.movimientos.filter((t) => t.tarjeta_final === prod.final);
      d.movimientos.forEach((t) => { if (loc.reclamadas[t.tx_ref]) t.caso_ref = loc.reclamadas[t.tx_ref]; });
      return d;
    }
    if ((m = camino.match(/^\/api\/banca\/movimientos\/([^/]+)\/reclamar$/))) {
      const d = await fixture("movimientos");
      const t = d.movimientos.find((x) => x.tx_ref === m[1]);
      if (!t) throw new ErrorApi(404);
      loc.reclamadas[t.tx_ref] = loc.reclamadas[t.tx_ref] || "c-" + t.tx_ref;
      loc.contexto = t;
      guardarLocal(loc);
      return { conversacion: "demo-" + t.tx_ref };
    }
    if ((m = camino.match(/^\/api\/banca\/movimientos\/([^/]+)$/))) {
      const d = await fixture("movimientos");
      const t = d.movimientos.find((x) => x.tx_ref === m[1]);
      if (!t) throw new ErrorApi(404);
      return t;
    }
    if (camino === "/api/banca/reclamos") {
      const lista = await fixture("reclamos");
      const d = await fixture("movimientos");
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

  function fechaLarga(iso) {
    const d = new Date(String(iso) + "T12:00:00");
    if (Number.isNaN(d.getTime())) return String(iso || "");
    return d.toLocaleDateString(locale(), { weekday: "long", day: "numeric", month: "long" });
  }
  function fechaCorta(iso) {
    const d = new Date(String(iso) + "T12:00:00");
    if (Number.isNaN(d.getTime())) return String(iso || "");
    return d.toLocaleDateString(locale(), { day: "numeric", month: "short", year: "numeric" });
  }
  const dinero = (monto, moneda) => (monto === null || monto === undefined ? "" : String(monto) + " " + String(moneda || ""));
  const enmascarar = (final) => "···· " + String(final || "").replace(/\D/g, "").slice(-4);
  const ESTADOS = {
    aprobada: ["Aprobada", "ok"], pendiente: ["Pendiente", "aviso"], rechazada: ["Rechazada", "mal"], reversada: ["Reversada", "neutro"],
    activa: ["Activa", "ok"], bloqueada: ["Bloqueada", "mal"],
    abierto: ["Abierto", "aviso"], en_revision: ["En revisión", "aviso"], resuelto: ["Resuelto", "ok"], cerrado: ["Cerrado", "neutro"],
  };
  function insignia(estado) {
    const [texto, tono] = ESTADOS[estado] || [String(estado || "").replace(/_/g, " "), "neutro"];
    return h("span", { clase: "bn-insignia bn-" + tono, texto: T(texto) });
  }
  // El backend manda el tipo como texto ("Tarjeta Crédito"), no como código: se normaliza antes de comparar.
  const minuscula = (t) => String(t || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const esTarjeta = (p) => /tarjeta|card/.test(minuscula(p.tipo) + " " + minuscula(p.etiqueta));

  // Piezas comunes ---------------------------------------------------------------------------------------------

  function anunciar(texto) {
    const n = $("anuncio");
    if (!n) return;
    n.textContent = "";
    window.setTimeout(() => { n.textContent = texto; }, 50);
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
    const b = h("button", { type: "button", clase: "bn-enlace", texto: T("Salir") });
    b.addEventListener("click", () => { salir(); window.location.href = "/banca/index.html"; });
    zona.append(h("span", { clase: "bn-quien", texto: s.cliente.alias }), b);
  }

  // Abre el widget ya dentro de la conversación de un reclamo.
  function abrirAsistente(conversacion, contexto) {
    if (window.BancaWidget) window.BancaWidget.abrir({ conversacion, contexto });
  }

  // Ingreso ----------------------------------------------------------------------------------------------------

  async function pintarIngreso() {
    const cont = $("ingreso-cuerpo");
    cont.textContent = "";
    cont.append(...esqueleto("bn-esq-linea", 3));
    let lista;
    try { lista = await llamar("/api/banca/clientes-demo"); } catch (e) {
      cont.textContent = "";
      cont.append(estadoError(mensajeDeError(e), pintarIngreso));
      return;
    }
    cont.textContent = "";
    const sel = h("select", { id: "cliente-demo", name: "cliente" });
    lista.forEach((c) => sel.append(h("option", { value: String(c.indice), texto: c.alias })));
    const btn = h("button", { type: "submit", clase: "primario", texto: T("Ingresar a la demostración") });
    const aviso = guardar.leer("banca_aviso") || "";
    guardar.borrar("banca_aviso");
    const err = h("p", { id: "ingreso-error", clase: "bn-msg-error", role: "alert", texto: aviso });
    const form = h("form", { id: "form-ingreso" },
      h("div", { clase: "campo" }, h("label", { for: "cliente-demo", texto: T("Cliente de demostración") }), sel),
      btn, err);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      btn.disabled = true;
      err.textContent = "";
      try {
        const r = await llamar("/api/banca/ingresar", { metodo: "POST", cuerpo: { indice: Number(sel.value), registro: registro() } });
        guardarSesion({ sesion: r.sesion, cliente: r.cliente });
        window.location.href = "/banca/index.html" + (MOCK ? "?demo=local" : "");
      } catch (e) {
        err.textContent = mensajeDeError(e);
        btn.disabled = false;
      }
    });
    cont.append(form);
  }

  // Tablero ----------------------------------------------------------------------------------------------------

  const tablero = { productos: [], movimientos: [], siguiente: null, producto: "", estado: "", texto: "" };

  function tarjetaProducto(p) {
    const cifras = [];
    if (p.saldo !== null && p.saldo !== undefined) {
      cifras.push(h("div", {}, h("dt", { texto: T(esTarjeta(p) && p.limite ? "Saldo utilizado" : "Saldo") }), h("dd", { clase: "bn-num", texto: dinero(p.saldo, p.moneda) })));
    }
    if (p.limite !== null && p.limite !== undefined) {
      cifras.push(h("div", {}, h("dt", { texto: T("Cupo") }), h("dd", { clase: "bn-num", texto: dinero(p.limite, p.moneda) })));
    }
    return h("li", { clase: "bn-producto" + (p.estado === "bloqueada" ? " bn-bloqueado" : "") },
      h("div", { clase: "bn-producto-cab" },
        h("h3", { texto: p.etiqueta }),
        insignia(p.estado)),
      h("p", { clase: "bn-final bn-num", texto: enmascarar(p.final) }),
      cifras.length ? h("dl", { clase: "bn-cifras" }, cifras) : h("p", { clase: "nota", texto: T("Sin saldo para mostrar.") }));
  }

  function filtrados() {
    const t = tablero.texto.trim().toLowerCase();
    return tablero.movimientos.filter((m) =>
      (!tablero.estado || m.estado === tablero.estado) &&
      (!t || [m.descripcion, m.categoria, m.monto].some((x) => String(x || "").toLowerCase().includes(t))));
  }

  function filaMovimiento(m) {
    const b = h("button", { type: "button", clase: "bn-fila", "aria-label": T("{desc}, {monto}, {estado}. Ver detalle", { desc: m.descripcion, monto: dinero(m.monto, m.moneda), estado: T((ESTADOS[m.estado] || [m.estado])[0]) }) },
      h("span", { clase: "bn-fila-txt" },
        h("span", { clase: "bn-fila-desc", texto: m.descripcion }),
        h("span", { clase: "bn-fila-meta", texto: `${m.hora} · ${m.categoria || m.tipo} · ${enmascarar(m.tarjeta_final)}` }),
        h("span", { clase: "bn-fila-marcas" }, insignia(m.estado),
          m.es_extranjera ? h("span", { clase: "bn-insignia bn-aviso", texto: T("Compra en el exterior") }) : null,
          m.caso_ref ? h("span", { clase: "bn-insignia bn-neutro", texto: T("Con reclamo") }) : null)),
      h("span", { clase: "bn-monto bn-num", texto: dinero(m.monto, m.moneda) }));
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
    for (const [fecha, filas] of grupos) {
      cont.append(h("section", { clase: "bn-grupo", "aria-label": fechaLarga(fecha) },
        h("h3", { texto: fechaLarga(fecha) }),
        h("ul", { clase: "bn-lista" }, filas.map(filaMovimiento))));
    }
  }

  async function cargarMovimientos(mas) {
    const cont = $("movimientos");
    if (!mas) { cont.textContent = ""; cont.append(...esqueleto("bn-esq-fila", 5)); tablero.movimientos = []; }
    const q = new URLSearchParams({ limite: "50" });
    if (tablero.producto) q.set("producto_ref", tablero.producto);
    if (mas && tablero.siguiente) q.set("antes_de", tablero.siguiente);
    try {
      const d = await llamar("/api/banca/movimientos?" + q.toString());
      tablero.movimientos = tablero.movimientos.concat(d.movimientos || []);
      tablero.siguiente = d.siguiente || null;
      pintarMovimientos();
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
    try {
      const r = await llamar("/api/banca/resumen");
      tablero.productos = r.productos || [];
      $("saludo").textContent = T("Hola, {nombre}", { nombre: r.cliente && r.cliente.alias ? r.cliente.alias : T("cliente") });
      cont.textContent = "";
      if (!tablero.productos.length) cont.append(estadoVacio(T("No tiene productos en esta demostración"), "", null));
      else cont.append(...tablero.productos.map(tarjetaProducto));
      const sel = $("f-producto");
      sel.textContent = "";
      sel.append(h("option", { value: "", texto: T("Todos los productos") }));
      tablero.productos.forEach((p) => sel.append(h("option", { value: p.producto_ref, texto: `${p.etiqueta} ${enmascarar(p.final)}` })));
    } catch (e) {
      cont.textContent = "";
      cont.append(estadoError(mensajeDeError(e), cargarResumen));
      sesionVencida(e);
    }
  }

  // Detalle y acciones ----------------------------------------------------------------------------------------

  let disparador = null;

  function filaDetalle(k, v) { return h("div", {}, h("dt", { texto: k }), h("dd", { clase: "bn-num", texto: v })); }

  function abrirDetalle(m, origen) {
    disparador = origen;
    const dlg = $("detalle");
    const cuerpo = $("detalle-cuerpo");
    cuerpo.textContent = "";
    const producto = tablero.productos.find((p) => esTarjeta(p) && p.final === m.tarjeta_final);
    $("detalle-titulo").textContent = m.descripcion;
    const marcas = h("p", { clase: "bn-fila-marcas" }, insignia(m.estado),
      m.es_extranjera ? h("span", { clase: "bn-insignia bn-aviso", texto: T("Compra en el exterior ({pais})", { pais: m.pais }) }) : h("span", { clase: "bn-insignia bn-neutro", texto: T("País: {pais}", { pais: m.pais }) }));
    cuerpo.append(
      h("p", { clase: "bn-detalle-monto bn-num", texto: dinero(m.monto, m.moneda) }),
      marcas,
      h("dl", { clase: "bn-datos" },
        filaDetalle(T("Fecha"), fechaCorta(m.fecha)), filaDetalle(T("Hora"), m.hora),
        filaDetalle(T("Tarjeta"), enmascarar(m.tarjeta_final)), filaDetalle(T("Categoría"), m.categoria || m.tipo),
        filaDetalle(T("Canal"), m.canal || "")));
    const res = h("p", { id: "detalle-resultado", clase: "bn-resultado", role: "status" });
    const acciones = h("div", { clase: "bn-acciones-detalle" });
    if (m.caso_ref) {
      acciones.append(h("a", { clase: "boton", href: "/banca/reclamos.html" + (MOCK ? "?demo=local" : ""), texto: T("Ver mi reclamo") }));
    } else if (m.reclamable) {
      const b = h("button", { type: "button", clase: "primario", texto: T("No reconozco este cargo") });
      b.addEventListener("click", () => reclamar(m, b, res));
      acciones.append(b);
    } else {
      acciones.append(h("p", { clase: "nota", texto: T("Este movimiento no admite reclamos.") }));
    }
    if (producto && producto.estado !== "bloqueada") {
      const b = h("button", { type: "button", texto: T("Bloquear tarjeta") });
      b.addEventListener("click", () => confirmarBloqueo(producto, res));
      acciones.append(b);
    } else if (producto) {
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
      abrirAsistente(r.conversacion, m);
    } catch (e) {
      boton.disabled = false;
      res.textContent = e.status === 409 ? T("Este cargo ya tiene un reclamo abierto.") : mensajeDeError(e);
    }
  }

  function confirmarBloqueo(p, res) {
    const dlg = $("confirmar");
    $("confirmar-texto").textContent = T("Va a bloquear la tarjeta {t}. No podrá usarla para compras ni retiros hasta que se reponga. Si no quiere bloquearla, elija Cancelar y no se hará ningún cambio.", { t: `${p.etiqueta} ${enmascarar(p.final)}` });
    const si = $("confirmar-si");
    const no = $("confirmar-no");
    si.disabled = false;
    si.onclick = async () => {
      si.disabled = true;
      try {
        const r = await llamar(`/api/banca/tarjetas/${encodeURIComponent(p.producto_ref)}/bloqueo`, { metodo: "POST", cuerpo: { confirmo: true } });
        p.estado = "bloqueada";
        dlg.close();
        const t = r.ya_estaba ? T("La tarjeta {t} ya estaba bloqueada. No hicimos ningún cambio.", { t: enmascarar(p.final) }) : T("Bloqueamos la tarjeta {t}.", { t: enmascarar(p.final) });
        res.textContent = t;
        anunciar(t);
        const cont = $("productos");
        cont.textContent = "";
        cont.append(...tablero.productos.map(tarjetaProducto));
      } catch (e) {
        si.disabled = false;
        dlg.close();
        res.textContent = e.status === 400 || e.status === 404
          ? T("No pudimos bloquear esta tarjeta desde aquí. Puede pedir ayuda a una persona desde el asistente.")
          : mensajeDeError(e);
      }
    };
    no.onclick = () => dlg.close();
    dlg.showModal();
    no.focus();
  }

  function iniciarTablero() {
    $("ingreso").classList.add("oculto");
    $("tablero").classList.remove("oculto");
    cargarResumen();
    cargarMovimientos(false);
    $("f-producto").addEventListener("change", (ev) => { tablero.producto = ev.target.value; cargarMovimientos(false); });
    $("f-estado").addEventListener("change", (ev) => { tablero.estado = ev.target.value; pintarMovimientos(); });
    $("f-texto").addEventListener("input", (ev) => { tablero.texto = ev.target.value; pintarMovimientos(); });
    $("mas").addEventListener("click", () => cargarMovimientos(true));
    $("detalle-cerrar").addEventListener("click", () => $("detalle").close());
    $("detalle").addEventListener("close", () => { if (disparador && document.contains(disparador)) disparador.focus(); });
    // Revisión visual en modo local: ?abrir=t1 abre el detalle y ?asistente=1 abre el asistente.
    if (MOCK && params.get("abrir")) {
      const timer = window.setInterval(() => {
        const m = tablero.movimientos.find((x) => x.tx_ref === params.get("abrir"));
        if (m && tablero.productos.length) { window.clearInterval(timer); abrirDetalle(m, null); }
      }, 200);
    }
  }

  // Reclamos ---------------------------------------------------------------------------------------------------

  function tarjetaReclamo(c) {
    const eventos = (c.historial || []).map((e) => h("li", {}, h("span", { clase: "bn-punto", "aria-hidden": "true" }),
      h("div", {}, h("p", { clase: "bn-evento", texto: T(e.evento) }), h("p", { clase: "nota", texto: fechaCorta(e.fecha) }))));
    const cifras = [filaDetalle(T("Monto reclamado"), dinero(c.monto, c.moneda)), filaDetalle(T("Abierto el"), fechaCorta(c.abierto_en))];
    cifras.push(filaDetalle(T("Devolución provisional"), c.credito_provisional ? dinero(c.credito_provisional, c.moneda) : T("Todavía no aplica")));
    cifras.push(filaDetalle(T("Plazo de respuesta"), c.plazo ? fechaCorta(c.plazo) : T("Se lo informaremos pronto")));
    return h("li", { clase: "bn-reclamo" },
      h("div", { clase: "bn-producto-cab" }, h("h2", { texto: c.descripcion || T("Cargo reclamado") }), insignia(c.estado)),
      h("dl", { clase: "bn-datos" }, cifras),
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
            h("a", { clase: "boton", href: "/banca/index.html" + (MOCK ? "?demo=local" : ""), texto: T("Ver mis movimientos") })));
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
      guardarSesion({ sesion: r.sesion, cliente: r.cliente });
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

  window.Banca = { llamar, h, sesion, MOCK, BASE, guardar, ErrorApi, pausa, anunciar, fixture, estadoLocal, T, registro };
  arrancar();
})();
