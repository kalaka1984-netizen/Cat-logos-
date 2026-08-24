# -*- coding: utf-8 -*-
import sys
import os
import json
import sqlite3
import pytest
from unittest.mock import MagicMock

# Inject dummy customtkinter and mocked tkinter before importing modulo_catalogos
class DummyWidget:
    def __init__(self, *args, **kwargs): pass
    def winfo_children(self): return []
    def pack(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def place(self, *args, **kwargs): pass
    def after(self, *args, **kwargs): pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkOptionMenu = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkTabview = DummyWidget
mock_ctk.CTkCheckBox = DummyWidget
mock_ctk.CTkToplevel = DummyWidget

mock_tk = MagicMock()
mock_root = MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root

sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = mock_tk
sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos.sqlite")


@pytest.fixture(autouse=True)
def setup_teardown_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    mc.CAT_DB_PATH = TEST_DB_PATH
    mc.cat_init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_cat_get_material_por_nombre_success():
    datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
    }
    mc.cat_guardar("materiales", datos)

    # Exact match with upper case
    mat = mc.cat_get_material_por_nombre("CUERO VACUNO")
    assert mat["tipo_material"] == "DIRECTO"
    assert mat["unidad_default"] == "DM"
    assert mat["departamento"] == "CORTE"

    # Case insensitive and spaces trimmed
    mat_lower = mc.cat_get_material_por_nombre("  cuero vacuno  ")
    assert mat_lower == mat


def test_cat_get_material_por_nombre_not_found():
    res = mc.cat_get_material_por_nombre("INEXISTENTE")
    assert res == {}


def test_cat_get_material_por_nombre_empty_input():
    assert mc.cat_get_material_por_nombre("") == {}
    assert mc.cat_get_material_por_nombre("   ") == {}
    assert mc.cat_get_material_por_nombre(None) == {}


def test_cat_get_material_por_nombre_invalid_json():
    # Manually insert invalid JSON
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)",
        ("CORRUPTED_MAT", "INVALID_JSON{", "ACTIVO", "2025-01-01", "2025-01-01")
    )
    con.commit()
    con.close()

    res = mc.cat_get_material_por_nombre("CORRUPTED_MAT")
    assert res == {}
