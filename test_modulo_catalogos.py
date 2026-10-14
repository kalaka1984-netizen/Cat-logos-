import os
import sqlite3

import pytest

import modulo_catalogos

TEST_DB = "test_catalogos_temp.sqlite"


@pytest.fixture(autouse=True)
def setup_teardown_db():
    original_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    modulo_catalogos.cat_init_db()
    yield
    modulo_catalogos.CAT_DB_PATH = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_index_creation():
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [r[0] for r in cur.fetchall()]
    con.close()

    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        assert f"idx_{tabla}_nombre" in indexes
        assert f"idx_{tabla}_estatus_nombre" in indexes


def test_get_nombres_tabla():
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_ACTIVO_1", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_ACTIVO_2", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_INACTIVO_1", "estatus": "INACTIVO"})

    activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert activos == ["MAT_ACTIVO_1", "MAT_ACTIVO_2"]

    todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert todos == ["MAT_ACTIVO_1", "MAT_ACTIVO_2", "MAT_INACTIVO_1"]


def test_get_nombres_invalid_tabla():
    with pytest.raises(ValueError, match="Tabla no permitida"):
        modulo_catalogos._cat_get_nombres_tabla("tabla_inexistente")


def test_get_material_por_nombre():
    material_datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
    }
    modulo_catalogos.cat_guardar("materiales", material_datos)

    res = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
    assert res["nombre"] == "CUERO VACUNO"
    assert res["tipo_material"] == "DIRECTO"
    assert res["unidad_default"] == "DM"

    res_empty = modulo_catalogos.cat_get_material_por_nombre("")
    assert res_empty == {}

    res_nonexistent = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
    assert res_nonexistent == {}


def test_nombres_trabajadores_proveedores_clientes():
    modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROVEEDOR ACME", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE GLOBAL", "estatus": "ACTIVO"})

    assert modulo_catalogos.cat_get_nombres_trabajadores() == ["JUAN PEREZ"]
    assert modulo_catalogos.cat_get_nombres_proveedores() == ["PROVEEDOR ACME"]
    assert modulo_catalogos.cat_get_nombres_clientes() == ["CLIENTE GLOBAL"]
