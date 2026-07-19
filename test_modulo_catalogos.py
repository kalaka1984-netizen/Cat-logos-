# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from unittest import mock

# Safely mock tkinter and customtkinter for headless/headless-like testing
mock_tk = mock.MagicMock()

# Setup winfo mock methods to return dummy integer values
mock_tk_instance = mock.MagicMock()
mock_tk_instance.winfo_screenwidth.return_value = 1920
mock_tk_instance.winfo_screenheight.return_value = 1080

mock_tk.Tk = lambda: mock_tk_instance

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()

# Mock CustomTkinter components carefully to avoid metaclass or class conflicts.
# Base dummy classes that implement minimum requirements
class DummyCTkFrame(mock.MagicMock):
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass
    def after_cancel(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass

mock_ctk = mock.MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkButton = mock.MagicMock()
mock_ctk.CTkLabel = mock.MagicMock()
mock_ctk.CTkScrollableFrame = mock.MagicMock()
mock_ctk.CTkEntry = mock.MagicMock()
mock_ctk.CTkComboBox = mock.MagicMock()
mock_ctk.CTkTextbox = mock.MagicMock()
mock_ctk.CTkSegmentedButton = mock.MagicMock()
mock_ctk.CTkScrollbar = mock.MagicMock()
mock_ctk.CTkToplevel = mock.MagicMock()

sys.modules['customtkinter'] = mock_ctk

# Import after module patching to prevent initialization errors
import modulo_catalogos  # noqa: E402

# Setup a clean test database file path context
DB_PATH = modulo_catalogos.CAT_DB_PATH

def setup_function():
    # Delete test database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

def teardown_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_database_initialization():
    assert os.path.exists(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Verify tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    assert "materiales" in tables
    assert "ic_estilos" in tables
    assert "ic_fracciones" in tables

    # Verify departamento index
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ic_estilos';")
    indexes = [r[0] for r in cur.fetchall()]
    assert "idx_ic_estilos_depto" in indexes
    con.close()

def test_cat_buscar_and_material_optimization():
    # Insert dummy materials
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA DE HULE", "tipo_material": "DIRECTO", "unidad_default": "PAR"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "FORRO PIEL", "tipo_material": "DIRECTO", "unidad_default": "DM"})

    # Test cat_get_material_por_nombre
    res = modulo_catalogos.cat_get_material_por_nombre("SUELA DE HULE")
    assert res.get("unidad_default") == "PAR"

    # Test search empty and with pattern
    all_mats = modulo_catalogos.cat_buscar("materiales", "")
    assert len(all_mats) == 2

def test_ic_estilos_and_fractions():
    # Insert styles
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo("MODELO 500", "PESPUNTE", 12.50)
    assert ok

    # Insert fractions
    modulo_catalogos.ic_guardar_fraccion(estilo_id, "COSTURA LATERAL", 4.50, 1)
    modulo_catalogos.ic_guardar_fraccion(estilo_id, "COSTURA TALON", 8.00, 2)

    # List styles
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "MODELO 500"

    # Get tariffs
    tarifa = modulo_catalogos.ic_get_tarifa("MODELO 500", "PESPUNTE")
    assert tarifa["precio_par"] == 12.50
    assert len(tarifa["fracciones"]) == 2
    assert tarifa["modo"] == "FRACCIONADO"
