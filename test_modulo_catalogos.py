import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# To prevent GUI/metaclass conflicts in a headless environment, we construct a dummy/mock 'customtkinter' module
# with the basic widgets we inherit from or use, and inject it into 'sys.modules' before importing modulo_catalogos.
class DummyCTkFrame:
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
    def after(self, *args, **kwargs):
        pass
    def after_cancel(self, *args, **kwargs):
        pass
    def update_idletasks(self):
        pass
    def winfo_width(self):
        return 100
    def winfo_height(self):
        return 100
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def bind(self, *args, **kwargs):
        pass

class DummyCTkTopLevel:
    def __init__(self, *args, **kwargs):
        pass
    def withdraw(self):
        pass
    def destroy(self):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def grab_set(self):
        pass
    def grab_release(self):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkScrollableFrame = DummyCTkFrame
mock_ctk.CTkToplevel = DummyCTkTopLevel
mock_ctk.set_appearance_mode = lambda mode: None
mock_ctk.set_default_color_theme = lambda theme: None
mock_ctk.set_widget_scaling = lambda scale: None
mock_ctk.set_window_scaling = lambda scale: None

sys.modules['customtkinter'] = mock_ctk

# Mock tkinter's Tk to prevent _tkinter.TclError in headless testing
mock_tk = MagicMock()
class DummyTk:
    def __init__(self):
        pass
    def withdraw(self):
        pass
    def destroy(self):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
mock_tk.Tk = DummyTk
sys.modules['tkinter'] = mock_tk

import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        # Override the database path to a test database and initialize tables
        self.original_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = "test_catalogos_db.sqlite"
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        # Clean up database after each test
        modulo_catalogos.CAT_DB_PATH = self.original_db_path
        if os.path.exists("test_catalogos_db.sqlite"):
            try:
                os.remove("test_catalogos_db.sqlite")
            except OSError:
                pass

    def test_cat_guardar_and_get_by_nombre(self):
        # Test inserting and exact lookup of material (expecting capitalized stored values)
        mat_data = {
            "nombre": "suela cuero",
            "tipo_material": "directo",
            "unidad_default": "par"
        }
        ok, res_id = modulo_catalogos.cat_guardar("materiales", mat_data)
        self.assertTrue(ok)
        self.assertIsNotNone(res_id)

        # Exact match should work and return upper-case values
        retrieved = modulo_catalogos.cat_get_material_por_nombre("suela cuero")
        self.assertEqual(retrieved.get("nombre"), "SUELA CUERO")
        self.assertEqual(retrieved.get("tipo_material"), "DIRECTO")

        # Non-existing material lookup
        not_found = modulo_catalogos.cat_get_material_por_nombre("not exist")
        self.assertEqual(not_found, {})

    def test_cat_get_nombres_materiales(self):
        # Insert multiple materials
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Hilo"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Cuero"})

        nombres = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        self.assertIn("HILO", nombres)
        self.assertIn("CUERO", nombres)

    def test_ic_listar_estilos_pre_aggregation(self):
        # Insert a style
        ok, estilo_id = modulo_catalogos.ic_guardar_estilo("Estilo-X", "PESPUNTE", 150.00)
        self.assertTrue(ok)

        # Initially, no fractions are assigned
        estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["estilo"], "ESTILO-X")
        self.assertEqual(estilos[0]["n_frac"], 0)
        self.assertEqual(estilos[0]["suma_frac"], 0.0)

        # Add some fractions
        modulo_catalogos.ic_guardar_fraccion(estilo_id, "Costura lateral", 40.0)
        modulo_catalogos.ic_guardar_fraccion(estilo_id, "Remate superior", 10.0)

        # Verify pre-aggregated counts and sums match
        estilos_updated = modulo_catalogos.ic_listar_estilos(buscar="Estilo-X", departamento="TODOS")
        self.assertEqual(len(estilos_updated), 1)
        self.assertEqual(estilos_updated[0]["n_frac"], 2)
        self.assertEqual(estilos_updated[0]["suma_frac"], 50.0)

if __name__ == "__main__":
    unittest.main()
