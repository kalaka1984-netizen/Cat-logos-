# -*- coding: utf-8 -*-
import os
import sqlite3
import pytest
import modulo_catalogos as mc

TEST_DB_PATH = mc.CAT_DB_PATH + ".test.sqlite"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    monkeypatch.setattr(mc, "CAT_DB_PATH", TEST_DB_PATH)
    mc.cat_init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_composite_indexes_created():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    for tbl in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (f"idx_{tbl}_estatus_nombre",)
        )
        assert cur.fetchone() is not None, f"Index idx_{tbl}_estatus_nombre missing"
    con.close()

def test_cat_get_nombres_functions():
    # Insert items into catalog tables
    mc.cat_guardar("materiales", {"nombre": "SUELA DE HULE", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "PIEL VACUNO", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "HILO OBSOLETO", "estatus": "INACTIVO"})

    mc.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    mc.cat_guardar("trabajadores", {"nombre": "MARIA GOMEZ", "estatus": "INACTIVO"})

    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR A", "estatus": "ACTIVO"})
    mc.cat_guardar("clientes", {"nombre": "CLIENTE X", "estatus": "ACTIVO"})

    # Test materiales
    mats_activos = mc.cat_get_nombres_materiales(solo_activos=True)
    assert mats_activos == ["PIEL VACUNO", "SUELA DE HULE"]

    mats_todos = mc.cat_get_nombres_materiales(solo_activos=False)
    assert mats_todos == ["HILO OBSOLETO", "PIEL VACUNO", "SUELA DE HULE"]

    # Test trabajadores
    trabs_activos = mc.cat_get_nombres_trabajadores(solo_activos=True)
    assert trabs_activos == ["JUAN PEREZ"]

    trabs_todos = mc.cat_get_nombres_trabajadores(solo_activos=False)
    assert trabs_todos == ["JUAN PEREZ", "MARIA GOMEZ"]

    # Test proveedores
    provs = mc.cat_get_nombres_proveedores(solo_activos=True)
    assert provs == ["PROVEEDOR A"]

    # Test clientes
    clis = mc.cat_get_nombres_clientes(solo_activos=True)
    assert clis == ["CLIENTE X"]

def test_invalid_table_whitelist():
    with pytest.raises(ValueError, match="Tabla no válida"):
        mc._cat_get_nombres_tabla("tabla_inexistente", True)
