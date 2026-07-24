# ruff: noqa: E402
import sys
from unittest.mock import MagicMock

# Sophisticated Mock for tkinter and customtkinter to support GUI-less testing

class DummyTk:
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
    def update_idletasks(self):
        pass

class DummyFrame:
    def __init__(self, *args, **kwargs):
        pass
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
    def winfo_exists(self):
        return True
    def winfo_toplevel(self):
        return DummyTk()
    def columnconfigure(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass

class DummyToplevel(DummyFrame):
    def resizable(self, *args, **kwargs):
        pass
    def lift(self, *args, **kwargs):
        pass
    def grab_set(self, *args, **kwargs):
        pass
    def grab_release(self, *args, **kwargs):
        pass
    def geometry(self, *args, **kwargs):
        pass

class DummyButton(DummyFrame):
    def configure(self, *args, **kwargs):
        pass

class DummyLabel(DummyFrame):
    def configure(self, *args, **kwargs):
        pass

class DummyEntry(DummyFrame):
    pass

class DummyComboBox(DummyFrame):
    pass

class DummyTextbox(DummyFrame):
    pass

class DummyScrollableFrame(DummyFrame):
    pass

class DummyScrollbar(DummyFrame):
    pass

class DummySegmentedButton(DummyFrame):
    pass

class DummyRadioButton(DummyFrame):
    pass

# Mock TK
mock_tk = MagicMock()
mock_tk.Tk = DummyTk
mock_tk.Frame = DummyFrame
mock_tk.Label = DummyLabel
mock_tk.Entry = DummyEntry
mock_tk.Listbox = MagicMock()
mock_tk.Scrollbar = MagicMock()
mock_tk.Toplevel = DummyToplevel

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

# Mock CustomTkinter
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyFrame
mock_ctk.CTkToplevel = DummyToplevel
mock_ctk.CTkButton = DummyButton
mock_ctk.CTkLabel = DummyLabel
mock_ctk.CTkEntry = DummyEntry
mock_ctk.CTkComboBox = DummyComboBox
mock_ctk.CTkTextbox = DummyTextbox
mock_ctk.CTkScrollableFrame = DummyScrollableFrame
mock_ctk.CTkScrollbar = DummyScrollbar
mock_ctk.CTkSegmentedButton = DummySegmentedButton
mock_ctk.CTkRadioButton = DummyRadioButton

sys.modules['customtkinter'] = mock_ctk

import os
import sqlite3
import pytest
import modulo_catalogos

@pytest.fixture(autouse=True)
def clean_db():
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()
    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM ic_estilos")
    cur.execute("DELETE FROM ic_fracciones")
    cur.execute("DELETE FROM materiales")
    con.commit()
    con.close()

def test_db_init():
    assert os.path.exists(modulo_catalogos.CAT_DB_PATH)

def test_ic_listar_estilos():
    # Insert some dummy records
    ok, est_id = modulo_catalogos.ic_guardar_estilo("TEST_ESTILO_UNIQUE", "PESPUNTE", 50.0)
    assert ok

    ok_f, _ = modulo_catalogos.ic_guardar_fraccion(est_id, "TEST_FRAC", 25.0)
    assert ok_f

    # Retrieve
    estilos = modulo_catalogos.ic_listar_estilos(buscar="TEST_ESTILO_UNIQUE")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "TEST_ESTILO_UNIQUE"
    assert estilos[0]["n_frac"] == 1
    assert estilos[0]["suma_frac"] == 25.0

def test_cat_get_material_por_nombre():
    nombre = "TEST_MATERIAL_DIRECT"
    datos = {
        "nombre": nombre,
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "proveedor_ref": "",
        "costo_ref": 15.0,
        "notes": "TEST"
    }
    ok, _ = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok

    res = modulo_catalogos.cat_get_material_por_nombre(nombre)
    assert res != {}
    assert res.get("tipo_material") == "DIRECTO"
