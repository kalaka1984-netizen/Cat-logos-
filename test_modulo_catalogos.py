# -*- coding: utf-8 -*-
import sys
import sqlite3
import pytest
import json
from unittest.mock import MagicMock

class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs):
        pass

# Mock tkinter and customtkinter to support importing modulo_catalogos in headless environments
mock_tk = MagicMock()
mock_ttk = MagicMock()
mock_messagebox = MagicMock()

# For customtkinter, we must use real classes for components that are used as base classes
# to prevent metaclass conflicts in Python's class creation.
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkToplevel = DummyCTkToplevel

# Avoid TypeError during screen scale calculation by making winfo methods return integer screen dimensions
mock_tk.Tk.return_value.winfo_screenwidth.return_value = 1920
mock_tk.Tk.return_value.winfo_screenheight.return_value = 1080

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_ttk
sys.modules['tkinter.messagebox'] = mock_messagebox
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos

@pytest.fixture
def test_db(tmp_path):
    # Setup temporary database path
    temp_db_file = tmp_path / "test_catalogos_db.sqlite"
    original_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = str(temp_db_file)

    # Initialize the database schemas
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield str(temp_db_file)

    # Restore original path
    modulo_catalogos.CAT_DB_PATH = original_db_path

def test_database_indices(test_db):
    """Verify that indices are successfully created, including the new department index."""
    con = sqlite3.connect(test_db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indices = [r[0] for r in cur.fetchall()]
    con.close()

    # Check for department-based index on ic_estilos
    assert "idx_ic_estilos_depto" in indices
    assert "idx_ic_estilo" in indices
    assert "idx_materiales_nombre" in indices

def test_cat_get_material_por_nombre_optimized(test_db):
    """Test that our direct SELECT optimization works as expected."""
    # Insert a dummy material
    con = sqlite3.connect(test_db)
    cur = con.cursor()
    dummy_datos = json.dumps({
        "tipo": "PIEL",
        "unidad": "DM2",
        "depto": "CORTE",
        "visible_monitor": "SI"
    })
    cur.execute("""
        INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod)
        VALUES (?, ?, ?, ?, ?)
    """, ("CUERO PREMIUM", dummy_datos, "ACTIVO", "2025-01-01", "2025-01-01"))
    con.commit()
    con.close()

    # Query using optimized function
    res = modulo_catalogos.cat_get_material_por_nombre("CUERO PREMIUM")
    assert res == {
        "tipo": "PIEL",
        "unidad": "DM2",
        "depto": "CORTE",
        "visible_monitor": "SI"
    }

    # Query non-existent
    res_none = modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT")
    assert res_none == {}

def test_ic_listar_estilos_n_plus_one_optimization(test_db):
    """Verify that the N+1 optimization correctly aggregates fraction count and total price."""
    # 1. Save style
    ok, res = modulo_catalogos.ic_guardar_estilo(
        estilo="BOTA VAQUERA",
        departamento="CORTE",
        precio_par=120.0,
        notas="Test bota"
    )
    assert ok is True
    estilo_id = res

    # Retrieve when there are no fractions yet
    estilos = modulo_catalogos.ic_listar_estilos(buscar="")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "BOTA VAQUERA"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # 2. Add fractions to style
    ok, frac1 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="CORTAR CHINELA",
        precio=15.5,
        orden=1
    )
    assert ok is True

    ok, frac2 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="CORTAR TALON",
        precio=10.25,
        orden=2
    )
    assert ok is True

    # 3. Retrieve style list and verify pre-aggregated fraction count and total price
    estilos = modulo_catalogos.ic_listar_estilos(buscar="")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "BOTA VAQUERA"
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 25.75

def test_ic_listar_estilos_search_filtering(test_db):
    """Verify that searching works correctly, with both empty and non-empty search queries."""
    # Save a couple of styles
    modulo_catalogos.ic_guardar_estilo("TENIS DEPORTIVO", "COSTURA", 85.0, "Running shoes")
    modulo_catalogos.ic_guardar_estilo("ZAPATO FORMAL", "CORTE", 150.0, "Formal wear")

    # Empty search - should list both
    all_styles = modulo_catalogos.ic_listar_estilos(buscar="")
    assert len(all_styles) == 2

    # Specific search - active LIKE query
    tennis = modulo_catalogos.ic_listar_estilos(buscar="tenis")
    assert len(tennis) == 1
    assert tennis[0]["estilo"] == "TENIS DEPORTIVO"

    formal = modulo_catalogos.ic_listar_estilos(buscar="formal")
    assert len(formal) == 1
    assert formal[0]["estilo"] == "ZAPATO FORMAL"

    # Specific department filtering
    corte_only = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(corte_only) == 1
    assert corte_only[0]["estilo"] == "ZAPATO FORMAL"
