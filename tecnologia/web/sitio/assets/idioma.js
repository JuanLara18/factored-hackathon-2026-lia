// Idioma y trato de la banca en línea, el asistente y el chat: Español usted, Español vos o Português (você).
// La elección viaja al servidor como registro ("usted", "vos" o "voce") y se recuerda en localStorage; si no está
// disponible, la página funciona igual con usted. Los textos que vienen del servidor (etiquetas, avisos, aprobaciones)
// ya llegan en el registro pedido; aquí solo se traduce lo que la interfaz escribe por su cuenta.
// El portugués es atención en ese idioma para clientes de la región (cuentas de México, Colombia y Argentina):
// los montos y las fechas siguen el formato del país de la cuenta, no el de Brasil.
"use strict";

(function () {
  var CLAVE = "latam.trato";
  var MODOS = ["usted", "vos", "voce"];
  var ETIQUETAS = { usted: "Español, usted", vos: "Español, vos", voce: "Português, você" };
  var LENGUAJES = { usted: "es", vos: "es", voce: "pt-BR" };
  var LOCALES = { usted: "es", vos: "es", voce: "pt-BR" };
  var NOTA_PT = "Atendimento em português para clientes da região (contas do México, da Colômbia e da Argentina). Valores, datas e normas seguem o país da conta.";

  function leer() {
    try {
      var v = window.localStorage.getItem(CLAVE);
      return MODOS.indexOf(v) >= 0 ? v : "usted";
    } catch (e) { return "usted"; }
  }
  function guardar(v) {
    try { window.localStorage.setItem(CLAVE, v); } catch (e) { /* sin almacenamiento */ }
  }
  var modo = leer();

  // Español usted -> español vos (solo lo que cambia de forma).
  var VOS = {
    "Su dinero, claro y con una persona cuando la necesite.": "Tu plata, clara y con una persona cuando la necesites.",
    "Revise sus movimientos con nombres claros": "Revisá tus movimientos con nombres claros",
    "Reporte un cargo que no reconoce en un minuto": "Reportá un cargo que no reconocés en un minuto",
    "Hable con una persona cuando prefiera": "Hablá con una persona cuando prefieras",
    "Saldo disponible": "Saldo disponible",
    "Reportar un cargo": "Reportar un cargo",
    "Hablar con una persona": "Hablar con una persona",
    "Toque el cargo que no reconoce y elija No reconozco este cargo.": "Tocá el cargo que no reconocés y elegí No reconozco este cargo.",
    "Necesito su confirmación": "Necesito tu confirmación",
    "Si reconoce este cargo, no tiene que hacer nada. Si no, puede reportarlo y lo revisamos.": "Si reconocés este cargo, no tenés que hacer nada. Si no, podés reportarlo y lo revisamos.",
    "Ya tiene un reclamo por este cargo": "Ya tenés un reclamo por este cargo",
    "Ingrese a la banca en línea": "Ingresá a la banca en línea",
    "Elija un cliente ficticio para recorrer la demostración. No se pide ninguna clave ni dato personal.": "Elegí un cliente ficticio para recorrer la demostración. No se pide ninguna clave ni dato personal.",
    "Estos son sus productos y sus últimos movimientos.": "Estos son tus productos y tus últimos movimientos.",
    "Sus productos": "Tus productos",
    "Aquí ve en qué va cada reclamo, si le devolvimos el monto de forma provisional y hasta cuándo le responderemos.": "Acá ves en qué va cada reclamo, si te devolvimos el monto de forma provisional y hasta cuándo te vamos a responder.",
    "Ingrese para ver sus reclamos": "Ingresá para ver tus reclamos",
    "Esta página muestra los reclamos del cliente de demostración con el que ingresó.": "Esta página muestra los reclamos del cliente de demostración con el que ingresaste.",
    "Su sesión venció. Vuelva a ingresar para continuar.": "Tu sesión venció. Volvé a ingresar para continuar.",
    "Pruebe con otra búsqueda o quite algún filtro.": "Probá con otra búsqueda o quitá algún filtro.",
    "Cuando haga una compra la verá aquí.": "Cuando hagas una compra la vas a ver acá.",
    "Va a bloquear la tarjeta {t}. No podrá usarla para compras ni retiros hasta que se reponga. Si no quiere bloquearla, elija Cancelar y no se hará ningún cambio.": "Vas a bloquear la tarjeta {t}. No vas a poder usarla para compras ni retiros hasta que se reponga. Si no querés bloquearla, elegí Cancelar y no se hará ningún cambio.",
    "No pudimos bloquear esta tarjeta desde aquí. Puede pedir ayuda a una persona desde el asistente.": "No pudimos bloquear esta tarjeta desde acá. Podés pedir ayuda a una persona desde el asistente.",
    "Si no reconoce un cargo, ábralo desde sus movimientos y le ayudamos.": "Si no reconocés un cargo, abrilo desde tus movimientos y te ayudamos.",
    "Abriendo su reclamo...": "Abriendo tu reclamo...",
    "Se lo informaremos pronto": "Te lo informaremos cuando tengamos la fecha",
    "Ocurrió un problema. Puede intentarlo de nuevo en unos minutos.": "Ocurrió un problema. Podés intentarlo de nuevo en unos minutos.",
    "Para revisar un cargo, ábralo desde sus movimientos y elija No reconozco este cargo. También puede pedir hablar con una persona.": "Para revisar un cargo, abrilo desde tus movimientos y elegí No reconozco este cargo. También podés pedir hablar con una persona.",
    "Para hablar con el asistente, abra primero un movimiento y elija No reconozco este cargo.": "Para hablar con el asistente, abrí primero un movimiento y elegí No reconozco este cargo.",
    "Ya avisamos a una persona. Le responderá en esta misma conversación.": "Ya avisamos a una persona. Te va a responder en esta misma conversación.",
    "No pudimos avisar a una persona en este momento. Puede intentarlo de nuevo.": "No pudimos avisar a una persona en este momento. Podés intentarlo de nuevo.",
    "Por ahora no podemos mostrar las respuestas de la persona. Vuelva a abrir el asistente en unos minutos.": "Por ahora no podemos mostrar las respuestas de la persona. Volvé a abrir el asistente en unos minutos.",
    "No pudimos enviar su mensaje. Inténtelo de nuevo.": "No pudimos enviar tu mensaje. Intentalo de nuevo.",
    "Todavía no hay una persona en este caso. Su mensaje no se envió.": "Todavía no hay una persona en este caso. Tu mensaje no se envió.",
    "Retomamos su conversación con una persona de LATAM Bank.": "Retomamos tu conversación con una persona de LATAM Bank.",
    "Demostración con clientes ficticios. Elija uno y cuéntele al asistente qué": "Demostración con clientes ficticios. Elegí uno y contale al asistente qué",
    "Allí puede abrir un movimiento y llegar al asistente con ese": "Allí podés abrir un movimiento y llegar al asistente con ese",
    "Para usted": "Para vos",
    "Hable con el asistente": "Hablá con el asistente"
  };

  // Español -> portugués de Brasil. La clave es el texto en español tal como lo escribe la página o el script.
  var PT = {
    "Su dinero, claro y con una persona cuando la necesite.": "Seu dinheiro, claro e com uma pessoa quando precisar.",
    "Revise sus movimientos con nombres claros": "Veja suas movimentações com nomes claros",
    "Reporte un cargo que no reconoce en un minuto": "Reporte uma cobrança que você não reconhece em um minuto",
    "Hable con una persona cuando prefiera": "Fale com uma pessoa quando preferir",
    "Demostración": "Demonstração",
    "Personas ficticias. No se usa ningún dato real.": "Pessoas fictícias. Nenhum dado real é usado.",
    "Saldo disponible": "Saldo disponível",
    "Suma de sus cuentas": "Soma das suas contas",
    "Compras aprobadas": "Compras aprovadas",
    "Gasto con tarjetas este mes": "Gasto com cartões neste mês",
    "Reclamos abiertos": "Reclamações abertas",
    "Ver mis reclamos": "Ver minhas reclamações",
    "Reportar un cargo": "Reportar uma cobrança",
    "Bloquear tarjeta": "Bloquear cartão",
    "Mis reclamos": "Minhas reclamações",
    "Hablar con una persona": "Falar com uma pessoa",
    "Todos": "Todos",
    "Aprobados": "Aprovados",
    "Pendientes": "Pendentes",
    "Rechazados": "Recusados",
    "En reclamo": "Em reclamação",
    "Exterior": "Exterior",
    "Hoy": "Hoje",
    "Ayer": "Ontem",
    "Necesito su confirmación": "Preciso da sua confirmação",
    "Persona del equipo": "Pessoa da equipe",
    "Toque el cargo que no reconoce y elija No reconozco este cargo.": "Toque na cobrança que você não reconhece e escolha Não reconheço esta cobrança.",
    "Ya tiene un reclamo por este cargo": "Você já tem uma reclamação por esta cobrança",
    "Recibido": "Recebido",
    "En revisión": "Em análise",
    "Resuelto": "Resolvido",
    "Activa": "Ativo",
    "Bloqueada": "Bloqueado",
    "Aprobada": "Aprovada",
    "Pendiente": "Pendente",
    "Rechazada": "Recusada",
    "Sus productos": "Seus produtos",
    "Movimientos recientes": "Movimentações recentes",
    "Detalle del movimiento": "Detalhe da movimentação",
    "Si reconoce este cargo, no tiene que hacer nada. Si no, puede reportarlo y lo revisamos.": "Se você reconhece esta cobrança, não precisa fazer nada. Se não, pode reportá-la e nós analisamos.",
    "Este dinero ya está en su cuenta.": "Este dinheiro já está na sua conta.",
    "Ir al contenido": "Ir para o conteúdo",
    "Demostración": "Demonstração",
    "Clientes y movimientos ficticios. LATAM Bank no es un banco real.": "Clientes e movimentos fictícios. O LATAM Bank não é um banco real.",
    "Datos de ejemplo locales, sin servidor.": "Dados de exemplo locais, sem servidor.",
    "Banca en línea": "Banco online",
    "Banca en línea, LATAM Bank": "Banco online, LATAM Bank",
    "Mis productos": "Meus produtos",
    "Mis reclamos": "Minhas contestações",
    "Mis reclamos, LATAM Bank": "Minhas contestações, LATAM Bank",
    "Transparencia": "Transparência",
    "Ingrese a la banca en línea": "Entre no banco online",
    "Elija un cliente ficticio para recorrer la demostración. No se pide ninguna clave ni dato personal.": "Escolha um cliente fictício para percorrer a demonstração. Não pedimos nenhuma senha nem dado pessoal.",
    "Cliente de demostración": "Cliente de demonstração",
    "Ingresar a la demostración": "Entrar na demonstração",
    "Hola": "Olá",
    "Hola, {nombre}": "Olá, {nombre}",
    "cliente": "cliente",
    "Estos son sus productos y sus últimos movimientos.": "Estes são seus produtos e seus últimos movimentos.",
    "Sus productos": "Seus produtos",
    "Movimientos recientes": "Movimentos recentes",
    "Buscar movimientos": "Buscar movimentos",
    "Buscar": "Buscar",
    "Comercio, categoría o monto": "Estabelecimento, categoria ou valor",
    "Producto": "Produto",
    "Todos los productos": "Todos os produtos",
    "Estado": "Status",
    "Todos": "Todos",
    "Aprobada": "Aprovada",
    "Pendiente": "Pendente",
    "Rechazada": "Recusada",
    "Reversada": "Estornada",
    "Revertida": "Estornada",
    "Activa": "Ativa",
    "Bloqueada": "Bloqueada",
    "Abierto": "Aberta",
    "En revisión": "Em análise",
    "Resuelto": "Resolvida",
    "Cerrado": "Encerrada",
    "Ver más movimientos": "Ver mais movimentos",
    "Cerrar": "Fechar",
    "Bloquear tarjeta": "Bloquear cartão",
    "Cancelar": "Cancelar",
    "LATAM Bank es un banco ficticio creado para el Factored AI & Data Hackathon 2026": "O LATAM Bank é um banco fictício criado para o Factored AI & Data Hackathon 2026",
    "Información": "Informações",
    "Cómo funciona un reclamo": "Como funciona uma contestação",
    "Privacidad": "Privacidade",
    "Aquí ve en qué va cada reclamo, si le devolvimos el monto de forma provisional y hasta cuándo le responderemos.": "Aqui você vê em que pé está cada contestação, se houve crédito provisório do valor e até quando vamos responder.",
    "Ingrese para ver sus reclamos": "Entre para ver suas contestações",
    "Esta página muestra los reclamos del cliente de demostración con el que ingresó.": "Esta página mostra as contestações do cliente de demonstração com o qual você entrou.",
    "Reclamos": "Contestações",
    "Estado de sus reclamos por cargos: historial, devolución provisional y plazo de respuesta.": "Status das suas contestações de cobranças: histórico, crédito provisório e prazo de resposta.",
    "Salir": "Sair",
    "Intentar de nuevo": "Tentar de novo",
    "No pudimos cargar esta información": "Não conseguimos carregar esta informação",
    "Su sesión venció. Vuelva a ingresar para continuar.": "Sua sessão expirou. Entre de novo para continuar.",
    "El servicio de la banca en línea no está disponible en este momento. En la demostración local puede usar la vista de ejemplo.": "O serviço do banco online não está disponível neste momento. Na demonstração local você pode usar a visão de exemplo.",
    "Ocurrió un problema. Puede intentarlo de nuevo en unos minutos.": "Ocorreu um problema. Você pode tentar de novo em alguns minutos.",
    "Saldo utilizado": "Saldo utilizado",
    "Saldo": "Saldo",
    "Cupo": "Limite",
    "Sin saldo para mostrar.": "Sem saldo para mostrar.",
    "Compra en el exterior": "Compra no exterior",
    "Compra en el exterior ({pais})": "Compra no exterior ({pais})",
    "País: {pais}": "País: {pais}",
    "Con reclamo": "Com contestação",
    "{n} movimiento": "{n} movimento",
    "{n} movimientos": "{n} movimentos",
    "{desc}, {monto}, {estado}. Ver detalle": "{desc}, {monto}, {estado}. Ver detalhes",
    "No hay movimientos con esos filtros": "Não há movimentos com esses filtros",
    "Todavía no hay movimientos": "Ainda não há movimentos",
    "Pruebe con otra búsqueda o quite algún filtro.": "Tente outra busca ou remova algum filtro.",
    "Cuando haga una compra la verá aquí.": "Quando fizer uma compra, você a verá aqui.",
    "No tiene productos en esta demostración": "Você não tem produtos nesta demonstração",
    "Fecha": "Data",
    "Hora": "Hora",
    "Tarjeta": "Cartão",
    "Categoría": "Categoria",
    "Canal": "Canal",
    "Ver mi reclamo": "Ver minha contestação",
    "No reconozco este cargo": "Não reconheço esta cobrança",
    "Este movimiento no admite reclamos.": "Este movimento não admite contestação.",
    "La tarjeta {t} está bloqueada.": "O cartão {t} está bloqueado.",
    "Abriendo su reclamo...": "Abrindo sua contestação...",
    "Este cargo ya tiene un reclamo abierto.": "Esta cobrança já tem uma contestação aberta.",
    "Va a bloquear la tarjeta {t}. No podrá usarla para compras ni retiros hasta que se reponga. Si no quiere bloquearla, elija Cancelar y no se hará ningún cambio.": "Você vai bloquear o cartão {t}. Não poderá usá-lo para compras nem saques até a reposição. Se não quiser bloqueá-lo, escolha Cancelar e nenhuma alteração será feita.",
    "La tarjeta {t} ya estaba bloqueada. No hicimos ningún cambio.": "O cartão {t} já estava bloqueado. Não fizemos nenhuma alteração.",
    "Bloqueamos la tarjeta {t}.": "Bloqueamos o cartão {t}.",
    "No pudimos bloquear esta tarjeta desde aquí. Puede pedir ayuda a una persona desde el asistente.": "Não conseguimos bloquear este cartão por aqui. Você pode pedir ajuda a uma pessoa pelo assistente.",
    "Cargo reclamado": "Cobrança contestada",
    "Historial": "Histórico",
    "Historial del reclamo": "Histórico da contestação",
    "Monto reclamado": "Valor contestado",
    "Abierto el": "Aberta em",
    "Devolución provisional": "Crédito provisório",
    "Todavía no aplica": "Ainda não se aplica",
    "Plazo de respuesta": "Prazo de resposta",
    "Se lo informaremos pronto": "Informaremos assim que tivermos a data",
    "No tiene reclamos": "Você não tem contestações",
    "Si no reconoce un cargo, ábralo desde sus movimientos y le ayudamos.": "Se não reconhecer uma cobrança, abra-a nos seus movimentos e ajudamos você.",
    "Ver mis movimientos": "Ver meus movimentos",
    "Recibimos su reclamo": "Recebemos sua contestação",
    // Asistente flotante
    "Asistente": "Assistente",
    "Asistente de LATAM Bank": "Assistente do LATAM Bank",
    "Asistente, mensaje nuevo": "Assistente, nova mensagem",
    "Cerrar el asistente": "Fechar o assistente",
    "Conversación": "Conversa",
    "Para revisar un cargo, ábralo desde sus movimientos y elija No reconozco este cargo. También puede pedir hablar con una persona.": "Para revisar uma cobrança, abra-a nos seus movimentos e escolha Não reconheço esta cobrança. Você também pode pedir para falar com uma pessoa.",
    "Para hablar con el asistente, abra primero un movimiento y elija No reconozco este cargo.": "Para falar com o assistente, abra primeiro um movimento e escolha Não reconheço esta cobrança.",
    "Ya avisamos a una persona. Le responderá en esta misma conversación.": "Já avisamos uma pessoa. Ela responderá nesta mesma conversa.",
    "No pudimos avisar a una persona en este momento. Puede intentarlo de nuevo.": "Não conseguimos avisar uma pessoa neste momento. Você pode tentar de novo.",
    "Esperando a una persona": "Aguardando uma pessoa",
    "Persona de LATAM Bank": "Pessoa do LATAM Bank",
    "Nueva respuesta de una persona de LATAM Bank": "Nova resposta de uma pessoa do LATAM Bank",
    "Por ahora no podemos mostrar las respuestas de la persona. Vuelva a abrir el asistente en unos minutos.": "Por enquanto não conseguimos mostrar as respostas da pessoa. Abra o assistente de novo em alguns minutos.",
    "Todavía no hay una persona en este caso. Su mensaje no se envió.": "Ainda não há uma pessoa neste caso. Sua mensagem não foi enviada.",
    "No pudimos enviar su mensaje. Inténtelo de nuevo.": "Não conseguimos enviar sua mensagem. Tente de novo.",
    "Retomamos su conversación con una persona de LATAM Bank.": "Retomamos sua conversa com uma pessoa do LATAM Bank.",
    "Transacción": "Transação",
    "Monto": "Valor",
    // Chat web
    "Principal": "Principal",
    "Personas": "Pessoas",
    "Productos": "Produtos",
    "Seguridad": "Segurança",
    "Ayuda": "Ajuda",
    "Empresas": "Empresas",
    "próximamente": "em breve",
    "País": "País",
    "Chat web": "Chat web",
    "Chat de disputas, LATAM Bank": "Chat de contestações, LATAM Bank",
    "Chat de demostración para resolver un cargo que no reconoce, con un asistente de inteligencia artificial.": "Chat de demonstração para resolver uma cobrança que você não reconhece, com um assistente de inteligência artificial.",
    "Demostración con clientes ficticios. Elija uno y cuéntele al asistente qué": "Demonstração com clientes fictícios. Escolha um e conte ao assistente qual",
    "no reconoce.": "não reconhece.",
    "El asistente vive en Banca en línea.": "O assistente fica no Banco online.",
    "Allí puede abrir un movimiento y llegar al asistente con ese": "Lá você pode abrir um movimento e chegar ao assistente com essa",
    "ya identificado. Este chat independiente sigue disponible.": "já identificada. Este chat independente continua disponível.",
    "Ir a Banca en línea": "Ir para o Banco online",
    "El chat en vivo no está conectado": "O chat ao vivo não está conectado",
    "Esta demostración necesita un servidor. En este momento no se puede llegar a él desde esta página.": "Esta demonstração precisa de um servidor. Neste momento não é possível chegar a ele a partir desta página.",
    "Mientras tanto, puede leer": "Enquanto isso, você pode ler",
    "cómo funciona un reclamo": "como funciona uma contestação",
    "Hable con el asistente": "Fale com o assistente",
    "Productos y ayuda": "Produtos e ajuda",
    "Para usted": "Para você",
    "Centro de ayuda": "Central de ajuda",
    "Contacto": "Contato",
    "Información legal": "Informações legais",
    "LATAM Bank es un banco ficticio creado para el Factored AI & Data Hackathon 2026. Nada de este sitio es una oferta real y ninguna acción mueve dinero.": "O LATAM Bank é um banco fictício criado para o Factored AI & Data Hackathon 2026. Nada neste site é uma oferta real e nenhuma ação movimenta dinheiro.",
    "Demostración sin valor legal. Los textos legales y de privacidad están pendientes de revisión por el área de Gobierno.": "Demonstração sem valor legal. Os textos legais e de privacidade aguardam revisão da área de Governança.",
    // Textos de respaldo del asistente (si /api/textos no responde)
    "Asistente de inteligencia artificial": "Assistente de inteligência artificial",
    "Hablar con una persona": "Falar com uma pessoa",
    "Escriba su mensaje": "Escreva sua mensagem",
    "Enviar": "Enviar",
    "Confirmo": "Confirmo",
    "No, gracias": "Não, obrigado",
    "Renovar la confirmación": "Renovar a confirmação",
    "Vence en": "Vence em",
    "La confirmación vence en un minuto.": "A confirmação vence em um minuto.",
    "La confirmación venció.": "A confirmação venceu.",
    "Reconozco este cargo": "Reconheço esta cobrança",
    "Hola. Soy el asistente virtual de LATAM Bank, un sistema de inteligencia artificial. Si prefiere hablar con una persona, puede pedirlo en cualquier momento.": "Olá. Sou o assistente virtual do LATAM Bank, um sistema de inteligência artificial. Se preferir falar com uma pessoa, você pode pedir a qualquer momento.",
    "El asistente está escribiendo": "O assistente está escrevendo",
    "No pude completar la solicitud. Puede intentarlo de nuevo o hablar con una persona.": "Não consegui concluir a solicitação. Você pode tentar de novo ou falar com uma pessoa.",
    "No se hizo ningún cambio.": "Nenhuma alteração foi feita."
  };

  // Traducción de una cadena: sin cambios en usted; vos y portugués buscan en su tabla y, si no hay, dejan el original.
  function t(texto, valores) {
    var base = String(texto);
    var tabla = modo === "voce" ? PT : modo === "vos" ? VOS : null;
    var r = tabla && Object.prototype.hasOwnProperty.call(tabla, base) ? tabla[base] : base;
    if (valores) {
      r = r.replace(/\{([a-z_]+)\}/g, function (m, k) { return Object.prototype.hasOwnProperty.call(valores, k) ? String(valores[k]) : m; });
    }
    return r;
  }

  // Traduce los nodos de texto y los atributos de una parte del DOM (las claves son el texto exacto en español).
  var ATRIBUTOS = ["aria-label", "placeholder", "title", "alt"];
  function aplicar(raiz) {
    if (modo === "usted") return;
    var base = raiz || document.body;
    var caminante = document.createTreeWalker(base, NodeFilter.SHOW_TEXT);
    var nodos = [];
    while (caminante.nextNode()) nodos.push(caminante.currentNode);
    nodos.forEach(function (n) {
      var original = n.nodeValue;
      var limpio = original.replace(/\s+/g, " ").trim();
      if (!limpio) return;
      var nuevo = t(limpio);
      if (nuevo !== limpio) n.nodeValue = original.match(/^\s*/)[0] + nuevo + original.match(/\s*$/)[0];
    });
    base.querySelectorAll("[" + ATRIBUTOS.join("],[") + "]").forEach(function (el) {
      ATRIBUTOS.forEach(function (a) {
        var v = el.getAttribute(a);
        if (v && t(v) !== v) el.setAttribute(a, t(v));
      });
    });
  }

  function nota() {
    if (modo !== "voce" || document.getElementById("nota-idioma")) return;
    var p = document.createElement("p");
    p.id = "nota-idioma";
    p.className = "nota nota-idioma";
    p.setAttribute("role", "note");
    p.textContent = NOTA_PT;
    var demo = document.querySelector(".bn-demo .contenedor");
    if (demo) { demo.appendChild(p); return; }
    var pagina = document.querySelector("main .contenedor");
    if (pagina) pagina.insertBefore(p, pagina.firstChild);
  }

  function selector() {
    var sitio = document.getElementById("selector-idioma");
    if (!sitio || sitio.firstChild) return;
    var etiqueta = document.createElement("label");
    etiqueta.className = "idioma";
    etiqueta.setAttribute("for", "idioma");
    var oculto = document.createElement("span");
    oculto.className = "visualmente-oculto";
    oculto.textContent = "Idioma y trato / Idioma e tratamento";
    var sel = document.createElement("select");
    sel.id = "idioma";
    sel.setAttribute("aria-label", "Idioma y trato / Idioma e tratamento");
    MODOS.forEach(function (m) {
      var o = document.createElement("option");
      o.value = m;
      o.textContent = ETIQUETAS[m];
      sel.appendChild(o);
    });
    sel.value = modo;
    sel.addEventListener("change", function () {
      guardar(sel.value);
      window.location.reload();
    });
    etiqueta.append(oculto, sel);
    sitio.appendChild(etiqueta);
  }

  function arrancar() {
    document.documentElement.setAttribute("lang", LENGUAJES[modo]);
    document.documentElement.setAttribute("data-trato", modo);
    selector();
    aplicar(document.body);
    nota();
    if (modo !== "usted") document.title = t(document.title);
  }

  window.Idioma = {
    modo: function () { return modo; },
    idioma: function () { return modo === "voce" ? "pt" : "es"; },
    locale: function () { return LOCALES[modo]; },
    t: t,
    aplicar: aplicar,
    poner: function (m) { if (MODOS.indexOf(m) >= 0) { modo = m; guardar(m); } },
    // Palabras con las que el cliente pide una persona, en los dos idiomas.
    pidePersona: /\b(persona|pessoa|humano|asesor|atendente)\b/i
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", arrancar);
  else arrancar();
})();
