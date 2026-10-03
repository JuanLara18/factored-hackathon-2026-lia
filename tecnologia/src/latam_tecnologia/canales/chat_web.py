"""Chat web (TEC-3): el endpoint AG-UI conectado al agente de disputas real, con sesión de demostración.

El cliente sale de la sesión, nunca del navegador ni del modelo. Las acciones con efecto se aprueban con el
evento de interrupción de AG-UI, con vencimiento de 5 minutos y de un solo uso (R-CLI-44, R-CLI-46).
El botón de persona no pasa por el modelo: llama a `escalar` y responde en el acto (R-CLI-34).
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, cast

from ag_ui.core import RunFinishedInterruptOutcome
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.api_core.exceptions import GoogleAPICallError, RetryError
from latam_comun.dominio import Canal
from pydantic_ai import DeferredToolRequests
from pydantic_ai.models import Model

from latam_tecnologia import observabilidad
from latam_tecnologia.banca.api import crear_router
from latam_tecnologia.banca.vista import enmascarar
from latam_tecnologia.banca.vista import monto as monto_pais
from latam_tecnologia.canales import textos
from latam_tecnologia.canales.chat_agui import ChatAdapter, FiltradoEventStream
from latam_tecnologia.canales.demo import Demo, Sesion, crear_demo
from latam_tecnologia.canales.modelo import crear_modelo
from latam_tecnologia.canales.runtime_cliente import (
    VARIABLE_RECURSO,
    AgenteNoDisponible,
    ClienteAgentRuntime,
    ClienteRuntime,
    estado_de_confianza,
    flujo_agui,
    id_usuario,
)
from latam_tecnologia.herramientas.agente import ContextoAgente, crear_agente_disputas
from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas

VIGENCIA_CONFIRMACION = timedelta(minutes=5)
MAX_CUERPO = 64 * 1024  # bytes; ningún cuerpo legítimo de la API se le acerca
MAX_MENSAJE = 4000  # caracteres del mensaje del cliente al agente
MAX_VIVAS = 2000  # confirmaciones emitidas y sin gastar, por proceso
log = logging.getLogger(__name__)
WEB_DIR = Path(__file__).resolve().parents[3] / "web" / "chat"
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
_PERSONA = re.compile(r"\b(persona|pessoa|humano|asesor|atendente)\b", re.IGNORECASE)

Enriquecedor = Callable[[str, str, dict[str, Any]], tuple[str, str]]


@dataclass
class Vencimientos:
    """Confirmaciones emitidas: vigentes 5 minutos, de una sesión y de un solo uso."""

    reloj: Callable[[], datetime] = lambda: datetime.now(UTC)
    _vivas: dict[tuple[str, str], datetime] = field(default_factory=dict[tuple[str, str], datetime])

    def emitir(self, sesion: str, interrupcion: str) -> datetime:
        ahora = self.reloj()
        expira = ahora + VIGENCIA_CONFIRMACION
        if len(self._vivas) >= MAX_VIVAS:  # sin esto, cada turno sin resolver se queda en memoria
            for clave in [c for c, e in self._vivas.items() if e <= ahora] or list(self._vivas)[:100]:
                del self._vivas[clave]
        self._vivas[(sesion, interrupcion)] = expira
        return expira

    def consumir(self, sesion: str, interrupcion: str) -> str:
        """`ok`, `vencida` o `desconocida`; en cualquier caso la confirmación queda gastada."""
        expira = self._vivas.pop((sesion, interrupcion), None)
        if expira is None:
            return "desconocida"
        return "ok" if self.reloj() < expira else "vencida"


@dataclass
class EventosChat(FiltradoEventStream):
    """Añade a cada interrupción el texto de la plantilla, el monto de la base y el vencimiento."""

    enriquecer: Enriquecedor | None = None

    def _build_outcome(self) -> Any:
        resultado = super()._build_outcome()
        salida = self._result.output if self._result else None
        if (
            self.enriquecer is None
            or not isinstance(resultado, RunFinishedInterruptOutcome)
            or not isinstance(salida, DeferredToolRequests)
        ):
            return resultado
        llamadas = {c.tool_call_id: c for c in salida.approvals}
        for interrupcion in resultado.interrupts:
            llamada = llamadas.get(interrupcion.tool_call_id or "")
            if llamada is None:
                continue
            mensaje, expira = self.enriquecer(interrupcion.id, llamada.tool_name, llamada.args_as_dict())
            interrupcion.message = mensaje
            interrupcion.expires_at = expira
            interrupcion.metadata = {"herramienta": llamada.tool_name, "vigencia_s": 300}
        return resultado


@dataclass
class AdaptadorChat(ChatAdapter):
    enriquecer: Enriquecedor | None = None
    registro: str = "usted"

    def build_event_stream(self) -> EventosChat:
        return EventosChat(
            self.run_input,
            accept=self.accept,
            ag_ui_version=self.ag_ui_version,
            traza=self.traza,
            registro=self.registro,
            enriquecer=self.enriquecer,
        )


def _cuerpo(crudo: bytes) -> dict[str, Any]:
    """El cuerpo JSON como objeto; vacío o malformado es `{}` y cada ruta decide qué responder."""
    try:
        valor: Any = json.loads(crudo or b"{}")
    except ValueError:
        return {}
    return cast(dict[str, Any], valor) if isinstance(valor, dict) else {}


def _mensajes(cuerpo: dict[str, Any]) -> list[dict[str, Any]]:
    crudos: object = cuerpo.get("messages")
    if not isinstance(crudos, list):
        return []
    return [cast(dict[str, Any], m) for m in cast(list[object], crudos) if isinstance(m, dict)]


def _texto_ultimo_usuario(cuerpo: dict[str, Any]) -> str:
    for m in reversed(_mensajes(cuerpo)):
        if m.get("role") == "user":
            return str(m.get("content", ""))
    return ""


def _aprobada(resume: dict[str, Any]) -> bool:
    carga: dict[str, Any] = resume.get("payload") or {}
    return bool(carga.get("approved"))


def _final(product_id: str) -> str:
    return re.sub(r"\D", "", product_id).rjust(4, "0")[-4:]


ORIGENES_SITIO = (
    "https://latam-bank-hackaton-2026.web.app",
    "https://latam-bank-hackaton-2026.firebaseapp.com",
    "http://localhost:5000",
    "http://localhost:8765",
)


def origenes_cors(entorno: dict[str, str] | None) -> list[str]:
    """Orígenes del sitio que pueden llamar a la API; `LATAM_CORS_ORIGINS` (con comas) los reemplaza."""
    valor = (entorno if entorno is not None else dict(os.environ)).get("LATAM_CORS_ORIGINS", "")
    return [o.strip() for o in valor.split(",") if o.strip()] or list(ORIGENES_SITIO)


async def _cuerpo_crudo(request: Request) -> bytes:
    """Lee el cuerpo antes del handler: los handlers síncronos corren en hilos y no bloquean el bucle."""
    return await request.body()


CuerpoCrudo = Annotated[bytes, Depends(_cuerpo_crudo)]


def crear_app(
    *,
    demo: Demo | None = None,
    modelo: Model | None = None,
    entorno: dict[str, str] | None = None,
    web_dir: Path | None = WEB_DIR,
    runtime: ClienteRuntime | None = None,
) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def _errores(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Límite de cuerpo y errores sin detalles: ni rastro de pila ni datos del cliente salen a la red."""
        largo = request.headers.get("content-length", "")
        if largo.isdigit() and int(largo) > MAX_CUERPO:
            return JSONResponse({"error": "cuerpo_demasiado_grande"}, status_code=413)
        try:
            return await call_next(request)
        except Exception as error:
            log.error("error no controlado en %s (%s)", request.url.path, type(error).__name__)
            if isinstance(error, GoogleAPICallError | RetryError):  # Firestore o BigQuery caídos
                return JSONResponse({"error": "servicio_no_disponible"}, status_code=503)
            return JSONResponse({"error": "interno"}, status_code=500)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes_cors(entorno),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    demo = demo or crear_demo(entorno)
    observabilidad.configurar(entorno if entorno is not None else os.environ)
    recurso = (entorno if entorno is not None else os.environ).get(VARIABLE_RECURSO, "")
    if runtime is None and recurso:
        runtime = ClienteAgentRuntime(recurso)
    if runtime is not None:  # el agente corre en Agent Runtime; aquí no se arma modelo ni agente
        nombre_modelo, agente = "agent_runtime", None
    else:
        if modelo is None:
            modelo, nombre_modelo = crear_modelo(entorno)
        else:
            nombre_modelo = "inyectado"
        agente = crear_agente_disputas(modelo)
    herramientas = Herramientas(demo.lectura, demo.banco, demo.almacen, reloj=demo.reloj)
    vencimientos = Vencimientos(reloj=demo.reloj)
    traza: list[str] = []
    app.state.demo = demo
    app.state.traza = traza
    app.state.vencimientos = vencimientos
    app.state.herramientas = herramientas

    @app.middleware("http")
    async def _seguridad(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        respuesta = await call_next(request)
        if len(traza) > 2000:  # la traza de pruebas no crece sin fin en un proceso largo
            del traza[:1000]
        respuesta.headers["Content-Security-Policy"] = CSP
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["Referrer-Policy"] = "no-referrer"
        return respuesta

    def sesion_de(request: Request) -> Sesion | None:
        s = demo.sesiones.get(request.headers.get("x-sesion", ""))
        if s is None or not s.autenticada.vigente(demo.reloj()):
            return None
        return s

    def registro_de(request: Request, s: Sesion) -> str:
        s.registro = textos.registro_valido(request.headers.get("x-registro") or s.registro)
        return s.registro

    @app.get("/api/estado")
    def estado() -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return {"clientes": demo.etiquetas_clientes(), "origen": demo.origen, "modelo": nombre_modelo}

    @app.get("/api/textos")
    def catalogo(registro: str = "usted") -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        return textos.catalogo_pagina(registro)

    def abrir(indice: int, registro: str) -> Sesion:
        s = demo.abrir(indice, registro)
        if runtime is not None:
            try:
                runtime.crear_sesion(
                    user_id=id_usuario(s.autenticada.cliente_id),
                    session_id=s.conversacion_id,
                    estado=estado_de_confianza(s.autenticada, s.conversacion_id),
                )
            except AgenteNoDisponible:
                demo.sesiones.pop(s.autenticada.id_sesion, None)  # sin agente no hay sesión a medias
                raise
        return s

    @app.post("/api/sesion")
    def abrir_sesion(request: Request, crudo: CuerpoCrudo) -> Response:  # pyright: ignore[reportUnusedFunction]
        cuerpo = _cuerpo(crudo)
        indice = cuerpo.get("cliente", 0)
        if not isinstance(indice, int) or isinstance(indice, bool) or not 0 <= indice < len(demo.clientes):
            return JSONResponse({"error": "cliente_desconocido"}, status_code=400)
        try:
            s = abrir(indice, textos.registro_valido(cuerpo.get("registro")))
        except AgenteNoDisponible:
            return JSONResponse({"error": "agente_no_disponible"}, status_code=503)
        return JSONResponse(
            {"sesion": s.autenticada.id_sesion, "conversacion": s.conversacion_id, "registro": s.registro}
        )

    def conversacion_de(s: Sesion, pedida: object) -> str | None:
        """La conversación de la sesión o una que abrió con `reclamar`; otra cosa no es suya."""
        if pedida in (None, "", s.conversacion_id):
            return s.conversacion_id
        return str(pedida) if pedida in s.contextos else None

    @app.post("/api/traspaso")
    def traspaso(request: Request, crudo: CuerpoCrudo) -> Response:  # pyright: ignore[reportUnusedFunction]
        s = sesion_de(request)
        if s is None:
            return JSONResponse({"error": "sesion"}, status_code=401)
        reg = registro_de(request, s)
        cuerpo = _cuerpo(crudo)
        conversacion = conversacion_de(s, cuerpo.get("conversacion"))
        if conversacion is None:
            return JSONResponse({"error": "conversacion"}, status_code=403)
        try:
            accion, _ = herramientas.escalar(s.autenticada, conversacion, "cliente_pidio_persona")
        except AccesoDenegado:
            return JSONResponse({"texto": textos.plantilla("falla_segura.chat", reg)})
        traza.append("traspaso_iniciado")
        return JSONResponse(
            {
                "texto": textos.plantilla("traspaso.chat", reg, rango_espera=textos.rango_espera(reg)),
                "turno": accion.resultado_releido,
            }
        )

    def enriquecedor(s: Sesion, reg: str) -> Enriquecedor:
        def enriquecer(interrupcion: str, herramienta: str, args: dict[str, Any]) -> tuple[str, str]:
            expira = vencimientos.emitir(s.autenticada.id_sesion, interrupcion)
            comercio, final, monto, moneda = None, None, None, ""
            try:
                if herramienta == "abrir_disputa":
                    tx = herramientas.transaccion(s.autenticada, str(args.get("transaction_id"))).valor
                    if tx is not None:
                        comercio = textos.describir_comercio(tx.comercio, tx.tipo, reg)
                        monto, moneda = monto_pais(tx.monto.monto, tx.monto.moneda), tx.monto.moneda
                elif herramienta == "bloquear_tarjeta":
                    final = _final(str(args.get("product_id")))
            except AccesoDenegado:
                pass
            objeto = textos.objeto_confirmacion(herramienta, reg, comercio, final)
            return textos.confirmacion(herramienta, reg, objeto, monto, moneda), expira.isoformat()

        return enriquecer

    def registrar_transcripcion(conversacion: str, cuerpo: dict[str, Any]) -> None:
        """Guarda, enmascarados, los turnos nuevos del historial AG-UI (para el paquete del experto)."""
        registro = demo.banco.conversacion(conversacion)
        if registro is None:
            return
        turnos = [
            (str(m["role"]), enmascarar(str(m["content"])))
            for m in _mensajes(cuerpo)
            if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str) and m["content"]
        ]
        for rol, texto in turnos[registro.turnos_guardados :]:
            demo.banco.agregar_transcripcion(conversacion, "cliente" if rol == "user" else "asistente", texto)

    @app.post("/api/agui")
    async def agui(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        s = sesion_de(request)
        if s is None:
            return JSONResponse({"error": "sesion"}, status_code=401)
        cuerpo = _cuerpo(await request.body())
        pedida: object = cuerpo.get("threadId")
        conversacion = conversacion_de(s, pedida)
        if conversacion is None or pedida != conversacion:
            return JSONResponse({"error": "conversacion"}, status_code=403)
        contexto = s.contextos.get(conversacion, "")
        reg = registro_de(request, s)
        if runtime is None:  # con Agent Runtime, el agente guarda los turnos
            registrar_transcripcion(conversacion, cuerpo)
        crudas: object = cuerpo.get("resume") or []
        if not isinstance(crudas, list) or not all(isinstance(r, dict) for r in crudas):  # pyright: ignore[reportUnknownVariableType]
            return JSONResponse({"error": "interrupcion_invalida"}, status_code=400)
        entradas = cast(list[dict[str, Any]], crudas)
        if len(_texto_ultimo_usuario(cuerpo)) > MAX_MENSAJE:
            return JSONResponse({"error": "mensaje_demasiado_largo"}, status_code=413)
        for r in entradas:
            iid = str(r.get("interruptId", ""))
            if not iid.startswith("int-"):
                return JSONResponse({"error": "interrupcion_invalida"}, status_code=400)
            veredicto = vencimientos.consumir(s.autenticada.id_sesion, iid)
            if veredicto != "ok":
                return JSONResponse({"error": f"confirmacion_{veredicto}"}, status_code=409)
        if _PERSONA.search(_texto_ultimo_usuario(cuerpo)):
            traza.append("pedido_de_persona_en_texto")

        def rearmar() -> None:
            """Turno fallido: la aprobación sigue pendiente en el agente; se puede confirmar de nuevo."""
            for r in entradas:
                vencimientos.emitir(s.autenticada.id_sesion, str(r["interruptId"]))

        if runtime is not None:
            aprobaciones = {str(r["interruptId"])[4:]: _aprobada(r) for r in entradas}
            return StreamingResponse(
                flujo_agui(
                    runtime,
                    thread_id=conversacion,
                    user_id=id_usuario(s.autenticada.cliente_id),
                    mensaje=None if aprobaciones else _texto_ultimo_usuario(cuerpo),
                    aprobaciones=aprobaciones or None,
                    registro=reg,
                    enriquecer=enriquecedor(s, reg),
                    traza=traza,
                    al_fallar=rearmar,
                ),
                media_type="text/event-stream",
            )
        assert agente is not None
        ctx = ContextoAgente(herramientas, s.autenticada, conversacion, Canal.CHAT, reg, contexto)
        return await AdaptadorChat.dispatch_request(
            request,
            agent=agente,
            deps=ctx,
            instructions=f"Registro: {reg}. {contexto}".strip(),
            traza=traza,
            registro=reg,
            enriquecer=enriquecedor(s, reg),
        )

    app.include_router(
        crear_router(
            demo=demo,
            herramientas=herramientas,
            sesion_de=sesion_de,
            abrir=abrir,
            runtime=runtime,
            entorno=entorno,
        )
    )

    if web_dir is not None and web_dir.is_dir():
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return app


def crear_app_desde_entorno() -> FastAPI:
    """Fábrica para uvicorn (`just chat`)."""
    return crear_app()
