/* Selector de país del sitio público: cambia el vocabulario y la moneda de los ejemplos.
   La elección se recuerda en localStorage; si no está disponible, la página funciona igual. */
(function () {
  "use strict";
  var CLAVE = "latam.pais";
  var PAISES = {
    MX: { cargo: "cargo", cargos: "cargos", documento: "estado de cuenta", moneda: "pesos mexicanos (MXN)" },
    CO: { cargo: "cobro", cargos: "cobros", documento: "extracto", moneda: "pesos colombianos (COP)" },
    AR: { cargo: "consumo", cargos: "consumos", documento: "resumen", moneda: "pesos argentinos (ARS)" }
  };
  function leer() {
    try { var v = window.localStorage.getItem(CLAVE); return PAISES[v] ? v : "MX"; } catch (e) { return "MX"; }
  }
  function guardar(v) {
    try { window.localStorage.setItem(CLAVE, v); } catch (e) { /* sin almacenamiento */ }
  }
  // En portugués (idioma.js) el cargo es siempre la cobrança y el documento mensual el extrato; la moneda sigue siendo la del país.
  var PT = { cargo: "cobrança", cargos: "cobranças", documento: "extrato" };
  function aplicar(pais) {
    var t = PAISES[pais];
    if (window.Idioma && window.Idioma.modo() === "voce") {
      t = { cargo: PT.cargo, cargos: PT.cargos, documento: PT.documento, moneda: t.moneda };
    }
    var nodos = document.querySelectorAll("[data-p]");
    for (var i = 0; i < nodos.length; i++) {
      var k = nodos[i].getAttribute("data-p");
      if (t[k]) { nodos[i].textContent = t[k]; }
    }
    document.documentElement.setAttribute("data-pais", pais);
  }
  var pais = leer();
  var sel = document.getElementById("pais");
  if (sel) {
    sel.value = pais;
    sel.addEventListener("change", function () {
      pais = sel.value; guardar(pais); aplicar(pais);
      document.dispatchEvent(new CustomEvent("latam:pais", { detail: pais }));
      if (window.Idioma && window.Idioma.alCambiarPais) { window.Idioma.alCambiarPais(); }
    });
  }
  aplicar(pais);
  // La banca lo usa para preseleccionar un cliente del país elegido.
  window.Pais = { actual: function () { return pais; } };
  // Menú de la cabecera en pantallas angostas: botón de despliegue, Escape lo cierra.
  var btn = document.querySelector(".menu-btn");
  var cab = document.querySelector(".cabecera");
  if (btn && cab) {
    function menu(abrir) {
      cab.classList.toggle("menu-abierto", abrir);
      btn.setAttribute("aria-expanded", abrir ? "true" : "false");
    }
    btn.addEventListener("click", function () { menu(btn.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && btn.getAttribute("aria-expanded") === "true") { menu(false); btn.focus(); }
    });
    window.addEventListener("resize", function () { if (window.innerWidth > 768) { menu(false); } });
  }
})();
