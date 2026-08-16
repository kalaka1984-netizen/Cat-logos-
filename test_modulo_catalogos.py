import os
import sys
import tempfile
import unittest
from types import ModuleType

# Create dummy module structure for tkinter and customtkinter
class DummyBase:
    def __init__(self, *args, **kwargs):
        pass

class DummyTk(DummyBase):
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def withdraw(self):
        pass
    def destroy(self):
        pass

tk_module = ModuleType("tkinter")
tk_module.Tk = DummyTk
tk_module.Frame = DummyBase
tk_module.Label = DummyBase
tk_module.Button = DummyBase
tk_module.Entry = DummyBase
tk_module.StringVar = DummyBase
tk_module.BooleanVar = DummyBase
tk_module.IntVar = DummyBase
tk_module.DoubleVar = DummyBase

ttk_module = ModuleType("tkinter.ttk")
ttk_module.Treeview = DummyBase
ttk_module.Style = DummyBase
ttk_module.Scrollbar = DummyBase

messagebox_module = ModuleType("tkinter.messagebox")

tk_module.ttk = ttk_module
tk_module.messagebox = messagebox_module

class DummyCTkModule(ModuleType):
    def __getattr__(self, name):
        if name in ("set_appearance_mode", "set_default_color_theme"):
            return lambda *args, **kwargs: None
        return DummyBase

ctk_module = DummyCTkModule("customtkinter")

sys.modules["tkinter"] = tk_module
sys.modules["tkinter.ttk"] = ttk_module
sys.modules["tkinter.messagebox"] = messagebox_module
sys.modules["customtkinter"] = ctk_module

import modulo_catalogos as mc


class TestModuloCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.db_fd)

        # Override CAT_DB_PATH
        self.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = self.db_path

        # Initialize databases
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_ic_listar_estilos_pre_aggregation(self):
        # Insert a test style
        ok, estilo_id = mc.ic_guardar_estilo(
            estilo="ESTILO_TEST",
            departamento="CORTE",
            precio_par=100.0,
            notas="Test note"
        )
        self.assertTrue(ok)

        # Initially, 0 fractions
        estilos = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["n_frac"], 0)
        self.assertEqual(estilos[0]["suma_frac"], 0.0)

        # Add fractions
        mc.ic_guardar_fraccion(estilo_id, "FRAC_1", 25.5, orden=1)
        mc.ic_guardar_fraccion(estilo_id, "FRAC_2", 14.5, orden=2)

        # Check pre-aggregation
        estilos_after = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(estilos_after), 1)
        self.assertEqual(estilos_after[0]["n_frac"], 2)
        self.assertEqual(estilos_after[0]["suma_frac"], 40.0)

    def test_ic_listar_estilos_filtering(self):
        mc.ic_guardar_estilo("ESTILO_A", "CORTE", 50.0)
        mc.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 60.0)

        corte_estilos = mc.ic_listar_estilos(buscar="", departamento="CORTE")
        self.assertEqual(len(corte_estilos), 1)
        self.assertEqual(corte_estilos[0]["estilo"], "ESTILO_A")

        search_estilos = mc.ic_listar_estilos(buscar="ESTILO_B", departamento="TODOS")
        self.assertEqual(len(search_estilos), 1)
        self.assertEqual(search_estilos[0]["estilo"], "ESTILO_B")


if __name__ == "__main__":
    unittest.main()
