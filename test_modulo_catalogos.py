import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock


# Dummy CTk / Tkinter mocks for headless execution before importing modulo_catalogos
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def place(self, *args, **kwargs):
        pass

    def destroy(self):
        pass

    def after(self, *args, **kwargs):
        return "timer_id"

    def after_cancel(self, *args, **kwargs):
        pass

    def bind(self, *args, **kwargs):
        pass

    def columnconfigure(self, *args, **kwargs):
        pass

    def configure(self, *args, **kwargs):
        pass

    def config(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        return ""

    def set(self, *args, **kwargs):
        pass

    def grab_release(self):
        pass

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080


class DummyCTk(DummyWidget):
    pass


class DummyCTkFrame(DummyWidget):
    pass


class DummyCTkLabel(DummyWidget):
    pass


class DummyCTkButton(DummyWidget):
    pass


class DummyCTkEntry(DummyWidget):
    pass


# Mock customtkinter in sys.modules if not available or headless
ctk_mock = MagicMock()
ctk_mock.CTk = DummyCTk
ctk_mock.CTkFrame = DummyCTkFrame
ctk_mock.CTkLabel = DummyCTkLabel
ctk_mock.CTkButton = DummyCTkButton
ctk_mock.CTkEntry = DummyCTkEntry

sys.modules["customtkinter"] = ctk_mock

import modulo_catalogos


class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            self.tmp_db_path = f.name
        self.old_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.tmp_db_path
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.old_db_path
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    def test_ic_init_db_creates_indices(self):
        """Verifica que ic_init_db crea los índices esperados, incluyendo idx_ic_estilos_depto."""
        con = modulo_catalogos.sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = [row[0] for row in cur.fetchall()]
        con.close()

        self.assertIn("idx_ic_estilo", indices)
        self.assertIn("idx_ic_estilos_depto", indices)
        self.assertIn("idx_ic_frac_estilo", indices)

    def test_ic_listar_estilos_pre_aggregation(self):
        """Verifies ic_listar_estilos computes n_frac and suma_frac accurately via JOIN."""
        # Insert style 1 with 2 fractions
        res1, id1 = modulo_catalogos.ic_guardar_estilo("BOTAS 101", "CORTE", 100.0, "ESTILO DE TRABAJO")
        self.assertTrue(res1)
        modulo_catalogos.ic_guardar_fraccion(id1, "CORTE CAPELLADA", 30.0, orden=1)
        modulo_catalogos.ic_guardar_fraccion(id1, "CORTE CHINELA", 70.0, orden=2)

        # Insert style 2 with 0 fractions
        res2, id2 = modulo_catalogos.ic_guardar_estilo("ZAPATO 202", "PESUNTE", 50.0, "CASUAL")
        self.assertTrue(res2)

        # List all styles
        estilos = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(estilos), 2)

        e1 = next(e for e in estilos if e["id"] == id1)
        self.assertEqual(e1["n_frac"], 2)
        self.assertAlmostEqual(e1["suma_frac"], 100.0)

        e2 = next(e for e in estilos if e["id"] == id2)
        self.assertEqual(e2["n_frac"], 0)
        self.assertAlmostEqual(e2["suma_frac"], 0.0)

    def test_ic_listar_estilos_filtering(self):
        """Verifies filtering by department and search text."""
        modulo_catalogos.ic_guardar_estilo("MODELO A", "CORTE", 10.0)
        modulo_catalogos.ic_guardar_estilo("MODELO B", "PESUNTE", 15.0)

        corte_estilos = modulo_catalogos.ic_listar_estilos(departamento="CORTE")
        self.assertEqual(len(corte_estilos), 1)
        self.assertEqual(corte_estilos[0]["estilo"], "MODELO A")

        search_estilos = modulo_catalogos.ic_listar_estilos(buscar="MODELO B")
        self.assertEqual(len(search_estilos), 1)
        self.assertEqual(search_estilos[0]["estilo"], "MODELO B")


if __name__ == "__main__":
    unittest.main()
