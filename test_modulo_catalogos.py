import os
import sqlite3

import pytest

import modulo_catalogos

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos_temp.sqlite")


@pytest.fixture(autouse=True)
def setup_test_db():
    orig_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    modulo_catalogos.CAT_DB_PATH = orig_path
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_cat_init_db_creates_indexes():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {r[0] for r in cur.fetchall()}
    con.close()

    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        assert f"idx_{tabla}_nombre" in indexes
        assert f"idx_{tabla}_estatus_nombre" in indexes


def test_cat_get_nombres_materiales():
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA NEGRA", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "PIEL AZUL", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO VIEJO", "estatus": "INACTIVO"})

    activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert activos == ["PIEL AZUL", "SUELA NEGRA"]

    todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert todos == ["HILO VIEJO", "PIEL AZUL", "SUELA NEGRA"]


def test_cat_get_nombres_trabajadores():
    modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("trabajadores", {"nombre": "ANA GOMEZ", "estatus": "INACTIVO"})

    activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
    assert activos == ["JUAN PEREZ"]

    todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)
    assert todos == ["ANA GOMEZ", "JUAN PEREZ"]


def test_cat_get_nombres_proveedores_and_clientes():
    modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROV B", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROV A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE Z", "estatus": "ACTIVO"})

    assert modulo_catalogos.cat_get_nombres_proveedores() == ["PROV A", "PROV B"]
    assert modulo_catalogos.cat_get_nombres_clientes() == ["CLIENTE Z"]
