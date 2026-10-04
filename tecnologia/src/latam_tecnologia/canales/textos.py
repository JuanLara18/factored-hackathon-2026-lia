"""Textos del chat: salen de `clientes/plantillas/es.yaml` y `pt.yaml`, nunca del código (CLI-2.1, R-CLI-21).

Este módulo lee los YAML directamente y no importa `latam_clientes`, que ya depende de Tecnología.
Los valores de los marcadores (acción, objeto, consecuencia) son vocabulario del canal; las frases
completas son siempre de la plantilla.

Tres registros: `usted` y `vos` (español) y `voce` (portugués de Brasil, CLI-1.5). El portugués es
atención en ese idioma para clientes de la región: el país de la cuenta sigue mandando en la norma, el
monto y la fecha.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml

_CLIENTES = Path(__file__).resolve().parents[4] / "clientes" / "plantillas"
RUTA_PLANTILLAS = _CLIENTES / "es.yaml"
RUTA_PLANTILLAS_PT = _CLIENTES / "pt.yaml"
REGISTROS = ("usted", "vos", "voce")
IDIOMA_POR_REGISTRO = {"usted": "es", "vos": "es", "voce": "pt"}
_MARCADOR = re.compile(r"\{([a-z_0-9]+)\}")

# Plantillas de chat que usa la página (id de plantilla por función).
PLANTILLAS_PAGINA = {
    "aviso": "inicio.chat",
    "procesando": "ejecutando.chat",
    "traspaso": "traspaso.chat",
    "falla": "falla_segura.chat",
    "sin_cambios": "cierre.sin_cambios",
}

# Etiquetas de los componentes (CLI-2.1 las llevará a la plantilla; hasta entonces viven aquí, cortas para
# respetar los 20 caracteres de R-CLI-47). Mismos textos en ambos registros salvo donde el verbo cambia.
ETIQUETAS: dict[str, dict[str, str]] = {
    "usted": {
        "persona": "Hablar con una persona",
        "confirmo": "Confirmo",
        "no": "No",
        "reconozco": "La reconozco",
        "no_reconozco": "No la reconozco",
        "renovar": "Volver a preguntar",
        "enviar": "Enviar",
        "escribir": "Escriba su mensaje",
        "ia": "Asistente de IA",
        "vence": "Esta confirmación vence en",
        "vencida": "La confirmación venció.",
        "vence_pronto": "Queda un minuto para confirmar.",
        "tarjeta": "Tarjeta terminada en",
        "registro": "Tratamiento",
        "cliente": "Cliente de demostración",
        "iniciar": "Iniciar conversación",
        "demo": "Demostración",
        "conversacion": "Conversación",
        "ir_mensaje": "Ir al campo de mensaje",
        "sesion_vencida": "La sesión terminó. Inicie una nueva conversación.",
        "error_red": "No pude conectarme.",
    },
    "vos": {
        "persona": "Hablar con una persona",
        "confirmo": "Confirmo",
        "no": "No",
        "reconozco": "La reconozco",
        "no_reconozco": "No la reconozco",
        "renovar": "Volver a preguntar",
        "enviar": "Enviar",
        "escribir": "Escribí tu mensaje",
        "ia": "Asistente de IA",
        "vence": "Esta confirmación vence en",
        "vencida": "La confirmación venció.",
        "vence_pronto": "Queda un minuto para confirmar.",
        "tarjeta": "Tarjeta terminada en",
        "registro": "Tratamiento",
        "cliente": "Cliente de demostración",
        "iniciar": "Iniciar conversación",
        "demo": "Demostración",
        "conversacion": "Conversación",
        "ir_mensaje": "Ir al campo de mensaje",
        "sesion_vencida": "La sesión terminó. Iniciá una nueva conversación.",
        "error_red": "No pude conectarme.",
    },
    "voce": {
        "persona": "Falar com uma pessoa",
        "confirmo": "Confirmo",
        "no": "Não",
        "reconozco": "Reconheço",
        "no_reconozco": "Não reconheço",
        "renovar": "Perguntar de novo",
        "enviar": "Enviar",
        "escribir": "Escreva sua mensagem",
        "ia": "Assistente de IA",
        "vence": "Esta confirmação vence em",
        "vencida": "A confirmação venceu.",
        "vence_pronto": "Falta um minuto para confirmar.",
        "tarjeta": "Cartão com final",
        "registro": "Tratamento",
        "cliente": "Cliente de demonstração",
        "iniciar": "Iniciar conversa",
        "demo": "Demonstração",
        "conversacion": "Conversa",
        "ir_mensaje": "Ir para o campo de mensagem",
        "sesion_vencida": "A sessão terminou. Inicie uma nova conversa.",
        "error_red": "Não consegui me conectar.",
    },
}

# Valores de marcadores para la confirmación de cada herramienta con efecto, por idioma.
CONFIRMACION: dict[str, dict[str, dict[str, str]]] = {
    "es": {
        "abrir_disputa": {
            "accion": "abrir un reclamo",
            "consecuencia": "el banco revisará el cargo; bloquear la tarjeta es un paso aparte",
        },
        "bloquear_tarjeta": {
            "accion": "bloquear",
            "consecuencia": "la tarjeta no podrá usarse; abrir un reclamo es un paso aparte",
        },
        "escalar": {
            "accion": "pasar el caso a",
            "consecuencia": "una persona del equipo lo retomará sin que tenga que repetir nada",
        },
    },
    "pt": {
        "abrir_disputa": {
            "accion": "abrir uma contestação",
            "consecuencia": "o banco vai analisar a cobrança; bloquear o cartão é um passo à parte",
        },
        "bloquear_tarjeta": {
            "accion": "bloquear",
            "consecuencia": "o cartão não poderá ser usado; abrir uma contestação é um passo à parte",
        },
        "escalar": {
            "accion": "encaminhar",
            "consecuencia": "uma pessoa da equipe vai retomar o caso sem que você precise repetir nada",
        },
    },
}

RANGO_ESPERA = {"es": "unos minutos", "pt": "alguns minutos"}


@lru_cache(maxsize=1)
def _plantillas() -> dict[str, dict[str, str]]:
    """Textos por id y registro; el español aporta usted y vos, el portugués aporta voce."""
    salida: dict[str, dict[str, str]] = {}
    for ruta in (RUTA_PLANTILLAS, RUTA_PLANTILLAS_PT):
        datos = cast(dict[str, Any], yaml.safe_load(ruta.read_text(encoding="utf-8")))
        for f in cast(list[dict[str, Any]], datos["plantillas"]):
            salida.setdefault(str(f["id"]), {}).update(cast(dict[str, str], f["textos"]))
    return salida


# Etiquetas de los dominios canónicos (datos/dominios/dominios_canonicos.csv) que el chat muestra al cliente.
TIPOS_TRANSACCION = {
    "Purchase": "Compra",
    "Withdrawal": "Retiro",
    "Transfer": "Transferencia",
    "Payment": "Pago",
    "Deposit": "Depósito",
    "Adjustment": "Ajuste",
}
ESTADOS_TRANSACCION = {
    "Approved": "Aprobada",
    "Declined": "Rechazada",
    "Pending": "Pendiente",
    "Reversed": "Revertida",
}
TIPOS_TRANSACCION_PT = {
    "Purchase": "Compra",
    "Withdrawal": "Saque",
    "Transfer": "Transferência",
    "Payment": "Pagamento",
    "Deposit": "Depósito",
    "Adjustment": "Ajuste",
}
ESTADOS_TRANSACCION_PT = {
    "Approved": "Aprovada",
    "Declined": "Recusada",
    "Pending": "Pendente",
    "Reversed": "Estornada",
}
SIN_COMERCIO = {"es": "Movimiento sin comercio", "pt": "Movimento sem estabelecimento"}


# Etiquetas de `categoria_comercio` y `canal_transaccion` (mismo CSV); se copian aquí porque la imagen de
# Cloud Run no trae `datos/`. Una prueba las compara con el CSV. Las del portugués son del canal.
CATEGORIAS = {
    "Food": "Alimentos",
    "Services": "Servicios",
    "Other": "Otros",
    "Transport": "Transporte",
    "Entertainment": "Entretenimiento",
    "Health": "Salud",
}
CATEGORIAS_PT = {
    "Food": "Alimentação",
    "Services": "Serviços",
    "Other": "Outros",
    "Transport": "Transporte",
    "Entertainment": "Entretenimento",
    "Health": "Saúde",
}
CANALES = {
    "POS": "Punto de venta",
    "ATM": "Cajero automático",
    "Web": "Web",
    "App": "Aplicación móvil",
    "Branch": "Sucursal",
    "Transfer": "Transferencia",
}
CANALES_PT = {
    "POS": "Ponto de venda",
    "ATM": "Caixa eletrônico",
    "Web": "Web",
    "App": "Aplicativo",
    "Branch": "Agência",
    "Transfer": "Transferência",
}
# Claves estables que el sitio mapea a SVG.
ICONOS_CATEGORIA = {
    "food": "comida",
    "transport": "transporte",
    "entertainment": "entretenimiento",
    "services": "servicios",
    "health": "salud",
    "other": "otro",
}
ICONOS_TIPO = {
    "withdrawal": "efectivo",
    "transfer": "transferencia",
    "payment": "pago",
    "deposit": "deposito",
}


def _buscar(tabla: dict[str, str], valor: object) -> str | None:
    clave = str(valor or "").strip().lower()
    return next((v for k, v in tabla.items() if k.lower() == clave), None)


def estado_texto(estado: object, registro: str = "usted") -> str:
    tabla = ESTADOS_TRANSACCION_PT if idioma_de(registro) == "pt" else ESTADOS_TRANSACCION
    return _buscar(tabla, estado) or str(estado or "")


def tipo_texto(tipo: object, registro: str = "usted") -> str:
    tabla = TIPOS_TRANSACCION_PT if idioma_de(registro) == "pt" else TIPOS_TRANSACCION
    return _buscar(tabla, tipo) or str(tipo or "")


def categoria_texto(categoria: object, registro: str = "usted") -> str:
    tabla = CATEGORIAS_PT if idioma_de(registro) == "pt" else CATEGORIAS
    return _buscar(tabla, categoria) or str(categoria or "")


def canal_texto(canal: object, registro: str = "usted") -> str:
    tabla = CANALES_PT if idioma_de(registro) == "pt" else CANALES
    return _buscar(tabla, canal) or str(canal or "")


def sentido(tipo: object, estado: object) -> str:
    """`abono` si el dinero entra al cliente (depósito, reverso); `cargo` en el resto."""
    t, e = str(tipo or "").lower(), str(estado or "").lower()
    return "abono" if t == "deposit" or e == "reversed" else "cargo"


def icono(tipo: object, categoria: object) -> str:
    """Lo que no es compra se dibuja por su tipo; la compra, por su categoría (`compras` si no hay)."""
    por_tipo = ICONOS_TIPO.get(str(tipo or "").lower())
    if por_tipo:
        return por_tipo
    por_categoria = ICONOS_CATEGORIA.get(str(categoria or "").lower())
    if por_categoria and por_categoria != "otro":
        return por_categoria
    return "compras" if str(tipo or "").lower() == "purchase" else "otro"


def idioma_de(registro: str | None) -> str:
    return IDIOMA_POR_REGISTRO.get(registro_valido(registro), "es")


def describir_comercio(comercio: object, tipo: object, registro: str = "usted") -> str:
    """El comercio si existe; si no, el tipo de transacción (transferencias, retiros) en el idioma."""
    if comercio:
        return str(comercio)
    if idioma_de(registro) == "pt":
        return TIPOS_TRANSACCION_PT.get(str(tipo), SIN_COMERCIO["pt"])
    return TIPOS_TRANSACCION.get(str(tipo), SIN_COMERCIO["es"])


def estado_transaccion(estado: object, registro: str = "usted") -> str:
    tabla = ESTADOS_TRANSACCION_PT if idioma_de(registro) == "pt" else ESTADOS_TRANSACCION
    return tabla.get(str(estado), str(estado))


def plantilla(plantilla_id: str, registro: str, **valores: str) -> str:
    """Rellena una plantilla; falla si faltan o sobran marcadores."""
    texto = " ".join(_plantillas()[plantilla_id][registro].split())
    usados = set(_MARCADOR.findall(texto))
    if usados != set(valores):
        raise KeyError(
            f"{plantilla_id}: faltan {sorted(usados - set(valores))} o sobran {sorted(set(valores) - usados)}"
        )
    return _MARCADOR.sub(lambda m: valores[m.group(1)], texto)


def registro_valido(registro: str | None) -> str:
    return registro if registro in REGISTROS else "usted"


def rango_espera(registro: str | None) -> str:
    return RANGO_ESPERA[idioma_de(registro)]


def catalogo_pagina(registro: str) -> dict[str, Any]:
    """Todo lo que la página necesita mostrar, en el registro pedido."""
    r = registro_valido(registro)
    textos = {
        clave: plantilla(pid, r, **({"rango_espera": rango_espera(r)} if pid == "traspaso.chat" else {}))
        for clave, pid in PLANTILLAS_PAGINA.items()
    }
    return {"registro": r, "idioma": idioma_de(r), "textos": textos, "etiquetas": ETIQUETAS[r]}


def objeto_confirmacion(herramienta: str, registro: str, comercio: str | None, final: str | None) -> str:
    """El objeto de la acción en el idioma del cliente; comercio y final salen de la base."""
    pt = idioma_de(registro) == "pt"
    if herramienta == "abrir_disputa" and comercio is not None:
        return f"sobre a cobrança de {comercio}" if pt else f"sobre el cargo de {comercio}"
    if herramienta == "bloquear_tarjeta" and final is not None:
        return f"o cartão com final {final}" if pt else f"la tarjeta terminada en {final}"
    return "o seu caso" if pt else "su caso"


def confirmacion(
    herramienta: str, registro: str, objeto: str, monto: str | None = None, moneda: str = ""
) -> str:
    """Texto de la confirmación; el monto, cuando hay, sale de la base (R-CLI-45)."""
    v = CONFIRMACION[idioma_de(registro)][herramienta]
    if monto is not None:
        return plantilla(
            "confirmacion.reclamo.chat",
            registro,
            accion=v["accion"],
            objeto=objeto,
            monto=monto,
            moneda=moneda,
            consecuencia=v["consecuencia"],
        )
    return plantilla(
        "confirmando.chat", registro, accion=v["accion"], objeto=objeto, consecuencia=v["consecuencia"]
    )
