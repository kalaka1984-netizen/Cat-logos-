import os
import sqlite3

import pytest

import modulo_catalogos
from modulo_catalogos import (
    cat_buscar,
    cat_get_material_por_nombre,
    cat_get_nombres_clientes,
    cat_get_nombres_materiales,
    cat_get_nombres_proveedores,
    cat_get_nombres_trabajadores,
    cat_guardar,
    cat_init_db,
)

TEST_DB_PATH = "test_catalogos_temp.sqlite"


@pytest.fixture(autouse=True)
def setup_teardown_db():
    original_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    cat_init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    modulo_catalogos.CAT_DB_PATH = original_path


def test_init_db_indexes():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cur.fetchall()}
    con.close()

    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        assert f"idx_{tabla}_nombre" in indexes
        assert f"idx_{tabla}_estatus_nombre" in indexes


def test_cat_guardar_and_buscar():
    datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "estatus": "ACTIVO",
    }
    success, reg_id = cat_guardar("materiales", datos)
    assert success is True
    assert reg_id > 0

    # Search with empty query
    rows_all = cat_buscar("materiales", "", "TODOS")
    assert len(rows_all) == 1
    assert rows_all[0][1] == "CUERO VACUNO"

    # Search with specific filter
    rows_filtered = cat_buscar("materiales", "CUERO", "ACTIVO")
    assert len(rows_filtered) == 1

    # Search non-matching text
    rows_empty = cat_buscar("materiales", "NONEXISTENT", "ACTIVO")
    assert len(rows_empty) == 0


def test_cat_get_material_por_nombre():
    datos = {
        "nombre": "SUELA DE GOMA",
        "tipo_material": "DIRECTO",
        "unidad_default": "PAR",
        "departamento": "ACABADO",
        "estatus": "ACTIVO",
    }
    cat_guardar("materiales", datos)

    res = cat_get_material_por_nombre("SUELA DE GOMA")
    assert res.get("nombre") == "SUELA DE GOMA"
    assert res.get("tipo_material") == "DIRECTO"

    res_missing = cat_get_material_por_nombre("INEXISTENTE")
    assert res_missing == {}


def test_cat_get_nombres():
    # Insert materials
    cat_guardar("materiales", {"nombre": "MAT 1", "estatus": "ACTIVO"})
    cat_guardar("materiales", {"nombre": "MAT 2", "estatus": "INACTIVO"})

    mats_active = cat_get_nombres_materiales(solo_activos=True)
    mats_all = cat_get_nombres_materiales(solo_activos=False)
    assert mats_active == ["MAT 1"]
    assert sorted(mats_all) == ["MAT 1", "MAT 2"]

    # Insert workers
    cat_guardar("trabajadores", {"nombre": "TRABAJADOR 1", "estatus": "ACTIVO"})
    workers = cat_get_nombres_trabajadores(solo_activos=True)
    assert workers == ["TRABAJADOR 1"]

    # Insert suppliers
    cat_guardar("proveedores", {"nombre": "PROVEEDOR 1", "estatus": "ACTIVO"})
    suppliers = cat_get_nombres_proveedores(solo_activos=True)
    assert suppliers == ["PROVEEDOR 1"]

    # Insert clients
    cat_guardar("clientes", {"nombre": "CLIENTE 1", "estatus": "ACTIVO"})
    clients = cat_get_nombres_clientes(solo_activos=True)
    assert clients == ["CLIENTE 1"]
