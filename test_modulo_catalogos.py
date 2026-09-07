import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest


# Mock GUI components before importing modulo_catalogos
class DummyCTkFrame:
    def __init__(self, *args, **kwargs): pass

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs): pass

ctk_mock = MagicMock()
ctk_mock.CTkFrame = DummyCTkFrame
ctk_mock.CTkToplevel = DummyCTkToplevel
sys.modules['customtkinter'] = ctk_mock

tk_mock = MagicMock()
mock_tk_inst = MagicMock()
mock_tk_inst.winfo_screenwidth.return_value = 1920
mock_tk_inst.winfo_screenheight.return_value = 1080
tk_mock.Tk.return_value = mock_tk_inst
sys.modules['tkinter'] = tk_mock
sys.modules['tkinter.ttk'] = MagicMock()

import modulo_catalogos as mc


@pytest.fixture(autouse=True)
def setup_temp_db():
    temp_db = tempfile.mktemp(suffix=".sqlite")
    original_db = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = temp_db
    mc.ic_init_db()
    yield temp_db
    mc.CAT_DB_PATH = original_db
    if os.path.exists(temp_db):
        os.remove(temp_db)

def test_ic_init_db():
    assert os.path.exists(mc.CAT_DB_PATH)

def test_ic_listar_estilos_pre_aggregation():
    # Insert test estilo
    ok, estilo_id = mc.ic_guardar_estilo("ESTILO_TEST", "CORTE", 100.0)
    assert ok is True

    # Insert test fracciones
    ok1, _ = mc.ic_guardar_fraccion(estilo_id, "FRAC_1", 30.0, 1)
    ok2, _ = mc.ic_guardar_fraccion(estilo_id, "FRAC_2", 70.0, 2)
    assert ok1 is True
    assert ok2 is True

    estilos = mc.ic_listar_estilos()
    assert len(estilos) == 1
    est = estilos[0]
    assert est["estilo"] == "ESTILO_TEST"
    assert est["departamento"] == "CORTE"
    assert est["precio_par"] == 100.0
    assert est["n_frac"] == 2
    assert est["suma_frac"] == 100.0

def test_ic_listar_estilos_without_fracciones():
    ok, _estilo_id = mc.ic_guardar_estilo("ESTILO_NO_FRAC", "PESPUNTE", 50.0)
    assert ok is True

    estilos = mc.ic_listar_estilos()
    assert len(estilos) == 1
    est = estilos[0]
    assert est["estilo"] == "ESTILO_NO_FRAC"
    assert est["n_frac"] == 0
    assert est["suma_frac"] == 0.0
