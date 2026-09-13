import os
import sys
import types
import unittest
from unittest import mock

# ── Mock GUI libraries for headless test environment ────────────────────────
ctk_module = types.ModuleType("customtkinter")
class DummyCTkComponent:
    def __init__(self, *args, **kwargs):
        pass

ctk_module.CTkFrame = DummyCTkComponent
ctk_module.CTkLabel = DummyCTkComponent
ctk_module.CTkButton = DummyCTkComponent
ctk_module.CTkEntry = DummyCTkComponent
ctk_module.CTkCheckBox = DummyCTkComponent
ctk_module.CTkComboBox = DummyCTkComponent
ctk_module.CTkOptionMenu = DummyCTkComponent
ctk_module.CTkTabview = DummyCTkComponent
ctk_module.CTkScrollableFrame = DummyCTkComponent
ctk_module.CTkToplevel = DummyCTkComponent
ctk_module.set_appearance_mode = lambda mode: None
ctk_module.set_default_color_theme = lambda theme: None
ctk_module.set_widget_scaling = lambda scale: None
ctk_module.set_window_scaling = lambda scale: None

sys.modules["customtkinter"] = ctk_module

mock_tk = mock.MagicMock()
mock_root = mock.MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root
sys.modules["tkinter"] = mock_tk
sys.modules["darkdetect"] = mock.MagicMock()

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos_temp.sqlite")


class TestModuloCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = TEST_DB_PATH

    @classmethod
    def tearDownClass(cls):
        mc.CAT_DB_PATH = cls.orig_db_path
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        mc.cat_init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_cat_get_material_por_nombre_existente(self):
        datos_input = {
            "nombre": "SUELA DE HULE",
            "tipo_material": "DIRECTO",
            "unidad_default": "PAR",
            "departamento": "MONTADO",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ"
        }
        ok, _reg_id = mc.cat_guardar("materiales", datos_input)
        self.assertTrue(ok)

        res = mc.cat_get_material_por_nombre("SUELA DE HULE")
        self.assertEqual(res.get("nombre"), "SUELA DE HULE")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")
        self.assertEqual(res.get("unidad_default"), "PAR")
        self.assertEqual(res.get("departamento"), "MONTADO")

    def test_cat_get_material_por_nombre_case_insensitive_and_whitespace(self):
        datos_input = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM"
        }
        ok, _ = mc.cat_guardar("materiales", datos_input)
        self.assertTrue(ok)

        res = mc.cat_get_material_por_nombre("  cuero vacuno  ")
        self.assertEqual(res.get("nombre"), "CUERO VACUNO")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")

    def test_cat_get_material_por_nombre_inexistente(self):
        res = mc.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
        self.assertEqual(res, {})

    def test_cat_get_material_por_nombre_empty_input(self):
        self.assertEqual(mc.cat_get_material_por_nombre(""), {})
        self.assertEqual(mc.cat_get_material_por_nombre("   "), {})


if __name__ == "__main__":
    unittest.main()
