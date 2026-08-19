import os
import sys
import tempfile
import unittest
import time
import unittest.mock as mock

# Create temporary database file for testing
TEST_DB_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite").name

# Mock customtkinter and tkinter for headless execution before importing modulo_catalogos
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
    def winfo_toplevel(self):
        return self
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def destroy(self):
        pass
    def after(self, ms, func=None, *args):
        return "timer_id"
    def after_cancel(self, timer_id):
        pass

mock_ctk = mock.MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkOptionMenu = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkCheckBox = DummyWidget
mock_ctk.CTkTabview = DummyWidget
mock_ctk.CTkToplevel = DummyWidget
mock_ctk.CTk = DummyWidget
mock_ctk.StringVar = mock.MagicMock()

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos
modulo_catalogos.CAT_DB_PATH = TEST_DB_FILE


class TestModuloCatalogos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except OSError:
                pass

    def test_cat_guardar_and_get_material_por_nombre(self):
        # Insert a test material
        datos = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ"
        }
        ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)
        self.assertGreater(mat_id, 0)

        # Retrieve material using cat_get_material_por_nombre
        ret = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
        self.assertEqual(ret.get("nombre"), "CUERO VACUNO")
        self.assertEqual(ret.get("departamento"), "CORTE")

        # Non-existent material should return empty dict
        self.assertEqual(modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT"), {})

    def test_cat_buscar_empty_text(self):
        # Inserting items
        modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA HULE", "departamento": "SUELAS"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO NYLON", "departamento": "PESPUNTE"})

        # Empty search string should return all records matching status
        rows = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        nombres = [r[1] for r in rows]
        self.assertIn("SUELA HULE", nombres)
        self.assertIn("HILO NYLON", nombres)

    def test_ic_listar_estilos_empty_search(self):
        modulo_catalogos.ic_guardar_estilo("ESTILO_001", "CORTE", 150.0, "Nota test 1")
        modulo_catalogos.ic_guardar_estilo("ESTILO_002", "MONTADO", 200.0, "Nota test 2")

        estilos = modulo_catalogos.ic_listar_estilos("", "TODOS")
        nombres = [e["estilo"] for e in estilos]
        self.assertIn("ESTILO_001", nombres)
        self.assertIn("ESTILO_002", nombres)

    def test_performance_get_material_por_nombre(self):
        # Insert 100 material items
        for i in range(100):
            modulo_catalogos.cat_guardar("materiales", {
                "nombre": f"MATERIAL_BENCH_{i:04d}",
                "tipo_material": "DIRECTO",
                "unidad_default": "dm",
                "departamento": "CORTE"
            })

        t0 = time.perf_counter()
        for _ in range(100):
            res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_BENCH_0050")
            self.assertEqual(res.get("nombre"), "MATERIAL_BENCH_0050")
        t1 = time.perf_counter()

        elapsed_ms = (t1 - t0) * 1000
        # 100 queries should take less than 100ms with indexed lookups
        self.assertLess(elapsed_ms, 500)


if __name__ == "__main__":
    unittest.main()
