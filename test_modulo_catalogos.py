import sys
import os
import unittest
from unittest.mock import MagicMock

# Setup headless dummy mocks for tkinter/customtkinter if GUI cannot run
class DummyCTkFrame:
    def __init__(self, *args, **kwargs): pass
    def pack(self, *args, **kwargs): pass
    def place(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def winfo_children(self): return []
    def winfo_width(self): return 800
    def winfo_height(self): return 600
    def after(self, ms, func=None, *args): return "timer"
    def after_cancel(self, id): pass
    def winfo_toplevel(self): return self

class DummyCTkWidget(DummyCTkFrame):
    def configure(self, *args, **kwargs): pass
    def config(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass
    def set(self, *args, **kwargs): pass
    def get(self, *args, **kwargs): return ""

# Mock tkinter before import
mock_tk = MagicMock()
mock_tk_instance = MagicMock()
mock_tk_instance.winfo_screenwidth.return_value = 1920
mock_tk_instance.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_instance

sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()

mock_ctk = MagicMock()
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkWidget
mock_ctk.CTkButton = DummyCTkWidget
mock_ctk.CTkEntry = DummyCTkWidget
mock_ctk.CTkComboBox = DummyCTkWidget
mock_ctk.CTkTextbox = DummyCTkWidget
mock_ctk.CTkScrollableFrame = DummyCTkFrame
mock_ctk.CTkSegmentedButton = DummyCTkWidget
mock_ctk.CTkRadioButton = DummyCTkWidget
mock_ctk.CTkToplevel = DummyCTkFrame
mock_ctk.CTkScrollbar = DummyCTkWidget
sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "test_catalogos_db.sqlite")
        modulo_catalogos.CAT_DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_cat_get_material_por_nombre(self):
        mat_data = {
            "nombre": "PIEL VACUNO NEGRA",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ"
        }
        ok, res_id = modulo_catalogos.cat_guardar("materiales", mat_data)
        self.assertTrue(ok)

        # Test exact match
        res = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRA")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")
        self.assertEqual(res.get("unidad_default"), "DM")

        # Test lowercase / untrimmed string matching
        res_lower = modulo_catalogos.cat_get_material_por_nombre("  piel vacuno negra  ")
        self.assertEqual(res_lower.get("tipo_material"), "DIRECTO")

        # Test non-existing item returns empty dict
        res_none = modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT_MATERIAL")
        self.assertEqual(res_none, {})

    def test_cat_get_material_por_nombre_empty(self):
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre(""), {})
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre("   "), {})

if __name__ == "__main__":
    unittest.main()
