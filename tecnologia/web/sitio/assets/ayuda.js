/* Buscador del centro de ayuda: filtra las preguntas por el texto escrito. */
(function () {
  "use strict";
  var campo = document.getElementById("buscar");
  var lista = document.querySelectorAll(".faq");
  var aviso = document.getElementById("resultado");
  var vacio = document.getElementById("sin-resultados");
  if (!campo) { return; }
  var T = function (texto, valores) { return window.Idioma ? window.Idioma.t(texto, valores) : texto.replace("{n}", valores.n); };
  function normal(s) { return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }
  function filtrar() {
    var q = normal(campo.value.trim());
    var n = 0;
    for (var i = 0; i < lista.length; i++) {
      var ok = q === "" || normal(lista[i].textContent).indexOf(q) !== -1;
      lista[i].classList.toggle("oculto", !ok);
      if (ok) { n++; }
    }
    vacio.classList.toggle("oculto", n !== 0);
    aviso.textContent = q === "" ? "" : T(n === 1 ? "{n} pregunta encontrada" : "{n} preguntas encontradas", { n: n });
  }
  campo.addEventListener("input", filtrar);
  // Temas frecuentes: cada botón escribe su palabra en el buscador.
  var temas = document.querySelectorAll("[data-buscar]");
  for (var t = 0; t < temas.length; t++) {
    temas[t].addEventListener("click", function () {
      var palabra = this.getAttribute("data-buscar") || "";
      var clave = "buscar:" + palabra;
      var traducida = window.Idioma ? window.Idioma.t(clave) : clave;
      campo.value = traducida === clave ? palabra : traducida;
      filtrar();
    });
  }
})();
