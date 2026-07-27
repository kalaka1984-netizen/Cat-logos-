import os
import sqlite3
import unittest
from unittest.mock import MagicMock, sys


# Mock tkinter and customtkinter correctly to prevent metaclass conflicts
class DummyFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after(self, *args, **kwargs):
        return "timer_id"
    def after_cancel(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return MagicMock()

class DummyTk:
    def __init__(self, *args, **kwargs):
        pass
    def withdraw(self):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def destroy(self):
        pass

# Create mock module for customtkinter
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkLabel = MagicMock()
mock_ctk.CTkButton = MagicMock()
mock_ctk.CTkEntry = MagicMock()
mock_ctk.CTkComboBox = MagicMock()
mock_ctk.CTkTextbox = MagicMock()
mock_ctk.CTkScrollableFrame = DummyFrame
mock_ctk.CTkSegmentedButton = MagicMock()
mock_ctk.CTkRadioButton = MagicMock()
mock_ctk.CTkScrollbar = DummyFrame
mock_ctk.CTkToplevel = DummyFrame

# Create mock module for tkinter
mock_tk = MagicMock()
mock_tk.Tk = DummyTk
mock_tk.Frame = DummyFrame
mock_tk.Label = MagicMock()
mock_tk.Canvas = MagicMock()
mock_tk.Scrollbar = DummyFrame

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


class TestModuloCatalogosOptimizations(unittest.TestCase):

    def setUp(self):
        # Initialize/clean the database
        self.db_path = "test_catalogos.sqlite"
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_cat_buscar_optimization_empty_query(self):
        # Insert test data
        con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod)
            VALUES (?, ?, ?, ?, ?)
        """, ("CUERO NEGRO", '{"nombre": "CUERO NEGRO", "tipo_material": "DIRECTO"}', "ACTIVO", "2024-01-01", "2024-01-01"))
        cur.execute("""
            INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod)
            VALUES (?, ?, ?, ?, ?)
        """, ("CUERO CAFE", '{"nombre": "CUERO CAFE", "tipo_material": "DIRECTO"}', "INACTIVO", "2024-01-01", "2024-01-01"))
        con.commit()
        con.close()

        # Test searching with empty text (should not use LIKE query but still return records)
        rows_all = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
        self.assertEqual(len(rows_all), 2)
        self.assertEqual(rows_all[0][1], "CUERO CAFE")
        self.assertEqual(rows_all[1][1], "CUERO NEGRO")

        rows_activo = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        self.assertEqual(len(rows_activo), 1)
        self.assertEqual(rows_activo[0][1], "CUERO NEGRO")

    def test_cat_get_material_por_nombre(self):
        # Insert test data
        con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod)
            VALUES (?, ?, ?, ?, ?)
        """, ("SUELA TR", '{"nombre": "SUELA TR", "tipo_material": "DIRECTO", "unidad_default": "par"}', "ACTIVO", "2024-01-01", "2024-01-01"))
        con.commit()
        con.close()

        # Direct O(1) fetch
        data = modulo_catalogos.cat_get_material_por_nombre("SUELA TR")
        self.assertEqual(data.get("unidad_default"), "par")
        self.assertEqual(data.get("tipo_material"), "DIRECTO")

        # Non-existent material
        data_empty = modulo_catalogos.cat_get_material_por_nombre("NON EXISTENT")
        self.assertEqual(data_empty, {})

    def test_ic_listar_estilos_pre_aggregation(self):
        # Add a style and some fractions to test the pre-aggregation optimization (N+1 query resolution)
        ok_estilo, estilo_id = modulo_catalogos.ic_guardar_estilo("ESTILO-999", "PESPUNTE", 150.00, "NOTAS TEST")
        self.assertTrue(ok_estilo)

        # Add fractions
        modulo_catalogos.ic_guardar_fraccion(estilo_id, "COSTURA APARADO", 60.00, 1)
        modulo_catalogos.ic_guardar_fraccion(estilo_id, "DOBLILLADO", 40.00, 2)

        # Retrieve styles
        estilos = modulo_catalogos.ic_listar_estilos("ESTILO-999", "PESPUNTE")
        self.assertEqual(len(estilos), 1)

        # Verify pre-aggregated fraction count and sum
        self.assertEqual(estilos[0]["n_frac"], 2)
        self.assertEqual(estilos[0]["suma_frac"], 100.00)
        self.assertEqual(estilos[0]["precio_par"], 150.00)

    def test_ic_estilos_department_index_exists(self):
        # Verify the new index on departamento was created correctly
        con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA index_list('ic_estilos')")
        indices = cur.fetchall()
        con.close()

        index_names = [ind[1] for ind in indices]
        self.assertIn("idx_ic_estilos_depto", index_names)

if __name__ == "__main__":
    unittest.main()
