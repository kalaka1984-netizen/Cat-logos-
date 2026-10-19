import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# ── Mock GUI components before import for headless environment ────────────
class DummyFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(row=0, column=0, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after_cancel(self, id_):
        pass
    def after(self, ms, func=None, *args):
        return "timer_id"

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkLabel = DummyFrame
mock_ctk.CTkButton = DummyFrame
mock_ctk.CTkEntry = DummyFrame
mock_ctk.CTkComboBox = DummyFrame
mock_ctk.CTkTextbox = DummyFrame
mock_ctk.CTkScrollableFrame = DummyFrame
mock_ctk.CTkSegmentedButton = DummyFrame
mock_ctk.CTkRadioButton = DummyFrame
mock_ctk.CTkToplevel = DummyFrame
mock_ctk.CTk = DummyFrame

sys.modules["customtkinter"] = mock_ctk
sys.modules["darkdetect"] = MagicMock()

import modulo_catalogos


class TestCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.cat_init_db()

        # Seed data
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ",
            "estatus": "ACTIVO"
        })
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": "HILO NYLON",
            "tipo_material": "INDIRECTO",
            "unidad_default": "m",
            "departamento": "PESPUNTE",
            "visible_monitor": "NO",
            "es_principal": "NO",
            "estatus": "INACTIVO"
        })

        modulo_catalogos.cat_guardar("trabajadores", {
            "nombre": "JUAN PEREZ",
            "puesto": "CORTADOR",
            "departamento": "CORTE",
            "estatus": "ACTIVO"
        })
        modulo_catalogos.cat_guardar("trabajadores", {
            "nombre": "MARIA GOMEZ",
            "puesto": "COSTURERA",
            "departamento": "PESPUNTE",
            "estatus": "INACTIVO"
        })

        modulo_catalogos.cat_guardar("proveedores", {
            "nombre": "PROVEEDOR A",
            "estatus": "ACTIVO"
        })
        modulo_catalogos.cat_guardar("clientes", {
            "nombre": "CLIENTE X",
            "estatus": "ACTIVO"
        })

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_get_nombres_materiales(self):
        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        self.assertEqual(activos, ["CUERO VACUNO"])

        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
        self.assertEqual(sorted(todos), ["CUERO VACUNO", "HILO NYLON"])

    def test_get_material_por_nombre(self):
        mat = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
        self.assertEqual(mat.get("nombre"), "CUERO VACUNO")
        self.assertEqual(mat.get("unidad_default"), "DM")

        # Case-insensitive / trailing spaces test
        mat_spaces = modulo_catalogos.cat_get_material_por_nombre("  cuero vacuno  ")
        self.assertEqual(mat_spaces.get("nombre"), "CUERO VACUNO")

        non_existent = modulo_catalogos.cat_get_material_por_nombre("NO_EXISTE")
        self.assertEqual(non_existent, {})

    def test_get_nombres_trabajadores(self):
        activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
        self.assertEqual(activos, ["JUAN PEREZ"])

        todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)
        self.assertEqual(sorted(todos), ["JUAN PEREZ", "MARIA GOMEZ"])

    def test_get_nombres_proveedores_y_clientes(self):
        provs = modulo_catalogos.cat_get_nombres_proveedores(solo_activos=True)
        self.assertEqual(provs, ["PROVEEDOR A"])

        clis = modulo_catalogos.cat_get_nombres_clientes(solo_activos=True)
        self.assertEqual(clis, ["CLIENTE X"])


if __name__ == "__main__":
    unittest.main()
