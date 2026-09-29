"""Chat web (TEC-3): el endpoint AG-UI conectado al agente de disputas real, con sesión de demostración.

El cliente sale de la sesión, nunca del navegador ni del modelo. Las acciones con efecto se aprueban con el
evento de interrupción de AG-UI, con vencimiento de 5 minutos y de un solo uso (R-CLI-44, R-CLI-46).
El botón de persona no pasa por el modelo: llama a `escalar` y responde en el acto (R-CLI-34).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ag_ui.core import RunFinishedInterruptOutcome
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from latam_comun.dominio import Canal
from pydantic_ai import DeferredToolRequests
from pydantic_ai.models import Model

from latam_tecnologia.canales import textos
from latam_tecnologia.canales.chat_agui import ChatAdapter, FiltradoEventStream
from latam_tecnologia.canales.demo import Demo, Sesion, crear_demo
from latam_tecnologia.canales.modelo import crear_modelo
from latam_tecnologia.herramientas.agente import ContextoAgente, crear_agente_disputas
from latam_tecnologia.herramientas.catalogo import AccesoDenegado, Herramientas

VIGENCIA_CONFIRMACION = timedelta(minutes=5)
WEB_DIR = Path(__file__).resolve().parents[3] / "web" / "chat"
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
_PERSONA = re.compile(r"\b(persona|humano|asesor)\b", re.IGNORECASE)

Enriquecedor = Callable[[str, str, dict[str, Any]], tuple[str, str]]


@dataclass
class Vencimientos:
    """Confirmaciones emitidas: vigentes 5 minutos, de una sesión y de un solo uso."""

    reloj: Callable[[], datetime] = lambda: datetime.now(UTC)
    _vivas: dict[tuple[str, str], datetime] = field(default_factory=dict[tuple[str, str], datetime])

    def emitir(self, sesion: str, interrupcion: str) -> datetime:
        expira = self.reloj() + VIGENCIA_CONFIRMACION
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

    def build_event_stream(self) -> EventosChat:
        return EventosChat(
            self.run_input,
            accept=self.accept,
            ag_ui_version=self.ag_ui_version,
            traza=self.traza,
            enriquecer=self.enriquecer,
        )


def _texto_ultimo_usuario(cuerpo: dict[str, Any]) -> str:
    for m in reversed(cuerpo.get("messages", [])):
        if m.get("role") == "user":
            return str(m.get("content", ""))
    return ""


def _dinero(monto: Any) -> str:
    entero, _, dec = f"{float(monto):,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{dec}"


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


def crear_app(
    *,
    demo: Demo | None = None,
    modelo: Model | None = None,
    entorno: dict[str, str] | None = None,
    web_dir: Path | None = WEB_DIR,
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes_cors(entorno),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    demo = demo or crear_demo(entorno)
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

    @app.post("/api/sesion")
    async def abrir_sesion(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        cuerpo: dict[str, Any] = await request.json()
        indice = int(cuerpo.get("cliente", 0))
        if not 0 <= indice < len(demo.clientes):
            return JSONResponse({"error": "cliente_desconocido"}, status_code=400)
        s = demo.abrir(indice, textos.registro_valido(cuerpo.get("registro")))
        return JSONResponse(
            {"sesion": s.autenticada.id_sesion, "conversacion": s.conversacion_id, "registro": s.registro}
        )

    @app.post("/api/traspaso")
    def traspaso(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        s = sesion_de(request)
        if s is None:
            return JSONResponse({"error": "sesion"}, status_code=401)
        reg = registro_de(request, s)
        try:
            accion, _ = herramientas.escalar(s.autenticada, s.conversacion_id, "cliente_pidio_persona")
        except AccesoDenegado:
            return JSONResponse({"texto": textos.plantilla("falla_segura.chat", reg)})
        traza.append("traspaso_iniciado")
        return JSONResponse(
            {
                "texto": textos.plantilla("traspaso.chat", reg, rango_espera="unos minutos"),
                "turno": accion.resultado_releido,
            }
        )

    def enriquecedor(s: Sesion, reg: str) -> Enriquecedor:
        def enriquecer(interrupcion: str, herramienta: str, args: dict[str, Any]) -> tuple[str, str]:
            expira = vencimientos.emitir(s.autenticada.id_sesion, interrupcion)
            objeto, monto, moneda = "su caso", None, ""
            try:
                if herramienta == "abrir_disputa":
                    tx = herramientas.transaccion(s.autenticada, str(args.get("transaction_id"))).valor
                    if tx is not None:
                        objeto = f"sobre el cargo de {tx.comercio}"
                        monto, moneda = _dinero(tx.monto.monto), tx.monto.moneda
                elif herramienta == "bloquear_tarjeta":
                    objeto = f"la tarjeta terminada en {_final(str(args.get('product_id')))}"
            except AccesoDenegado:
                pass
            return textos.confirmacion(herramienta, reg, objeto, monto, moneda), expira.isoformat()

        return enriquecer

    @app.post("/api/agui")
    async def agui(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        s = sesion_de(request)
        if s is None:
            return JSONResponse({"error": "sesion"}, status_code=401)
        cuerpo: dict[str, Any] = json.loads(await request.body())
        if cuerpo.get("threadId") != s.conversacion_id:
            return JSONResponse({"error": "conversacion"}, status_code=403)
        reg = registro_de(request, s)
        entradas: list[dict[str, Any]] = cuerpo.get("resume") or []
        for r in entradas:
            iid = str(r.get("interruptId", ""))
            if not iid.startswith("int-"):
                return JSONResponse({"error": "interrupcion_invalida"}, status_code=400)
            veredicto = vencimientos.consumir(s.autenticada.id_sesion, iid)
            if veredicto != "ok":
                return JSONResponse({"error": f"confirmacion_{veredicto}"}, status_code=409)
        if _PERSONA.search(_texto_ultimo_usuario(cuerpo)):
            traza.append("pedido_de_persona_en_texto")
        ctx = ContextoAgente(herramientas, s.autenticada, s.conversacion_id, Canal.CHAT)
        return await AdaptadorChat.dispatch_request(
            request,
            agent=agente,
            deps=ctx,
            instructions=f"Registro: {reg}. Responde en español, en frases cortas y sin inventar cifras.",
            traza=traza,
            enriquecer=enriquecedor(s, reg),
        )

    if web_dir is not None and web_dir.is_dir():
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return app


def crear_app_desde_entorno() -> FastAPI:
    """Fábrica para uvicorn (`just chat`)."""
    return crear_app()
