# -*- coding: utf-8 -*-
import os
import sys
import tempfile
from unittest.mock import MagicMock


# Set up dummy CTk and Tk mocks before importing modulo_catalogos
class DummyCTkWidget:
    def __init__(self, *args, **kwargs):
        pass


class DummyCTkFrame(DummyCTkWidget):
    pass


class DummyCTkLabel(DummyCTkWidget):
    pass


class DummyCTkButton(DummyCTkWidget):
    pass


class DummyCTkEntry(DummyCTkWidget):
    pass


class DummyCTk(DummyCTkWidget):
    pass


mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkLabel
mock_ctk.CTkButton = DummyCTkButton
mock_ctk.CTkEntry = DummyCTkEntry
mock_ctk.CTk = DummyCTk

mock_tk = MagicMock()
mock_root = MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root

sys.modules["tkinter"] = mock_tk
sys.modules["customtkinter"] = mock_ctk
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinter.ttk"] = MagicMock()

import modulo_catalogos  # noqa: E402


def setup_module(module):
    # Use temporary DB path for testing
    module.temp_db = tempfile.mktemp(suffix=".sqlite")
    modulo_catalogos.CAT_DB_PATH = module.temp_db
    modulo_catalogos.ic_init_db()


def teardown_module(module):
    if hasattr(module, "temp_db") and os.path.exists(module.temp_db):
        try:
            os.remove(module.temp_db)
        except Exception:
            pass


def test_ic_listar_estilos_aggregation():
    # Insert test style
    ok, estilo_id1 = modulo_catalogos.ic_guardar_estilo("TEST_ESTILO_1", "CORTE", 100.0)
    assert ok is True

    # Check initially 0 fractions
    estilos = modulo_catalogos.ic_listar_estilos(buscar="TEST_ESTILO_1")
    assert len(estilos) == 1
    assert estilos[0]["id"] == estilo_id1
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # Add 2 fractions to estilo_id1
    ok1, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id1, "FRAC 1", 30.0, orden=1)
    ok2, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id1, "FRAC 2", 70.0, orden=2)
    assert ok1 is True and ok2 is True

    # Verify aggregation
    estilos = modulo_catalogos.ic_listar_estilos(buscar="TEST_ESTILO_1")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 2
    assert round(estilos[0]["suma_frac"], 2) == 100.0


def test_ic_listar_estilos_filtros():
    # Insert style in another department
    ok, estilo_id2 = modulo_catalogos.ic_guardar_estilo("TEST_ESTILO_2", "PESPUNTE", 50.0)
    assert ok is True

    # Filter by department
    estilos_corte = modulo_catalogos.ic_listar_estilos(departamento="CORTE")
    assert any(e["id"] == 1 for e in estilos_corte)
    assert not any(e["id"] == estilo_id2 for e in estilos_corte)

    estilos_pespunte = modulo_catalogos.ic_listar_estilos(departamento="PESPUNTE")
    assert any(e["id"] == estilo_id2 for e in estilos_pespunte)
    assert not any(e["id"] == 1 for e in estilos_pespunte)
