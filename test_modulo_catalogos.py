# -*- coding: utf-8 -*-
import sys
import unittest
from unittest.mock import MagicMock

# Mock customtkinter before importing modulo_catalogos if running headless
if "customtkinter" not in sys.modules:
    mock_ctk = MagicMock()
    mock_ctk.CTkFrame = type("CTkFrame", (object,), {})
    mock_ctk.CTkLabel = type("CTkLabel", (object,), {})
    mock_ctk.CTkButton = type("CTkButton", (object,), {})
    sys.modules["customtkinter"] = mock_ctk

import os
import tempfile
import sqlite3
import modulo_catalogos as mc

class TestModuloCatalogosOptimized(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        mc.CAT_DB_PATH = self.db_path
        mc.ic_init_db()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_ic_listar_estilos_pre_aggregation(self):
        # Test inserting styles and fractions
        ok1, est_id1 = mc.ic_guardar_estilo("MODELO_A", "CORTE", 100.0)
        self.assertTrue(ok1)

        ok2, est_id2 = mc.ic_guardar_estilo("MODELO_B", "PESPUNTE", 150.0)
        self.assertTrue(ok2)

        # MODELO_A has 2 fractions totaling 45.0
        mc.ic_guardar_fraccion(est_id1, "FRAC_1", 20.0)
        mc.ic_guardar_fraccion(est_id1, "FRAC_2", 25.0)

        # MODELO_B has 0 fractions

        estilos = mc.ic_listar_estilos("", "TODOS")
        self.assertEqual(len(estilos), 2)

        # Find MODELO_A
        m_a = next(e for e in estilos if e["estilo"] == "MODELO_A")
        self.assertEqual(m_a["n_frac"], 2)
        self.assertEqual(m_a["suma_frac"], 45.0)

        # Find MODELO_B
        m_b = next(e for e in estilos if e["estilo"] == "MODELO_B")
        self.assertEqual(m_b["n_frac"], 0)
        self.assertEqual(m_b["suma_frac"], 0.0)

    def test_ic_listar_estilos_filtro_departamento(self):
        mc.ic_guardar_estilo("STYLE_CORTE", "CORTE", 100.0)
        mc.ic_guardar_estilo("STYLE_PESPUNTE", "PESPUNTE", 120.0)

        corte_list = mc.ic_listar_estilos("", "CORTE")
        self.assertEqual(len(corte_list), 1)
        self.assertEqual(corte_list[0]["estilo"], "STYLE_CORTE")

if __name__ == "__main__":
    unittest.main()
