import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# Base dummy class to serve as bases for CustomTkinter components without metaclass conflicts
class DummyBase:
    def __init__(self, *args, **kwargs):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass

mock_tk = MagicMock()
mock_tk.Tk = DummyBase

mock_ctk = MagicMock()
mock_ctk.CTk = DummyBase
mock_ctk.CTkFrame = DummyBase
mock_ctk.CTkLabel = DummyBase
mock_ctk.CTkButton = DummyBase
mock_ctk.CTkEntry = DummyBase
mock_ctk.CTkComboBox = DummyBase
mock_ctk.CTkTabview = DummyBase
mock_ctk.CTkScrollableFrame = DummyBase
mock_ctk.CTkOptionMenu = DummyBase
mock_ctk.CTkCheckBox = DummyBase
mock_ctk.CTkSegmentedButton = DummyBase
mock_ctk.CTkToplevel = DummyBase

sys.modules['tkinter'] = mock_tk
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


class TestModuloCatalogosOptimizations(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
        self.temp_db.close()
        self.original_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.temp_db.name
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        modulo_catalogos.CAT_DB_PATH = self.original_db_path
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_cat_init_db_indexes(self):
        con = modulo_catalogos.sqlite3.connect(self.temp_db.name)
        cur = con.cursor()
        for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
            cur.execute(f"PRAGMA index_list({tabla})")
            indexes = [row[1] for row in cur.fetchall()]
            self.assertIn(f"idx_{tabla}_nombre", indexes)
            self.assertIn(f"idx_{tabla}_estatus_nombre", indexes)
        con.close()

    def test_cat_get_material_por_nombre(self):
        # Insert material
        datos = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ"
        }
        ok, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        # Retrieve material
        mat = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
        self.assertEqual(mat.get("nombre"), "CUERO VACUNO")
        self.assertEqual(mat.get("unidad_default"), "DM")

        # Non-existent material
        empty_mat = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
        self.assertEqual(empty_mat, {})

    def test_nombres_tabla_and_helpers(self):
        # Insert active and inactive items
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_A", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_B", "estatus": "INACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT_C", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        self.assertEqual(activos, ["MAT_A", "MAT_C"])

        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
        self.assertEqual(todos, ["MAT_A", "MAT_B", "MAT_C"])

    def test_cat_buscar_empty_and_query(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA HULLE", "estatus": "ACTIVO", "notas": "NEGRO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Hilo NYLON", "estatus": "ACTIVO", "notas": "BLANCO"})

        # Empty search string
        res_empty = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        self.assertEqual(len(res_empty), 2)

        # Search with keyword
        res_kw = modulo_catalogos.cat_buscar("materiales", "HILO", "ACTIVO")
        self.assertEqual(len(res_kw), 1)
        self.assertEqual(res_kw[0][1], "HILO NYLON")


if __name__ == "__main__":
    unittest.main()
