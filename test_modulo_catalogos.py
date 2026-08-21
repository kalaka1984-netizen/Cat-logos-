import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock


# Dummy classes for CTk and Tk
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTk:
    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def destroy(self):
        pass


class DummyTk:
    def withdraw(self):
        pass

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def destroy(self):
        pass


dummy_ctk = MagicMock()
dummy_ctk.CTkFrame = DummyCTkFrame
dummy_ctk.CTk = DummyCTk

dummy_tk = MagicMock()
dummy_tk.Tk = DummyTk

sys.modules["customtkinter"] = dummy_ctk
sys.modules["tkinter"] = dummy_tk
sys.modules["tkinter.ttk"] = MagicMock()

import modulo_catalogos


class TestCatGetMaterialPorNombre(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)
        self.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_material_por_nombre_success(self):
        datos_input = {
            "nombre": "CUERO VACUNO",
            "tipo": "DIR",
            "unidad": "DM",
            "departamento": "CORTE",
            "estatus": "ACTIVO",
        }
        status, _mat_id = modulo_catalogos.cat_guardar("materiales", datos_input)
        self.assertTrue(status)

        mat_info = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
        self.assertEqual(mat_info.get("nombre"), "CUERO VACUNO")
        self.assertEqual(mat_info.get("unidad"), "DM")
        self.assertEqual(mat_info.get("departamento"), "CORTE")

    def test_get_material_por_nombre_not_found(self):
        mat_info = modulo_catalogos.cat_get_material_por_nombre(
            "MATERIAL_INEXISTENTE"
        )
        self.assertEqual(mat_info, {})

    def test_get_material_por_nombre_empty(self):
        mat_info = modulo_catalogos.cat_get_material_por_nombre("")
        self.assertEqual(mat_info, {})

    def test_performance_benchmark(self):
        # Populate DB with 1000 items
        for i in range(1000):
            datos = {
                "nombre": f"MATERIAL_{i}",
                "tipo": "DIR",
                "unidad": "DM",
                "estatus": "ACTIVO",
                "extra": "x" * 200,
            }
            modulo_catalogos.cat_guardar("materiales", datos)

        target = "MATERIAL_500"

        t0 = time.perf_counter()
        for _ in range(100):
            res = modulo_catalogos.cat_get_material_por_nombre(target)
        t1 = time.perf_counter()

        elapsed_ms = (t1 - t0) * 1000
        self.assertEqual(res.get("nombre"), "MATERIAL_500")
        # Ensure 100 lookup queries take well under 200ms
        self.assertLess(elapsed_ms, 200.0)


if __name__ == "__main__":
    unittest.main()
