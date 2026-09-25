# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import json
import types

# Create dummy customtkinter module to avoid metaclass conflicts
dummy_ctk = types.ModuleType("customtkinter")

class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []

def set_appearance_mode(*args, **kwargs):
    pass

def set_default_color_theme(*args, **kwargs):
    pass

def set_widget_scaling(*args, **kwargs):
    pass

def set_window_scaling(*args, **kwargs):
    pass

dummy_ctk.set_appearance_mode = set_appearance_mode
dummy_ctk.set_default_color_theme = set_default_color_theme
dummy_ctk.set_widget_scaling = set_widget_scaling
dummy_ctk.set_window_scaling = set_window_scaling

for attr in [
    "CTkFrame", "CTkLabel", "CTkButton", "CTkEntry", "CTkComboBox",
    "CTkTextbox", "CTkScrollableFrame", "CTkScrollbar", "CTkSegmentedButton",
    "CTkToplevel", "CTkRadioButton", "CTk"
]:
    setattr(dummy_ctk, attr, type(attr, (DummyWidget,), {}))

sys.modules["customtkinter"] = dummy_ctk

import unittest
import modulo_catalogos as mc

class TestModuloCatalogos(unittest.TestCase):

    def setUp(self):
        self.test_db = "test_catalogos_temp.sqlite"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.original_db = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = self.test_db
        mc.cat_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.original_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_cat_get_material_por_nombre_success(self):
        datos = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ"
        }
        ok, reg_id = mc.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        res = mc.cat_get_material_por_nombre("CUERO VACUNO")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")
        self.assertEqual(res.get("unidad_default"), "DM")
        self.assertEqual(res.get("departamento"), "CORTE")

    def test_cat_get_material_por_nombre_case_insensitive_and_whitespace(self):
        datos = {
            "nombre": "Hilo Nylon 40",
            "tipo_material": "INDIRECTO",
            "unidad_default": "m"
        }
        ok, reg_id = mc.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        res = mc.cat_get_material_por_nombre("  hilo nylon 40  ")
        self.assertEqual(res.get("tipo_material"), "INDIRECTO")

    def test_cat_get_material_por_nombre_not_found(self):
        res = mc.cat_get_material_por_nombre("INEXISTENTE")
        self.assertEqual(res, {})

    def test_cat_get_material_por_nombre_empty_string(self):
        res = mc.cat_get_material_por_nombre("")
        self.assertEqual(res, {})
        res_none = mc.cat_get_material_por_nombre(None)
        self.assertEqual(res_none, {})

    def test_cat_get_material_por_nombre_corrupted_json(self):
        # Directly insert corrupted JSON row
        con = sqlite3.connect(self.test_db)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)",
            ("CORRUPTED_MAT", "{bad_json", "ACTIVO", "2025-01-01", "2025-01-01")
        )
        con.commit()
        con.close()

        res = mc.cat_get_material_por_nombre("CORRUPTED_MAT")
        self.assertEqual(res, {})


if __name__ == "__main__":
    unittest.main()
