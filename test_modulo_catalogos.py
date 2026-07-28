import os
import sqlite3
import pytest
import unittest.mock as mock

# Import the module under test
import modulo_catalogos

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """
    Sets up a clean temporary database file for each test, mocking CAT_DB_PATH
    to isolate database tests from the production database.
    """
    test_db = tmp_path / "test_catalogos_db.sqlite"
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", str(test_db))
    yield str(test_db)
    if test_db.exists():
        try:
            test_db.unlink()
        except OSError:
            pass

def test_ic_init_db_creates_indexes():
    """
    Verifies that the required tables and indexes (specifically idx_ic_estilos_depto
    and idx_ic_estilo) are correctly created during DB initialization.
    """
    modulo_catalogos.ic_init_db()

    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()

    # Verify tables are created
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    assert "ic_estilos" in tables
    assert "ic_fracciones" in tables

    # Verify index idx_ic_estilos_depto exists on departamento
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ic_estilos'")
    indexes = {row[0] for row in cur.fetchall()}
    assert "idx_ic_estilos_depto" in indexes
    assert "idx_ic_estilo" in indexes

    con.close()

def test_ic_listar_estilos_pre_aggregation():
    """
    Verifies that the optimized SQL LEFT JOIN query in ic_listar_estilos correctly pre-aggregates
    both the number of fractions ('n_frac') and sum of fraction prices ('suma_frac') for each style.
    """
    modulo_catalogos.ic_init_db()

    # Insert a style and some fractions to test pre-aggregation
    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()

    # Add a style with fractions
    modulo_catalogos.ic_guardar_estilo("ESTILO_TEST", "CORTE", 120.0, "MOCK NOTES")

    # Retrieve style id
    cur.execute("SELECT id FROM ic_estilos WHERE estilo='ESTILO_TEST'")
    estilo_id = cur.fetchone()[0]

    # Add some fractions
    modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRACCION 1", 25.5, 1)
    modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRACCION 2", 14.5, 2)

    # Add another style with no fractions
    modulo_catalogos.ic_guardar_estilo("ESTILO_EMPTY", "CORTE", 80.0, "NO FRACS")

    con.close()

    # List styles
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    # Verify the style with fractions has correct aggregates
    style_with_fracs = next(e for e in estilos if e["estilo"] == "ESTILO_TEST")
    assert style_with_fracs["n_frac"] == 2
    assert style_with_fracs["suma_frac"] == 40.0

    # Verify the empty style has 0 aggregates (TOTAL aggregates to 0.0)
    style_empty = next(e for e in estilos if e["estilo"] == "ESTILO_EMPTY")
    assert style_empty["n_frac"] == 0
    assert style_empty["suma_frac"] == 0.0

def test_ic_listar_estilos_search_and_filter():
    """
    Verifies search-string filters and department-specific filtering are correctly handled.
    """
    modulo_catalogos.ic_init_db()

    modulo_catalogos.ic_guardar_estilo("ST-01", "CORTE", 50.0)
    modulo_catalogos.ic_guardar_estilo("ST-02", "PESPUNTE", 60.0)
    modulo_catalogos.ic_guardar_estilo("ST-03", "CORTE", 70.0, "SPECIAL STYLE")

    # Filter by department
    estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos_corte) == 2
    assert {e["estilo"] for e in estilos_corte} == {"ST-01", "ST-03"}

    # Filter by search string
    estilos_search = modulo_catalogos.ic_listar_estilos(buscar="special", departamento="TODOS")
    assert len(estilos_search) == 1
    assert estilos_search[0]["estilo"] == "ST-03"

    # Filter by both
    estilos_both = modulo_catalogos.ic_listar_estilos(buscar="ST", departamento="PESPUNTE")
    assert len(estilos_both) == 1
    assert estilos_both[0]["estilo"] == "ST-02"
