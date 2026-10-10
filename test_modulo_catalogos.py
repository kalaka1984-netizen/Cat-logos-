"""Unit tests for modulo_catalogos.py database, query optimizations, and lookup functions."""

import os
import sqlite3

import pytest

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_catalogos_temp.sqlite",
)


@pytest.fixture(autouse=True)
def setup_teardown_db():
    """Setup a temporary test database for catalog tests."""
    mc.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    mc.cat_init_db()
    mc.ic_init_db()

    yield

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass


def test_db_initialization_and_indexes():
    """Verify that all expected tables and indexes are created."""
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    expected_tables = {
        "materiales",
        "trabajadores",
        "proveedores",
        "clientes",
        "proveedor_materiales",
        "ic_config",
        "ic_estilos",
        "ic_fracciones",
    }
    assert expected_tables.issubset(tables)

    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {r[0] for r in cur.fetchall()}
    assert "idx_ic_estilos_depto" in indexes
    assert "idx_materiales_nombre" in indexes
    con.close()


def test_catalog_crud_and_optimizations():
    """Test cat_guardar, cat_buscar, cat_get_material_por_nombre, and cat_get_nombres_*."""
    # Save test materials
    ok1, _ = mc.cat_guardar(
        "materiales",
        {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "estatus": "ACTIVO",
        },
    )
    assert ok1 is True

    ok2, _ = mc.cat_guardar(
        "materiales",
        {
            "nombre": "HILO NYLON",
            "tipo_material": "INDIRECTO",
            "unidad_default": "pza",
            "departamento": "PESPUNTE",
            "estatus": "INACTIVO",
        },
    )
    assert ok2 is True

    # Test cat_get_nombres_materiales (only active vs all)
    activos = mc.cat_get_nombres_materiales(solo_activos=True)
    assert activos == ["CUERO VACUNO"]

    todos = mc.cat_get_nombres_materiales(solo_activos=False)
    assert sorted(todos) == ["CUERO VACUNO", "HILO NYLON"]

    # Test cat_get_material_por_nombre (direct point query)
    mat_data = mc.cat_get_material_por_nombre("CUERO VACUNO")
    assert mat_data.get("tipo_material") == "DIRECTO"
    assert mat_data.get("unidad_default") == "DM"

    # Test non-existent lookup
    assert mc.cat_get_material_por_nombre("NON_EXISTENT") == {}

    # Test empty query optimization in cat_buscar
    rows = mc.cat_buscar("materiales", texto="", estatus="ACTIVO")
    assert len(rows) == 1
    assert rows[0][1] == "CUERO VACUNO"


def test_ic_estilos_and_preaggregation():
    """Test ic_listar_estilos SQL JOIN pre-aggregation (N+1 query fix)."""
    ok1, est_id1 = mc.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 100.0, "Nota A")
    assert ok1 is True

    ok2, _ = mc.ic_guardar_estilo("ESTILO_B", "CORTE", 150.0, "Nota B")
    assert ok2 is True

    # Add fractions to ESTILO_A
    mc.ic_guardar_fraccion(est_id1, "COSTURA_1", 40.0, 1)
    mc.ic_guardar_fraccion(est_id1, "COSTURA_2", 60.0, 2)

    # List styles
    estilos = mc.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    estilo_a = next(e for e in estilos if e["estilo"] == "ESTILO_A")
    assert estilo_a["n_frac"] == 2
    assert estilo_a["suma_frac"] == 100.0

    estilo_b = next(e for e in estilos if e["estilo"] == "ESTILO_B")
    assert estilo_b["n_frac"] == 0
    assert estilo_b["suma_frac"] == 0.0

    # Test department filter
    pespunte = mc.ic_listar_estilos(buscar="", departamento="PESPUNTE")
    assert len(pespunte) == 1
    assert pespunte[0]["estilo"] == "ESTILO_A"
