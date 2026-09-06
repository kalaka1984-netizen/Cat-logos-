import os
import sys
import tempfile
import unittest


# Create dummy base classes for customtkinter to avoid metaclass conflicts
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def after(self, *args, **kwargs):
        pass


class DummyCTkModule:
    CTkFrame = DummyCTkFrame
    CTkLabel = DummyCTkFrame
    CTkButton = DummyCTkFrame
    CTkEntry = DummyCTkFrame
    CTk = DummyCTkFrame
    CTkFont = DummyCTkFrame
    CTkTabview = DummyCTkFrame
    CTkOptionMenu = DummyCTkFrame
    CTkComboBox = DummyCTkFrame
    CTkScrollableFrame = DummyCTkFrame
    CTkCheckBox = DummyCTkFrame
    CTkSegmentedButton = DummyCTkFrame
    CTkProgressBar = DummyCTkFrame
    CTkTextbox = DummyCTkFrame
    CTkCanvas = DummyCTkFrame

    @staticmethod
    def set_appearance_mode(*args, **kwargs):
        pass

    @staticmethod
    def set_default_color_theme(*args, **kwargs):
        pass

    def __getattr__(self, item):
        return DummyCTkFrame


if "customtkinter" not in sys.modules:
    sys.modules["customtkinter"] = DummyCTkModule()

if "darkdetect" not in sys.modules:
    import types

    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = lambda: "Dark"
    sys.modules["darkdetect"] = mock_dd

import modulo_catalogos


class TestCatGetMaterialPorNombre(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            self.temp_db_path = f.name
        self.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.temp_db_path
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_cat_get_material_por_nombre_exists(self):
        datos = {
            "nombre": "PIEL VACUNA",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
        }
        ok, _ = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        mat = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNA")
        self.assertEqual(mat.get("nombre"), "PIEL VACUNA")
        self.assertEqual(mat.get("tipo_material"), "DIRECTO")
        self.assertEqual(mat.get("unidad_default"), "DM")

    def test_cat_get_material_por_nombre_case_insensitive_and_whitespace(self):
        datos = {
            "nombre": "SUELA HULE",
            "tipo_material": "DIRECTO",
            "unidad_default": "PAR",
        }
        ok, _ = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        mat = modulo_catalogos.cat_get_material_por_nombre("   suela hule  ")
        self.assertEqual(mat.get("nombre"), "SUELA HULE")
        self.assertEqual(mat.get("unidad_default"), "PAR")

    def test_cat_get_material_por_nombre_not_found(self):
        mat = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_INEXISTENTE")
        self.assertEqual(mat, {})

    def test_cat_get_material_por_nombre_empty(self):
        mat = modulo_catalogos.cat_get_material_por_nombre("")
        self.assertEqual(mat, {})


if __name__ == "__main__":
    unittest.main()
