import sqlite3
import sys
from unittest.mock import MagicMock

import pytest

# Mock GUI dependencies before importing modulo_catalogos

class DummyCTkWidget:
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
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def destroy(self):
        pass
    def after(self, ms, func=None, *args):
        return "timer_id"
    def after_cancel(self, id):
        pass

class DummyCTkModule:
    CTk = DummyCTkWidget
    CTkToplevel = DummyCTkWidget
    CTkFrame = DummyCTkWidget
    CTkLabel = DummyCTkWidget
    CTkButton = DummyCTkWidget
    CTkEntry = DummyCTkWidget
    CTkOptionMenu = DummyCTkWidget
    CTkComboBox = DummyCTkWidget
    CTkCheckBox = DummyCTkWidget
    CTkRadioButton = DummyCTkWidget
    CTkTabview = DummyCTkWidget
    CTkScrollableFrame = DummyCTkWidget
    CTkFont = MagicMock
    set_appearance_mode = staticmethod(lambda *a, **k: None)
    set_default_color_theme = staticmethod(lambda *a, **k: None)

mock_ctk = DummyCTkModule()

mock_tk = MagicMock()
mock_tk_root = MagicMock()
mock_tk_root.winfo_screenwidth.return_value = 1920
mock_tk_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_root

sys.modules['customtkinter'] = mock_ctk
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

import modulo_catalogos


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    temp_db = str(tmp_path / "test_catalogos_temp.sqlite")
    old_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db
    modulo_catalogos.cat_init_db()
    yield
    modulo_catalogos.CAT_DB_PATH = old_db_path


def test_cat_init_db_and_indexes():
    """Verify that cat_init_db creates tables and required indexes."""
    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()

    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='idx_{tabla}_estatus_nombre'")
        row = cur.fetchone()
        assert row is not None, f"Index idx_{tabla}_estatus_nombre should exist"

    con.close()


def test_cat_guardar_and_get_material_por_nombre():
    """Test saving materials and exact name lookup optimization."""
    datos_mat = {
        "nombre": "PIEL VACUNO NEGRO 1.2MM",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
    }

    ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos_mat)
    assert ok is True
    assert isinstance(mat_id, int)

    # Test exact lookup function
    fetched = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRO 1.2MM")
    assert fetched.get("nombre") == "PIEL VACUNO NEGRO 1.2MM"
    assert fetched.get("unidad_default") == "DM"
    assert fetched.get("departamento") == "CORTE"

    # Test case insensitivity and whitespace trimming
    fetched_insensitive = modulo_catalogos.cat_get_material_por_nombre("  piel vacuno negro 1.2mm  ")
    assert fetched_insensitive.get("nombre") == "PIEL VACUNO NEGRO 1.2MM"

    # Test non-existent item
    assert modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE") == {}


def test_cat_buscar_empty_text():
    """Test searching with empty string (optimization path) vs filtered search."""
    datos1 = {"nombre": "HILO ROJO 20", "tipo_material": "INDIRECTO", "estatus": "ACTIVO"}
    datos2 = {"nombre": "HILO AZUL 20", "tipo_material": "INDIRECTO", "estatus": "INACTIVO"}

    modulo_catalogos.cat_guardar("materiales", datos1)
    modulo_catalogos.cat_guardar("materiales", datos2)

    # Search all
    all_rows = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(all_rows) == 2

    # Search active only
    active_rows = modulo_catalogos.cat_buscar("materiales", "   ", "ACTIVO")
    assert len(active_rows) == 1
    assert active_rows[0][1] == "HILO ROJO 20"

    # Search by text query
    query_rows = modulo_catalogos.cat_buscar("materiales", "AZUL", "TODOS")
    assert len(query_rows) == 1
    assert query_rows[0][1] == "HILO AZUL 20"


def test_cat_get_nombres_listing():
    """Test name listing optimization functions."""
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})
    modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROVEEDOR X", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE Y", "estatus": "ACTIVO"})

    # Test active only
    act_mats = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert act_mats == ["MAT A"]

    # Test all
    all_mats = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert all_mats == ["MAT A", "MAT B"]

    assert modulo_catalogos.cat_get_nombres_trabajadores() == ["JUAN PEREZ"]
    assert modulo_catalogos.cat_get_nombres_proveedores() == ["PROVEEDOR X"]
    assert modulo_catalogos.cat_get_nombres_clientes() == ["CLIENTE Y"]


def test_cat_precarga_material():
    """Test precarga helper for Fichas Técnicas integration."""
    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "SUELA CAUCHO 40",
        "tipo_material": "DIRECTO",
        "unidad_default": "PAR",
        "departamento": "SUELAS",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    })

    precarga = modulo_catalogos.cat_precarga_material("SUELA CAUCHO 40")
    assert precarga == {
        "tipo_ft": "DIR",
        "unidad": "PAR",
        "departamento": "SUELAS",
        "monitor": True,
        "principal": True
    }
