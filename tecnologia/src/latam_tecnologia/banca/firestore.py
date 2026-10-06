"""Banco sobre Firestore nativo (proyecto latam-bank-hackaton-2026, base "(default)").

Colecciones: `casos`, `bloqueos`, `traspasos` y `conversaciones/{id}/mensajes`. Los ids de documento son
deterministas (caso por cliente y transacción, bloqueo por cliente y producto, traspaso por conversación), así
que `create` (falla si existe) da la idempotencia sin transacciones y sin depender del proceso que escribe.
Las consultas filtran por un solo campo: no piden índices compuestos.

Retención (D-27): cada documento lleva `expira_en`, una marca de tiempo nativa a 30 días de su creación, y la
política de TTL de Firestore sobre ese campo lo borra (`tecnologia/infra/terraform/modules/firestore`). El
campo es de almacenamiento: se quita al leer y no existe en los modelos.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue]
from google.cloud.firestore_v1.base_query import FieldFilter
from latam_comun.dominio import Dinero, PaqueteTraspaso

from latam_tecnologia.banca.banco import (
    LIMITE_TRANSCRIPCION,
    RETENCION_OPERATIVA,
    caso_abierto,
    caso_nuevo,
    id_caso,
    id_traspaso,
    mensaje_nuevo,
    orden_cola,
    paquete_minimo,
    prioridad_de,
)
from latam_tecnologia.banca.modelos import Caso, Mensaje, RegistroConversacion, Traspaso
from latam_tecnologia.banca.refs import hash_corto
from latam_tecnologia.herramientas.puertos import CasoAbierto

CAMPO_VENCIMIENTO = "expira_en"
COLECCIONES_CON_VENCIMIENTO = ("casos", "bloqueos", "traspasos", "conversaciones", "mensajes")


def _ahora() -> datetime:
    return datetime.now(UTC)


def sin_vencimiento(datos: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in datos.items() if k != CAMPO_VENCIMIENTO}


class BancoFirestore:
    def __init__(
        self,
        proyecto: str,
        base: str = "(default)",
        *,
        cliente: Any = None,
        reloj: Callable[[], datetime] = _ahora,
    ) -> None:
        self._db: Any = cliente or firestore.Client(project=proyecto, database=base)
        self._reloj = reloj

    def _con_vencimiento(self, datos: dict[str, Any]) -> dict[str, Any]:
        return {**datos, CAMPO_VENCIMIENTO: self._reloj() + RETENCION_OPERATIVA}

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
        documento = self._db.collection("casos").document(caso_ref)
        caso = caso_nuevo(cliente_id, transaccion_id, monto, motivo, credito_provisional, self._reloj())

        def _abrir(transaccion: Any) -> None:
            existente = documento.get(transaction=transaccion)
            if existente.exists and existente.to_dict().get("estado") == "abierto":
                return  # otra instancia lo abrió antes: el crédito lo concedió ella
            # caso cerrado: se reabre uno nuevo sobre el mismo documento
            transaccion.set(documento, self._con_vencimiento(caso.model_dump(mode="json")))

        transaccional: Any = getattr(firestore, "transactional")  # noqa: B009
        transaccional(_abrir)(self._db.transaction())
        return caso_ref

    def casos_abiertos(self, cliente_id: str) -> tuple[CasoAbierto, ...]:
        return tuple(caso_abierto(c) for c in self.casos_de(cliente_id) if c.estado == "abierto")

    def credito_provisional_de(self, caso: str) -> bool:
        registro = self.caso(caso)
        return registro is not None and registro.credito_provisional

    def bloquear_tarjeta(self, llave: str, cliente_id: str, producto_id: str) -> str:
        documento = self._db.collection("bloqueos").document(hash_corto("bloqueo", cliente_id, producto_id))
        with contextlib.suppress(AlreadyExists):
            documento.create(
                self._con_vencimiento(
                    {
                        "cliente_id": cliente_id,
                        "producto_id": producto_id,
                        "bloqueado_en": self._reloj().isoformat(),
                    }
                )
            )
        return f"bloqueada:{producto_id}"

    def encolar_traspaso(
        self, llave: str, cliente_id: str, conversacion_id: str, motivo: str, urgente: bool
    ) -> str:
        return self.encolar_paquete(
            llave, cliente_id, conversacion_id, paquete_minimo(motivo, urgente, conversacion_id)
        )

    # Lectura para el sitio

    def caso(self, caso_ref: str) -> Caso | None:
        d = self._db.collection("casos").document(caso_ref).get()
        return Caso.model_validate(sin_vencimiento(d.to_dict())) if d.exists else None

    def casos_de(self, cliente_id: str) -> tuple[Caso, ...]:
        consulta = self._db.collection("casos").where(filter=FieldFilter("cliente_id", "==", cliente_id))
        return tuple(Caso.model_validate(sin_vencimiento(d.to_dict())) for d in consulta.stream())

    def bloqueado(self, cliente_id: str, producto_id: str) -> bool:
        return bool(
            self._db.collection("bloqueos")
            .document(hash_corto("bloqueo", cliente_id, producto_id))
            .get()
            .exists
        )

    # Conversaciones y mensajes

    def _conv(self, conversacion_id: str) -> Any:
        return self._db.collection("conversaciones").document(conversacion_id)

    def registrar_conversacion(self, conversacion: RegistroConversacion) -> None:
        with contextlib.suppress(AlreadyExists):
            self._conv(conversacion.id).create(self._con_vencimiento(conversacion.model_dump(mode="json")))

    def conversacion(self, conversacion_id: str) -> RegistroConversacion | None:
        d = self._conv(conversacion_id).get()
        return RegistroConversacion.model_validate(sin_vencimiento(d.to_dict())) if d.exists else None

    def registrar_solicitud(self, conversacion_id: str, texto: str) -> None:
        if self.conversacion(conversacion_id) is not None:
            self._conv(conversacion_id).update({"solicitud": texto})

    def agregar_transcripcion(self, conversacion_id: str, autor: str, texto: str) -> None:
        documento = self._conv(conversacion_id)
        nuevo = mensaje_nuevo(autor, texto, self._reloj())

        def _agregar(transaccion: Any) -> None:
            d = documento.get(transaction=transaccion)
            if not d.exists:
                return
            actual = RegistroConversacion.model_validate(sin_vencimiento(d.to_dict()))
            turnos = [*actual.transcripcion, nuevo][-LIMITE_TRANSCRIPCION:]
            transaccion.update(
                documento,
                {
                    "transcripcion": [t.model_dump(mode="json") for t in turnos],
                    "turnos_guardados": actual.turnos_guardados + 1,
                },
            )

        transaccional: Any = getattr(firestore, "transactional")  # noqa: B009
        transaccional(_agregar)(self._db.transaction())  # dos turnos a la vez no se pisan

    def agregar_mensaje(self, conversacion_id: str, autor: str, texto: str) -> str:
        mensaje = mensaje_nuevo(autor, texto, self._reloj())
        self._conv(conversacion_id).collection("mensajes").document(mensaje.id).set(
            self._con_vencimiento(mensaje.model_dump(mode="json"))
        )
        return mensaje.id

    def mensajes(self, conversacion_id: str, desde: str | None = None) -> list[Mensaje]:
        todos = [
            Mensaje.model_validate(sin_vencimiento(d.to_dict()))
            for d in self._conv(conversacion_id).collection("mensajes").stream()
        ]
        return sorted((m for m in todos if desde is None or m.id > desde), key=lambda m: m.id)

    # Traspasos

    def _guardar(self, t: Traspaso) -> dict[str, Any]:
        return {
            "id_traspaso": t.id_traspaso,
            "cliente_id": t.cliente_id,
            "conversacion_id": t.conversacion_id,
            "prioridad": t.prioridad,
            "estado": t.estado,
            "creado_en": t.creado_en.isoformat(),
            "tomado_por": t.tomado_por,
            "resultado": t.resultado,
            "etiqueta_correccion": t.etiqueta_correccion,
            "nota": t.nota,
            "paquete_json": t.paquete.model_dump_json(),
        }

    @staticmethod
    def _leer(datos: dict[str, Any]) -> Traspaso:
        crudo = sin_vencimiento(datos)
        crudo["paquete"] = PaqueteTraspaso.model_validate_json(crudo.pop("paquete_json"))
        return Traspaso.model_validate(crudo)

    def encolar_paquete(
        self, llave: str, cliente_id: str, conversacion_id: str, paquete: PaqueteTraspaso
    ) -> str:
        identificador = id_traspaso(conversacion_id)
        registro = Traspaso.model_validate(
            {
                "id_traspaso": identificador,
                "cliente_id": cliente_id,
                "conversacion_id": conversacion_id,
                "prioridad": prioridad_de(paquete),
                "creado_en": self._reloj(),
                "paquete": paquete.model_copy(update={"id_traspaso": identificador}),
            }
        )
        with contextlib.suppress(AlreadyExists):
            self._db.collection("traspasos").document(identificador).create(
                self._con_vencimiento(self._guardar(registro))
            )
        return identificador

    def traspaso(self, id_traspaso: str) -> Traspaso | None:
        d = self._db.collection("traspasos").document(id_traspaso).get()
        return self._leer(d.to_dict()) if d.exists else None

    def traspaso_de_conversacion(self, conversacion_id: str) -> Traspaso | None:
        return self.traspaso(id_traspaso(conversacion_id))

    def cola(self) -> list[Traspaso]:
        consulta = self._db.collection("traspasos").where(
            filter=FieldFilter("estado", "in", ["en_cola", "tomado"])
        )
        return sorted((self._leer(d.to_dict()) for d in consulta.stream()), key=orden_cola)

    def tomar(self, id_traspaso: str, operador: str) -> str:
        documento = self._db.collection("traspasos").document(id_traspaso)

        def _tomar(transaccion: Any) -> str:
            d = documento.get(transaction=transaccion)
            if not d.exists:
                return "inexistente"
            datos = d.to_dict()
            if datos["estado"] == "resuelto":
                return "resuelto"
            if datos["estado"] == "tomado" and datos.get("tomado_por") != operador:
                return "ya_tomado"
            transaccion.update(documento, {"estado": "tomado", "tomado_por": operador})
            return "tomado"

        transaccional: Any = getattr(firestore, "transactional")  # noqa: B009
        return str(transaccional(_tomar)(self._db.transaction()))

    def resolver(
        self, id_traspaso: str, resultado: str, etiqueta: dict[str, Any] | str | None, nota: str | None
    ) -> Traspaso | None:
        documento = self._db.collection("traspasos").document(id_traspaso)

        def _resolver(transaccion: Any) -> None:
            d = documento.get(transaction=transaccion)
            if not d.exists or d.to_dict()["estado"] == "resuelto":
                return  # ya resuelto: la primera resolución es la que vale
            transaccion.update(
                documento,
                {"estado": "resuelto", "resultado": resultado, "etiqueta_correccion": etiqueta, "nota": nota},
            )

        transaccional: Any = getattr(firestore, "transactional")  # noqa: B009
        transaccional(_resolver)(self._db.transaction())
        return self.traspaso(id_traspaso)

    def restablecer(self, clientes: Sequence[str]) -> dict[str, int]:
        cuentas = {"casos": 0, "bloqueos": 0, "traspasos": 0, "conversaciones": 0}
        for cliente in clientes:
            for coleccion in ("casos", "bloqueos", "traspasos", "conversaciones"):
                consulta = self._db.collection(coleccion).where(
                    filter=FieldFilter("cliente_id", "==", cliente)
                )
                for d in list(consulta.stream()):
                    if coleccion == "conversaciones":
                        for m in list(d.reference.collection("mensajes").stream()):
                            m.reference.delete()
                    d.reference.delete()
                    cuentas[coleccion] += 1
        return cuentas
