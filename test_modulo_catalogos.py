import os
import sqlite3

import pytest

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_catalogos_temp.sqlite"
)


@pytest.fixture(autouse=True)
def setup_teardown_db():
    orig_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    mc.cat_init_db()
    mc.ic_init_db()

    yield

    mc.CAT_DB_PATH = orig_path
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_composite_indexes_created():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(f"PRAGMA index_list({tabla})")
        indexes = [r[1] for r in cur.fetchall()]
        assert f"idx_{tabla}_estatus_nombre" in indexes
    con.close()


def test_cat_get_nombres_tabla_whitelist():
    assert mc._cat_get_nombres_tabla("malicious_table; DROP TABLE materiales; --") == []
    assert mc._cat_get_nombres_tabla("usuarios") == []


def test_cat_get_nombres_materiales_empty():
    assert mc.cat_get_nombres_materiales(solo_activos=True) == []
    assert mc.cat_get_nombres_materiales(solo_activos=False) == []


def test_cat_get_nombres_filtering_and_ordering():
    # Insert materials with different statuses and unordered names
    mc.cat_guardar("materiales", {"nombre": "ZAPATO PIEL", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "AGUJA #5", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "BROCHE OBSOLETO", "estatus": "INACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "CORDON NEGRO", "estatus": "ACTIVO"})

    activos = mc.cat_get_nombres_materiales(solo_activos=True)
    assert activos == ["AGUJA #5", "CORDON NEGRO", "ZAPATO PIEL"]

    todos = mc.cat_get_nombres_materiales(solo_activos=False)
    assert todos == ["AGUJA #5", "BROCHE OBSOLETO", "CORDON NEGRO", "ZAPATO PIEL"]


def test_cat_get_nombres_trabajadores():
    mc.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    mc.cat_guardar("trabajadores", {"nombre": "ANA GOMEZ", "estatus": "INACTIVO"})

    assert mc.cat_get_nombres_trabajadores(solo_activos=True) == ["JUAN PEREZ"]
    assert mc.cat_get_nombres_trabajadores(solo_activos=False) == ["ANA GOMEZ", "JUAN PEREZ"]


def test_cat_get_nombres_proveedores():
    mc.cat_guardar("proveedores", {"nombre": "PELETERIA CENTRAL", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "CURTIDOS DEL NORTE", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "BAJA PROVEEDOR", "estatus": "INACTIVO"})

    assert mc.cat_get_nombres_proveedores(solo_activos=True) == ["CURTIDOS DEL NORTE", "PELETERIA CENTRAL"]
    assert mc.cat_get_nombres_proveedores(solo_activos=False) == ["BAJA PROVEEDOR", "CURTIDOS DEL NORTE", "PELETERIA CENTRAL"]


def test_cat_get_nombres_clientes():
    mc.cat_guardar("clientes", {"nombre": "ZAPATERIA EL SOL", "estatus": "ACTIVO"})
    mc.cat_guardar("clientes", {"nombre": "BOUTIQUE LUNA", "estatus": "ACTIVO"})

    assert mc.cat_get_nombres_clientes(solo_activos=True) == ["BOUTIQUE LUNA", "ZAPATERIA EL SOL"]


def test_query_plan_uses_covering_index():
    mc.cat_guardar("materiales", {"nombre": "MAT1", "estatus": "ACTIVO"})
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute(
        "EXPLAIN QUERY PLAN SELECT nombre FROM materiales WHERE estatus = ? ORDER BY nombre ASC",
        ("ACTIVO",),
    )
    plan = cur.fetchall()
    con.close()
    plan_text = " ".join(r[3] for r in plan)
    assert "idx_materiales_estatus_nombre" in plan_text
