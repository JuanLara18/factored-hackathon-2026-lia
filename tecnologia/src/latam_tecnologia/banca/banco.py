"""El banco compartido (D-33): puerto, doble en memoria y elección por entorno.

Casos, bloqueos, traspasos y mensajes viven en Firestore para que los vean el chat de Cloud Run, el agente en
Agent Runtime y la consola. Cada escritura es idempotente: el caso por (cliente, transacción) mientras esté
abierto, el bloqueo por (cliente, producto) y el traspaso por conversación.
"""

from __future__ import annotations

import os
import secrets
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from latam_comun.dominio import Dinero, Idioma, PaqueteTraspaso

from latam_tecnologia.banca.modelos import Caso, Evento, Mensaje, RegistroConversacion, Traspaso
from latam_tecnologia.banca.refs import hash_corto
from latam_tecnologia.herramientas.puertos import CasoAbierto, ServiciosBanco

VARIABLE_BANCO = "LATAM_BANCO"
VARIABLE_PROYECTO = "LATAM_GCP_PROJECT"
ORDEN_PRIORIDAD = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
PLAZO_MXN = "48 horas"  # abono provisional de México (MX-06)
LIMITE_TRANSCRIPCION = 60


def _ahora() -> datetime:
    return datetime.now(UTC)


def id_caso(cliente_id: str, transaccion_id: str) -> str:
    return "caso-" + hash_corto("caso", cliente_id, transaccion_id)


def id_traspaso(conversacion_id: str) -> str:
    return "tr-" + hash_corto("traspaso", conversacion_id)


_ultimo_ns = 0
_candado_ids = threading.Lock()


def id_mensaje() -> str:
    """Ordenable por tiempo: sirve de cursor en `desde`.

    Estrictamente creciente dentro del proceso: el reloj de Windows tiene poca resolución y dos mensajes
    seguidos podían recibir el mismo instante (el sufijo aleatorio decidía el orden y `desde` los perdía).
    """
    global _ultimo_ns
    with _candado_ids:
        _ultimo_ns = max(time.time_ns(), _ultimo_ns + 1)
        instante = _ultimo_ns
    return f"m{instante:020d}{secrets.token_hex(2)}"


def caso_nuevo(
    cliente_id: str, transaccion_id: str, monto: Dinero, motivo: str, credito: bool, ahora: datetime
) -> Caso:
    historial = [Evento(fecha=ahora, evento="Reclamo abierto")]
    if credito:
        historial.append(Evento(fecha=ahora, evento="Crédito provisional registrado en el caso"))
    return Caso(
        caso_ref=id_caso(cliente_id, transaccion_id),
        cliente_id=cliente_id,
        transaccion_id=transaccion_id,
        monto=monto.monto,
        moneda=monto.moneda,
        motivo=motivo[:200],
        abierto_en=ahora,
        credito_provisional=credito,
        plazo=PLAZO_MXN if monto.moneda == "MXN" and credito else None,
        historial=historial,
    )


def paquete_minimo(motivo: str, urgente: bool, conversacion_id: str) -> PaqueteTraspaso:
    """Solo para quien encola sin contexto (puerto heredado); `Herramientas.escalar` arma el completo."""
    return PaqueteTraspaso(
        solicitud="no disponible",
        hechos=(),
        interpretaciones=(),
        motivo=motivo,
        idioma=Idioma.ES,
        prioridad="P1" if urgente else "P3",
        hilo_id=conversacion_id,
    )


def prioridad_de(paquete: PaqueteTraspaso) -> str:
    p = paquete.prioridad
    return p if p in ORDEN_PRIORIDAD else ("P1" if p == "urgente" else "P3")


def mensaje_nuevo(autor: str, texto: str, en: datetime) -> Mensaje:
    return Mensaje.model_validate({"id": id_mensaje(), "autor": autor, "texto": texto, "en": en})


@runtime_checkable
class Banco(ServiciosBanco, Protocol):
    """`ServiciosBanco` (efectos del agente) más lo que leen el sitio y la consola."""

    def caso(self, caso_ref: str) -> Caso | None: ...

    def casos_de(self, cliente_id: str) -> tuple[Caso, ...]: ...

    def bloqueado(self, cliente_id: str, producto_id: str) -> bool: ...

    def registrar_conversacion(self, conversacion: RegistroConversacion) -> None:
        """Crea el registro si no existe; nunca pisa uno anterior."""
        ...

    def conversacion(self, conversacion_id: str) -> RegistroConversacion | None: ...

    def registrar_solicitud(self, conversacion_id: str, texto: str) -> None: ...

    def agregar_transcripcion(self, conversacion_id: str, autor: str, texto: str) -> None:
        """Turno ya enmascarado, para el paquete del experto."""
        ...

    def agregar_mensaje(self, conversacion_id: str, autor: str, texto: str) -> str: ...

    def mensajes(self, conversacion_id: str, desde: str | None = None) -> list[Mensaje]: ...

    def encolar_paquete(
        self, llave: str, cliente_id: str, conversacion_id: str, paquete: PaqueteTraspaso
    ) -> str: ...

    def traspaso(self, id_traspaso: str) -> Traspaso | None: ...

    def traspaso_de_conversacion(self, conversacion_id: str) -> Traspaso | None: ...

    def cola(self) -> list[Traspaso]:
        """En cola y tomados, por prioridad y antigüedad."""
        ...

    def tomar(self, id_traspaso: str, operador: str) -> str:
        """`tomado`, `ya_tomado` (por otra persona), `resuelto` o `inexistente`."""
        ...

    def resolver(
        self, id_traspaso: str, resultado: str, etiqueta: dict[str, Any] | str | None, nota: str | None
    ) -> Traspaso | None: ...

    def restablecer(self, clientes: Sequence[str]) -> dict[str, int]:
        """Borra casos, bloqueos, traspasos y conversaciones (y mensajes) de esos clientes; idempotente."""
        ...


def orden_cola(t: Traspaso) -> tuple[int, datetime]:
    return ORDEN_PRIORIDAD[t.prioridad], t.creado_en


class BancoMemoria:
    """Doble en memoria del banco. Conserva los contadores que usan las pruebas."""

    def __init__(self, reloj: Callable[[], datetime] = _ahora) -> None:
        self._reloj = reloj
        self._casos: dict[str, Caso] = {}
        self._bloqueos: set[tuple[str, str]] = set()
        self._traspasos: dict[str, Traspaso] = {}
        self._conversaciones: dict[str, RegistroConversacion] = {}
        self._mensajes: dict[str, list[Mensaje]] = {}
        self.llamadas = 0
        self.creditos_provisionales: list[str] = []

    # Efectos del agente (ServiciosBanco)

    def abrir_caso(
        self,
        llave: str,
        cliente_id: str,
        transaccion_id: str,
        monto: Dinero,
        motivo: str,
        credito_provisional: bool,
    ) -> str:
        caso_ref = id_caso(cliente_id, transaccion_id)
        existente = self._casos.get(caso_ref)
        if existente is not None and existente.estado == "abierto":
            return caso_ref  # misma llave o mismo caso abierto: sin efecto y sin otro crédito
        self.llamadas += 1
        caso = caso_nuevo(cliente_id, transaccion_id, monto, motivo, credito_provisional, self._reloj())
        self._casos[caso_ref] = caso
        if credito_provisional:
            self.creditos_provisionales.append(caso_ref)
        return caso_ref

    def casos_abiertos(self, cliente_id: str) -> tuple[CasoAbierto, ...]:
        return tuple(
            CasoAbierto(transaction_id=c.transaccion_id, caso=c.caso_ref)
            for c in self._casos.values()
            if c.cliente_id == cliente_id and c.estado == "abierto"
        )

    def credito_provisional_de(self, caso: str) -> bool:
        registro = self._casos.get(caso)
        return registro is not None and registro.credito_provisional

    def bloquear_tarjeta(self, llave: str, cliente_id: str, producto_id: str) -> str:
        if (cliente_id, producto_id) not in self._bloqueos:
            self.llamadas += 1
            self._bloqueos.add((cliente_id, producto_id))
        return f"bloqueada:{producto_id}"

    def encolar_traspaso(
        self, llave: str, cliente_id: str, conversacion_id: str, motivo: str, urgente: bool
    ) -> str:
        return self.encolar_paquete(
            llave, cliente_id, conversacion_id, paquete_minimo(motivo, urgente, conversacion_id)
        )

    # Lectura para el sitio

    def caso(self, caso_ref: str) -> Caso | None:
        return self._casos.get(caso_ref)

    def casos_de(self, cliente_id: str) -> tuple[Caso, ...]:
        return tuple(c for c in self._casos.values() if c.cliente_id == cliente_id)

    def bloqueado(self, cliente_id: str, producto_id: str) -> bool:
        return (cliente_id, producto_id) in self._bloqueos

    # Conversaciones y mensajes

    def registrar_conversacion(self, conversacion: RegistroConversacion) -> None:
        self._conversaciones.setdefault(conversacion.id, conversacion)

    def conversacion(self, conversacion_id: str) -> RegistroConversacion | None:
        return self._conversaciones.get(conversacion_id)

    def registrar_solicitud(self, conversacion_id: str, texto: str) -> None:
        actual = self._conversaciones.get(conversacion_id)
        if actual is not None:
            self._conversaciones[conversacion_id] = actual.model_copy(update={"solicitud": texto})

    def agregar_transcripcion(self, conversacion_id: str, autor: str, texto: str) -> None:
        actual = self._conversaciones.get(conversacion_id)
        if actual is None:
            return
        turnos = [*actual.transcripcion, mensaje_nuevo(autor, texto, self._reloj())]
        self._conversaciones[conversacion_id] = actual.model_copy(
            update={
                "transcripcion": turnos[-LIMITE_TRANSCRIPCION:],
                "turnos_guardados": actual.turnos_guardados + 1,
            }
        )

    def agregar_mensaje(self, conversacion_id: str, autor: str, texto: str) -> str:
        mensaje = mensaje_nuevo(autor, texto, self._reloj())
        self._mensajes.setdefault(conversacion_id, []).append(mensaje)
        return mensaje.id

    def mensajes(self, conversacion_id: str, desde: str | None = None) -> list[Mensaje]:
        return [m for m in self._mensajes.get(conversacion_id, []) if desde is None or m.id > desde]

    # Traspasos

    def encolar_paquete(
        self, llave: str, cliente_id: str, conversacion_id: str, paquete: PaqueteTraspaso
    ) -> str:
        identificador = id_traspaso(conversacion_id)
        if identificador not in self._traspasos:
            self.llamadas += 1
            self._traspasos[identificador] = Traspaso.model_validate(
                {
                    "id_traspaso": identificador,
                    "cliente_id": cliente_id,
                    "conversacion_id": conversacion_id,
                    "prioridad": prioridad_de(paquete),
                    "creado_en": self._reloj(),
                    "paquete": paquete.model_copy(update={"id_traspaso": identificador}),
                }
            )
        return identificador

    def traspaso(self, id_traspaso: str) -> Traspaso | None:
        return self._traspasos.get(id_traspaso)

    def traspaso_de_conversacion(self, conversacion_id: str) -> Traspaso | None:
        return self._traspasos.get(id_traspaso(conversacion_id))

    def cola(self) -> list[Traspaso]:
        return sorted((t for t in self._traspasos.values() if t.estado != "resuelto"), key=orden_cola)

    def tomar(self, id_traspaso: str, operador: str) -> str:
        t = self._traspasos.get(id_traspaso)
        if t is None:
            return "inexistente"
        if t.estado == "resuelto":
            return "resuelto"
        if t.estado == "tomado" and t.tomado_por != operador:
            return "ya_tomado"
        self._traspasos[id_traspaso] = t.model_copy(update={"estado": "tomado", "tomado_por": operador})
        return "tomado"

    def resolver(
        self, id_traspaso: str, resultado: str, etiqueta: dict[str, Any] | str | None, nota: str | None
    ) -> Traspaso | None:
        t = self._traspasos.get(id_traspaso)
        if t is None or t.estado == "resuelto":
            return t  # resolver dos veces (reintento o dos pestañas) no pisa la primera resolución
        nuevo = t.model_copy(
            update={
                "estado": "resuelto",
                "resultado": resultado,
                "etiqueta_correccion": etiqueta,
                "nota": nota,
            }
        )
        self._traspasos[id_traspaso] = nuevo
        return nuevo

    def restablecer(self, clientes: Sequence[str]) -> dict[str, int]:
        return _restablecer_memoria(self, clientes)


def _restablecer_memoria(b: BancoMemoria, clientes: Sequence[str]) -> dict[str, int]:
    propios = set(clientes)
    casos = [k for k, c in b._casos.items() if c.cliente_id in propios]  # pyright: ignore[reportPrivateUsage]
    bloqueos = {x for x in b._bloqueos if x[0] in propios}  # pyright: ignore[reportPrivateUsage]
    traspasos = [k for k, t in b._traspasos.items() if t.cliente_id in propios]  # pyright: ignore[reportPrivateUsage]
    convs = [k for k, c in b._conversaciones.items() if c.cliente_id in propios]  # pyright: ignore[reportPrivateUsage]
    for k in casos:
        del b._casos[k]  # pyright: ignore[reportPrivateUsage]
    b._bloqueos -= bloqueos  # pyright: ignore[reportPrivateUsage]
    for k in traspasos:
        del b._traspasos[k]  # pyright: ignore[reportPrivateUsage]
    for k in convs:
        del b._conversaciones[k]  # pyright: ignore[reportPrivateUsage]
        b._mensajes.pop(k, None)  # pyright: ignore[reportPrivateUsage]
    return {
        "casos": len(casos),
        "bloqueos": len(bloqueos),
        "traspasos": len(traspasos),
        "conversaciones": len(convs),
    }


def crear_banco(entorno: Mapping[str, str] | None = None, reloj: Callable[[], datetime] = _ahora) -> Banco:
    """`LATAM_BANCO=firestore|memoria`; sin él, Firestore si hay `LATAM_GCP_PROJECT` y memoria si no."""
    env = os.environ if entorno is None else entorno
    proyecto = env.get(VARIABLE_PROYECTO)
    modo = (env.get(VARIABLE_BANCO) or ("firestore" if proyecto else "memoria")).lower()
    if modo == "memoria":
        return BancoMemoria(reloj)
    if modo != "firestore":
        raise ValueError(f"{VARIABLE_BANCO} debe ser firestore o memoria, no {modo!r}")
    if not proyecto:
        raise ValueError(f"{VARIABLE_BANCO}=firestore exige {VARIABLE_PROYECTO}")
    from latam_tecnologia.banca.firestore import BancoFirestore

    return BancoFirestore(proyecto, reloj=reloj)
