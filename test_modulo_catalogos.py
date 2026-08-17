# -*- coding: utf-8 -*-
"""
Unit tests for modulo_catalogos.py performance optimizations and core DB logic.
Mocks GUI components (tkinter / customtkinter) to run cleanly in headless environments.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# ── Mock GUI components before importing modulo_catalogos ─────────────────────
mock_tk = MagicMock()
mock_ctk = MagicMock()

# Setup CTkFrame / CTkLabel dummy base classes for inheritance
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
    def bind(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def destroy(self):
        pass

mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkTextbox = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkScrollbar = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkRadioButton = DummyWidget
mock_ctk.CTkToplevel = DummyWidget
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()

mock_tk_inst = MagicMock()
mock_tk_inst.winfo_screenwidth.return_value = 1920
mock_tk_inst.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_inst

sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc


class TestModuloCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp_db.close()
        self.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = self.tmp_db.name
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.tmp_db.name):
            os.remove(self.tmp_db.name)

    def test_ic_listar_estilos_preaggregation(self):
        # Create style 1 with 2 fractions
        ok1, est1_id = mc.ic_guardar_estilo("EST_001", "PESPUNTE", 100.0, "Nota 1")
        self.assertTrue(ok1)
        mc.ic_guardar_fraccion(est1_id, "FRAC_A", 40.0, 1)
        mc.ic_guardar_fraccion(est1_id, "FRAC_B", 60.0, 2)

        # Create style 2 without fractions
        ok2, est2_id = mc.ic_guardar_estilo("EST_002", "CORTE", 50.0, "Nota 2")
        self.assertTrue(ok2)

        # List all styles
        estilos = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(estilos), 2)

        # Check pre-aggregated fields for style 1
        e1 = next(e for e in estilos if e["id"] == est1_id)
        self.assertEqual(e1["estilo"], "EST_001")
        self.assertEqual(e1["departamento"], "PESPUNTE")
        self.assertEqual(e1["precio_par"], 100.0)
        self.assertEqual(e1["n_frac"], 2)
        self.assertAlmostEqual(e1["suma_frac"], 100.0)

        # Check pre-aggregated fields for style 2
        e2 = next(e for e in estilos if e["id"] == est2_id)
        self.assertEqual(e2["estilo"], "EST_002")
        self.assertEqual(e2["departamento"], "CORTE")
        self.assertEqual(e2["precio_par"], 50.0)
        self.assertEqual(e2["n_frac"], 0)
        self.assertEqual(e2["suma_frac"], 0.0)

    def test_ic_listar_estilos_filtro_departamento(self):
        mc.ic_guardar_estilo("EST_CORTE", "CORTE", 30.0)
        mc.ic_guardar_estilo("EST_PESP", "PESPUNTE", 40.0)

        corte = mc.ic_listar_estilos(buscar="", departamento="CORTE")
        self.assertEqual(len(corte), 1)
        self.assertEqual(corte[0]["estilo"], "EST_CORTE")

        pesp = mc.ic_listar_estilos(buscar="", departamento="PESPUNTE")
        self.assertEqual(len(pesp), 1)
        self.assertEqual(pesp[0]["estilo"], "EST_PESP")


if __name__ == "__main__":
    unittest.main()
