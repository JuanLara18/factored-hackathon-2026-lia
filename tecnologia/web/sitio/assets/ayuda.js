/* Buscador del centro de ayuda: filtra las preguntas por el texto escrito. */
(function () {
  "use strict";
  var campo = document.getElementById("buscar");
  var lista = document.querySelectorAll(".faq");
  var aviso = document.getElementById("resultado");
  var vacio = document.getElementById("sin-resultados");
  if (!campo) { return; }
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
    aviso.textContent = q === "" ? "" : n + (n === 1 ? " pregunta encontrada" : " preguntas encontradas");
  }
  campo.addEventListener("input", filtrar);
  // Temas frecuentes: cada botón escribe su palabra en el buscador.
  var temas = document.querySelectorAll("[data-buscar]");
  for (var t = 0; t < temas.length; t++) {
    temas[t].addEventListener("click", function () {
      campo.value = this.getAttribute("data-buscar");
      filtrar();
    });
  }
})();
