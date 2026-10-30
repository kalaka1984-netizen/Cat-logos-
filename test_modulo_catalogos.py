import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# Create dummy CustomTkinter / Tkinter mock classes to support import in headless environments
class DummyCTkFrame:
    def __init__(self, *args, **kwargs): pass

class DummyCTkLabel:
    def __init__(self, *args, **kwargs): pass

class DummyCTkButton:
    def __init__(self, *args, **kwargs): pass

class DummyCTkEntry:
    def __init__(self, *args, **kwargs): pass

class DummyCTkScrollableFrame:
    def __init__(self, *args, **kwargs): pass

class DummyCTkComboBox:
    def __init__(self, *args, **kwargs): pass

class DummyCTkTextbox:
    def __init__(self, *args, **kwargs): pass

class DummyCTkSegmentedButton:
    def __init__(self, *args, **kwargs): pass

class DummyCTkScrollbar:
    def __init__(self, *args, **kwargs): pass

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs): pass

class DummyCTkRadioButton:
    def __init__(self, *args, **kwargs): pass

ctk_mock = MagicMock()
ctk_mock.CTkFrame = DummyCTkFrame
ctk_mock.CTkLabel = DummyCTkLabel
ctk_mock.CTkButton = DummyCTkButton
ctk_mock.CTkEntry = DummyCTkEntry
ctk_mock.CTkScrollableFrame = DummyCTkScrollableFrame
ctk_mock.CTkComboBox = DummyCTkComboBox
ctk_mock.CTkTextbox = DummyCTkTextbox
ctk_mock.CTkSegmentedButton = DummyCTkSegmentedButton
ctk_mock.CTkScrollbar = DummyCTkScrollbar
ctk_mock.CTkToplevel = DummyCTkToplevel
ctk_mock.CTkRadioButton = DummyCTkRadioButton

tk_mock = MagicMock()
root_mock = MagicMock()
root_mock.winfo_screenwidth.return_value = 1920
root_mock.winfo_screenheight.return_value = 1080
tk_mock.Tk.return_value = root_mock

sys.modules['tkinter'] = tk_mock
sys.modules['customtkinter'] = ctk_mock

import modulo_catalogos as mc  # noqa: E402

class TestModuloCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        mc.CAT_DB_PATH = self.tmp_db.name
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        if os.path.exists(self.tmp_db.name):
            os.remove(self.tmp_db.name)

    def test_ic_listar_estilos_preaggregation(self):
        # Create style A with fractions
        ok1, id1 = mc.ic_guardar_estilo('ESTILO_A', 'CORTE', 150.0)
        self.assertTrue(ok1)
        mc.ic_guardar_fraccion(id1, 'FRAC_1', 50.0)
        mc.ic_guardar_fraccion(id1, 'FRAC_2', 100.0)

        # Create style B without fractions
        ok2, id2 = mc.ic_guardar_estilo('ESTILO_B', 'PESPUNTE', 80.0)
        self.assertTrue(ok2)

        res = mc.ic_listar_estilos()
        self.assertEqual(len(res), 2)

        # Verify pre-aggregated counts and totals
        item_a = next(r for r in res if r['id'] == id1)
        self.assertEqual(item_a['estilo'], 'ESTILO_A')
        self.assertEqual(item_a['departamento'], 'CORTE')
        self.assertEqual(item_a['precio_par'], 150.0)
        self.assertEqual(item_a['n_frac'], 2)
        self.assertEqual(item_a['suma_frac'], 150.0)

        item_b = next(r for r in res if r['id'] == id2)
        self.assertEqual(item_b['estilo'], 'ESTILO_B')
        self.assertEqual(item_b['departamento'], 'PESPUNTE')
        self.assertEqual(item_b['precio_par'], 80.0)
        self.assertEqual(item_b['n_frac'], 0)
        self.assertEqual(item_b['suma_frac'], 0.0)

    def test_ic_listar_estilos_filtering(self):
        mc.ic_guardar_estilo('S_CORTE_1', 'CORTE', 100.0)
        mc.ic_guardar_estilo('S_PESP_1', 'PESPUNTE', 110.0)

        # Department filtering
        res_corte = mc.ic_listar_estilos(departamento='CORTE')
        self.assertEqual(len(res_corte), 1)
        self.assertEqual(res_corte[0]['estilo'], 'S_CORTE_1')

        # Search filtering
        res_search = mc.ic_listar_estilos(buscar='PESP')
        self.assertEqual(len(res_search), 1)
        self.assertEqual(res_search[0]['estilo'], 'S_PESP_1')

    def test_department_index_exists(self):
        import sqlite3
        con = sqlite3.connect(mc.CAT_DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA index_list('ic_estilos')")
        indexes = [row[1] for row in cur.fetchall()]
        con.close()
        self.assertIn('idx_ic_estilos_depto', indexes)

if __name__ == '__main__':
    unittest.main()
