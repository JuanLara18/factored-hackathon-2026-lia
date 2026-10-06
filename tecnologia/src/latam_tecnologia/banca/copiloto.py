"""Copiloto del experto: un borrador de resumen y de respuesta al cliente. La persona decide y envía.

El borrador se escribe solo con lo que trae el paquete de traspaso (hechos verificados, acciones realizadas y
no realizadas, preguntas abiertas) y con las fuentes de política recuperadas. Nunca se envía solo: llega a la
consola como texto editable, marcado como borrador de inteligencia artificial. Antes de mostrarse pasa por el
mismo filtro de salida del chat; si el filtro lo bloquea, o el modelo falla, se entrega un borrador de
plantilla (caída segura). Al modelo no viajan nombre, documento ni identificadores internos: el paquete ya
viene enmascarado.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Mapping
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel

from latam_tecnologia.canales.frases import filtrar_frase
from latam_tecnologia.herramientas.conocimiento import Recuperador

_log = logging.getLogger(__name__)
MODELO_DEFECTO = "gemini-3.1-flash-lite"
MAX_CARACTERES = 700

INSTRUCCION = (
    "Usted asiste a una persona experta de un banco que acaba de tomar un caso. No habla con el "
    "cliente: escribe un borrador que la persona experta va a revisar y editar. Devuelva dos textos. "
    "`resumen`: tres frases cortas para la persona experta, en español, con lo que pide el cliente, "
    "lo que ya está verificado o hecho y lo que falta. `respuesta`: un borrador de mensaje para el "
    "cliente, en el idioma y el trato indicados, de dos a cuatro frases cortas. Reglas del borrador: "
    "use solo hechos del paquete y de las fuentes de política; no invente cifras, fechas ni estados; "
    "no prometa devoluciones, abonos, plazos ni resultados; no diga que algo se hizo si no figura en "
    "las acciones realizadas; no acuse al cliente; no pida datos que el paquete ya trae; no escriba "
    "identificadores internos ni números completos; no diga que es una inteligencia artificial, "
    "porque el mensaje lo enviará una persona del equipo. Si falta información para responder, el "
    "borrador debe decir qué va a revisar la persona, sin comprometer un resultado."
)
TRATO = {"usted": "español, de usted", "vos": "español rioplatense, de vos", "voce": "portugués, de você"}
RESPALDO = {
    "usted": (
        "Hola, soy del equipo de LATAM Bank. Ya leí lo que le contó al asistente y no tiene que "
        "repetirlo. Voy a revisar su caso y le escribo por este mismo chat."
    ),
    "vos": (
        "Hola, soy del equipo de LATAM Bank. Ya leí lo que le contaste al asistente y no tenés que "
        "repetirlo. Voy a revisar tu caso y te escribo por este mismo chat."
    ),
    "voce": (
        "Olá, sou da equipe do LATAM Bank. Já li o que você contou ao assistente e não precisa repetir. "
        "Vou revisar o seu caso e escrevo por este mesmo chat."
    ),
}


class Borrador(BaseModel):
    resumen: str
    respuesta: str
    fuentes: list[str] = []  # reglas de política que sustentan el borrador
    origen: Literal["modelo", "plantilla"]
    aviso: str | None = None  # por qué no hay borrador del modelo, si no lo hay


class Generador(Protocol):
    """Devuelve `{"resumen": ..., "respuesta": ...}` a partir de la instrucción y del contexto del caso."""

    def __call__(self, instruccion: str, contexto: str) -> Mapping[str, str]: ...


def contexto_del_caso(vista: Mapping[str, Any], fuentes: list[dict[str, Any]]) -> str:
    """Lo que ve el modelo: los campos del paquete que sirven para redactar, ya enmascarados."""
    datos = {
        "idioma_y_trato": TRATO.get(str(vista.get("registro")), TRATO["usted"]),
        "pais_de_la_cuenta": vista.get("pais_cuenta"),
        "motivo_del_traspaso": vista.get("motivo", {}).get("texto"),
        "prioridad": vista.get("prioridad"),
        "solicitud_del_cliente": vista.get("solicitud", {}).get("cita"),
        "hechos_verificados": [h["texto"] for h in vista.get("hechos_verificados", [])],
        "acciones_realizadas": [
            f"{a['accion']}: {a['resultado']}" for a in vista.get("acciones_realizadas", [])
        ],
        "acciones_no_realizadas": vista.get("acciones_no_realizadas", []),
        "preguntas_abiertas": [q["pregunta"] for q in vista.get("preguntas_abiertas", [])],
        "compromisos_ya_comunicados": [c["texto"] for c in vista.get("compromisos_comunicados", [])],
        "ultimos_mensajes": [f"{m['autor']}: {m['texto']}" for m in vista.get("transcripcion", [])][-8:],
        "fuentes_de_politica": fuentes,
    }
    return json.dumps(datos, ensure_ascii=False)


def resumen_de_plantilla(vista: Mapping[str, Any]) -> str:
    hechos = len(vista.get("hechos_verificados", []))
    acciones = len(vista.get("acciones_realizadas", []))
    abiertas = len(vista.get("preguntas_abiertas", []))
    motivo = vista.get("motivo", {}).get("texto") or "sin motivo registrado"
    return (
        f"Motivo del traspaso: {motivo}. Hay {hechos} hechos verificados y {acciones} acciones realizadas. "
        f"Quedan {abiertas} preguntas abiertas en el paquete."
    )


def sugerir(
    vista: Mapping[str, Any],
    generador: Generador | None,
    recuperador: Recuperador | None = None,
) -> Borrador:
    """Borrador para la consola. Nunca lanza: ante cualquier falla entrega el de plantilla con su aviso."""
    registro = str(vista.get("registro") or "usted")
    respaldo = RESPALDO.get(registro, RESPALDO["usted"])
    idioma = "pt" if registro == "voce" else "es"
    hallazgos = ()
    solicitud = str(vista.get("solicitud", {}).get("cita") or "")
    if recuperador is not None and solicitud:
        try:
            hallazgos = recuperador.buscar(solicitud, cast(str | None, vista.get("pais_cuenta"))).hallazgos
        except Exception:
            hallazgos = ()
    fuentes = [{"reglas": list(h.articulo.reglas), "texto": h.articulo.textos[idioma]} for h in hallazgos]
    reglas = list(dict.fromkeys(r for h in hallazgos for r in h.articulo.reglas))

    def de_plantilla(aviso: str) -> Borrador:
        return Borrador(
            resumen=resumen_de_plantilla(vista), respuesta=respaldo, origen="plantilla", aviso=aviso
        )

    if generador is None:
        return de_plantilla("El modelo no está configurado: este es el texto de plantilla.")
    contexto = contexto_del_caso(vista, fuentes)
    salida: Mapping[str, str] | None = None
    for intento in range(2):  # un reintento acotado: cuota (429) o error transitorio del modelo
        try:
            salida = generador(INSTRUCCION, contexto)
            break
        except Exception as error:
            _log.warning("copiloto: el modelo falló (%s), intento %d", type(error).__name__, intento + 1)
            if intento == 0:
                time.sleep(1.5)
    if salida is None:
        return de_plantilla("El modelo no respondió: este es el texto de plantilla.")
    resumen, respuesta = str(salida.get("resumen", "")).strip(), str(salida.get("respuesta", "")).strip()
    if not resumen or not respuesta or len(respuesta) > MAX_CARACTERES:
        return de_plantilla("El borrador del modelo no era utilizable: este es el texto de plantilla.")
    filtrado = filtrar_frase(respuesta)  # sin acciones permitidas: el borrador no afirma que algo se hizo
    if filtrado.bloqueada:
        return de_plantilla(
            "El filtro de salida bloqueó el borrador del modelo: este es el texto de plantilla."
        )
    return Borrador(
        resumen=filtrar_frase(resumen).texto, respuesta=filtrado.texto, fuentes=reglas, origen="modelo"
    )


def crear_generador(entorno: Mapping[str, str] | None = None) -> Generador | None:
    """Gemini en Vertex AI con salida JSON tipada; `None` si no hay proyecto (local y pruebas)."""
    env = os.environ if entorno is None else entorno
    proyecto = env.get("LATAM_GCP_PROJECT")
    if not proyecto or env.get("LATAM_MODELO", "").lower() == "guionado":
        return None
    from google import genai
    from google.genai import types

    cliente = genai.Client(
        vertexai=True,
        project=proyecto,
        location=env.get("LATAM_GEAP_LOCATION") or "global",
        http_options=types.HttpOptions(timeout=20000),
    )
    modelo = env.get("LATAM_MODELO_COPILOTO") or MODELO_DEFECTO
    esquema = {
        "type": "OBJECT",
        "properties": {"resumen": {"type": "STRING"}, "respuesta": {"type": "STRING"}},
        "required": ["resumen", "respuesta"],
    }

    def generar(instruccion: str, contexto: str) -> Mapping[str, str]:
        respuesta = cliente.models.generate_content(
            model=modelo,
            contents=contexto,
            config=types.GenerateContentConfig(
                system_instruction=instruccion,
                temperature=0.2,
                max_output_tokens=500,
                response_mime_type="application/json",
                response_schema=cast(Any, esquema),
            ),
        )
        return cast(dict[str, str], json.loads(respuesta.text or "{}"))

    return generar
