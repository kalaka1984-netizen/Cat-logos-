"""
Unit tests for modulo_catalogos optimizations.
"""
import os
import sqlite3

import pytest

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_temp.sqlite")


@pytest.fixture(autouse=True)
def setup_test_db():
    # Override database path to temporary database file
    orig_db_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    mc.cat_init_db()
    yield
    mc.CAT_DB_PATH = orig_db_path
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass


def test_composite_indexes_created():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(f"PRAGMA index_list({tabla})")
        indexes = [row[1] for row in cur.fetchall()]
        assert f"idx_{tabla}_estatus_nombre" in indexes
    con.close()


def test_cat_guardar_and_get_material_por_nombre():
    datos = {
        "nombre": "PIEL VACUNA NEGRA",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "estatus": "ACTIVO",
    }
    ok, mat_id = mc.cat_guardar("materiales", datos)
    assert ok is True
    assert isinstance(mat_id, int)

    res = mc.cat_get_material_por_nombre("PIEL VACUNA NEGRA")
    assert res.get("nombre") == "PIEL VACUNA NEGRA"
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Non-existent material
    res_empty = mc.cat_get_material_por_nombre("INEXISTENTE")
    assert res_empty == {}


def test_cat_buscar_empty_search():
    mc.cat_guardar("materiales", {"nombre": "MAT_A", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "MAT_B", "estatus": "INACTIVO"})

    activos = mc.cat_buscar("materiales", "", "ACTIVO")
    assert len(activos) == 1
    assert activos[0][1] == "MAT_A"

    todos = mc.cat_buscar("materiales", "", "TODOS")
    assert len(todos) == 2


def test_cat_get_nombres_functions():
    mc.cat_guardar("materiales", {"nombre": "SUELA HULE", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "HILO NYLON", "estatus": "INACTIVO"})

    nombres_activos = mc.cat_get_nombres_materiales(solo_activos=True)
    assert nombres_activos == ["SUELA HULE"]

    nombres_todos = mc.cat_get_nombres_materiales(solo_activos=False)
    assert nombres_todos == ["HILO NYLON", "SUELA HULE"]


def test_cat_precarga_material():
    mc.cat_guardar("materiales", {
        "nombre": "CASCO TERMOPLÁSTICO",
        "tipo_material": "INDIRECTO",
        "unidad_default": "PAR",
        "departamento": "MONTADO",
        "visible_monitor": "NO",
        "es_principal": "NO",
        "estatus": "ACTIVO",
    })

    precarga = mc.cat_precarga_material("CASCO TERMOPLÁSTICO")
    assert precarga["tipo_ft"] == "IND"
    assert precarga["unidad"] == "PAR"
    assert precarga["departamento"] == "MONTADO"
    assert precarga["monitor"] is False
    assert precarga["principal"] is False
