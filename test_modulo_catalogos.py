# -*- coding: utf-8 -*-
"""
Tests and benchmarks for modulo_catalogos.py.
"""
import os
import sys
import unittest
import sqlite3
import time
from unittest.mock import MagicMock

# Inject dummy customtkinter and tkinter modules to avoid GUI initialization issues during headless test runs
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def winfo_toplevel(self):
        return self
    def destroy(self):
        pass
    def yview(self, *args, **kwargs):
        pass
    def yview_scroll(self, *args, **kwargs):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkTextbox = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkScrollbar = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkToplevel = DummyWidget
mock_ctk.CTk = DummyWidget

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc

# Set temporary database path for testing
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos_temp.sqlite")
mc.CAT_DB_PATH = TEST_DB_PATH


class TestModuloCatalogos(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_ic_listar_estilos_pre_aggregation(self):
        """Verify that ic_listar_estilos accurately aggregates fraction counts and price totals."""
        ok, est_id1 = mc.ic_guardar_estilo("ESTILO_A", "CORTE", 100.0, "Notas A")
        self.assertTrue(ok)
        ok, est_id2 = mc.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 50.0, "Notas B")
        self.assertTrue(ok)

        # Add 3 fractions to ESTILO_A (total 45.0)
        mc.ic_guardar_fraccion(est_id1, "Frac 1", 10.0, 1)
        mc.ic_guardar_fraccion(est_id1, "Frac 2", 15.0, 2)
        mc.ic_guardar_fraccion(est_id1, "Frac 3", 20.0, 3)

        estilos = mc.ic_listar_estilos("", "TODOS")
        self.assertEqual(len(estilos), 2)

        est_a = next(e for e in estilos if e["estilo"] == "ESTILO_A")
        est_b = next(e for e in estilos if e["estilo"] == "ESTILO_B")

        self.assertEqual(est_a["n_frac"], 3)
        self.assertAlmostEqual(est_a["suma_frac"], 45.0)

        self.assertEqual(est_b["n_frac"], 0)
        self.assertAlmostEqual(est_b["suma_frac"], 0.0)

    def test_ic_listar_estilos_department_filter(self):
        """Verify department filtering in ic_listar_estilos."""
        mc.ic_guardar_estilo("ESTILO_1", "CORTE", 10.0)
        mc.ic_guardar_estilo("ESTILO_2", "PESPUNTE", 20.0)

        corte_estilos = mc.ic_listar_estilos("", "CORTE")
        self.assertEqual(len(corte_estilos), 1)
        self.assertEqual(corte_estilos[0]["estilo"], "ESTILO_1")

    def test_ic_listar_estilos_performance_benchmark(self):
        """Benchmark listing 200 styles with pre-aggregated JOIN vs N+1 queries."""
        # Populate 200 styles with 5 fractions each
        for i in range(200):
            ok, est_id = mc.ic_guardar_estilo(f"PERF_EST_{i}", "PESPUNTE", 25.0)
            for f in range(5):
                mc.ic_guardar_fraccion(est_id, f"Frac_{f}", 5.0, f)

        # Measure optimized pre-aggregated call
        t0 = time.perf_counter()
        filas = mc.ic_listar_estilos("", "TODOS")
        for row in filas:
            n_frac = row["n_frac"]
            suma_frac = row["suma_frac"]
        t1 = time.perf_counter()
        optimized_time = t1 - t0

        self.assertEqual(len(filas), 200)
        print(f"\n[BENCHMARK] Optimized ic_listar_estilos (200 records): {optimized_time:.6f} seconds")


if __name__ == "__main__":
    unittest.main()
