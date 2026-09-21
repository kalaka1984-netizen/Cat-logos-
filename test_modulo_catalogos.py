import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock


# ── Mock tkinter and customtkinter for headless testing environment ──────────
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def place(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []

    def configure(self, *args, **kwargs):
        pass

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080


mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTk = DummyWidget
mock_ctk.set_appearance_mode = lambda x: None
mock_ctk.set_default_color_theme = lambda x: None

sys.modules["customtkinter"] = mock_ctk
sys.modules["darkdetect"] = MagicMock()

# Now import module under test
import modulo_catalogos  # noqa: E402


class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.tmp_dir.name, "test_catalogos.sqlite")
        self.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.test_db_path
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()

    def test_cat_init_db_indexes(self):
        """Verify that composite indexes idx_{tabla}_estatus_nombre are created."""
        import sqlite3

        con = sqlite3.connect(self.test_db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [r[0] for r in cur.fetchall()]
        con.close()

        for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
            self.assertIn(f"idx_{tabla}_nombre", indexes)
            self.assertIn(f"idx_{tabla}_estatus_nombre", indexes)

    def test_cat_guardar_and_get_material_por_nombre(self):
        """Test material saving and direct indexed lookup."""
        mat_data = {
            "nombre": "CUERO VACUNO NEGRO",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ",
        }
        ok, reg_id = modulo_catalogos.cat_guardar("materiales", mat_data)
        self.assertTrue(ok)
        self.assertIsInstance(reg_id, int)

        # Retrieve material by exact name (case-insensitive search)
        res = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno negro")
        self.assertEqual(res.get("nombre"), "CUERO VACUNO NEGRO")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")

        # Test non-existent material lookup returns empty dict
        res_empty = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
        self.assertEqual(res_empty, {})

    def test_cat_buscar_empty_string(self):
        """Test cat_buscar with empty text query bypasses LIKE evaluation."""
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT 1", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT 2", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        self.assertEqual(len(activos), 1)
        self.assertEqual(activos[0][1], "MAT 1")

        todos = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
        self.assertEqual(len(todos), 2)

    def test_cat_get_nombres(self):
        """Test index-only names retrieval for materials, workers, suppliers, and clients."""
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROVEEDOR X", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE Y", "estatus": "ACTIVO"})

        self.assertEqual(modulo_catalogos.cat_get_nombres_materiales(solo_activos=True), ["MAT A"])
        self.assertEqual(modulo_catalogos.cat_get_nombres_materiales(solo_activos=False), ["MAT A", "MAT B"])
        self.assertEqual(modulo_catalogos.cat_get_nombres_trabajadores(), ["JUAN PEREZ"])
        self.assertEqual(modulo_catalogos.cat_get_nombres_proveedores(), ["PROVEEDOR X"])
        self.assertEqual(modulo_catalogos.cat_get_nombres_clientes(), ["CLIENTE Y"])


if __name__ == "__main__":
    unittest.main()
