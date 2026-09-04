# -*- coding: utf-8 -*-
"""
Tests for modulo_catalogos performance and correctness.
Mocks UI dependencies using dummy classes to avoid metaclass conflicts in headless environments.
"""

import sys
import os
import sqlite3
import json
import pytest
from unittest.mock import MagicMock

# Create dummy classes for CTk components to prevent metaclass conflict
class DummyCTkComponent:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after(self, *args, **kwargs):
        pass

ctk_mock = MagicMock()
ctk_mock.set_appearance_mode = MagicMock()
ctk_mock.set_default_color_theme = MagicMock()
ctk_mock.CTkFrame = DummyCTkComponent
ctk_mock.CTkLabel = DummyCTkComponent
ctk_mock.CTkButton = DummyCTkComponent
ctk_mock.CTkEntry = DummyCTkComponent
ctk_mock.CTkComboBox = DummyCTkComponent
ctk_mock.CTkTextbox = DummyCTkComponent
ctk_mock.CTkScrollableFrame = DummyCTkComponent
ctk_mock.CTkSegmentedButton = DummyCTkComponent
ctk_mock.CTkToplevel = DummyCTkComponent
ctk_mock.CTk = DummyCTkComponent

sys.modules["customtkinter"] = ctk_mock
sys.modules["darkdetect"] = MagicMock()

import modulo_catalogos as mc

@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    db_file = tmp_path / "test_catalogos.sqlite"
    old_db_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = str(db_file)
    mc.cat_init_db()
    yield
    mc.CAT_DB_PATH = old_db_path

def test_cat_get_material_por_nombre_found():
    datos = {
        "nombre": "PIEL VACUNA NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    mc.cat_guardar("materiales", datos)

    # Test exact match
    res = mc.cat_get_material_por_nombre("PIEL VACUNA NEGRA")
    assert res.get("nombre") == "PIEL VACUNA NEGRA"
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Test case insensitivity and whitespace trimming
    res_case = mc.cat_get_material_por_nombre("  piel vacuna negra  ")
    assert res_case.get("nombre") == "PIEL VACUNA NEGRA"

def test_cat_get_material_por_nombre_not_found():
    res = mc.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
    assert res == {}

def test_cat_get_material_por_nombre_empty():
    res = mc.cat_get_material_por_nombre("")
    assert res == {}
