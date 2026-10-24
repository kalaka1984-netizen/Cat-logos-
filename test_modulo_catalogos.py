import sys
import unittest
from unittest.mock import MagicMock

# Mock customtkinter before importing modulo_catalogos
mock_ctk = MagicMock()
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080

mock_ctk.CTk = DummyWidget
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
sys.modules['customtkinter'] = mock_ctk

import os
import sqlite3
import json
import modulo_catalogos

TEST_DB = "test_catalogos_temp.sqlite"

def setup_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    modulo_catalogos.CAT_DB_PATH = TEST_DB
    modulo_catalogos.cat_init_db()

def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

class TestCatNombresTabla(unittest.TestCase):
    def setUp(self):
        # Clear database
        con = sqlite3.connect(TEST_DB)
        cur = con.cursor()
        for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
            cur.execute(f"DELETE FROM {tabla}")
        con.commit()
        con.close()

    def test_cat_get_nombres_materiales(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "PIEL NEGRA", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA GOMA", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO VIEJO", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)

        self.assertEqual(activos, ["PIEL NEGRA", "SUELA GOMA"])
        self.assertEqual(todos, ["HILO VIEJO", "PIEL NEGRA", "SUELA GOMA"])

    def test_cat_get_nombres_trabajadores(self):
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "CARLOS SANCHEZ", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "ANA GOMEZ", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
        todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)

        self.assertEqual(activos, ["CARLOS SANCHEZ"])
        self.assertEqual(todos, ["ANA GOMEZ", "CARLOS SANCHEZ"])

    def test_invalid_table_raises(self):
        with self.assertRaises(ValueError):
            modulo_catalogos._cat_get_nombres_tabla("tabla_invalida")
