"""
Tests for modulo_catalogos.py performance optimizations and database queries.
Mocks GUI dependencies (tkinter, customtkinter) for headless execution.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock


# Dummy mock classes for customtkinter to prevent metaclass conflict
class DummyFrame:
    def __init__(self, *args, **kwargs): pass
    def pack(self, *args, **kwargs): pass
    def place(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass
    def columnconfigure(self, *args, **kwargs): pass
    def winfo_children(self): return []
    def after(self, ms, func=None): return "after_id"
    def after_cancel(self, id): pass


class DummyToplevel:
    def __init__(self, *args, **kwargs): pass
    def geometry(self, *args, **kwargs): pass
    def title(self, *args, **kwargs): pass
    def resizable(self, *args, **kwargs): pass
    def grab_set(self, *args, **kwargs): pass
    def grab_release(self, *args, **kwargs): pass
    def destroy(self, *args, **kwargs): pass


mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkToplevel = DummyToplevel
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc  # noqa: E402


class TestModuloCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)
        self.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = self.db_path
        mc.ic_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_ic_listar_estilos_pre_aggregation(self):
        """Verify ic_listar_estilos aggregates n_frac and suma_frac with SQL JOIN."""
        ok1, e_id1 = mc.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 100.0)
        self.assertTrue(ok1)

        ok2, _ = mc.ic_guardar_estilo("ESTILO_B", "CORTE", 50.0)
        self.assertTrue(ok2)

        # Add 3 fractions to ESTILO_A
        mc.ic_guardar_fraccion(e_id1, "FRAC 1", 30.0, 1)
        mc.ic_guardar_fraccion(e_id1, "FRAC 2", 20.0, 2)
        mc.ic_guardar_fraccion(e_id1, "FRAC 3", 50.0, 3)

        estilos = mc.ic_listar_estilos()
        self.assertEqual(len(estilos), 2)

        est_a = next(e for e in estilos if e["estilo"] == "ESTILO_A")
        est_b = next(e for e in estilos if e["estilo"] == "ESTILO_B")

        # ESTILO_A pre-aggregated check
        self.assertEqual(est_a["n_frac"], 3)
        self.assertAlmostEqual(est_a["suma_frac"], 100.0)

        # ESTILO_B (no fractions) check
        self.assertEqual(est_b["n_frac"], 0)
        self.assertAlmostEqual(est_b["suma_frac"], 0.0)

    def test_ic_listar_estilos_filtering(self):
        """Verify department filtering in ic_listar_estilos."""
        mc.ic_guardar_estilo("ESTILO_PESP", "PESPUNTE", 80.0)
        mc.ic_guardar_estilo("ESTILO_CORTE", "CORTE", 60.0)

        est_pesp = mc.ic_listar_estilos(departamento="PESPUNTE")
        self.assertEqual(len(est_pesp), 1)
        self.assertEqual(est_pesp[0]["estilo"], "ESTILO_PESP")

        est_corte = mc.ic_listar_estilos(departamento="CORTE")
        self.assertEqual(len(est_corte), 1)
        self.assertEqual(est_corte[0]["estilo"], "ESTILO_CORTE")

if __name__ == "__main__":
    unittest.main()
