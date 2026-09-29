"""Agente de disputas como agente propio de Agent Runtime (GEAP, D-32 fase 2).

Envuelve `crear_agente_disputas` (PydanticAI) con los métodos que Agent Runtime pide a un agente propio:
`query`, `stream_query`, `async_query` y `async_stream_query`. La clase se serializa por valor con
cloudpickle, así que este módulo solo importa la biblioteca estándar arriba; lo demás se importa en `set_up`,
cuando el paquete ya está en el `sys.path` del runtime.

Confianza: el cliente, el nivel de autenticación y el vencimiento salen del estado de la sesión de Agent
Runtime (Sessions), que fija el canal al abrirla. Ni el modelo ni los argumentos de `query` los nombran.
Las herramientas con efecto devuelven una solicitud de aprobación; el canal la resuelve con `aprobaciones`.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Protocol

ESTADO_REQUERIDO = ("cliente_id", "nivel", "expira", "conversacion_id")
AUTOR = "agente"
DENEGADA = "El cliente no aprobó esta acción."


class Sesiones(Protocol):
    """Lo que el agente necesita de Agent Runtime Sessions."""

    def estado(self, session_id: str, user_id: str) -> dict[str, Any]: ...

    def eventos(self, session_id: str, user_id: str) -> list[str]:
        """Textos JSON de los mensajes guardados, en orden."""
        ...

    def agregar(self, session_id: str, user_id: str, invocacion: str, texto: str) -> None: ...


class SesionesMemoria:
    """Doble en memoria de Sessions, para pruebas y ejecución local."""

    def __init__(self) -> None:
        self.estados: dict[tuple[str, str], dict[str, Any]] = {}
        self.historial: dict[tuple[str, str], list[str]] = {}

    def crear(self, session_id: str, user_id: str, estado: dict[str, Any]) -> None:
        self.estados[(user_id, session_id)] = dict(estado)
        self.historial[(user_id, session_id)] = []

    def estado(self, session_id: str, user_id: str) -> dict[str, Any]:
        return self.estados.get((user_id, session_id), {})

    def eventos(self, session_id: str, user_id: str) -> list[str]:
        return list(self.historial.get((user_id, session_id), []))

    def agregar(self, session_id: str, user_id: str, invocacion: str, texto: str) -> None:
        self.historial.setdefault((user_id, session_id), []).append(texto)


def crear_cliente_sdk(proyecto: str, ubicacion: str, **opciones: Any) -> Any:
    """Cliente del SDK de Agent Platform (`agentplatform`) o, en versiones previas, de `vertexai`."""
    for nombre in ("agentplatform", "vertexai"):
        try:
            modulo: Any = importlib.import_module(nombre)
        except ImportError:
            continue
        return modulo.Client(project=proyecto, location=ubicacion, **opciones)
    raise ImportError("falta el SDK: google-cloud-aiplatform")


class SesionesAgentPlatform:
    """Sessions gestionado de Agent Platform. El cliente se crea al primer uso (no se serializa)."""

    def __init__(self, proyecto: str, ubicacion: str, motor_id: str) -> None:
        self._raiz = f"projects/{proyecto}/locations/{ubicacion}/reasoningEngines/{motor_id}"
        self._proyecto, self._ubicacion = proyecto, ubicacion
        self._cliente: Any = None

    def _c(self) -> Any:
        if self._cliente is None:
            self._cliente = crear_cliente_sdk(self._proyecto, self._ubicacion)
        return self._cliente

    def _sesiones(self) -> Any:
        c = self._c()
        return getattr(c, "sessions", None) or c.agent_engines.sessions

    def _nombre(self, session_id: str) -> str:
        return f"{self._raiz}/sessions/{session_id}"

    def estado(self, session_id: str, user_id: str) -> dict[str, Any]:
        s = self._sesiones().get(name=self._nombre(session_id), user_id=user_id)
        return dict(getattr(s, "session_state", None) or {})

    def eventos(self, session_id: str, user_id: str) -> list[str]:
        salida: list[str] = []
        evento: Any
        for evento in self._sesiones().events.list(name=self._nombre(session_id)):
            partes: list[Any] = getattr(getattr(evento, "content", None), "parts", None) or []
            texto: Any = getattr(partes[0], "text", None) if partes else None
            if texto:
                salida.append(str(texto))
        return salida

    def agregar(self, session_id: str, user_id: str, invocacion: str, texto: str) -> None:
        from datetime import UTC, datetime

        self._sesiones().events.append(
            name=self._nombre(session_id),
            author=AUTOR,
            invocation_id=invocacion,
            timestamp=datetime.now(tz=UTC),
            config={"content": {"role": "model", "parts": [{"text": texto}]}},
        )


def _buscar_paquete() -> str | None:
    """Carpeta `latam_paquete` que `extra_packages` deja junto al código en el runtime.

    Primero en `sys.path` y el directorio actual; si no, recorre cuatro niveles bajo esas bases y `/code`.
    """
    bases = [Path(b or ".") for b in (*sys.path, os.getcwd(), "/code", "/home")]
    for base in bases:
        candidata = base / "latam_paquete"
        if (candidata / "tecnologia" / "src").is_dir():
            return str(candidata)
    for base in bases:
        if not base.is_dir():
            continue
        raiz_nivel = len(base.parts)
        for actual, dirs, _ in os.walk(base):
            if len(Path(actual).parts) - raiz_nivel >= 4:
                dirs[:] = []
                continue
            if "latam_paquete" in dirs and (Path(actual) / "latam_paquete" / "tecnologia" / "src").is_dir():
                return str(Path(actual) / "latam_paquete")
    return None


def _en_hilo(corrutina: Any) -> Any:
    """Corre una corrutina desde código síncrono, también si el hilo ya tiene un bucle de eventos."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(corrutina)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, corrutina).result()


class AgenteDisputasRuntime:
    """Agente propio de Agent Runtime. `__init__` solo guarda configuración (debe poder serializarse)."""

    def __init__(
        self,
        proyecto: str | None = None,
        ubicacion_modelo: str = "global",
        dataset: str = "latam_bank",
        raiz_paquete: str | None = None,
        *,
        modelo: Any = None,
        lectura: Any = None,
        sesiones: Sesiones | None = None,
        reloj: Callable[[], Any] | None = None,
    ) -> None:
        self.proyecto = proyecto
        self.ubicacion_modelo = ubicacion_modelo
        self.dataset = dataset
        self.raiz_paquete = raiz_paquete
        # Solo pruebas: en el despliegue se dejan en None y `set_up` los arma con GEAP y BigQuery.
        self._modelo, self._lectura, self._sesiones, self._reloj = modelo, lectura, sesiones, reloj
        self._agente: Any = None

    # Ciclo de vida

    def set_up(self) -> None:
        if self._agente is not None:
            return
        raiz = self.raiz_paquete or os.environ.get("LATAM_RAIZ_PAQUETE") or _buscar_paquete()
        if raiz is None and importlib.util.find_spec("latam_tecnologia") is None:
            raise RuntimeError(f"no se encontró latam_paquete; cwd={os.getcwd()} sys.path={sys.path}")
        if raiz:
            for miembro in ("comun", "gobierno", "tecnologia"):
                ruta = str(Path(raiz) / miembro / "src")
                if ruta not in sys.path:
                    sys.path.insert(0, ruta)
        from datetime import UTC, datetime

        from latam_tecnologia import observabilidad
        from latam_tecnologia.canales.geap import VARIABLE_PROYECTO, VARIABLE_UBICACION, crear_modelo_geap
        from latam_tecnologia.herramientas.agente import crear_agente_disputas
        from latam_tecnologia.herramientas.bigquery import LecturaBigQuery
        from latam_tecnologia.herramientas.catalogo import Herramientas
        from latam_tecnologia.herramientas.falsos import ServiciosBancoFalsos
        from latam_tecnologia.servicios.almacen import AlmacenMemoria

        proyecto = self.proyecto or os.environ[VARIABLE_PROYECTO]
        entorno = {
            **os.environ,
            VARIABLE_PROYECTO: proyecto,
            VARIABLE_UBICACION: os.environ.get(VARIABLE_UBICACION) or self.ubicacion_modelo,
        }
        if self._modelo is None:  # con modelo inyectado (pruebas) no se exportan trazas
            observabilidad.configurar(entorno)
        modelo = self._modelo or crear_modelo_geap(entorno)[0]
        lectura = self._lectura or LecturaBigQuery(proyecto, self.dataset)
        self._reloj = self._reloj or (lambda: datetime.now(UTC))
        # Banco y almacén siguen simulados, como en el chat en proceso (ver tecnologia/README.md).
        self._banco = ServiciosBancoFalsos()
        self._almacen = AlmacenMemoria()
        self._herramientas = Herramientas(lectura, self._banco, self._almacen, reloj=self._reloj)
        self._agente = crear_agente_disputas(modelo)
        if self._sesiones is None:
            motor = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID") or os.environ["LATAM_MOTOR_ID"]
            ubicacion = os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get(
                "LATAM_RUNTIME_LOCATION", "us-central1"
            )
            self._sesiones = SesionesAgentPlatform(proyecto, ubicacion, motor)

    def register_operations(self) -> dict[str, list[str]]:
        return {
            "": ["query"],
            "async": ["async_query"],
            "stream": ["stream_query"],
            "async_stream": ["async_stream_query"],
        }

    # Turno

    def _sesion(self, session_id: str, user_id: str) -> tuple[Any, str] | str:
        """Sesión autenticada desde el estado que fijó el canal, o el código de error."""
        from datetime import datetime

        from latam_comun.dominio import Canal, NivelAcr, SesionAutenticada

        from latam_tecnologia.motor.retoma import Conversacion

        estado = self._sesiones.estado(session_id, user_id)  # type: ignore[union-attr]
        if any(k not in estado for k in ESTADO_REQUERIDO):
            return "sesion_desconocida"
        sesion = SesionAutenticada(
            id_sesion=session_id,
            cliente_id=str(estado["cliente_id"]),
            nivel=NivelAcr(estado["nivel"]),
            expira=datetime.fromisoformat(str(estado["expira"])),
        )
        reloj = self._reloj
        assert reloj is not None
        if not sesion.vigente(reloj()):
            return "sesion_vencida"
        conversacion_id = str(estado["conversacion_id"])
        if self._almacen.cargar(conversacion_id) is None:
            self._almacen.crear_conversacion(
                Conversacion(
                    id=conversacion_id,
                    cliente_ref=sesion.cliente_id,
                    canal_actual=Canal.CHAT,
                    estado="inicio",
                )
            )
        return sesion, conversacion_id

    async def _turno(
        self,
        mensaje: str | None,
        user_id: str,
        session_id: str,
        aprobaciones: dict[str, bool] | None,
        registro: str,
    ) -> AsyncIterator[dict[str, Any]]:
        from latam_comun.dominio import Canal
        from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolDenied
        from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, ModelResponse, ToolCallPart

        from latam_tecnologia.herramientas.agente import ContextoAgente

        self.set_up()
        resuelta = self._sesion(session_id, user_id)
        if isinstance(resuelta, str):
            yield {"tipo": "error", "codigo": resuelta}
            return
        sesion, conversacion_id = resuelta
        historial: list[ModelMessage] = []
        for texto in self._sesiones.eventos(session_id, user_id):  # type: ignore[union-attr]
            historial += ModelMessagesTypeAdapter.validate_json(texto)
        ultimo = historial[-1] if historial else None
        pendientes = (
            {p.tool_call_id for p in ultimo.parts if isinstance(p, ToolCallPart)}
            if isinstance(ultimo, ModelResponse)
            else set[str]()
        )
        resultados: DeferredToolResults | None = None
        if aprobaciones:
            if set(aprobaciones) != pendientes:
                yield {"tipo": "error", "codigo": "aprobacion_invalida"}
                return
            resultados = DeferredToolResults(
                approvals={i: (True if ok else ToolDenied(DENEGADA)) for i, ok in aprobaciones.items()}
            )
            mensaje = None
        elif pendientes:  # un "sí" escrito no resuelve una aprobación pendiente
            yield {"tipo": "error", "codigo": "aprobacion_pendiente"}
            return
        elif not mensaje:
            yield {"tipo": "error", "codigo": "mensaje_vacio"}
            return
        ctx = ContextoAgente(self._herramientas, sesion, conversacion_id, Canal.CHAT)
        instrucciones = f"Registro: {registro}. Responde en español, en frases cortas y sin inventar cifras."
        async with self._agente.run_stream(
            mensaje,
            deps=ctx,
            message_history=historial,
            deferred_tool_results=resultados,
            instructions=instrucciones,
        ) as corrida:
            async for delta in corrida.stream_text(delta=True):
                yield {"tipo": "texto", "delta": delta}
            salida = await corrida.get_output()
            nuevos = corrida.new_messages()
        self._sesiones.agregar(  # type: ignore[union-attr]
            session_id,
            user_id,
            str(len(historial)),
            ModelMessagesTypeAdapter.dump_json(nuevos).decode(),
        )
        if isinstance(salida, DeferredToolRequests):
            yield {
                "tipo": "aprobacion",
                "aprobaciones": [
                    {"id": c.tool_call_id, "herramienta": c.tool_name, "args": c.args_as_dict()}
                    for c in salida.approvals
                ],
            }
        else:
            yield {"tipo": "fin"}

    # Métodos que Agent Runtime expone

    async def async_stream_query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str | None = None,
        aprobaciones: dict[str, bool] | None = None,
        registro: str = "usted",
    ) -> AsyncIterator[dict[str, Any]]:
        async for evento in self._turno(message, user_id, session_id, aprobaciones, registro):
            yield evento

    async def async_query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str | None = None,
        aprobaciones: dict[str, bool] | None = None,
        registro: str = "usted",
    ) -> dict[str, Any]:
        eventos = [e async for e in self._turno(message, user_id, session_id, aprobaciones, registro)]
        texto = "".join(e["delta"] for e in eventos if e["tipo"] == "texto")
        final = eventos[-1] if eventos else {"tipo": "error", "codigo": "sin_respuesta"}
        return {**final, "texto": texto}

    def query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str | None = None,
        aprobaciones: dict[str, bool] | None = None,
        registro: str = "usted",
    ) -> dict[str, Any]:
        return _en_hilo(  # type: ignore[no-any-return]
            self.async_query(
                user_id=user_id,
                session_id=session_id,
                message=message,
                aprobaciones=aprobaciones,
                registro=registro,
            )
        )

    def stream_query(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str | None = None,
        aprobaciones: dict[str, bool] | None = None,
        registro: str = "usted",
    ) -> Iterator[dict[str, Any]]:
        yield from _en_hilo(self._recolectar(user_id, session_id, message, aprobaciones, registro))

    async def _recolectar(
        self,
        user_id: str,
        session_id: str,
        message: str | None,
        aprobaciones: dict[str, bool] | None,
        registro: str,
    ) -> list[dict[str, Any]]:
        return [e async for e in self._turno(message, user_id, session_id, aprobaciones, registro)]
