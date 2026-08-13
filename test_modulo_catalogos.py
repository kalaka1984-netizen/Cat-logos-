import os
import sqlite3
import sys
from unittest.mock import MagicMock

import pytest


# 1. Mock customtkinter to avoid GUI issues in headless environment
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def winfo_exists(self):
        return True
    def winfo_children(self):
        return []

class MockCTk(DummyWidget):
    pass

class MockCTkFrame(DummyWidget):
    pass

class MockCTkLabel(DummyWidget):
    pass

class MockCTkButton(DummyWidget):
    pass

class MockCTkScrollableFrame(DummyWidget):
    pass

class MockCTkEntry(DummyWidget):
    pass

class MockCTkComboBox(DummyWidget):
    pass

class MockCTkTextbox(DummyWidget):
    pass

class MockCTkSegmentedButton(DummyWidget):
    pass

class MockCTkScrollbar(DummyWidget):
    pass

class MockCTkToplevel(DummyWidget):
    pass

mock_ctk = MagicMock()
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkFrame
mock_ctk.CTkLabel = MockCTkLabel
mock_ctk.CTkButton = MockCTkButton
mock_ctk.CTkScrollableFrame = MockCTkScrollableFrame
mock_ctk.CTkEntry = MockCTkEntry
mock_ctk.CTkComboBox = MockCTkComboBox
mock_ctk.CTkTextbox = MockCTkTextbox
mock_ctk.CTkSegmentedButton = MockCTkSegmentedButton
mock_ctk.CTkScrollbar = MockCTkScrollbar
mock_ctk.CTkToplevel = MockCTkToplevel

mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()

sys.modules['customtkinter'] = mock_ctk

# 2. Setup the temporary database for isolated testing
TEMP_DB_PATH = "test_catalogos_db.sqlite"
if os.path.exists(TEMP_DB_PATH):
    os.remove(TEMP_DB_PATH)

import modulo_catalogos

modulo_catalogos.CAT_DB_PATH = TEMP_DB_PATH

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Initialize DB before each test
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()
    yield
    # Clean up DB file after each test
    if os.path.exists(TEMP_DB_PATH):
        try:
            os.remove(TEMP_DB_PATH)
        except OSError:
            pass

def test_ic_init_db():
    # Verify that tables exist
    con = sqlite3.connect(TEMP_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    con.close()

    assert "ic_config" in tables
    assert "ic_estilos" in tables
    assert "ic_fracciones" in tables

def test_ic_guardar_and_listar_estilos():
    # Save a style
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo(
        estilo="ESTILO_A",
        departamento="PESPUNTE",
        precio_par=15.50,
        notas="TEST NOTAS"
    )
    assert ok is True
    assert isinstance(estilo_id, int)

    # List styles
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_A", departamento="PESPUNTE")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "ESTILO_A"
    assert estilos[0]["departamento"] == "PESPUNTE"
    assert estilos[0]["precio_par"] == 15.50
    assert estilos[0]["notas"] == "TEST NOTAS"

def test_ic_guardar_fraccion_and_aggregates():
    # Save style
    ok_est, estilo_id = modulo_catalogos.ic_guardar_estilo(
        estilo="ESTILO_B",
        departamento="PESPUNTE",
        precio_par=50.00
    )
    assert ok_est is True

    # Save fractions
    ok_frac1, _msg1 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="COSTURA COPETE",
        precio=12.50,
        orden=1
    )
    assert ok_frac1 is True

    ok_frac2, _msg2 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="COSTURA TALÓN",
        precio=17.50,
        orden=2
    )
    assert ok_frac2 is True

    # Verify fractions are listed correctly via ic_listar_fracciones
    fracciones = modulo_catalogos.ic_listar_fracciones(estilo_id)
    assert len(fracciones) == 2
    assert fracciones[0]["nombre"] == "COSTURA COPETE"
    assert fracciones[0]["precio"] == 12.50
    assert fracciones[1]["nombre"] == "COSTURA TALÓN"
    assert fracciones[1]["precio"] == 17.50

    # Verify that ic_listar_estilos returns aggregated fraction counts and sums correctly
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_B")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 30.00
