# -*- coding: utf-8 -*-
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
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    modulo_catalogos.CAT_DB_PATH = original_db


def test_cat_get_material_por_nombre_success():
    datos = {
        "nombre": "PIEL VACUNO NEGRA",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "costo_ref": 45.50
    }
    ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok is True

    # Test exact match
    res = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRA")
    assert res["nombre"] == "PIEL VACUNO NEGRA"
    assert res["unidad_default"] == "DM"  # cat_guardar converts string fields to uppercase

    # Test case insensitivity and whitespace trimming
    res_lower = modulo_catalogos.cat_get_material_por_nombre("  piel vacuno negra  ")
    assert res_lower["nombre"] == "PIEL VACUNO NEGRA"


def test_cat_get_material_por_nombre_not_found():
    res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
    assert res == {}


def test_cat_get_material_por_nombre_empty():
    res = modulo_catalogos.cat_get_material_por_nombre("")
    assert res == {}
    res_spaces = modulo_catalogos.cat_get_material_por_nombre("   ")
    assert res_spaces == {}
