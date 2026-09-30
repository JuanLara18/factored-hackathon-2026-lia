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
  function aplicar(pais) {
    var t = PAISES[pais];
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
    sel.addEventListener("change", function () { pais = sel.value; guardar(pais); aplicar(pais); });
  }
  aplicar(pais);
})();
