import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock


# Dummy base classes to avoid metaclass conflicts when subclassing ctk.CTkFrame etc.
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass

class DummyFrame(DummyWidget):
    pass

# Mock GUI dependencies before importing modulo_catalogos
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkOptionMenu = DummyWidget
mock_ctk.CTkScrollableFrame = DummyFrame
mock_ctk.CTkTabview = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkToplevel = DummyWidget

mock_tk = MagicMock()
root_mock = MagicMock()
root_mock.winfo_screenwidth.return_value = 1920
root_mock.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = root_mock

sys.modules['customtkinter'] = mock_ctk
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['darkdetect'] = MagicMock()

import modulo_catalogos


class TestModuloCatalogos:

    def setup_method(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self.temp_db_fd)
        modulo_catalogos.CAT_DB_PATH = self.temp_db_path
        modulo_catalogos.cat_init_db()

    def teardown_method(self):
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_cat_init_db_indexes(self):
        con = sqlite3.connect(self.temp_db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [r[0] for r in cur.fetchall()]
        con.close()

        for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
            assert f"idx_{tabla}_nombre" in indexes
            assert f"idx_{tabla}_estatus_nombre" in indexes

    def test_cat_get_nombres_tabla_whitelist(self):
        res = modulo_catalogos._cat_get_nombres_tabla("invalid_table")
        assert res == []

    def test_cat_get_nombres_materiales(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA DE HULE", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "PIEL VACUNO", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO OBSOLETO", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        assert activos == ["PIEL VACUNO", "SUELA DE HULE"]

        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
        assert todos == ["HILO OBSOLETO", "PIEL VACUNO", "SUELA DE HULE"]

    def test_cat_get_nombres_trabajadores(self):
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("trabajadores", {"nombre": "ANA GOMEZ", "estatus": "INACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=True)
        assert activos == ["JUAN PEREZ"]

        todos = modulo_catalogos.cat_get_nombres_trabajadores(solo_activos=False)
        assert todos == ["ANA GOMEZ", "JUAN PEREZ"]

    def test_cat_get_nombres_proveedores(self):
        modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROVEEDOR A", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_proveedores(solo_activos=True)
        assert activos == ["PROVEEDOR A"]

    def test_cat_get_nombres_clientes(self):
        modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE Z", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_clientes(solo_activos=True)
        assert activos == ["CLIENTE Z"]
