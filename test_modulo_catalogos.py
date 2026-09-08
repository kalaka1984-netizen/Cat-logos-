import os
import sys
import unittest
from unittest.mock import MagicMock

# Inject dummy customtkinter/tkinter modules if necessary for headless environment
try:
    import customtkinter  # noqa: F401
except ImportError:
    mock_ctk = MagicMock()
    sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = "test_catalogos_temp.sqlite"
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        # Override CAT_DB_PATH in modulo_catalogos for test isolation
        modulo_catalogos.CAT_DB_PATH = cls.test_db_path
        modulo_catalogos.cat_init_db()

        # Seed sample materials
        cls.mat_1_data = {
            "nombre": "CUERO VACUNO BLACK",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "notas": "TEST NOTE"
        }
        cls.mat_2_data = {
            "nombre": "HILO NYLON #40",
            "tipo_material": "INDIRECTO",
            "es_principal": "NO",
            "unidad_default": "m",
            "departamento": "PESPUNTE",
            "visible_monitor": "NO",
            "notas": "TEST NOTE 2"
        }
        modulo_catalogos.cat_guardar("materiales", cls.mat_1_data)
        modulo_catalogos.cat_guardar("materiales", cls.mat_2_data)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def test_get_material_por_nombre_exact_match(self):
        res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO BLACK")
        self.assertIsNotNone(res)
        self.assertEqual(res.get("nombre"), "CUERO VACUNO BLACK")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")
        self.assertEqual(res.get("unidad_default"), "DM")  # Note cat_guardar forces upper

    def test_get_material_por_nombre_case_insensitive_and_whitespace(self):
        res = modulo_catalogos.cat_get_material_por_nombre("  cuero vacuno black  ")
        self.assertIsNotNone(res)
        self.assertEqual(res.get("nombre"), "CUERO VACUNO BLACK")

    def test_get_material_por_nombre_non_existent(self):
        res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_INEXISTENTE")
        self.assertEqual(res, {})

    def test_get_material_por_nombre_empty_string(self):
        res = modulo_catalogos.cat_get_material_por_nombre("   ")
        self.assertEqual(res, {})

if __name__ == "__main__":
    unittest.main()
