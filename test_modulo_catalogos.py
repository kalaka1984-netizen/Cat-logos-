"""
Unit tests for modulo_catalogos performance optimizations and database functions.
"""

import os
import sqlite3
import sys
import unittest
from unittest.mock import MagicMock


# Setup mock for customtkinter and tkinter if needed before import
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
    def winfo_children(self):
        return []
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def after(self, ms, func=None, *args):
        return 1
    def after_cancel(self, timer_id):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkTextbox = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkRadioButton = DummyWidget
mock_ctk.CTkToplevel = DummyWidget

sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos

TEST_DB_PATH = "test_catalogos_temp.sqlite"

class TestModuloCatalogosOptimizations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH

    @classmethod
    def tearDownClass(cls):
        modulo_catalogos.CAT_DB_PATH = cls.orig_db_path
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_cat_get_material_por_nombre(self):
        """Verify direct indexed SELECT query in cat_get_material_por_nombre."""
        mat_data = {
            "nombre": "CUERO VACUNO 1.2MM",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ"
        }
        ok, _res_id = modulo_catalogos.cat_guardar("materiales", mat_data)
        self.assertTrue(ok)

        # Exact match lookup
        res = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno 1.2mm")
        self.assertEqual(res.get("nombre"), "CUERO VACUNO 1.2MM")
        self.assertEqual(res.get("unidad_default"), "DM")

        # Non-existent lookup
        empty_res = modulo_catalogos.cat_get_material_por_nombre("PIEL INEXISTENTE")
        self.assertEqual(empty_res, {})

        # Empty lookup
        empty_arg = modulo_catalogos.cat_get_material_por_nombre("")
        self.assertEqual(empty_arg, {})

    def test_ic_listar_estilos_preaggregation(self):
        """Verify SQL LEFT JOIN pre-aggregates n_frac and suma_frac correctly."""
        # Create style
        ok, est_id = modulo_catalogos.ic_guardar_estilo("ESTILO_ALPHA", "CORTE", 120.0)
        self.assertTrue(ok)

        # Add 3 fractions totaling 120.0
        modulo_catalogos.ic_guardar_fraccion(est_id, "CORTE PIEL", 50.0, 1)
        modulo_catalogos.ic_guardar_fraccion(est_id, "CORTE FORRO", 40.0, 2)
        modulo_catalogos.ic_guardar_fraccion(est_id, "REBAJADO", 30.0, 3)

        # Create style with no fractions
        ok2, _est_id2 = modulo_catalogos.ic_guardar_estilo("ESTILO_BETA", "PESPUNTE", 80.0)
        self.assertTrue(ok2)

        # List all styles
        estilos_all = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(estilos_all), 2)

        alpha = next(e for e in estilos_all if e["estilo"] == "ESTILO_ALPHA")
        self.assertEqual(alpha["n_frac"], 3)
        self.assertAlmostEqual(alpha["suma_frac"], 120.0)

        beta = next(e for e in estilos_all if e["estilo"] == "ESTILO_BETA")
        self.assertEqual(beta["n_frac"], 0)
        self.assertAlmostEqual(beta["suma_frac"], 0.0)

        # Filter by department
        estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
        self.assertEqual(len(estilos_corte), 1)
        self.assertEqual(estilos_corte[0]["estilo"], "ESTILO_ALPHA")

    def test_ic_index_exists(self):
        """Verify idx_ic_estilos_depto index is created in ic_init_db."""
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_ic_estilos_depto'")
        row = cur.fetchone()
        con.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "idx_ic_estilos_depto")

if __name__ == "__main__":
    unittest.main()
