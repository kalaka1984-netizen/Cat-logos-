# -*- coding: utf-8 -*-
"""Unit tests for modulo_catalogos.py performance optimizations and core database lookups."""

import os
import tempfile
import sys
from unittest.mock import MagicMock

# ── Mock tkinter and customtkinter for headless environment ──────────────────
# Create dummy classes to prevent metaclass conflict when classes inherit from CTkFrame
class DummyFrame:
    def __init__(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return self
    def bind(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        return "after_id"
    def after_cancel(self, *args, **kwargs):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkScrollableFrame = DummyFrame
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkEntry = MagicMock
mock_ctk.CTkComboBox = MagicMock
mock_ctk.CTkTextbox = MagicMock
mock_ctk.CTkSegmentedButton = MagicMock
mock_ctk.CTkScrollbar = MagicMock
mock_ctk.CTkToplevel = DummyFrame
mock_ctk.CTkRadioButton = MagicMock
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()

sys.modules["customtkinter"] = mock_ctk

import pytest
import modulo_catalogos as mc


@pytest.fixture
def temp_db():
    db_file = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False).name
    original_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = db_file
    mc.cat_init_db()
    yield db_file
    mc.CAT_DB_PATH = original_path
    if os.path.exists(db_file):
        os.remove(db_file)


def test_cat_get_material_por_nombre_success(temp_db):
    """Test direct indexed lookup for material by name."""
    mat_data = {
        "nombre": "PIEL VACUNO FLOR",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    ok, reg_id = mc.cat_guardar("materiales", mat_data)
    assert ok is True

    # Test exact lookup
    res = mc.cat_get_material_por_nombre("PIEL VACUNO FLOR")
    assert res.get("nombre") == "PIEL VACUNO FLOR"
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Test case insensitive & leading/trailing space handling
    res_case = mc.cat_get_material_por_nombre("  piel vacuno flor  ")
    assert res_case.get("nombre") == "PIEL VACUNO FLOR"


def test_cat_get_material_por_nombre_nonexistent(temp_db):
    """Test lookup returns empty dict when material is not found."""
    res = mc.cat_get_material_por_nombre("INEXISTENTE_MATERIAL")
    assert res == {}


def test_cat_get_material_por_nombre_empty_input(temp_db):
    """Test lookup with empty or space string returns empty dict."""
    assert mc.cat_get_material_por_nombre("") == {}
    assert mc.cat_get_material_por_nombre("   ") == {}


def test_cat_precarga_material_integration(temp_db):
    """Test cat_precarga_material correctly uses optimized lookup."""
    mat_data = {
        "nombre": "HILO NYLON 40",
        "tipo_material": "INDIRECTO",
        "unidad_default": "MTS",
        "departamento": "PESPUNTE",
        "visible_monitor": "SÍ",
        "es_principal": "NO"
    }
    mc.cat_guardar("materiales", mat_data)

    precarga = mc.cat_precarga_material("hilo nylon 40")
    assert precarga["tipo_ft"] == "IND"
    assert precarga["unidad"] == "MTS"
    assert precarga["departamento"] == "PESPUNTE"
    assert precarga["monitor"] is True
    assert precarga["principal"] is False
