import sys
import os
import sqlite3
from unittest.mock import MagicMock
import pytest

# Create Dummy CTk base classes to prevent GUI/metaclass conflicts and allow safe inheritance
class DummyCTkFrame(object):
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
    def after(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return MagicMock()
    def winfo_exists(self):
        return True

class DummyCTkToplevel(DummyCTkFrame):
    def resizable(self, *args, **kwargs):
        pass
    def grab_set(self):
        pass
    def grab_release(self):
        pass
    def destroy(self):
        pass

# Mock customtkinter module before importing modulo_catalogos
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkToplevel = DummyCTkToplevel
mock_ctk.CTkScrollableFrame = DummyCTkFrame
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkEntry = MagicMock
mock_ctk.CTkComboBox = MagicMock
mock_ctk.CTkTextbox = MagicMock
mock_ctk.CTkSegmentedButton = MagicMock
mock_ctk.CTkScrollbar = MagicMock
mock_ctk.CTkRadioButton = MagicMock
sys.modules['customtkinter'] = mock_ctk

# Mock tkinter and its scaling-related functions returning integer values
mock_tk_inst = MagicMock()
mock_tk_inst.winfo_screenwidth.return_value = 1920
mock_tk_inst.winfo_screenheight.return_value = 1080
mock_tk = MagicMock()
mock_tk.Tk.return_value = mock_tk_inst

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

import modulo_catalogos  # noqa: E402

TEST_DB_PATH = "test_catalogos_db.sqlite"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Patch CAT_DB_PATH to use our test db path
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", TEST_DB_PATH)
    # Initialize database
    modulo_catalogos.ic_init_db()
    yield
    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_ic_init_db_indexes():
    """Verifies database initialization and checks index idx_ic_estilos_depto exists."""
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [r[0] for r in cur.fetchall()]
    con.close()
    assert "idx_ic_estilo" in indexes
    assert "idx_ic_estilos_depto" in indexes

def test_ic_listar_estilos_preaggregate_and_search_bypass():
    """Verifies ic_listar_estilos pre-aggregation logic and search bypass functionality."""
    # 1. Guardar estilo
    ok, est_id = modulo_catalogos.ic_guardar_estilo("ESTILO-A", "PESPUNTE", 120.0, "Prueba A")
    assert ok is True
    assert est_id is not None

    # 2. Agregar fracciones
    ok, _ = modulo_catalogos.ic_guardar_fraccion(est_id, "OP-1", 40.0, 1)
    assert ok is True
    ok, _ = modulo_catalogos.ic_guardar_fraccion(est_id, "OP-2", 80.0, 2)
    assert ok is True

    # 3. Listar estilos - search empty (bypasses LIKE clauses)
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
    assert len(estilos) == 1
    style = estilos[0]
    assert style["estilo"] == "ESTILO-A"
    assert style["n_frac"] == 2
    assert style["suma_frac"] == 120.0

    # 4. Listar estilos - search with text
    estilos = modulo_catalogos.ic_listar_estilos(buscar="PRUEBA", departamento="TODOS")
    assert len(estilos) == 1
    style = estilos[0]
    assert style["estilo"] == "ESTILO-A"
    assert style["n_frac"] == 2
    assert style["suma_frac"] == 120.0
