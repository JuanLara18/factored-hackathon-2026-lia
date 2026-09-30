"""API de la banca en línea y de la consola del experto (D-33, contrato en `tecnologia/web/API_BANCA.md`).

El cliente sale siempre de la sesión (`X-Sesion`); las referencias (`*_ref`) son opacas y se resuelven solo
entre lo que es del cliente de la sesión; lo ajeno responde 404 como si no existiera. Ningún campo lleva
nombre, documento, correo, teléfono, número de tarjeta ni identificadores internos.
"""

from __future__ import annotations

import hmac
import os
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from latam_comun.dominio import Canal, Confirmacion

from latam_tecnologia.banca.banco import Banco
from latam_tecnologia.banca.modelos import RegistroConversacion, Traspaso
from latam_tecnologia.banca.motivos import MOTIVOS
from latam_tecnologia.banca.refs import ref
from latam_tecnologia.banca.vista import (
    PAIS_POR_MONEDA,
    PAISES,
    enmascarar,
    final,
    hora,
    monto,
    vista_paquete,
)
from latam_tecnologia.canales import textos
from latam_tecnologia.canales.demo import Demo, Sesion
from latam_tecnologia.canales.runtime_cliente import ClienteRuntime, estado_de_confianza, id_usuario
from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion

VARIABLE_CODIGO = "LATAM_OPERADOR_CODIGO"
MAX_MOVIMIENTOS = 50
MAX_TEXTO = 2000
RESULTADOS = ("resuelto", "radicado", "escalado", "sin_accion")
NO_DISPUTABLES = ("declined", "failed", "reversed")  # ESC-02 de policy/v1
TIPOS_PRODUCTO = {
    "credit_card": "Tarjeta de crédito",
    "debit_card": "Tarjeta débito",
    "savings": "Cuenta de ahorros",
    "checking": "Cuenta corriente",
    "loan": "Préstamo",
}
# El oro operacional ya trae el tipo en español ("Tarjeta Crédito"); se normaliza a la forma del sitio.
TIPOS_PRODUCTO_ES = {
    "tarjeta crédito": "Tarjeta de crédito",
    "tarjeta débito": "Tarjeta débito",
    "cuenta ahorro": "Cuenta de ahorros",
    "cuenta corriente": "Cuenta corriente",
    "préstamo personal": "Préstamo personal",
    "préstamo hipotecario": "Crédito hipotecario",
    "inversión": "Inversión",
    "seguro": "Seguro",
}


def etiqueta_producto(tipo: str | None) -> str:
    clave = (tipo or "").strip().lower()
    return TIPOS_PRODUCTO.get(clave) or TIPOS_PRODUCTO_ES.get(clave) or (tipo or "Producto").strip()


ESTADOS_PRODUCTO = {
    "active": "activa",
    "blocked": "bloqueada",
    "suspended": "suspendida",
    "closed": "cerrada",
    "inactive": "inactiva",
}

Abrir = Callable[[int, str], Sesion]


def _error(codigo: str, estado: int) -> JSONResponse:
    return JSONResponse({"error": codigo}, status_code=estado)


async def _json(request: Request) -> dict[str, Any]:
    try:
        cuerpo = await request.json()
    except ValueError:
        return {}
    return cuerpo if isinstance(cuerpo, dict) else {}  # pyright: ignore[reportUnknownVariableType]


def contexto_reclamo(tx: Transaccion) -> str:
    """Lo que el servidor le fija al agente sobre el reclamo; el modelo no elige ni cambia al cliente."""
    return (
        "Contexto fijado por el servidor: el cliente abrió desde la banca en línea el movimiento "
        f"{tx.transaction_id} ({textos.describir_comercio(tx.comercio, tx.tipo)}, "
        f"{monto(tx.monto.monto)} {tx.monto.moneda}) y dice no reconocerlo. Ya está identificado: no le pida "
        "que lo busque ni que lo describa. Empiece consultándolo con consultar_transaccion, cuéntele lo que "
        "ve y ofrézcale abrir la disputa."
    )


def crear_router(
    *,
    demo: Demo,
    herramientas: Herramientas,
    sesion_de: Callable[[Request], Sesion | None],
    abrir: Abrir,
    runtime: ClienteRuntime | None = None,
    entorno: Mapping[str, str] | None = None,
) -> APIRouter:
    router = APIRouter()
    banco: Banco = demo.banco
    lectura = demo.lectura
    env = os.environ if entorno is None else entorno
    operadores: dict[str, str] = {}

    # Ayudas

    def _productos(s: Sesion) -> dict[str, Producto]:
        cliente = s.autenticada.cliente_id
        return {ref("prod", cliente, p.product_id): p for p in lectura.productos(cliente)}

    def _movimientos(s: Sesion) -> dict[str, Transaccion]:
        cliente = s.autenticada.cliente_id
        recientes = lectura.transacciones_recientes(cliente, MAX_MOVIMIENTOS)
        return {ref("tx", cliente, t.transaction_id): t for t in recientes}

    def _estado_producto(cliente: str, p: Producto) -> str:
        if banco.bloqueado(cliente, p.product_id):
            return "bloqueada"
        return ESTADOS_PRODUCTO.get((p.estado or "").lower(), p.estado or "desconocido")

    def _casos_abiertos(cliente: str) -> dict[str, str]:
        return {c.transaccion_id: c.caso_ref for c in banco.casos_de(cliente) if c.estado == "abierto"}

    def _movimiento(s: Sesion, tx: Transaccion, abiertos: dict[str, str]) -> dict[str, Any]:
        cliente = s.autenticada.cliente_id
        caso = abiertos.get(tx.transaction_id)
        return {
            "tx_ref": ref("tx", cliente, tx.transaction_id),
            "fecha": tx.event_ts.date().isoformat(),
            "hora": tx.event_ts.strftime("%H:%M"),
            "descripcion": textos.describir_comercio(tx.comercio, tx.tipo),
            "categoria": tx.categoria,
            "tipo": tx.tipo,
            "canal": tx.canal,
            "monto": monto(tx.monto.monto),
            "moneda": tx.monto.moneda,
            "estado": tx.estado,
            "pais": tx.pais,
            "es_extranjera": tx.es_extranjera,
            "tarjeta_final": final(tx.product_id),
            "reclamable": caso is None and (tx.estado or "").lower() not in NO_DISPUTABLES,
            "caso_ref": caso,
        }

    def _propia(s: Sesion, conversacion: str) -> RegistroConversacion | None:
        c = banco.conversacion(conversacion)
        if c is None or c.cliente_id != s.autenticada.cliente_id:
            return None
        return c

    def _requiere_sesion(request: Request) -> Sesion | JSONResponse:
        s = sesion_de(request)
        return _error("sesion", 401) if s is None else s

    # Cliente

    @router.get("/api/banca/clientes-demo")
    def clientes_demo() -> list[dict[str, Any]]:
        salida: list[dict[str, Any]] = []
        for i, cliente in enumerate(demo.clientes):
            pais = demo.pais_de(cliente)
            salida.append({"indice": i, "alias": f"Cliente {i + 1} · {PAISES.get(pais, pais)}", "pais": pais})
        return salida

    @router.post("/api/banca/ingresar")
    async def ingresar(request: Request) -> Response:
        cuerpo = await _json(request)
        indice = cuerpo.get("indice")
        if not isinstance(indice, int) or isinstance(indice, bool) or not 0 <= indice < len(demo.clientes):
            return _error("cliente_desconocido", 400)
        s = abrir(indice, textos.registro_valido(cuerpo.get("registro")))
        cliente = s.autenticada.cliente_id
        pais = demo.pais_de(cliente)
        moneda = next((p.moneda for p in lectura.productos(cliente) if p.moneda), None)
        return JSONResponse(
            {
                "sesion": s.autenticada.id_sesion,
                "cliente": {
                    "alias": f"Cliente {indice + 1} · {PAISES.get(pais, pais)}",
                    "pais": pais,
                    "moneda": moneda or {v: k for k, v in PAIS_POR_MONEDA.items()}.get(pais, "COP"),
                    "registro": s.registro,
                },
            }
        )

    @router.get("/api/banca/resumen")
    def resumen(request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cliente = s.autenticada.cliente_id
        pais = demo.pais_de(cliente)
        productos = [
            {
                "producto_ref": pref,
                "tipo": p.tipo,
                "etiqueta": etiqueta_producto(p.tipo),
                "final": final(p.product_id),
                "estado": _estado_producto(cliente, p),
                "moneda": p.moneda,
                "saldo": None,
                "limite": None,
            }
            for pref, p in _productos(s).items()
        ]
        indice = demo.clientes.index(cliente)
        return JSONResponse(
            {
                "cliente": {
                    "alias": f"Cliente {indice + 1} · {PAISES.get(pais, pais)}",
                    "pais": pais,
                    "moneda": next((p["moneda"] for p in productos if p["moneda"]), None),
                    "registro": s.registro,
                },
                "productos": productos,
            }
        )

    @router.get("/api/banca/movimientos")
    def movimientos(
        request: Request, producto_ref: str = "", limite: int = MAX_MOVIMIENTOS, antes_de: str = ""
    ) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cliente = s.autenticada.cliente_id
        filtrar: str | None = None
        if producto_ref:
            producto = _productos(s).get(producto_ref)
            if producto is None:
                return _error("producto_desconocido", 404)
            filtrar = producto.product_id
        corte: datetime | None = None
        if antes_de:
            try:
                corte = datetime.fromisoformat(antes_de)
            except ValueError:
                return _error("antes_de_invalido", 400)
        txs = sorted(_movimientos(s).values(), key=lambda t: t.event_ts, reverse=True)
        if filtrar:
            txs = [t for t in txs if t.product_id == filtrar]
        if corte is not None:
            txs = [t for t in txs if t.event_ts < corte]
        limite = max(1, min(limite, MAX_MOVIMIENTOS))
        pagina = txs[:limite]
        abiertos = _casos_abiertos(cliente)
        return JSONResponse(
            {
                "movimientos": [_movimiento(s, t, abiertos) for t in pagina],
                "siguiente": pagina[-1].event_ts.isoformat() if len(txs) > limite else None,
            }
        )

    @router.get("/api/banca/movimientos/{tx_ref}")
    def movimiento(tx_ref: str, request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        tx = _movimientos(s).get(tx_ref)
        if tx is None:
            return _error("movimiento_desconocido", 404)
        return JSONResponse(_movimiento(s, tx, _casos_abiertos(s.autenticada.cliente_id)))

    @router.post("/api/banca/movimientos/{tx_ref}/reclamar")
    async def reclamar(tx_ref: str, request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cuerpo = await _json(request)
        cliente = s.autenticada.cliente_id
        tx = _movimientos(s).get(tx_ref)
        if tx is None:
            return _error("movimiento_desconocido", 404)
        abiertos = _casos_abiertos(cliente)
        if tx.transaction_id in abiertos:
            return JSONResponse(
                {"error": "ya_reclamado", "caso_ref": abiertos[tx.transaction_id]}, status_code=409
            )
        if (tx.estado or "").lower() in NO_DISPUTABLES:
            return _error("no_reclamable", 409)
        existente = s.reclamos.get(tx_ref)
        if existente is not None:  # el mismo movimiento reabre la misma conversación
            return JSONResponse({"conversacion": existente})
        registro = textos.registro_valido(cuerpo.get("registro") or s.registro)
        conversacion = f"c-{uuid.uuid4().hex[:12]}"
        demo.almacen.crear_conversacion(
            Conversacion(id=conversacion, cliente_ref=cliente, canal_actual=Canal.CHAT, estado="inicio")
        )
        banco.registrar_conversacion(
            RegistroConversacion(
                id=conversacion,
                cliente_id=cliente,
                registro=registro,
                pais=demo.pais_de(cliente),
                transaccion_id=tx.transaction_id,
                creada_en=demo.reloj(),
            )
        )
        contexto = contexto_reclamo(tx)
        s.contextos[conversacion] = contexto
        s.reclamos[tx_ref] = conversacion
        if runtime is not None:
            runtime.crear_sesion(
                user_id=id_usuario(cliente),
                session_id=conversacion,
                estado={
                    **estado_de_confianza(s.autenticada, conversacion),
                    "contexto": contexto,
                },
            )
        return JSONResponse({"conversacion": conversacion})

    @router.get("/api/banca/reclamos")
    def reclamos(request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cliente = s.autenticada.cliente_id
        hilos = [s.conversacion_id, *s.contextos]
        traspasos = [t for t in (banco.traspaso_de_conversacion(c) for c in hilos) if t is not None]
        salida: list[dict[str, Any]] = []
        for c in sorted(banco.casos_de(cliente), key=lambda c: c.abierto_en, reverse=True):
            tx = lectura.transaccion(cliente, c.transaccion_id)
            historial = [(e.fecha, e.evento) for e in c.historial]
            historial += [
                (t.creado_en, "El caso pasó a una persona del equipo")
                for t in traspasos
                if t.paquete.caso_id == c.caso_ref
            ]
            salida.append(
                {
                    "caso_ref": c.caso_ref,
                    "tx_ref": ref("tx", cliente, c.transaccion_id),
                    "descripcion": textos.describir_comercio(tx.comercio, tx.tipo) if tx else "Movimiento",
                    "monto": monto(c.monto),
                    "moneda": c.moneda,
                    "estado": c.estado,
                    "abierto_en": c.abierto_en.isoformat(),
                    "credito_provisional": c.credito_provisional,
                    "plazo": c.plazo,
                    "historial": [
                        {"fecha": f.isoformat(), "evento": e}
                        for f, e in sorted(historial, key=lambda x: x[0])
                    ],
                }
            )
        return JSONResponse(salida)

    @router.post("/api/banca/tarjetas/{producto_ref}/bloqueo")
    async def bloqueo(producto_ref: str, request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cuerpo = await _json(request)
        if cuerpo.get("confirmo") is not True:
            return _error("confirmacion_requerida", 400)
        cliente = s.autenticada.cliente_id
        producto = _productos(s).get(producto_ref)
        if producto is None:
            return _error("producto_desconocido", 404)
        if "card" not in (producto.tipo or "").lower():
            return _error("no_es_tarjeta", 400)
        ya = _estado_producto(cliente, producto) == "bloqueada"
        try:
            herramientas.bloquear_tarjeta(
                s.autenticada,
                s.conversacion_id,
                producto.product_id,
                Confirmacion(
                    accion="bloquear_tarjeta", canal=Canal.CHAT, evidencia="boton", nonce=uuid.uuid4().hex
                ),
            )
        except AccesoDenegado:
            return _error("acceso_denegado", 403)
        return JSONResponse({"estado": "bloqueada", "ya_estaba": ya})

    @router.get("/api/banca/conversaciones/{conversacion}/mensajes")
    def mensajes(conversacion: str, request: Request, desde: str = "") -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        if _propia(s, conversacion) is None:
            return _error("conversacion_desconocida", 404)
        return JSONResponse(
            [
                {"id": m.id, "autor": m.autor, "texto": m.texto, "en": hora(m.en)}
                for m in banco.mensajes(conversacion, desde or None)
            ]
        )

    @router.post("/api/banca/conversaciones/{conversacion}/mensajes")
    async def escribir(conversacion: str, request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        if _propia(s, conversacion) is None:
            return _error("conversacion_desconocida", 404)
        texto = str((await _json(request)).get("texto", "")).strip()
        if not texto or len(texto) > MAX_TEXTO:
            return _error("texto_invalido", 400)
        t = banco.traspaso_de_conversacion(conversacion)
        if t is None or t.estado == "resuelto":
            return _error("sin_persona", 409)
        return JSONResponse({"id": banco.agregar_mensaje(conversacion, "cliente", texto)})

    # Experto

    def _operador(request: Request) -> str | JSONResponse:
        alias = operadores.get(request.headers.get("x-operador", ""))
        return _error("operador", 401) if alias is None else alias

    @router.post("/api/operador/ingresar")
    async def operador_ingresar(request: Request) -> Response:
        esperado = env.get(VARIABLE_CODIGO, "")
        if not esperado:
            return _error("operador_no_configurado", 503)
        codigo = str((await _json(request)).get("codigo", ""))
        if not hmac.compare_digest(codigo.encode(), esperado.encode()):
            return _error("codigo", 401)
        token = uuid.uuid4().hex
        operadores[token] = f"Experto {len(operadores) + 1}"
        return JSONResponse({"sesion_operador": token})

    def _fila(t: Traspaso) -> dict[str, Any]:
        p = t.paquete
        return {
            "id_traspaso": t.id_traspaso,
            "prioridad": t.prioridad,
            "motivo": p.motivo,
            "motivo_texto": p.motivo_texto,
            "pais": p.pais_cuenta,
            "idioma": p.idioma.value,
            "registro": p.registro,
            "canal": p.canal_actual.value,
            "creado_hace_s": max(0, int((demo.reloj() - t.creado_en).total_seconds())),
            "estado": t.estado,
            "tomado_por": t.tomado_por,
        }

    @router.get("/api/operador/cola")
    def cola(request: Request) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        return JSONResponse([_fila(t) for t in banco.cola()])

    @router.get("/api/operador/traspasos/{identificador}")
    def traspaso(identificador: str, request: Request) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        t = banco.traspaso(identificador)
        if t is None:
            return _error("traspaso_desconocido", 404)
        conv = banco.conversacion(t.conversacion_id)
        sugerencia = MOTIVOS.get(t.paquete.motivo) or MOTIVOS["FUERA_DE_RUTINA"]
        return JSONResponse(
            vista_paquete(
                t,
                demo.reloj(),
                conv.transcripcion if conv else [],
                banco.mensajes(t.conversacion_id),
                sugerencia,
            )
        )

    @router.post("/api/operador/traspasos/{identificador}/tomar")
    def tomar(identificador: str, request: Request) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        resultado = banco.tomar(identificador, o)
        if resultado == "inexistente":
            return _error("traspaso_desconocido", 404)
        if resultado != "tomado":
            return _error(resultado, 409)
        return JSONResponse({"estado": "tomado"})

    def _mio(identificador: str, o: str) -> Traspaso | JSONResponse:
        t = banco.traspaso(identificador)
        if t is None:
            return _error("traspaso_desconocido", 404)
        if t.estado != "tomado" or t.tomado_por != o:
            return _error("no_tomado_por_usted", 409)
        return t

    @router.post("/api/operador/traspasos/{identificador}/mensaje")
    async def operador_mensaje(identificador: str, request: Request) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        t = _mio(identificador, o)
        if isinstance(t, JSONResponse):
            return t
        texto = str((await _json(request)).get("texto", "")).strip()
        if not texto or len(texto) > MAX_TEXTO:
            return _error("texto_invalido", 400)
        return JSONResponse({"id": banco.agregar_mensaje(t.conversacion_id, "persona", texto)})

    @router.post("/api/operador/traspasos/{identificador}/resolver")
    async def resolver(identificador: str, request: Request) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        t = _mio(identificador, o)
        if isinstance(t, JSONResponse):
            return t
        cuerpo = await _json(request)
        resultado = str(cuerpo.get("resultado", ""))
        if resultado not in RESULTADOS:
            return _error("resultado_invalido", 400)
        etiqueta: Any = cuerpo.get("etiqueta_correccion")
        if isinstance(etiqueta, dict):
            etiqueta = {
                str(k)[:60]: (enmascarar(v, 1000) if isinstance(v, str) else v)
                for k, v in list(cast(dict[Any, Any], etiqueta).items())[:20]
                if isinstance(v, str | int | float | bool | None)
            }
        else:
            etiqueta = None
        banco.resolver(identificador, resultado, etiqueta, enmascarar(str(cuerpo.get("nota", "")), 1000))
        return JSONResponse({"estado": "resuelto"})

    return router
