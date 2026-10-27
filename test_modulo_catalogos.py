"""Unit test suite for modulo_catalogos.py optimizations and database queries."""

import os
import sqlite3
import sys
import tempfile
import time
import types


# Construct a dummy customtkinter module to prevent metaclass conflicts with MagicMock
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkLabel:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkButton:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkEntry:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkComboBox:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkTextbox:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkScrollableFrame(DummyCTkFrame):
    pass


class DummyCTkSegmentedButton:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkRadioButton:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkScrollbar:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkToplevel:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTk:
    def __init__(self, *args, **kwargs):
        pass


mock_ctk = types.ModuleType("customtkinter")
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkLabel
mock_ctk.CTkButton = DummyCTkButton
mock_ctk.CTkEntry = DummyCTkEntry
mock_ctk.CTkComboBox = DummyCTkComboBox
mock_ctk.CTkTextbox = DummyCTkTextbox
mock_ctk.CTkScrollableFrame = DummyCTkScrollableFrame
mock_ctk.CTkSegmentedButton = DummyCTkSegmentedButton
mock_ctk.CTkRadioButton = DummyCTkRadioButton
mock_ctk.CTkScrollbar = DummyCTkScrollbar
mock_ctk.CTkToplevel = DummyCTkToplevel
mock_ctk.CTk = DummyCTk
mock_ctk.set_appearance_mode = lambda mode: None
mock_ctk.set_default_color_theme = lambda theme: None
mock_ctk.set_widget_scaling = lambda scale: None
mock_ctk.set_window_scaling = lambda scale: None

sys.modules["customtkinter"] = mock_ctk

import unittest  # noqa: E402
import modulo_catalogos  # noqa: E402


class TestModuloCatalogosIC(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)
        self.old_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.old_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_ic_init_db_indexes(self):
        """Verify indexes on ic_estilos exist."""
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("PRAGMA index_list('ic_estilos')")
        indexes = [row[1] for row in cur.fetchall()]
        con.close()

        self.assertIn("idx_ic_estilo", indexes)
        self.assertIn("idx_ic_estilos_depto", indexes)

    def test_ic_listar_estilos_pre_aggregation(self):
        """Test that ic_listar_estilos pre-aggregates fraction count and total price in one query."""
        # 1. Style with no fractions
        ok1, est1_id = modulo_catalogos.ic_guardar_estilo("ESTILO_A", "CORTE", 120.0)
        self.assertTrue(ok1)

        # 2. Style with 1 fraction
        ok2, est2_id = modulo_catalogos.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 150.0)
        self.assertTrue(ok2)
        modulo_catalogos.ic_guardar_fraccion(est2_id, "COSTURA LATERAL", 150.0, 1)

        # 3. Style with 3 fractions
        ok3, est3_id = modulo_catalogos.ic_guardar_estilo("ESTILO_C", "MONTADO", 200.0)
        self.assertTrue(ok3)
        modulo_catalogos.ic_guardar_fraccion(est3_id, "ARMADO", 80.0, 1)
        modulo_catalogos.ic_guardar_fraccion(est3_id, "TALONERA", 70.0, 2)
        modulo_catalogos.ic_guardar_fraccion(est3_id, "CONTRAFUERTE", 50.0, 3)

        # Fetch all
        estilos = modulo_catalogos.ic_listar_estilos("", "TODOS")
        self.assertEqual(len(estilos), 3)

        # Map by id
        e_map = {e["id"]: e for e in estilos}

        # Check ESTILO_A
        self.assertEqual(e_map[est1_id]["n_frac"], 0)
        self.assertEqual(e_map[est1_id]["suma_frac"], 0.0)

        # Check ESTILO_B
        self.assertEqual(e_map[est2_id]["n_frac"], 1)
        self.assertEqual(e_map[est2_id]["suma_frac"], 150.0)

        # Check ESTILO_C
        self.assertEqual(e_map[est3_id]["n_frac"], 3)
        self.assertEqual(e_map[est3_id]["suma_frac"], 200.0)

    def test_ic_listar_estilos_department_filter(self):
        """Test filtering by department using the new index and pre-aggregation."""
        modulo_catalogos.ic_guardar_estilo("EST_CORTE_1", "CORTE", 100.0)
        modulo_catalogos.ic_guardar_estilo("EST_PESP_1", "PESPUNTE", 110.0)
        modulo_catalogos.ic_guardar_estilo("EST_PESP_2", "PESPUNTE", 120.0)

        corte_list = modulo_catalogos.ic_listar_estilos("", "CORTE")
        self.assertEqual(len(corte_list), 1)
        self.assertEqual(corte_list[0]["estilo"], "EST_CORTE_1")

        pesp_list = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
        self.assertEqual(len(pesp_list), 2)

    def test_ic_listar_estilos_search_filter(self):
        """Test searching by estilo name or notes."""
        modulo_catalogos.ic_guardar_estilo("BOTA_BOTIN", "CORTE", 100.0, "EDICION ESPECIAL")
        modulo_catalogos.ic_guardar_estilo("ZAPATO_TENIS", "CORTE", 110.0, "LINEA ESCOLAR")

        res_bota = modulo_catalogos.ic_listar_estilos("BOTIN", "TODOS")
        self.assertEqual(len(res_bota), 1)
        self.assertEqual(res_bota[0]["estilo"], "BOTA_BOTIN")

        res_escolar = modulo_catalogos.ic_listar_estilos("ESCOLAR", "TODOS")
        self.assertEqual(len(res_escolar), 1)
        self.assertEqual(res_escolar[0]["estilo"], "ZAPATO_TENIS")

    def test_performance_benchmark(self):
        """Benchmark 200 styles listing to verify execution time is fast (< 20ms)."""
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        for i in range(200):
            cur.execute(
                "INSERT INTO ic_estilos (estilo, departamento, precio_par, notas, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
                (f"ESTILO_{i:03d}", "PESPUNTE", 150.0, "", "2025-01-01", "2025-01-01")
            )
            est_id = cur.lastrowid
            for j in range(i % 5):
                cur.execute(
                    "INSERT INTO ic_fracciones (ic_estilo_id, nombre, precio, orden, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
                    (est_id, f"FRAC_{j}", 30.0, j, "2025-01-01", "2025-01-01")
                )
        con.commit()
        con.close()

        t0 = time.perf_counter()
        rows = modulo_catalogos.ic_listar_estilos("", "TODOS")
        t1 = time.perf_counter()

        elapsed_ms = (t1 - t0) * 1000
        self.assertEqual(len(rows), 200)
        self.assertLess(elapsed_ms, 20.0, f"Query took too long: {elapsed_ms:.2f} ms")


if __name__ == "__main__":
    unittest.main()
