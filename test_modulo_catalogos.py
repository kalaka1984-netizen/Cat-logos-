import os
import sys
import unittest


# Dummy class base for customtkinter widgets
class DummyBase:
    def __init__(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass

# Dummy customtkinter module
class DummyCTK:
    CTkFrame = DummyBase
    CTkLabel = DummyBase
    CTkButton = DummyBase
    CTkEntry = DummyBase
    CTkComboBox = DummyBase
    CTkOptionMenu = DummyBase
    CTkCheckBox = DummyBase
    CTkFont = DummyBase
    CTkScrollableFrame = DummyBase
    CTkSegmentedButton = DummyBase
    CTkToplevel = DummyBase
    CTkTabview = DummyBase
    CTkTextbox = DummyBase

    @staticmethod
    def set_appearance_mode(mode):
        pass

    @staticmethod
    def set_default_color_theme(theme):
        pass

from unittest.mock import MagicMock

mock_tk = MagicMock()
mock_root = MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root

sys.modules['tkinter'] = mock_tk
sys.modules['customtkinter'] = DummyCTK

import modulo_catalogos


class TestCatNombres(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_catalogos_temp.sqlite"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_cat_get_nombres_materiales(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "PIEL NEGRA", "tipo": "DIRECTO", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO BLANCO", "tipo": "DIRECTO", "estatus": "INACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA GOMA", "tipo": "DIRECTO", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)

        self.assertEqual(activos, ["PIEL NEGRA", "SUELA GOMA"])
        self.assertEqual(todos, ["HILO BLANCO", "PIEL NEGRA", "SUELA GOMA"])

    def test_cat_get_nombres_trabajadores(self):
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "puesto": "CORTADOR", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "ANA GOMEZ", "puesto": "COSTURERA", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
        todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)

        self.assertEqual(activos, ["JUAN PEREZ"])
        self.assertEqual(todos, ["ANA GOMEZ", "JUAN PEREZ"])

    def test_tabla_no_permitida(self):
        with self.assertRaises(ValueError):
            modulo_catalogos._cat_get_nombres_tabla("tabla_invalida")


if __name__ == "__main__":
    unittest.main()
