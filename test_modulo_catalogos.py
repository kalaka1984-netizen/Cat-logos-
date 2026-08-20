import os
import sys
import unittest
import sqlite3
import json
from unittest.mock import MagicMock

# Dummy module mock for customtkinter to enable headless testing
class DummyCTkWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def config(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def winfo_toplevel(self):
        return self
    def winfo_width(self):
        return 100
    def winfo_height(self):
        return 100
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def update_idletasks(self):
        pass
    def bind(self, *args, **kwargs):
        pass
    def destroy(self):
        pass
    def grab_release(self):
        pass
    def lift(self):
        pass
    def lower(self):
        pass
    def after(self, ms, func=None, *args):
        return "timer_id"
    def after_cancel(self, timer_id):
        pass

class DummyCTk(DummyCTkWidget):
    def title(self, title):
        pass
    def geometry(self, geom):
        pass
    def mainloop(self):
        pass

class DummyCTkToplevel(DummyCTkWidget):
    def resizable(self, *args):
        pass
    def grab_set(self):
        pass

# Setup sys.modules mocks before importing modulo_catalogos
dummy_ctk = MagicMock()
dummy_ctk.set_appearance_mode = lambda mode: None
dummy_ctk.set_default_color_theme = lambda theme: None
dummy_ctk.set_widget_scaling = lambda scale: None
dummy_ctk.set_window_scaling = lambda scale: None

dummy_ctk.CTkFrame = DummyCTkWidget
dummy_ctk.CTkLabel = DummyCTkWidget
dummy_ctk.CTkButton = DummyCTkWidget
dummy_ctk.CTkEntry = DummyCTkWidget
dummy_ctk.CTkComboBox = DummyCTkWidget
dummy_ctk.CTkTextbox = DummyCTkWidget
dummy_ctk.CTkScrollableFrame = DummyCTkWidget
dummy_ctk.CTkScrollbar = DummyCTkWidget
dummy_ctk.CTkSegmentedButton = DummyCTkWidget
dummy_ctk.CTkRadioButton = DummyCTkWidget
dummy_ctk.CTk = DummyCTk
dummy_ctk.CTkToplevel = DummyCTkToplevel

sys.modules['customtkinter'] = dummy_ctk

import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_catalogos_temp.sqlite"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        self.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.test_db
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_cat_get_material_por_nombre(self):
        # Test empty input
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre(""), {})
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre("   "), {})

        # Test non-existent material
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre("MATERIAL_INEXISTENTE"), {})

        # Insert material
        datos_mat = {
            "nombre": "PIEL VACUNO NEGRA",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ"
        }
        ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos_mat)
        self.assertTrue(ok)

        # Retrieve material exact match, lowercase, and with spaces
        res1 = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRA")
        self.assertEqual(res1.get("nombre"), "PIEL VACUNO NEGRA")
        self.assertEqual(res1.get("tipo_material"), "DIRECTO")
        self.assertEqual(res1.get("unidad_default"), "DM")

        res2 = modulo_catalogos.cat_get_material_por_nombre("piel vacuno negra")
        self.assertEqual(res2.get("nombre"), "PIEL VACUNO NEGRA")

        res3 = modulo_catalogos.cat_get_material_por_nombre("  PIEL VACUNO NEGRA   ")
        self.assertEqual(res3.get("nombre"), "PIEL VACUNO NEGRA")

if __name__ == "__main__":
    unittest.main()
