import os
import sqlite3
import pytest
import modulo_catalogos

TEST_DB_PATH = "test_catalogos_temp.sqlite"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", TEST_DB_PATH)
    modulo_catalogos.cat_init_db()

    # Pre-populate sample materials
    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "PIEL VACUNO NEGRO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ"
    })

    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "HILO NYLON 40",
        "tipo_material": "INDIRECTO",
        "unidad_default": "mts",
        "departamento": "PESPUNTE",
        "visible_monitor": "NO"
    })

    yield

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_cat_get_material_por_nombre_exact():
    mat = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRO")
    assert mat.get("nombre") == "PIEL VACUNO NEGRO"
    assert mat.get("tipo_material") == "DIRECTO"
    assert mat.get("unidad_default") == "DM"

def test_cat_get_material_por_nombre_case_insensitive_and_whitespace():
    mat = modulo_catalogos.cat_get_material_por_nombre("  hilo nylon 40  ")
    assert mat.get("nombre") == "HILO NYLON 40"
    assert mat.get("unidad_default") == "MTS"

def test_cat_get_material_por_nombre_nonexistent():
    mat = modulo_catalogos.cat_get_material_por_nombre("NONEXISTENT MATERIAL")
    assert mat == {}

def test_cat_get_material_por_nombre_empty():
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}
    assert modulo_catalogos.cat_get_material_por_nombre(None) == {}
