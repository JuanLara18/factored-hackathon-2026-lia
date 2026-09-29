from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from doble_duckdb import AlmacenLocal, MotorDuckDB
from latam_datos.bronce import construir_bronce, lote_id_de
from latam_datos.corrida import correr_bronce
from latam_datos.espejo import ObjetoGCS, registrar_inventario
from latam_datos.reglas import REGLAS, evaluar_globales

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
K1 = "data/ventas/2025-01-01.csv"
K2 = "data/ventas/2025-01-02.csv"
BUENO = b"id,valor\n1,a\n2,\n3,c\n"
BOM = b"\xef\xbb\xbf"


def _md5(datos: bytes) -> str:
    return hashlib.md5(datos).hexdigest()


def _lotes(m: MotorDuckDB) -> list[tuple[object, ...]]:
    return m.consultar(
        "SELECT source_key, estado, clase, tenia_bom, filas, huella_lote FROM latam_bronce._lotes "
        "ORDER BY source_key, etag"
    )


def _reglas(m: MotorDuckDB) -> dict[str, set[str]]:
    salida: dict[str, set[str]] = {}
    for regla, res in m.consultar("SELECT regla_id, resultado FROM latam_platino.reporte_calidad_corrida"):
        salida.setdefault(regla, set()).add(res)
    return salida


def test_todo_texto_metadatos_y_bom(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BOM + BUENO)
    almacen.poner(K2, BUENO)
    res, _ = correr_bronce(almacen, motor, AHORA)
    assert len(res.aplicados) == 2
    lotes = {str(f[0]): f for f in _lotes(motor)}
    assert lotes[K1][3] is True and lotes[K2][3] is False
    cols = motor.consultar("DESCRIBE latam_bronce.ventas")
    assert [c[0] for c in cols] == ["id", "valor", "_lote_id", "_linea", "_huella_fila"]  # sin U+FEFF
    assert [c[1] for c in cols] == ["VARCHAR", "VARCHAR", "VARCHAR", "BIGINT", "VARCHAR"]
    lote = lote_id_de(K2, _md5(BUENO))
    filas = motor.consultar(
        f"SELECT id, valor, _lote_id, _linea FROM latam_bronce.ventas "
        f"WHERE _lote_id = '{lote}' ORDER BY _linea"
    )
    assert filas == [("1", "a", lote, 2), ("2", "", lote, 3), ("3", "c", lote, 4)]


def test_huella_determinista_e_idempotente(almacen: AlmacenLocal, motor: MotorDuckDB, tmp_path: Path) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    antes = _lotes(motor)
    res, hallazgos = correr_bronce(almacen, motor, AHORA)
    assert res.aplicados == [] and len(res.ignorados) == 1
    assert _lotes(motor) == antes
    assert any(h.regla_id == "Q-BRZ-10" for h in hallazgos)
    # otro entorno con el mismo contenido y BOM: otro lote, la misma huella de contenido
    otro = AlmacenLocal(tmp_path / "otro")
    m2 = MotorDuckDB()
    otro.poner(K1, BOM + BUENO)
    correr_bronce(otro, m2, AHORA)
    assert _lotes(m2)[0][5] == antes[0][5]


def test_reporte_cubre_las_once_reglas(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    assert set(_reglas(motor)) == set(REGLAS)


def test_bom_residual_bloquea(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BOM + BOM + b"id,valor\n1,a\n")
    res, _ = correr_bronce(almacen, motor, AHORA)
    assert len(res.bloqueados) == 1
    assert _lotes(motor)[0][1] == "bloqueado_esquema"
    assert "bloqueado" in _reglas(motor)["Q-BRZ-02"]


def test_utf8_invalido_bloquea(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, b"id,valor\n1,\xe9\n")
    correr_bronce(almacen, motor, AHORA)
    assert "bloqueado" in _reglas(motor)["Q-BRZ-04"]


def test_encabezado_aditivo_avisa_y_faltante_bloquea(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    almacen.poner(K2, b"id,valor,extra\n1,a,x\n")
    almacen.poner("data/ventas/2025-01-03.csv", b"id,otro\n1,a\n")
    correr_bronce(almacen, motor, AHORA)
    estados = {str(f[0]): f[1] for f in _lotes(motor)}
    assert estados[K2] == "aplicado"
    assert estados["data/ventas/2025-01-03.csv"] == "bloqueado_esquema"
    assert _reglas(motor)["Q-BRZ-03"] == {"aviso", "bloqueado"}
    assert motor.consultar("SELECT extra FROM latam_bronce.ventas WHERE extra IS NOT NULL") == [("x",)]


def test_filas_malformadas_a_cuarentena_o_bloqueo(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    grande = "id,valor\n" + "".join(f"{i},x\n" for i in range(200)) + "solo_un_campo\n"
    almacen.poner(K1, grande.encode())
    almacen.poner(K2, b"id,valor\n1,a\nmala\nmala2\n3,c\n")
    correr_bronce(almacen, motor, AHORA)
    estados = {str(f[0]): f for f in _lotes(motor)}
    assert estados[K1][1] == "aplicado" and estados[K1][4] == 200
    assert estados[K2][1] == "bloqueado_sistematico"
    assert motor.consultar("SELECT linea, linea_cruda FROM latam_bronce._cuarentena") == [
        (202, "solo_un_campo\n")
    ]


def test_archivo_vacio_avisa(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, b"id,valor\n")
    correr_bronce(almacen, motor, AHORA)
    assert _lotes(motor)[0][1:5] == ("aplicado", "NUEVO", False, 0)
    assert "aviso" in _reglas(motor)["Q-BRZ-11"]


def test_reentrega_ok_agrega_lote_y_no_toca_el_anterior(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    previo = motor.consultar("SELECT * FROM latam_bronce.ventas ORDER BY _linea")
    almacen.poner(K1, b"id,valor\n1,a\n2,b\n3,c\n4,d\n")
    correr_bronce(almacen, motor, AHORA + timedelta(hours=1))
    lotes = _lotes(motor)
    assert sorted(str(f[2]) for f in lotes) == ["NUEVO", "REENTREGA"]
    assert all(f[1] == "aplicado" for f in lotes)
    despues = motor.consultar(
        f"SELECT * FROM latam_bronce.ventas WHERE _lote_id = '{previo[0][2]}' ORDER BY _linea"
    )
    assert despues == previo


def test_regeneracion_bloquea(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    almacen.poner(K1, b"id,valor\n7,a\n8,b\n9,c\n")
    res, _ = correr_bronce(almacen, motor, AHORA + timedelta(hours=1))
    assert len(res.bloqueados) == 1
    assert "bloqueado_regeneracion" in {f[1] for f in _lotes(motor)}
    assert "bloqueado" in _reglas(motor)["Q-BRZ-08"]
    assert motor.consultar("SELECT count(*) FROM latam_bronce.ventas") == [(3,)]


def test_no_autorizados_no_se_ingieren_y_se_avisan(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner("data_backup_20260831/ventas/2025-01-01.csv", BUENO)
    almacen.poner("marketing_campaigns.csv", b"x\n1\n")
    res, _ = correr_bronce(almacen, motor, AHORA)
    assert res.aplicados == []
    registrar_inventario(motor, "c0", almacen.listar(), AHORA)
    _, hallazgos = correr_bronce(almacen, motor, AHORA + timedelta(hours=1))
    assert {h.source_key for h in hallazgos if h.regla_id == "Q-BRZ-09"} == {
        "data_backup_20260831/ventas/2025-01-01.csv",
        "marketing_campaigns.csv",
    }


def test_q_brz_01_dias_faltantes(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner("data/ventas/2023-06-17.csv", BUENO)
    almacen.poner("data/ventas/2023-06-19.csv", BUENO)
    _, hallazgos = correr_bronce(almacen, motor, AHORA)
    q1 = next(h for h in hallazgos if h.regla_id == "Q-BRZ-01")
    assert q1.filas_afectadas == 1095


def test_q_brz_06_conteo_fuera_de_percentiles(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    lunes = date(2025, 1, 6)
    for i in range(26):
        n = 500 if i == 25 else 10
        cuerpo = "id\n" + "".join(f"{j}\n" for j in range(n))
        almacen.poner(f"data/ventas/{(lunes + timedelta(weeks=i)).isoformat()}.csv", cuerpo.encode())
    _, hallazgos = correr_bronce(almacen, motor, AHORA)
    assert [h.filas_afectadas for h in hallazgos if h.regla_id == "Q-BRZ-06"] == [500]


def test_generacion_ajena_bloquea_q_brz_07(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    motor.ejecutar("UPDATE latam_bronce._lotes SET generacion = 'respaldo'")
    assert [h.resultado for h in evaluar_globales(motor) if h.regla_id == "Q-BRZ-07"] == ["bloqueado"]


def test_contrato_de_fuente_manda_sobre_la_referencia(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    res = construir_bronce(almacen, motor, AHORA, {"ventas": ["id", "valor", "requerida"]})
    assert res.aplicados == [] and len(res.bloqueados) == 1


def test_staging_se_limpia(almacen: AlmacenLocal, motor: MotorDuckDB) -> None:
    almacen.poner(K1, BUENO)
    correr_bronce(almacen, motor, AHORA)
    assert not list((almacen.raiz / "_staging").glob("*"))
    assert motor.consultar(
        "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE '%stg%'"
    ) == [(0,)]


def test_objeto_gcs_autorizado() -> None:
    def o(k: str) -> ObjetoGCS:
        return ObjetoGCS(k, 1, "", "", 0, AHORA)

    assert o("data/t/a.csv").autorizado
    assert not o("data/a.csv").autorizado and not o("otro/t/a.csv").autorizado
