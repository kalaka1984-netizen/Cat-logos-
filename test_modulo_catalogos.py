import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

# Set up mock tkinter & customtkinter prior to importing application code
mock_tk = MagicMock()
mock_root = MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root


class DummyCTkWidget:
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

    def bind(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []


mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkWidget
mock_ctk.CTkLabel = DummyCTkWidget
mock_ctk.CTkButton = DummyCTkWidget
mock_ctk.CTkEntry = DummyCTkWidget
mock_ctk.CTkTabview = DummyCTkWidget
mock_ctk.CTkOptionMenu = DummyCTkWidget
mock_ctk.CTk = MagicMock

sys.modules["tkinter"] = mock_tk
sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", db_path)
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_index_creation(temp_db):
    con = sqlite3.connect(temp_db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [r[0] for r in cur.fetchall()]
    con.close()

    assert "idx_ic_estilos_depto" in indexes
    assert "idx_ic_estilo" in indexes
    assert "idx_ic_frac_estilo" in indexes


def test_ic_listar_estilos_pre_aggregation(temp_db):
    ok1, est_id1 = modulo_catalogos.ic_guardar_estilo("BOTIN_01", "CORTE", 25.0, "Nota 1")
    assert ok1 is True
    ok2, est_id2 = modulo_catalogos.ic_guardar_estilo("BOTIN_02", "PESPUNTE", 30.0, "Nota 2")
    assert ok2 is True

    # Add fractions for est_id1
    modulo_catalogos.ic_guardar_fraccion(est_id1, "CORTE CAPELLADA", 10.0, 1)
    modulo_catalogos.ic_guardar_fraccion(est_id1, "CORTE CHINELA", 15.0, 2)

    # Fetch all styles
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    e1 = next(e for e in estilos if e["id"] == est_id1)
    e2 = next(e for e in estilos if e["id"] == est_id2)

    assert e1["n_frac"] == 2
    assert abs(e1["suma_frac"] - 25.0) < 1e-4

    assert e2["n_frac"] == 0
    assert abs(e2["suma_frac"] - 0.0) < 1e-4

    # Test filtering by department
    estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos_corte) == 1
    assert estilos_corte[0]["estilo"] == "BOTIN_01"
    assert estilos_corte[0]["n_frac"] == 2
    assert abs(estilos_corte[0]["suma_frac"] - 25.0) < 1e-4

    estilos_pespunte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
    assert len(estilos_pespunte) == 1
    assert estilos_pespunte[0]["estilo"] == "BOTIN_02"
    assert estilos_pespunte[0]["n_frac"] == 0
    assert abs(estilos_pespunte[0]["suma_frac"] - 0.0) < 1e-4
