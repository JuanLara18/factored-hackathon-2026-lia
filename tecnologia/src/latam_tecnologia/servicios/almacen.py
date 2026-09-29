"""Implementaciones del almacén de la retoma: memoria (unitarias) y Postgres (integración, D-23)."""

from __future__ import annotations

from typing import Any

import psycopg
from latam_comun.dominio import AccionVerificada, Canal
from psycopg.types.json import Jsonb

from latam_tecnologia.motor.retoma import Conversacion


class AlmacenMemoria:
    def __init__(self) -> None:
        self._conversaciones: dict[str, Conversacion] = {}
        self._efectos: dict[str, tuple[str, str, AccionVerificada | None]] = {}

    def crear_conversacion(self, conversacion: Conversacion) -> None:
        self._conversaciones[conversacion.id] = conversacion

    def cargar(self, conversacion_id: str) -> Conversacion | None:
        return self._conversaciones.get(conversacion_id)

    def cambiar_canal(self, conversacion_id: str, canal: Canal) -> None:
        actual = self._conversaciones[conversacion_id]
        self._conversaciones[conversacion_id] = actual.model_copy(update={"canal_actual": canal})

    def actualizar(self, conversacion_id: str, estado: str, datos: dict[str, str]) -> None:
        actual = self._conversaciones[conversacion_id]
        self._conversaciones[conversacion_id] = actual.model_copy(
            update={"estado": estado, "datos": dict(datos)}
        )

    def reservar_efecto(self, llave: str, conversacion_id: str, numero: int, tipo: str) -> bool:
        if llave in self._efectos:
            return False
        self._efectos[llave] = (conversacion_id, "en_curso", None)
        return True

    def completar_efecto(self, llave: str, accion: AccionVerificada) -> None:
        conversacion_id, _, _ = self._efectos[llave]
        self._efectos[llave] = (conversacion_id, "hecho", accion)

    def estado_efecto(self, llave: str) -> tuple[str, AccionVerificada | None] | None:
        registro = self._efectos.get(llave)
        return None if registro is None else (registro[1], registro[2])

    def acciones_hechas(self, conversacion_id: str) -> tuple[AccionVerificada, ...]:
        return tuple(
            accion
            for cid, estado, accion in self._efectos.values()
            if cid == conversacion_id and estado == "hecho" and accion is not None
        )


ESQUEMA = """
create table if not exists conversaciones (
    id text primary key, cliente_ref text not null, estado text not null, canal_actual text not null,
    datos jsonb not null default '{}');
create table if not exists efectos (
    llave_idempotencia text primary key, conversacion_id text not null references conversaciones(id),
    numero_transicion int not null, tipo text not null, estado text not null, resultado jsonb);
"""


class AlmacenPostgres:
    def __init__(self, dsn: str) -> None:
        self._con: psycopg.Connection[Any] = psycopg.connect(dsn, autocommit=True)
        self._con.execute(ESQUEMA)  # pyright: ignore[reportArgumentType]

    def cerrar(self) -> None:
        self._con.close()

    def crear_conversacion(self, conversacion: Conversacion) -> None:
        self._con.execute(
            "insert into conversaciones (id, cliente_ref, estado, canal_actual, datos)"
            " values (%s, %s, %s, %s, %s) on conflict do nothing",
            (
                conversacion.id,
                conversacion.cliente_ref,
                conversacion.estado,
                conversacion.canal_actual.value,
                Jsonb(conversacion.datos),
            ),
        )

    def cargar(self, conversacion_id: str) -> Conversacion | None:
        fila = self._con.execute(
            "select id, cliente_ref, estado, canal_actual, datos from conversaciones where id = %s",
            (conversacion_id,),
        ).fetchone()
        if fila is None:
            return None
        return Conversacion(
            id=fila[0], cliente_ref=fila[1], estado=fila[2], canal_actual=Canal(fila[3]), datos=fila[4]
        )

    def cambiar_canal(self, conversacion_id: str, canal: Canal) -> None:
        self._con.execute(
            "update conversaciones set canal_actual = %s where id = %s", (canal.value, conversacion_id)
        )

    def actualizar(self, conversacion_id: str, estado: str, datos: dict[str, str]) -> None:
        self._con.execute(
            "update conversaciones set estado = %s, datos = %s where id = %s",
            (estado, Jsonb(datos), conversacion_id),
        )

    def reservar_efecto(self, llave: str, conversacion_id: str, numero: int, tipo: str) -> bool:
        fila = self._con.execute(
            "insert into efectos (llave_idempotencia, conversacion_id, numero_transicion, tipo, estado)"
            " values (%s, %s, %s, %s, 'en_curso') on conflict (llave_idempotencia) do nothing"
            " returning llave_idempotencia",
            (llave, conversacion_id, numero, tipo),
        ).fetchone()
        return fila is not None

    def completar_efecto(self, llave: str, accion: AccionVerificada) -> None:
        self._con.execute(
            "update efectos set estado = 'hecho', resultado = %s where llave_idempotencia = %s",
            (Jsonb(accion.model_dump(mode="json")), llave),
        )

    def estado_efecto(self, llave: str) -> tuple[str, AccionVerificada | None] | None:
        fila = self._con.execute(
            "select estado, resultado from efectos where llave_idempotencia = %s", (llave,)
        ).fetchone()
        if fila is None:
            return None
        return fila[0], None if fila[1] is None else AccionVerificada.model_validate(fila[1])

    def acciones_hechas(self, conversacion_id: str) -> tuple[AccionVerificada, ...]:
        filas = self._con.execute(
            "select resultado from efectos where conversacion_id = %s and estado = 'hecho'"
            " order by numero_transicion",
            (conversacion_id,),
        ).fetchall()
        return tuple(AccionVerificada.model_validate(f[0]) for f in filas)
