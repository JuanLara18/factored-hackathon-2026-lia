"""Banco sobre Firestore real (opt-in: `--integracion` y `LATAM_GCP_PROJECT`); limpia lo que crea."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from latam_comun.dominio import Dinero, Idioma, PaqueteTraspaso
from latam_tecnologia.banca.banco import id_caso, id_traspaso
from latam_tecnologia.banca.firestore import BancoFirestore
from latam_tecnologia.banca.modelos import RegistroConversacion
from latam_tecnologia.banca.refs import hash_corto


@pytest.mark.integracion
def test_firestore_casos_bloqueos_traspasos_y_mensajes() -> None:
    proyecto = os.environ.get("LATAM_GCP_PROJECT")
    if not proyecto:
        pytest.skip("requiere LATAM_GCP_PROJECT")
    banco = BancoFirestore(proyecto)
    sufijo = uuid.uuid4().hex[:8]
    cliente, tx, producto, conv = f"test-{sufijo}", f"tx-{sufijo}", f"prod-{sufijo}", f"c-test-{sufijo}"
    dinero = Dinero(monto=Decimal("100.50"), moneda="MXN")
    db = banco._db  # pyright: ignore[reportPrivateUsage]
    try:
        caso = banco.abrir_caso("k1", cliente, tx, dinero, "fraude", True)
        assert banco.abrir_caso("k2", cliente, tx, dinero, "fraude", False) == caso == id_caso(cliente, tx)
        assert banco.credito_provisional_de(caso)  # la segunda apertura no lo pisó
        assert [c.caso for c in banco.casos_abiertos(cliente)] == [caso]
        assert banco.casos_de(cliente)[0].monto == Decimal("100.50")
        vence = db.collection("casos").document(caso).get().to_dict()["expira_en"]
        assert isinstance(vence, datetime) and timedelta(days=29) < vence - datetime.now(UTC) < timedelta(
            days=31
        )

        assert not banco.bloqueado(cliente, producto)
        assert banco.bloquear_tarjeta("a", cliente, producto) == banco.bloquear_tarjeta(
            "b", cliente, producto
        )
        assert banco.bloqueado(cliente, producto)

        banco.registrar_conversacion(
            RegistroConversacion(id=conv, cliente_id=cliente, creada_en=banco._reloj())
        )  # pyright: ignore[reportPrivateUsage]
        banco.agregar_transcripcion(conv, "cliente", "hola")
        paquete = PaqueteTraspaso(
            solicitud="hola",
            hechos=(),
            interpretaciones=(),
            motivo="CLIENTE_PIDE_PERSONA",
            idioma=Idioma.ES,
            prioridad="P3",
        )
        idt = banco.encolar_paquete("k", cliente, conv, paquete)
        assert idt == banco.encolar_paquete("k", cliente, conv, paquete) == id_traspaso(conv)
        assert idt in [t.id_traspaso for t in banco.cola()]
        assert banco.tomar(idt, "Experto 1") == "tomado" and banco.tomar(idt, "Experto 2") == "ya_tomado"
        m = banco.agregar_mensaje(conv, "persona", "buenas")
        assert [x.texto for x in banco.mensajes(conv)] == ["buenas"] and banco.mensajes(conv, desde=m) == []
        conversacion = banco.conversacion(conv)
        assert conversacion is not None and conversacion.transcripcion[0].texto == "hola"
        resuelto = banco.resolver(idt, "resuelto", {"comentario": "ok"}, "nota")
        assert resuelto is not None and resuelto.estado == "resuelto"
        assert idt not in [t.id_traspaso for t in banco.cola()]
    finally:
        db.collection("casos").document(id_caso(cliente, tx)).delete()
        db.collection("bloqueos").document(hash_corto("bloqueo", cliente, producto)).delete()
        db.collection("traspasos").document(id_traspaso(conv)).delete()
        for d in db.collection("conversaciones").document(conv).collection("mensajes").stream():
            d.reference.delete()
        db.collection("conversaciones").document(conv).delete()
