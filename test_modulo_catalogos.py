import os
import sys
import unittest
from unittest.mock import MagicMock


# ── Headless environment mocking for tkinter & customtkinter ──────────────────
# Create dummy classes to serve as bases for GUI components to avoid metaclass conflicts.
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after(self, *args, **kwargs):
        return "after_id"

class DummyCTkLabel:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass

class DummyCTkButton:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs):
        pass

# Setup fake modules with correct return values for winfo_screenwidth/height
tk_mock = MagicMock()
tk_instance = MagicMock()
tk_instance.winfo_screenwidth.return_value = 1920
tk_instance.winfo_screenheight.return_value = 1080
tk_mock.Tk.return_value = tk_instance

sys.modules['tkinter'] = tk_mock
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

ctk_mock = MagicMock()
ctk_mock.CTkFrame = DummyCTkFrame
ctk_mock.CTkLabel = DummyCTkLabel
ctk_mock.CTkButton = DummyCTkButton
ctk_mock.CTkToplevel = DummyCTkToplevel
ctk_mock.CTkScrollableFrame = DummyCTkFrame
sys.modules['customtkinter'] = ctk_mock

# Now import the module under test after mocking is set up
import modulo_catalogos


class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        # Override database path to use a temporary test sqlite file
        self.temp_db_path = "test_catalogos_db.sqlite"
        modulo_catalogos.CAT_DB_PATH = self.temp_db_path
        # Re-initialize the database
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        # Remove temporary database
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_cat_guardar_and_buscar_empty_optimization(self):
        # Test basic cat_guardar works and forces uppercase
        ok, reg_id = modulo_catalogos.cat_guardar("materiales", {
            "nombre": "hilo de nylon",
            "unidad_default": "m",
            "estatus": "ACTIVO"
        })
        self.assertTrue(ok)
        self.assertIsNotNone(reg_id)

        # Test retrieving material
        mat = modulo_catalogos.cat_get_material_por_nombre("HILO DE NYLON")
        self.assertEqual(mat.get("unidad_default"), "M")

        # Test empty query optimization
        rows = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "HILO DE NYLON")

    def test_ic_listar_estilos_pre_aggregation(self):
        # Save a new style
        ok, est_id = modulo_catalogos.ic_guardar_estilo("bota texana", "PESPUNTE", 120.00)
        self.assertTrue(ok)

        # List styles (empty search optimization should return 0 fractions)
        estilos = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["estilo"], "BOTA TEXANA")
        self.assertEqual(estilos[0]["n_frac"], 0)
        self.assertEqual(estilos[0]["suma_frac"], 0.0)

        # Add fractions
        ok, _msg = modulo_catalogos.ic_guardar_fraccion(est_id, "costura de adorno", 50.00)
        self.assertTrue(ok)
        ok, _msg = modulo_catalogos.ic_guardar_fraccion(est_id, "pespunte lateral", 70.00)
        self.assertTrue(ok)

        # List styles again, must have pre-aggregated n_frac=2 and suma_frac=120.00
        estilos = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["n_frac"], 2)
        self.assertEqual(estilos[0]["suma_frac"], 120.00)

if __name__ == "__main__":
    unittest.main()
