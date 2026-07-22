import os
import sys
import json
import sqlite3
import pytest
from unittest import mock

# Mocking customtkinter and tkinter to avoid GUI and metaclass conflicts in headless environments.
class DummyCTkFrame:
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
    def configure(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return self

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs):
        pass

mock_ctk = mock.MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkToplevel = DummyCTkToplevel

mock_tk = mock.MagicMock()
mock_tk_instance = mock.MagicMock()
mock_tk_instance.winfo_screenwidth.return_value = 1920
mock_tk_instance.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_instance

sys.modules['tkinter'] = mock_tk
sys.modules['customtkinter'] = mock_ctk

# Import the module under test
import modulo_catalogos

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Store the original DB path
    orig_db_path = modulo_catalogos.CAT_DB_PATH

    # Use a temporary database file
    test_db_path = "test_catalogos_db.sqlite"
    modulo_catalogos.CAT_DB_PATH = test_db_path

    # Initialize the database
    modulo_catalogos.cat_init_db()

    yield

    # Clean up test database file if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Restore original path
    modulo_catalogos.CAT_DB_PATH = orig_db_path

def test_cat_get_material_por_nombre_success():
    # Insert dummy material data
    material_data = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }

    # Save the material using cat_guardar
    success, reg_id = modulo_catalogos.cat_guardar("materiales", material_data)
    assert success is True

    # Query the material by name
    res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert res != {}
    assert res.get("nombre") == "CUERO VACUNO"
    assert res.get("unidad_default") == "DM"

    # Query with leading/trailing spaces and lowercase
    res_mixed = modulo_catalogos.cat_get_material_por_nombre("  cuero vacuno  ")
    assert res_mixed != {}
    assert res_mixed.get("nombre") == "CUERO VACUNO"

def test_cat_get_material_por_nombre_not_found():
    # Query a non-existent material
    res = modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT")
    assert res == {}

def test_cat_get_material_por_nombre_empty():
    # Query with empty / space-only strings
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}
    assert modulo_catalogos.cat_get_material_por_nombre("   ") == {}
