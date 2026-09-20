import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# Dummy GUI class to avoid tkinter/customtkinter window popups in headless tests
class DummyWidget:
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
    def winfo_children(self):
        return []
    def after(self, ms, func=None, *args):
        return "after_id"
    def after_cancel(self, id):
        pass

# Setup mock customtkinter
mock_ctk = MagicMock()
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkTextbox = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkScrollbar = DummyWidget

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos
from modulo_catalogos import (
    cat_get_material_por_nombre,
    cat_guardar,
    cat_init_db,
    cat_precarga_material,
)

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)
        modulo_catalogos.CAT_DB_PATH = self.db_path
        cat_init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_cat_guardar_y_get_material_por_nombre(self):
        mat_data = {
            "nombre": "PIEL VACUNO NEGRA",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "notas": "Piel de prueba"
        }
        ok, res_id = cat_guardar("materiales", mat_data)
        self.assertTrue(ok)
        self.assertIsInstance(res_id, int)

        # Retrieve material by exact name
        fetched = cat_get_material_por_nombre("PIEL VACUNO NEGRA")
        self.assertEqual(fetched.get("nombre"), "PIEL VACUNO NEGRA")
        self.assertEqual(fetched.get("tipo_material"), "DIRECTO")
        self.assertEqual(fetched.get("unidad_default"), "DM")

        # Non-existent material should return empty dict
        empty_res = cat_get_material_por_nombre("MATERIAL INEXISTENTE")
        self.assertEqual(empty_res, {})

    def test_cat_precarga_material(self):
        mat_data = {
            "nombre": "SUELA CAUCHO",
            "tipo_material": "INDIRECTO",
            "es_principal": "NO",
            "unidad_default": "PAR",
            "departamento": "MONTADO",
            "visible_monitor": "NO"
        }
        cat_guardar("materiales", mat_data)

        precarga = cat_precarga_material("suela caucho")
        self.assertEqual(precarga.get("tipo_ft"), "IND")
        self.assertEqual(precarga.get("unidad"), "PAR")
        self.assertEqual(precarga.get("departamento"), "MONTADO")
        self.assertFalse(precarga.get("monitor"))
        self.assertFalse(precarga.get("principal"))

if __name__ == "__main__":
    unittest.main()
