from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import duckdb
from latam_datos.almacen import abrir_zona
from latam_datos.bronce import construir_bronce, lote_id_de
from latam_datos.config import Rutas
from latam_datos.corrida import correr_bronce
from latam_datos.espejo import ObjetoS3, registrar_inventario
from latam_datos.reglas import REGLAS, dias_faltantes, evaluar_globales, percentil, solapamiento

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
LM = "2026-09-01T00:00:00+00:00"
K1 = "data/ventas/2025-01-01.csv"
K2 = "data/ventas/2025-01-02.csv"
BUENO = b"id,valor\n1,a\n2,\n3,c\n"
BOM = b"\xef\xbb\xbf"


def _poner(rutas: Rutas, key: str, contenido: bytes, etag: str = "e1") -> None:
    ruta = rutas.espejo / key
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    indice = rutas.espejo / "_indice_etags.json"
    datos = json.loads(indice.read_text()) if indice.exists() else {}
    datos[key] = {"etag": etag, "tamano": len(contenido), "last_modified": LM}
    indice.write_text(json.dumps(datos))


def _lotes(rutas: Rutas) -> list[tuple[object, ...]]:
    con = duckdb.connect(str(rutas.bronce_db), read_only=True)
    try:
        return con.execute(
            "SELECT source_key, estado, clase, tenia_bom, filas, huella_lote "
            "FROM bronce._lotes ORDER BY source_key, etag"
        ).fetchall()
    finally:
        con.close()


def _reglas(rutas: Rutas) -> dict[str, set[str]]:
    con = duckdb.connect(str(rutas.platino_db), read_only=True)
    try:
        filas = con.execute("SELECT regla_id, resultado FROM platino.reporte_calidad_corrida").fetchall()
    finally:
        con.close()
    salida: dict[str, set[str]] = {}
    for regla, res in filas:
        salida.setdefault(regla, set()).add(res)
    return salida


def test_todo_texto_metadatos_y_bom(rutas: Rutas) -> None:
    _poner(rutas, K1, BOM + BUENO)
    _poner(rutas, K2, BUENO)
    res, _ = correr_bronce(rutas, AHORA)
    assert len(res.aplicados) == 2
    lotes = {str(f[0]): f for f in _lotes(rutas)}
    assert lotes[K1][3] is True and lotes[K2][3] is False
    lote = lote_id_de(K1, "e1")
    ruta = (rutas.bronce / f"ventas/process_date=2025-01-01/{lote}.parquet").as_posix()
    con = duckdb.connect()
    cols = con.execute("DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning=false)", [ruta]).fetchall()
    assert [c[0] for c in cols] == ["id", "valor", "_lote_id", "_linea", "_huella_fila"]
    assert {c[1] for c in cols} == {"VARCHAR"}
    filas = con.execute(
        "SELECT id, valor, _lote_id, _linea FROM read_parquet(?) ORDER BY 1", [ruta]
    ).fetchall()
    assert filas == [("1", "a", lote, "2"), ("2", "", lote, "3"), ("3", "c", lote, "4")]


def test_dos_corridas_misma_huella_y_sin_lotes_nuevos(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO)
    correr_bronce(rutas, AHORA)
    antes = _lotes(rutas)
    res, hallazgos = correr_bronce(rutas, AHORA)
    assert res.aplicados == [] and len(res.ignorados) == 1
    assert _lotes(rutas) == antes
    assert any(h.regla_id == "Q-BRZ-10" for h in hallazgos)
    # el mismo contenido, con BOM y otro etag, da la misma huella de lote
    otro = Rutas(rutas.raiz.parent / "otro")
    _poner(otro, K1, BOM + BUENO, etag="e9")
    correr_bronce(otro, AHORA)
    assert _lotes(otro)[0][5] == antes[0][5]


def test_reporte_cubre_las_once_reglas(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO)
    correr_bronce(rutas, AHORA)
    assert set(_reglas(rutas)) == set(REGLAS)


def test_bom_residual_bloquea(rutas: Rutas) -> None:
    _poner(rutas, K1, BOM + BOM + b"id,valor\n1,a\n")
    res, _ = correr_bronce(rutas, AHORA)
    assert len(res.bloqueados) == 1
    assert _lotes(rutas)[0][1] == "bloqueado_esquema"
    assert "bloqueado" in _reglas(rutas)["Q-BRZ-02"]
    assert not list(rutas.bronce.rglob("*.parquet"))


def test_utf8_invalido_bloquea(rutas: Rutas) -> None:
    _poner(rutas, K1, b"id,valor\n1,\xe9\n")
    correr_bronce(rutas, AHORA)
    assert "bloqueado" in _reglas(rutas)["Q-BRZ-04"]


def test_encabezado_aditivo_avisa_y_faltante_bloquea(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO)
    _poner(rutas, K2, b"id,valor,extra\n1,a,x\n")
    _poner(rutas, "data/ventas/2025-01-03.csv", b"id,otro\n1,a\n")
    correr_bronce(rutas, AHORA)
    estados = {str(f[0]): f[1] for f in _lotes(rutas)}
    assert estados[K2] == "aplicado"
    assert estados["data/ventas/2025-01-03.csv"] == "bloqueado_esquema"
    assert _reglas(rutas)["Q-BRZ-03"] == {"aviso", "bloqueado"}


def test_filas_malformadas_a_cuarentena_o_bloqueo(rutas: Rutas) -> None:
    grande = "id,valor\n" + "".join(f"{i},x\n" for i in range(200)) + "solo_un_campo\n"
    _poner(rutas, K1, grande.encode())
    _poner(rutas, K2, b"id,valor\n1,a\nmala\nmala2\n3,c\n")
    correr_bronce(rutas, AHORA)
    estados = {str(f[0]): f for f in _lotes(rutas)}
    assert estados[K1][1] == "aplicado" and estados[K1][4] == 200
    assert estados[K2][1] == "bloqueado_sistematico"
    con = duckdb.connect()
    ruta = next((rutas.bronce / "_cuarentena").rglob("*.parquet")).as_posix()
    cuarentena = con.execute("SELECT _linea, linea_cruda FROM read_parquet(?)", [ruta]).fetchall()
    assert cuarentena == [("202", "solo_un_campo\n")]


def test_archivo_vacio_avisa(rutas: Rutas) -> None:
    _poner(rutas, K1, b"id,valor\n")
    correr_bronce(rutas, AHORA)
    assert _lotes(rutas)[0][1:5] == ("aplicado", "NUEVO", False, 0)
    assert "aviso" in _reglas(rutas)["Q-BRZ-11"]


def test_reentrega_ok_agrega_lote_y_no_toca_el_anterior(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO, etag="e1")
    correr_bronce(rutas, AHORA)
    anterior = rutas.bronce / f"ventas/process_date=2025-01-01/{lote_id_de(K1, 'e1')}.parquet"
    previo = anterior.read_bytes()
    _poner(rutas, K1, b"id,valor\n1,a\n2,b\n3,c\n4,d\n", etag="e2")
    correr_bronce(rutas, AHORA)
    lotes = _lotes(rutas)
    assert sorted(str(f[2]) for f in lotes) == ["NUEVO", "REENTREGA"]
    assert all(f[1] == "aplicado" for f in lotes)
    assert anterior.read_bytes() == previo


def test_regeneracion_bloquea(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO, etag="e1")
    correr_bronce(rutas, AHORA)
    _poner(rutas, K1, b"id,valor\n7,a\n8,b\n9,c\n", etag="e2")
    res, _ = correr_bronce(rutas, AHORA)
    assert len(res.bloqueados) == 1
    assert "bloqueado_regeneracion" in {f[1] for f in _lotes(rutas)}
    assert "bloqueado" in _reglas(rutas)["Q-BRZ-08"]


def test_objetos_no_autorizados_no_se_ingieren_y_se_avisan(rutas: Rutas) -> None:
    _poner(rutas, "data_backup_20260831/ventas/2025-01-01.csv", BUENO)
    con = abrir_zona(rutas.platino_db)
    registrar_inventario(con, "c1", [ObjetoS3("marketing_campaigns.csv", "x", 1, AHORA)], AHORA)
    con.close()
    res, _ = correr_bronce(rutas, AHORA)
    assert res.aplicados == []
    assert "aviso" in _reglas(rutas)["Q-BRZ-09"]


def test_q_brz_01_dias_faltantes(rutas: Rutas) -> None:
    _poner(rutas, "data/ventas/2023-06-17.csv", BUENO)
    _poner(rutas, "data/ventas/2023-06-19.csv", BUENO)
    _, hallazgos = correr_bronce(rutas, AHORA)
    q1 = next(h for h in hallazgos if h.regla_id == "Q-BRZ-01")
    assert q1.filas_afectadas == 1095


def test_q_brz_06_conteo_fuera_de_percentiles(rutas: Rutas) -> None:
    lunes = date(2025, 1, 6)
    for i in range(26):
        n = 500 if i == 25 else 10
        cuerpo = "id\n" + "".join(f"{j}\n" for j in range(n))
        _poner(rutas, f"data/ventas/{(lunes + timedelta(weeks=i)).isoformat()}.csv", cuerpo.encode())
    _, hallazgos = correr_bronce(rutas, AHORA)
    fuera = [h for h in hallazgos if h.regla_id == "Q-BRZ-06"]
    assert [h.filas_afectadas for h in fuera] == [500]


def test_generacion_ajena_bloquea_q_brz_07(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO)
    correr_bronce(rutas, AHORA)
    con = duckdb.connect(str(rutas.bronce_db))
    con.execute("UPDATE bronce._lotes SET generacion = 'respaldo'")
    hallazgos = evaluar_globales(con, [])
    con.close()
    assert [h.resultado for h in hallazgos if h.regla_id == "Q-BRZ-07"] == ["bloqueado"]


def test_contrato_de_fuente_manda_sobre_la_referencia(rutas: Rutas) -> None:
    _poner(rutas, K1, BUENO)
    con = abrir_zona(rutas.bronce_db)
    res = construir_bronce(rutas, con, AHORA, {"ventas": ["id", "valor", "requerida"]})
    con.close()
    assert res.aplicados == [] and len(res.bloqueados) == 1


def test_funciones_puras() -> None:
    assert solapamiento({"1", "2"}, {"2", "3"}) == 0.5
    assert percentil([1, 2, 3, 4, 5], 50) == 3
    assert len(dias_faltantes({date(2025, 1, 1)}, date(2025, 1, 1), date(2025, 1, 3))) == 2
