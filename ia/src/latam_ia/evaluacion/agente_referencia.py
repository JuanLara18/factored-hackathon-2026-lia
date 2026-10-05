"""Agente de referencia sin red: una política guionada sobre `FunctionModel`.

Es la línea base B-reglas de 2.8.7 (palabras clave y reglas de ruta simples) sobre las mismas herramientas
tipadas del agente de disputas. Sirve para que el arnés corra completo y sin llave: prueba el arnés, los
verificadores y las herramientas, no la calidad de un modelo. La decisión de disputar o escalar la toma
`decidir` del motor (P4); aquí solo se ubica la transacción y se redacta con plantillas.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from latam_gobierno.politica import cargar as cargar_politica
from latam_tecnologia.herramientas.agente import AVISO_ESCALAR
from latam_tecnologia.herramientas.puertos import CasoAbierto, Producto, Transaccion
from latam_tecnologia.motor.caso import decidir
from pydantic import TypeAdapter
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from latam_ia.evaluacion.idioma import detectar_idioma

_TXS = TypeAdapter(tuple[Transaccion, ...])
_POLITICA = cargar_politica()
_PRODS = TypeAdapter(tuple[Producto, ...])


def _productos(texto: str) -> tuple[Producto, ...]:
    """Productos de la lectura, sin las anotaciones de la herramienta (p. ej. `bloqueable_aqui`)."""
    campos = set(Producto.model_fields)
    filas: list[dict[str, object]] = json.loads(texto or "[]")
    return _PRODS.validate_python([{k: v for k, v in f.items() if k in campos} for f in filas])


def _transacciones(texto: str) -> tuple[Transaccion, ...]:
    """Transacciones de la lectura, sin las anotaciones de la herramienta (p. ej. `tarjeta_final`)."""
    campos = set(Transaccion.model_fields)
    filas: list[dict[str, object]] = json.loads(texto or "[]")
    return _TXS.validate_python([{k: v for k, v in f.items() if k in campos} for f in filas])


_CASOS = TypeAdapter(tuple[CasoAbierto, ...])


def norm(texto: str) -> str:
    sin = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin if unicodedata.category(c) != "Mn")


HUMANO = ("persona", "humano", "asesor", "pessoa", "atendente")
URGENTE = ("me llamaron", "transferencia", "en curso", "em andamento", "urgente")
ROBO = ("perdi", "robaron", "roubaram", "roubado", "extravi", "clonaron", "clonaram", "bloquee", "bloqueei")
CREDITO = ("credito", "prestamo", "emprestimo")
RECHAZO = ("rechaz", "recus")
FUERA = ("clima", "receta", "futbol", "chiste", "previsao")
CAMBIO = ("si la hice", "ya me acorde", "ah no", "fui yo")
FRUSTRACION = ("harto", "pesimo", "inutil", "no sirve", "molesto", "ridiculo", "desastre")
DISPUTA = ("cobr", "cargo", "compra", "tarjeta", "cartao", "fraude", "transaccion", "disput", "contest")

TEXTOS: dict[str, dict[str, str]] = {
    "es": {
        "aclarar": "No encuentro ese cobro entre sus transacciones recientes. "
        "¿Me indica el monto, la fecha o el comercio?",
        "opciones": "Encontré varios cobros que podrían ser: {lista}. ¿Cuál es el que no reconoce?",
        "ya_abierto": "Ya tiene un reclamo abierto por ese cobro ({ret}). No abro otro; una persona del "
        "equipo lo está revisando.",
        "radicado_y_escalado": "Su reclamo quedó radicado. Resultado: {caso}. Por el monto, paso además "
        "su caso a una persona del equipo. Quedó en cola ({ret}) y no puedo prometer una hora de atención.",
        "abrir_ok": "Su reclamo quedó radicado. Resultado: {ret}. Una persona del equipo lo revisará.",
        "bloqueo_ok": "Su tarjeta quedó bloqueada. ",
        "ya_bloqueada": "Su tarjeta ya estaba bloqueada, no hace falta bloquearla de nuevo. ",
        "escalar_ok": "Paso su caso a una persona del equipo. Quedó en cola ({ret}) y no puedo prometer "
        "una hora de atención.",
        "denegado": "Entendido, no realizo ninguna acción.",
        "cambio": "Entendido, no abro ninguna disputa. Si más adelante ve algo que no reconoce, con gusto "
        "le ayudo.",
        "credito": "Aquí no se evalúan solicitudes de crédito. Puede consultar esa opción en una sucursal.",
        "fuera": "Solo puedo ayudarle con cobros que no reconoce. Para otros temas use otro canal.",
        "rechazo": "Las compras rechazadas son otro servicio. Puede consultarlas en la app del banco.",
        "oferta_humano": "Lamento la molestia. ¿Prefiere que lo pase con una persona del equipo?",
        "sin_datos": "¿Me cuenta qué cobro le preocupa?",
    },
    "pt": {
        "aclarar": "Não encontro essa cobrança entre as transações recentes. "
        "Pode informar o valor, a data ou o comércio?",
        "opciones": "Encontrei várias cobranças possíveis: {lista}. Qual delas você não reconhece?",
        "ya_abierto": "Você já tem uma contestação aberta para essa cobrança ({ret}). Não abro outra; uma "
        "pessoa da equipe está analisando.",
        "radicado_y_escalado": "Sua contestação foi registrada. Resultado: {caso}. Pelo valor, passo também "
        "o seu caso a uma pessoa da equipe. Ficou na fila ({ret}) e não posso prometer um horário.",
        "abrir_ok": "Sua contestação foi registrada. Resultado: {ret}. Uma pessoa da equipe vai analisar.",
        "bloqueo_ok": "Seu cartão foi bloqueado. ",
        "ya_bloqueada": "Seu cartão já estava bloqueado, não precisa bloquear de novo. ",
        "escalar_ok": "Passo o seu caso a uma pessoa da equipe. Ficou na fila ({ret}) e não posso "
        "prometer um horário de atendimento.",
        "denegado": "Entendido, não vou fazer nenhuma ação.",
        "cambio": "Entendido, não abro nenhuma contestação.",
        "credito": "Aqui não avaliamos pedidos de crédito. Procure uma agência.",
        "fuera": "Só posso ajudar com cobranças que você não reconhece.",
        "rechazo": "Compras recusadas são outro serviço. Consulte o aplicativo do banco.",
        "oferta_humano": "Lamento o transtorno. Prefere falar com uma pessoa da equipe?",
        "sin_datos": "Pode contar qual cobrança preocupa você?",
    },
}


@dataclass(frozen=True)
class Llamada:
    nombre: str
    args: dict[str, Any]
    retorno: str | None
    denegada: bool


def _textos_usuario(mensajes: list[ModelMessage]) -> list[str]:
    salida: list[str] = []
    for m in mensajes:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, UserPromptPart) and isinstance(p.content, str):
                    salida.append(p.content)
    return salida


def _llamadas_del_turno(mensajes: list[ModelMessage]) -> list[Llamada]:
    """Llamadas y retornos desde el último mensaje del cliente."""
    llamadas: list[tuple[str, str, dict[str, Any]]] = []
    retornos: dict[str, ToolReturnPart] = {}
    for m in mensajes:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, UserPromptPart):
                    llamadas, retornos = [], {}
                elif isinstance(p, ToolReturnPart):
                    retornos[p.tool_call_id] = p
        else:
            for p in m.parts:
                if isinstance(p, ToolCallPart):
                    llamadas.append((p.tool_call_id, p.tool_name, p.args_as_dict()))
    salida: list[Llamada] = []
    for id_, nombre, args in llamadas:
        r = retornos.get(id_)
        salida.append(
            Llamada(
                nombre,
                args,
                None if r is None else str(r.content),
                r is not None and r.outcome == "denied",
            )
        )
    return salida


def _numeros(texto: str) -> set[int]:
    salida: set[int] = set()
    for tramo in re.findall(r"\d[\d.,]*", texto):
        limpio = re.sub(r"[.,]", "", tramo)
        if 0 < len(limpio) <= 9:
            salida.add(int(limpio))
    return salida


def _candidatas(txs: tuple[Transaccion, ...], texto: str) -> list[Transaccion]:
    t = norm(texto)
    por_id = [x for x in txs if x.transaction_id.lower() in t]
    if por_id:
        return por_id
    nums = _numeros(texto)
    por_comercio = [x for x in txs if x.comercio and norm(x.comercio) in t]
    por_monto = [x for x in txs if int(x.monto.monto) in nums]
    if por_comercio and por_monto:
        return [x for x in por_comercio if x in por_monto] or por_monto
    return por_comercio or por_monto


def _llamar(nombre: str, **args: object) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart(tool_name=nombre, args=dict(args))])


def _decir(t: dict[str, str], clave: str, prefijo: str = "", **valores: str) -> ModelResponse:
    return ModelResponse(parts=[TextPart(content=prefijo + t[clave].format(**valores))])


def _cualquiera(t: str, palabras: tuple[str, ...]) -> bool:
    return any(p in t for p in palabras)


def _inicio(usuarios: list[str], t: dict[str, str]) -> ModelResponse:
    actual, todo = norm(usuarios[-1]), norm(" ".join(usuarios))
    negativos = sum(_cualquiera(norm(u), FRUSTRACION) for u in usuarios)
    if _cualquiera(actual, HUMANO):
        return _llamar("escalar", motivo="pedido_del_cliente", urgente=False)
    if negativos >= 3 and _cualquiera(actual, FRUSTRACION):
        return _decir(t, "oferta_humano")
    if _cualquiera(actual, URGENTE):
        if _cualquiera(actual, ROBO):
            return _llamar("estado_productos")
        return _llamar("escalar", motivo="fraude_en_curso", urgente=True)
    if _cualquiera(actual, ROBO):
        return _llamar("estado_productos")
    if _cualquiera(actual, CREDITO):
        return _decir(t, "credito")
    if _cualquiera(actual, RECHAZO):
        return _decir(t, "rechazo")
    if _cualquiera(actual, FUERA):
        return _decir(t, "fuera")
    if _cualquiera(actual, CAMBIO):
        return _decir(t, "cambio")
    if _cualquiera(todo, DISPUTA):
        return _llamar("listar_transacciones", limite=50)
    return _decir(t, "sin_datos")


def _tras_listar(txs: tuple[Transaccion, ...], usuarios: list[str], t: dict[str, str]) -> ModelResponse:
    cands = _candidatas(txs, " ".join(usuarios))
    if not cands:
        return _decir(t, "aclarar")
    if len(cands) > 1:
        if len({(c.comercio, c.monto.monto) for c in cands}) == 1:  # cobro duplicado: el más reciente
            elegida = max(cands, key=lambda c: c.event_ts)
            return _llamar("consultar_transaccion", transaction_id=elegida.transaction_id)
        lista = "; ".join(
            f"{i}) {c.comercio} por {c.monto.monto:.0f} {c.monto.moneda}" for i, c in enumerate(cands, 1)
        )
        return _decir(t, "opciones", lista=lista)
    return _llamar("consultar_transaccion", transaction_id=cands[0].transaction_id)


def _historial_con_comercio(tx: Transaccion, historial: tuple[Transaccion, ...]) -> bool:
    return any(
        h.transaction_id != tx.transaction_id
        and h.comercio == tx.comercio
        and h.event_ts < tx.event_ts
        and (h.estado or "").lower() == "completed"
        for h in historial
    )


def _prefijo(llamadas: list[Llamada], t: dict[str, str], robo: bool) -> str:
    """Lo dicho sobre la tarjeta sale de lo que se hizo o se leyó en este turno, nunca de una suposición."""
    if any(x.nombre == "bloquear_tarjeta" and x.retorno is not None and not x.denegada for x in llamadas):
        return t["bloqueo_ok"]
    leidas = next((x for x in llamadas if x.nombre == "estado_productos"), None)
    if robo and leidas is not None and not any(x.nombre == "bloquear_tarjeta" for x in llamadas):
        tarjetas = [p for p in _productos(leidas.retorno or "[]") if p.tipo == "card"]
        if tarjetas and all(p.estado == "blocked" for p in tarjetas):
            return t["ya_bloqueada"]
    return ""


def _resolver(
    llamadas: list[Llamada], usuarios: list[str], urgente: bool, t: dict[str, str]
) -> ModelResponse:
    """Con la transacción y los productos leídos: escalar, o abrir la disputa si no hay ya un caso abierto."""
    productos = _productos(
        next(x for x in reversed(llamadas) if x.nombre == "estado_productos").retorno or "[]"
    )
    consultada = next(x for x in llamadas if x.nombre == "consultar_transaccion")
    tx = _transacciones(f"[{consultada.retorno}]")[0]
    listada = next((x for x in llamadas if x.nombre == "listar_transacciones"), None)
    historial = _transacciones(listada.retorno or "[]") if listada else ()
    propuesta = decidir(tx, productos, urgente, _POLITICA)
    alega_fraude = "fraud" in norm(" ".join(usuarios))
    if propuesta.accion == "abrir_disputa" and alega_fraude and _historial_con_comercio(tx, historial):
        return _llamar("escalar", motivo="historial_con_el_comercio", urgente=False)
    if propuesta.accion == "escalar":
        return _llamar("escalar", motivo=propuesta.motivo, urgente=urgente)
    previos = next((x for x in llamadas if x.nombre == "casos_abiertos"), None)
    if previos is None:
        return _llamar("casos_abiertos")
    abierto = next(
        (c for c in _CASOS.validate_json(previos.retorno or "[]") if c.transaction_id == tx.transaction_id),
        None,
    )
    if abierto is not None:
        return _decir(t, "ya_abierto", ret=abierto.caso)
    return _llamar("abrir_disputa", transaction_id=tx.transaction_id, motivo=propuesta.motivo)


def _aviso_de_escalar(llamadas: list[Llamada]) -> str | None:
    """Motivo que la herramienta pidió tras radicar, si aún no se escaló."""
    abierta = next((x for x in llamadas if x.nombre == "abrir_disputa"), None)
    if abierta is None or abierta.retorno is None or "Siguiente paso obligatorio" not in abierta.retorno:
        return None
    return None if any(x.nombre == "escalar" for x in llamadas) else abierta.retorno


def _paso(mensajes: list[ModelMessage], idioma: str) -> ModelResponse:
    usuarios = _textos_usuario(mensajes)
    # Guarda de idioma: se contesta en el idioma del último mensaje del cliente; sin pista, el del escenario.
    t = TEXTOS[(detectar_idioma(usuarios[-1]) if usuarios else None) or idioma]
    llamadas = _llamadas_del_turno(mensajes)
    if not llamadas:
        return _inicio(usuarios, t)
    ult = llamadas[-1]
    ret = ult.retorno or ""
    actual = norm(usuarios[-1])
    urgente = _cualquiera(actual, URGENTE)
    robo = _cualquiera(norm(" ".join(usuarios)), ROBO)
    consulto = any(x.nombre == "consultar_transaccion" for x in llamadas)
    if ult.denegada:
        return _decir(t, "denegado")
    match ult.nombre:
        case "listar_transacciones":
            return _tras_listar(_transacciones(ret), usuarios, t)
        case "consultar_transaccion":
            if ret == "null":
                return _decir(t, "aclarar")
            return _llamar("estado_productos")
        case "estado_productos":
            productos = _productos(ret)
            if not consulto:  # tarjeta perdida o robada: contener primero
                activas = [p for p in productos if p.tipo == "card" and p.estado != "blocked"]
                if activas:
                    return _llamar("bloquear_tarjeta", product_id=activas[0].product_id)
                if urgente:
                    return _llamar("escalar", motivo="fraude_en_curso", urgente=True)
                return _llamar("listar_transacciones", limite=50)
            return _resolver(llamadas, usuarios, urgente, t)
        case "casos_abiertos":
            return _resolver(llamadas, usuarios, urgente, t)
        case "bloquear_tarjeta":
            if urgente:
                return _llamar("escalar", motivo="fraude_en_curso", urgente=True)
            return _llamar("listar_transacciones", limite=50)
        case "abrir_disputa":
            if _aviso_de_escalar(llamadas) is not None:
                return _llamar("escalar", motivo="monto_sobre_umbral", urgente=False)
            return _decir(t, "abrir_ok", _prefijo(llamadas, t, robo), ret=ret)
        case "escalar":
            abierta = next((x for x in llamadas if x.nombre == "abrir_disputa" and x.retorno), None)
            if abierta is not None and AVISO_ESCALAR.split("{")[0] in (abierta.retorno or ""):
                caso = (abierta.retorno or "").split(AVISO_ESCALAR.split("{")[0])[0]
                return _decir(t, "radicado_y_escalado", _prefijo(llamadas, t, robo), caso=caso, ret=ret)
            return _decir(t, "escalar_ok", _prefijo(llamadas, t, robo), ret=ret)
        case _:
            return _decir(t, "sin_datos")


def crear_modelo_referencia(idioma: str = "es") -> FunctionModel:
    def funcion(mensajes: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return _paso(mensajes, idioma)

    return FunctionModel(funcion, model_name="referencia-guionada")
