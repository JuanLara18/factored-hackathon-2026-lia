"""Estados y eventos del caso de disputa (definición 2.6.2), compartidos por motor y clientes."""

from __future__ import annotations

from enum import StrEnum


class Estado(StrEnum):
    INICIO = "inicio"
    IDENTIFICANDO_TRANSACCION = "identificando_transaccion"
    CONFIRMANDO_ACCION = "confirmando_accion"
    EJECUTANDO = "ejecutando"
    VERIFICANDO = "verificando"
    INFORMANDO = "informando"
    TRASPASO = "traspaso"
    CIERRE = "cierre"
    FALLA_SEGURA = "falla_segura"
    NEGADO = "negado"


class Evento(StrEnum):
    ABRIR = "abrir"
    TRANSACCION_ENCONTRADA = "transaccion_encontrada"
    TRANSACCION_NO_ENCONTRADA = "transaccion_no_encontrada"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"
    EFECTO_HECHO = "efecto_hecho"
    EFECTO_FALLIDO = "efecto_fallido"
    VERIFICADO = "verificado"
    ESCALAR = "escalar"
    INFORMADO = "informado"
    ACCESO_DENEGADO = "acceso_denegado"
