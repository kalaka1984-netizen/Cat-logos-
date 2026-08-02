# ruff: noqa: E402, F401
import sys
from unittest import mock

class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080

class DummyCTkFrame(DummyWidget):
    pass

# Mock tkinter and customtkinter to prevent headless environment issues
mock_ctk = mock.MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
sys.modules['customtkinter'] = mock_ctk

mock_tk = mock.MagicMock()
mock_tk.Tk = DummyWidget
sys.modules['tkinter'] = mock_tk

import unittest
import os
import sqlite3
import json
import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        # Use a separate test database path to avoid polluting the development DB
        self.original_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = "test_catalogos_db.sqlite"
        if os.path.exists(modulo_catalogos.CAT_DB_PATH):
            os.remove(modulo_catalogos.CAT_DB_PATH)
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        if os.path.exists(modulo_catalogos.CAT_DB_PATH):
            os.remove(modulo_catalogos.CAT_DB_PATH)
        modulo_catalogos.CAT_DB_PATH = self.original_db_path

    def test_cat_get_material_por_nombre(self):
        # Assertions must expect uppercase output per constraints
        material_data = {
            "nombre": "hilo rojo",
            "unidad_default": "dm",
            "tipo_material": "DIRECTO",
            "departamento": "PESPUNTE"
        }
        ok, reg_id = modulo_catalogos.cat_guardar("materiales", material_data)
        self.assertTrue(ok)

        # Retrieve using direct SELECT optimized function
        result = modulo_catalogos.cat_get_material_por_nombre("hilo rojo")
        self.assertEqual(result.get("nombre"), "HILO ROJO")
        self.assertEqual(result.get("unidad_default"), "DM")

        # Non-existent material
        result_none = modulo_catalogos.cat_get_material_por_nombre("inexistente")
        self.assertEqual(result_none, {})

    def test_ic_listar_estilos_pre_aggregation(self):
        # Create an style
        ok, estilo_id = modulo_catalogos.ic_guardar_estilo("EST-100", "CORTE", 200.0)
        self.assertTrue(ok)

        # Add fractions
        ok1, msg1 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "Corte Inicial", 80.0, 1)
        ok2, msg2 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "Corte Secundario", 120.0, 2)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # Call the optimized list function which pre-aggregates
        estilos = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["estilo"], "EST-100")
        self.assertEqual(estilos[0]["departamento"], "CORTE")
        self.assertEqual(estilos[0]["precio_par"], 200.0)
        self.assertEqual(estilos[0]["n_frac"], 2)
        self.assertEqual(estilos[0]["suma_frac"], 200.0)

        # Query with search criteria and specific department
        estilos_search = modulo_catalogos.ic_listar_estilos("EST-100", "CORTE")
        self.assertEqual(len(estilos_search), 1)
        self.assertEqual(estilos_search[0]["n_frac"], 2)

        # Bypassing LIKE checks for empty queries (verified via query execution)
        estilos_empty = modulo_catalogos.ic_listar_estilos("", "CORTE")
        self.assertEqual(len(estilos_empty), 1)

    def test_idx_ic_estilos_depto_exists(self):
        # Check that the index idx_ic_estilos_depto is created on department column
        con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA index_list(ic_estilos)")
        indexes = cur.fetchall()
        con.close()

        index_names = [idx[1] for idx in indexes]
        self.assertIn("idx_ic_estilos_depto", index_names)

if __name__ == "__main__":
    unittest.main()
