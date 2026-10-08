import os
import sys
import unittest
from unittest.mock import MagicMock


# Mock GUI components before importing application code
class DummyCTkWidget:
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


class DummyCTkFrame(DummyCTkWidget):
    pass


class DummyCTkLabel(DummyCTkWidget):
    pass


class DummyCTkButton(DummyCTkWidget):
    pass


class DummyCTkEntry(DummyCTkWidget):
    pass


mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkLabel
mock_ctk.CTkButton = DummyCTkButton
mock_ctk.CTkEntry = DummyCTkEntry

mock_tk = MagicMock()
mock_tk.Tk().winfo_screenwidth.return_value = 1920
mock_tk.Tk().winfo_screenheight.return_value = 1080

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_tk
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


class TestModuloCatalogosNombres(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_catalogos_temp.sqlite"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        modulo_catalogos.CAT_DB_PATH = self.test_db
        modulo_catalogos.cat_init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_cat_get_nombres_materiales(self):
        # Insert sample materials (note cat_guardar converts names to uppercase)
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Cuero Negro", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Suela Goma", "estatus": "INACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "Hilo Blanco", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        self.assertEqual(activos, ["CUERO NEGRO", "HILO BLANCO"])

        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
        self.assertEqual(todos, ["CUERO NEGRO", "HILO BLANCO", "SUELA GOMA"])

    def test_cat_get_nombres_trabajadores(self):
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "Juan Perez", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "Ana Gomez", "estatus": "BAJA"})

        activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
        self.assertEqual(activos, ["JUAN PEREZ"])

        todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)
        self.assertEqual(todos, ["ANA GOMEZ", "JUAN PEREZ"])

    def test_cat_get_nombres_proveedores(self):
        modulo_catalogos.cat_guardar("proveedores", {"nombre": "Proveedor Alpha", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("proveedores", {"nombre": "Proveedor Beta", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_proveedores(solo_activos=True)
        self.assertEqual(activos, ["PROVEEDOR ALPHA"])

        todos = modulo_catalogos.cat_get_nombres_proveedores(solo_activos=False)
        self.assertEqual(todos, ["PROVEEDOR ALPHA", "PROVEEDOR BETA"])

    def test_cat_get_nombres_clientes(self):
        modulo_catalogos.cat_guardar("clientes", {"nombre": "Cliente Zapateria", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("clientes", {"nombre": "Cliente Boutique", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_clientes(solo_activos=True)
        self.assertEqual(activos, ["CLIENTE BOUTIQUE", "CLIENTE ZAPATERIA"])


if __name__ == "__main__":
    unittest.main()
