import os
import sqlite3
import sys
import time
import unittest
from unittest.mock import MagicMock


# Ensure GUI components do not fail in headless environment
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def destroy(self):
        pass

    def after(self, *args, **kwargs):
        pass


# Mock customtkinter and tkinter components if needed
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

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos_temp.sqlite")


class TestModuloCatalogosOptimizations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = TEST_DB_PATH
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        mc.ic_init_db()

    @classmethod
    def tearDownClass(cls):
        mc.CAT_DB_PATH = cls.orig_db_path
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        # Clear tables before each test
        con = sqlite3.connect(TEST_DB_PATH)
        con.execute("DELETE FROM ic_fracciones")
        con.execute("DELETE FROM ic_estilos")
        con.commit()
        con.close()

    def test_ic_listar_estilos_pre_aggregation(self):
        """Verify ic_listar_estilos accurately aggregates n_frac and suma_frac."""
        ok1, id1 = mc.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 100.0, "Nota A")
        self.assertTrue(ok1)
        ok2, id2 = mc.ic_guardar_estilo("ESTILO_B", "CORTE", 50.0, "Nota B")
        self.assertTrue(ok2)

        # Add fractions to ESTILO_A
        mc.ic_guardar_fraccion(id1, "FRAC_1", 30.0, orden=1)
        mc.ic_guardar_fraccion(id1, "FRAC_2", 70.0, orden=2)

        styles = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(styles), 2)

        # Map by id
        styles_map = {s["id"]: s for s in styles}

        # Check ESTILO_A
        style_a = styles_map[id1]
        self.assertEqual(style_a["n_frac"], 2)
        self.assertAlmostEqual(style_a["suma_frac"], 100.0)

        # Check ESTILO_B (no fractions)
        style_b = styles_map[id2]
        self.assertEqual(style_b["n_frac"], 0)
        self.assertAlmostEqual(style_b["suma_frac"], 0.0)

    def test_ic_listar_estilos_filtering(self):
        """Verify department and search filtering in ic_listar_estilos."""
        mc.ic_guardar_estilo("BOTIN_ROJO", "PESPUNTE", 120.0)
        mc.ic_guardar_estilo("ZAPATO_NEGRO", "CORTE", 90.0)
        mc.ic_guardar_estilo("BOTIN_NEGRO", "PESPUNTE", 110.0)

        # Department filter
        pespunte_styles = mc.ic_listar_estilos(buscar="", departamento="PESPUNTE")
        self.assertEqual(len(pespunte_styles), 2)
        self.assertTrue(all(s["departamento"] == "PESPUNTE" for s in pespunte_styles))

        # Search filter
        botin_styles = mc.ic_listar_estilos(buscar="BOTIN", departamento="TODOS")
        self.assertEqual(len(botin_styles), 2)
        self.assertTrue(all("BOTIN" in s["estilo"] for s in botin_styles))

    def test_ic_listar_estilos_performance_benchmark(self):
        """Benchmark performance improvement against simulated N+1 queries."""
        # Insert 100 styles with 3 fractions each
        for i in range(100):
            _ok, est_id = mc.ic_guardar_estilo(f"ESTILO_{i:03d}", "PESPUNTE", 30.0)
            for j in range(3):
                mc.ic_guardar_fraccion(est_id, f"OP_{j}", 10.0, orden=j)

        # Single optimized query
        t0 = time.perf_counter()
        styles = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        for s in styles:
            _n_frac = s["n_frac"]
            _suma_frac = s["suma_frac"]
        t_opt = time.perf_counter() - t0

        # Simulated N+1 approach
        t0 = time.perf_counter()
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, estilo, departamento, precio_par, notas, fecha_alta FROM ic_estilos")
        rows = cur.fetchall()
        for r in rows:
            fracs = mc.ic_listar_fracciones(r[0])
            _n_frac = len(fracs)
            _suma_frac = sum(fr["precio"] for fr in fracs)
        con.close()
        t_nplus1 = time.perf_counter() - t0

        self.assertEqual(len(styles), 100)
        print(f"\n[Benchmark] N+1 Query Time: {t_nplus1:.5f}s vs Single JOIN Query Time: {t_opt:.5f}s")
        self.assertLess(t_opt, t_nplus1)


if __name__ == "__main__":
    unittest.main()
