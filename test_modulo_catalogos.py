"""
Unit tests for modulo_catalogos optimizations.
This file is designed to run in headless test environments.
It mocks tkinter and customtkinter to prevent GUI crashes or metaclass conflicts.
"""

import json
import os
import sqlite3
import sys
from unittest.mock import MagicMock

import pytest

# ── Mock GUI elements to prevent import and metaclass errors in headless test environment ──
mock_tk = MagicMock()
mock_tk_instance = MagicMock()
mock_tk_instance.winfo_screenwidth.return_value = 1920
mock_tk_instance.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_instance

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

mock_ctk = MagicMock()
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
         pass
    def winfo_children(self):
         return []
    def pack(self, *args, **kwargs):
         pass
    def after(self, *args, **kwargs):
         pass

mock_ctk.CTkFrame = DummyCTkFrame
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path, monkeypatch):
    """Set up a temporary clean database for each test."""
    temp_db = tmp_path / "test_catalogos_db.sqlite"
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", str(temp_db))
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()
    yield temp_db
    if temp_db.exists():
        try:
            os.remove(temp_db)
        except OSError:
            pass

def test_cat_guardar_and_uppercase_conversion():
    """Verify that cat_guardar converts all input fields to uppercase."""
    datos = {
        "nombre": "hilo premium",
        "tipo_material": "directo",
        "unidad_default": "dm",
        "departamento": "corte"
    }
    ok, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok is True
    assert reg_id is not None

    # Retrieve and assert they are uppercase
    row = modulo_catalogos.cat_get_by_id("materiales", reg_id)
    assert row is not None
    assert row[1] == "HILO PREMIUM"  # 'nombre' column

    retrieved_json = json.loads(row[2])
    assert retrieved_json["nombre"] == "HILO PREMIUM"
    assert retrieved_json["tipo_material"] == "DIRECTO"
    assert retrieved_json["unidad_default"] == "DM"
    assert retrieved_json["departamento"] == "CORTE"

def test_cat_get_material_por_nombre_optimized():
    """Verify optimized direct-select lookup on exact name match."""
    datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE"
    }
    modulo_catalogos.cat_guardar("materiales", datos)

    # Perform direct lookup
    res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert res != {}
    assert res["nombre"] == "CUERO VACUNO"
    assert res["tipo_material"] == "DIRECTO"

    # Non-existent material
    res_none = modulo_catalogos.cat_get_material_por_nombre("NON EXISTENT")
    assert res_none == {}

def test_empty_query_like_bypass_cat_buscar():
    """Verify empty text bypasses LIKE operator in cat_buscar."""
    # Insert few items
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA COMODA", "tipo_material": "DIRECTO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "PEGA EXTRA", "tipo_material": "INDIRECTO"})

    # Perform empty lookup
    res = modulo_catalogos.cat_buscar("materiales", "")
    assert len(res) == 2
    assert res[0][1] == "PEGA EXTRA"
    assert res[1][1] == "SUELA COMODA"

def test_ic_listar_estilos_nplusone_optimization():
    """Verify that ic_listar_estilos pre-aggregates fractions with LEFT JOIN and TOTAL()."""
    # Create style
    ok, est_id = modulo_catalogos.ic_guardar_estilo("ESTILO-XYZ", "PESPUNTE", 150.0)
    assert ok is True

    # Check n_frac and suma_frac with 0 fractions
    estilos = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # Add a couple of fractions
    modulo_catalogos.ic_guardar_fraccion(est_id, "COSTURA-1", 45.5)
    modulo_catalogos.ic_guardar_fraccion(est_id, "COSTURA-2", 30.5)

    # Re-fetch styles and verify pre-aggregated counts and totals
    estilos = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 76.0

def test_indices_created_correctly():
    """Verify database indices (including the new department index) are created."""
    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indices = {row[0] for row in cur.fetchall()}
    con.close()

    assert "idx_materiales_nombre" in indices
    assert "idx_ic_estilo" in indices
    assert "idx_ic_estilos_depto" in indices
