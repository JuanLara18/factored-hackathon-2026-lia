"""API de la banca en línea y de la consola del experto (D-33, contrato en `tecnologia/web/API_BANCA.md`).

El cliente sale siempre de la sesión (`X-Sesion`); las referencias (`*_ref`) son opacas y se resuelven solo
entre lo que es del cliente de la sesión; lo ajeno responde 404 como si no existiera. Ningún campo lleva
nombre, documento, correo, teléfono, número de tarjeta ni identificadores internos.
"""

from __future__ import annotations

import hmac
import logging
import os
import uuid
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from latam_comun.dominio import Canal, Confirmacion

from latam_tecnologia.banca.banco import Banco
from latam_tecnologia.banca.modelos import RegistroConversacion, Traspaso
from latam_tecnologia.banca.motivos import MOTIVOS
from latam_tecnologia.banca.refs import ref
from latam_tecnologia.banca.vista import (
    PAIS_POR_MONEDA,
    PAISES,
    en_utc,
    enmascarar,
    es_tarjeta,
    fecha,
    final,
    hora,
    monto,
    vista_paquete,
)
from latam_tecnologia.canales import textos
from latam_tecnologia.canales.demo import Demo, Sesion
from latam_tecnologia.canales.runtime_cliente import (
    AgenteNoDisponible,
    ClienteRuntime,
    estado_de_confianza,
    id_usuario,
)
from latam_tecnologia.herramientas.catalogo import NO_DISPUTABLES, AccesoDenegado, Herramientas
from latam_tecnologia.herramientas.puertos import Producto, Transaccion
from latam_tecnologia.motor.retoma import Conversacion

log = logging.getLogger(__name__)
# Nombres ficticios de los clientes demo, por índice (no son personas reales).
NOMBRES_DEMO = (
    "Valentina Ríos",
    "Mateo Herrera",
    "Camila Duarte",
    "Santiago Vélez",
    "Isabela Mora",
    "Andrés Quintero",
)
VARIABLE_CODIGO = "LATAM_OPERADOR_CODIGO"
MAX_MOVIMIENTOS = 50  # por página
MAX_HISTORIAL = 200  # lo que se lee del oro para paginar y filtrar por producto
VIGENCIA_OPERADOR = timedelta(hours=8)
MAX_OPERADORES = 50
MAX_FALLOS_CODIGO = 5  # intentos fallidos por ventana antes de responder 429
VENTANA_FALLOS = timedelta(minutes=1)
MAX_TEXTO = 2000
RESULTADOS = ("resuelto", "radicado", "escalado", "sin_accion")
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


@dataclass
class _Numeracion:
    """Contadores de la consola: alias que no se reutilizan y fallos recientes del código."""

    desde: datetime
    siguiente: int = 1
    fallos: int = 0


def _error(codigo: str, estado: int) -> JSONResponse:
    return JSONResponse({"error": codigo}, status_code=estado)


async def _json(request: Request) -> dict[str, Any]:
    try:
        cuerpo = await request.json()
    except ValueError:
        return {}
    return cuerpo if isinstance(cuerpo, dict) else {}  # pyright: ignore[reportUnknownVariableType]


# El cuerpo se lee antes del handler; los handlers son síncronos y FastAPI los corre en hilos, así las
# consultas a BigQuery y Firestore no bloquean el bucle de eventos (con una instancia, bloqueaban a todos).
CuerpoJson = Annotated[dict[str, Any], Depends(_json)]


def contexto_reclamo(tx: Transaccion) -> str:
    """Lo que el servidor le fija al agente sobre el reclamo; el modelo no elige ni cambia al cliente."""
    return (
        "Contexto fijado por el servidor: el cliente abrió desde la banca en línea el movimiento "
        f"{tx.transaction_id} ({textos.describir_comercio(tx.comercio, tx.tipo)}, "
        f"{monto(tx.monto.monto, tx.monto.moneda)} {tx.monto.moneda}) y dice no reconocerlo. "
        "Ya está identificado: no le pida "
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
    operadores: dict[str, tuple[str, datetime]] = {}  # token -> (alias, vencimiento)
    numeracion = _Numeracion(desde=demo.reloj())

    # Ayudas

    def _productos(s: Sesion) -> dict[str, Producto]:
        cliente = s.autenticada.cliente_id
        return {ref("prod", cliente, p.product_id): p for p in lectura.productos(cliente)}

    def _movimientos(s: Sesion) -> dict[str, Transaccion]:
        cliente = s.autenticada.cliente_id
        recientes = lectura.transacciones_recientes(cliente, MAX_HISTORIAL)
        return {ref("tx", cliente, t.transaction_id): t for t in recientes}

    def _estado_producto(cliente: str, p: Producto) -> str:
        if banco.bloqueado(cliente, p.product_id):
            return "bloqueada"
        return ESTADOS_PRODUCTO.get((p.estado or "").lower(), p.estado or "desconocido")

    def _casos_abiertos(cliente: str) -> dict[str, str]:
        return {c.transaccion_id: c.caso_ref for c in banco.casos_de(cliente) if c.estado == "abierto"}

    def _cliente_vista(indice: int, pais: str) -> dict[str, Any]:
        return {
            "nombre": NOMBRES_DEMO[indice % len(NOMBRES_DEMO)],
            "alias": f"Cliente {indice + 1} · {PAISES.get(pais, pais)}",
            "pais": pais,
        }

    def _movimiento(s: Sesion, tx: Transaccion, abiertos: dict[str, str]) -> dict[str, Any]:
        cliente = s.autenticada.cliente_id
        caso = abiertos.get(tx.transaction_id)
        lado = textos.sentido(tx.tipo, tx.estado)
        texto_monto = monto(tx.monto.monto, tx.monto.moneda, demo.pais_de(cliente))
        return {
            "tx_ref": ref("tx", cliente, tx.transaction_id),
            "fecha": fecha(tx.event_ts),  # Bogotá; el oro guarda UTC
            "hora": hora(tx.event_ts),
            "descripcion": textos.describir_comercio(tx.comercio, tx.tipo, s.registro),
            "categoria": tx.categoria,
            "categoria_texto": textos.categoria_texto(tx.categoria, s.registro),
            "tipo": tx.tipo,
            "tipo_texto": textos.tipo_texto(tx.tipo, s.registro),
            "canal": tx.canal,
            "canal_texto": textos.canal_texto(tx.canal, s.registro),
            "icono": textos.icono(tx.tipo, tx.categoria),
            "sentido": lado,
            "monto": texto_monto,
            "monto_con_signo": ("+" if lado == "abono" else "-") + texto_monto,
            "moneda": tx.monto.moneda,
            "estado": tx.estado,
            "estado_texto": textos.estado_texto(tx.estado, s.registro),
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
            salida.append({"indice": i, **_cliente_vista(i, pais)})
        return salida

    @router.post("/api/banca/ingresar")
    def ingresar(request: Request, cuerpo_json: CuerpoJson) -> Response:
        cuerpo = cuerpo_json
        indice = cuerpo.get("indice")
        if not isinstance(indice, int) or isinstance(indice, bool) or not 0 <= indice < len(demo.clientes):
            return _error("cliente_desconocido", 400)
        try:
            s = abrir(indice, textos.registro_valido(cuerpo.get("registro")))
        except AgenteNoDisponible:
            return _error("agente_no_disponible", 503)
        cliente = s.autenticada.cliente_id
        pais = demo.pais_de(cliente)
        moneda = next((p.moneda for p in lectura.productos(cliente) if p.moneda), None)
        return JSONResponse(
            {
                "sesion": s.autenticada.id_sesion,
                # Conversación general de la sesión: el asistente atiende sin llegar desde un movimiento.
                "conversacion": s.conversacion_id,
                "cliente": {
                    **_cliente_vista(indice, pais),
                    "moneda": moneda or {v: k for k, v in PAIS_POR_MONEDA.items()}.get(pais, "COP"),
                    "registro": s.registro,
                },
            }
        )

    def _totales(s: Sesion, cliente: str, pais: str, saldos: dict[str, tuple[Any, Any]]) -> dict[str, Any]:
        """Saldo disponible por moneda, gasto del mes en tarjetas y reclamos abiertos."""
        productos = lectura.productos(cliente)
        tarjetas = {p.product_id for p in productos if es_tarjeta(p.tipo)}
        disponible: dict[str, Decimal] = {}
        for p in productos:
            saldo = saldos.get(p.product_id, (None, None))[0]
            if saldo is not None and p.moneda and p.product_id not in tarjetas:
                tipo = (p.tipo or "").lower()
                if "préstamo" not in tipo and "loan" not in tipo and "seguro" not in tipo:
                    disponible[p.moneda] = disponible.get(p.moneda, Decimal(0)) + Decimal(str(saldo))
        mes = fecha(demo.reloj())[:7]
        gasto: dict[str, Decimal] = {}
        for t in lectura.transacciones_recientes(cliente, MAX_HISTORIAL):
            if (
                t.product_id in tarjetas
                and fecha(t.event_ts)[:7] == mes
                and textos.sentido(t.tipo, t.estado) == "cargo"
                and (t.estado or "").lower() in ("approved", "pending")
            ):
                gasto[t.monto.moneda] = gasto.get(t.monto.moneda, Decimal(0)) + Decimal(str(t.monto.monto))

        def _por_moneda(valores: dict[str, Decimal]) -> list[dict[str, Any]]:
            return [{"moneda": m, "monto": monto(v, m, pais)} for m, v in sorted(valores.items())]

        return {
            "saldo_disponible": _por_moneda(disponible),
            "gasto_mes_tarjetas": _por_moneda(gasto),
            "reclamos_abiertos": len(_casos_abiertos(cliente)),
        }

    @router.get("/api/banca/resumen")
    def resumen(request: Request) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cliente = s.autenticada.cliente_id
        pais = demo.pais_de(cliente)
        leer_saldos = getattr(demo.lectura, "saldos", None)
        leidos: object = leer_saldos(cliente) if callable(leer_saldos) else {}
        saldos = cast(dict[str, tuple[Any, Any]], leidos) if isinstance(leidos, dict) else {}

        def _dinero(valor: Any, moneda: str | None) -> str | None:
            return None if valor is None else monto(valor, moneda, pais)

        propios = _productos(s)

        # El estado de bloqueo es una lectura de Firestore por producto: van en paralelo, no una tras otra.
        def _estado(p: Producto) -> str:
            return _estado_producto(cliente, p)

        with ThreadPoolExecutor(max_workers=8) as hilos:
            estados = dict(zip(propios, hilos.map(_estado, propios.values()), strict=True))
        productos = [
            {
                "producto_ref": pref,
                "tipo": p.tipo,
                "etiqueta": etiqueta_producto(p.tipo),
                "final": final(p.product_id),
                "estado": estados[pref],
                "moneda": p.moneda,
                "saldo": _dinero(saldos.get(p.product_id, (None, None))[0], p.moneda),
                "limite": _dinero(saldos.get(p.product_id, (None, None))[1], p.moneda),
            }
            for pref, p in propios.items()
        ]
        indice = demo.clientes.index(cliente)
        return JSONResponse(
            {
                "cliente": {
                    **_cliente_vista(indice, pais),
                    "moneda": next((p["moneda"] for p in productos if p["moneda"]), None),
                    "registro": s.registro,
                },
                "productos": productos,
                "resumen": _totales(s, cliente, pais, saldos),
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
                corte = en_utc(datetime.fromisoformat(antes_de))
            except ValueError:
                return _error("antes_de_invalido", 400)
        txs = sorted(
            _movimientos(s).values(), key=lambda t: (en_utc(t.event_ts), t.transaction_id), reverse=True
        )
        if filtrar:
            txs = [t for t in txs if t.product_id == filtrar]
        if corte is not None:
            txs = [t for t in txs if en_utc(t.event_ts) < corte]
        limite = max(1, min(limite, MAX_MOVIMIENTOS))
        while limite < len(txs) and en_utc(txs[limite].event_ts) == en_utc(txs[limite - 1].event_ts):
            limite += 1  # un empate en el borde no se parte: `antes_de` es estricto y se perdería
        pagina = txs[:limite]
        abiertos = _casos_abiertos(cliente)
        return JSONResponse(
            {
                "movimientos": [_movimiento(s, t, abiertos) for t in pagina],
                "siguiente": en_utc(pagina[-1].event_ts).isoformat() if len(txs) > limite else None,
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
    def reclamar(tx_ref: str, request: Request, cuerpo_json: CuerpoJson) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cuerpo = cuerpo_json
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
        if runtime is not None:  # primero el agente: sin su sesión la conversación no serviría
            try:
                runtime.crear_sesion(
                    user_id=id_usuario(cliente),
                    session_id=conversacion,
                    estado={
                        **estado_de_confianza(s.autenticada, conversacion),
                        "contexto": contexto,
                    },
                )
            except AgenteNoDisponible:
                return _error("agente_no_disponible", 503)
        s.contextos[conversacion] = contexto
        s.reclamos[tx_ref] = conversacion
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
                    "monto": monto(c.monto, c.moneda, demo.pais_de(cliente)),
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
    def bloqueo(producto_ref: str, request: Request, cuerpo_json: CuerpoJson) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        cuerpo = cuerpo_json
        if cuerpo.get("confirmo") is not True:
            return _error("confirmacion_requerida", 400)
        cliente = s.autenticada.cliente_id
        producto = _productos(s).get(producto_ref)
        if producto is None:
            return _error("producto_desconocido", 404)
        if not es_tarjeta(producto.tipo):
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
    def escribir(conversacion: str, request: Request, cuerpo_json: CuerpoJson) -> Response:
        s = _requiere_sesion(request)
        if isinstance(s, JSONResponse):
            return s
        if _propia(s, conversacion) is None:
            return _error("conversacion_desconocida", 404)
        texto = str(cuerpo_json.get("texto", "")).strip()
        if not texto or len(texto) > MAX_TEXTO:
            return _error("texto_invalido", 400)
        t = banco.traspaso_de_conversacion(conversacion)
        if t is None or t.estado == "resuelto":
            return _error("sin_persona", 409)
        return JSONResponse({"id": banco.agregar_mensaje(conversacion, "cliente", texto)})

    # Experto

    def _operador(request: Request) -> str | JSONResponse:
        token = request.headers.get("x-operador", "")
        entrada = operadores.get(token)
        if entrada is None:
            return _error("operador", 401)
        if demo.reloj() >= entrada[1]:
            operadores.pop(token, None)
            return _error("operador", 401)
        return entrada[0]

    @router.post("/api/operador/ingresar")
    def operador_ingresar(request: Request, cuerpo_json: CuerpoJson) -> Response:
        esperado = env.get(VARIABLE_CODIGO, "")
        if not esperado:
            return _error("operador_no_configurado", 503)
        ahora = demo.reloj()
        if ahora - numeracion.desde > VENTANA_FALLOS:
            numeracion.fallos, numeracion.desde = 0, ahora
        if numeracion.fallos >= MAX_FALLOS_CODIGO:
            return _error("demasiados_intentos", 429)
        codigo = str(cuerpo_json.get("codigo", ""))
        if not hmac.compare_digest(codigo.encode(), esperado.encode()):
            numeracion.fallos += 1
            return _error("codigo", 401)
        numeracion.fallos = 0
        for vencido in [t for t, (_, exp) in operadores.items() if ahora >= exp]:
            del operadores[vencido]
        # Con el cupo lleno sale la sesión más antigua: negar el ingreso dejaba la consola cerrada durante horas
        # (pasó el 5 oct, cuando la instancia dejó de apagarse y las pruebas agotaron las cincuenta sesiones).
        while len(operadores) >= MAX_OPERADORES:
            del operadores[min(operadores, key=lambda t: operadores[t][1])]
        token = uuid.uuid4().hex
        operadores[token] = (f"Experto {numeracion.siguiente}", ahora + VIGENCIA_OPERADOR)
        numeracion.siguiente += 1
        return JSONResponse({"sesion_operador": token})

    @router.post("/api/demo/restablecer")
    def restablecer(request: Request, cuerpo_json: CuerpoJson) -> Response:
        """Deja limpio el estado de los clientes demo; lo pide el operador (sesión o código)."""
        if isinstance(_operador(request), JSONResponse):
            esperado = env.get(VARIABLE_CODIGO, "")
            if not esperado:
                return _error("operador_no_configurado", 503)
            ahora = demo.reloj()
            if ahora - numeracion.desde > VENTANA_FALLOS:
                numeracion.fallos, numeracion.desde = 0, ahora
            if numeracion.fallos >= MAX_FALLOS_CODIGO:
                return _error("demasiados_intentos", 429)
            codigo = str(cuerpo_json.get("codigo", ""))
            if not hmac.compare_digest(codigo.encode(), esperado.encode()):
                numeracion.fallos += 1
                return _error("operador", 401)
        cuentas = banco.restablecer(demo.clientes)
        propios = set(demo.clientes)
        for sesion in demo.sesiones.values():
            if sesion.autenticada.cliente_id in propios:
                sesion.reclamos.clear()
                sesion.contextos.clear()
        log.info("demo restablecida: %s", cuentas)  # solo conteos
        return JSONResponse({"restablecido": True, **cuentas})

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
    def operador_mensaje(identificador: str, request: Request, cuerpo_json: CuerpoJson) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        t = _mio(identificador, o)
        if isinstance(t, JSONResponse):
            return t
        texto = str(cuerpo_json.get("texto", "")).strip()
        if not texto or len(texto) > MAX_TEXTO:
            return _error("texto_invalido", 400)
        return JSONResponse({"id": banco.agregar_mensaje(t.conversacion_id, "persona", texto)})

    @router.post("/api/operador/traspasos/{identificador}/resolver")
    def resolver(identificador: str, request: Request, cuerpo_json: CuerpoJson) -> Response:
        o = _operador(request)
        if isinstance(o, JSONResponse):
            return o
        t = _mio(identificador, o)
        if isinstance(t, JSONResponse):
            return t
        cuerpo = cuerpo_json
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
