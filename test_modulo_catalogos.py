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

    assert "idx_materiales_estatus_nombre" in indexes
    assert "idx_trabajadores_estatus_nombre" in indexes
    assert "idx_proveedores_estatus_nombre" in indexes
    assert "idx_clientes_estatus_nombre" in indexes
    assert "idx_ic_estilos_depto" in indexes


def test_cat_get_nombres_and_get_by_name(temp_db):
    mat_data1 = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
        "estatus": "ACTIVO",
    }
    mat_data2 = {
        "nombre": "HILO PESPUNTE",
        "tipo_material": "INDIRECTO",
        "unidad_default": "mts",
        "departamento": "PESPUNTE",
        "visible_monitor": "NO",
        "es_principal": "NO",
        "estatus": "INACTIVO",
    }
    modulo_catalogos.cat_guardar("materiales", mat_data1)
    modulo_catalogos.cat_guardar("materiales", mat_data2)

    # Test cat_get_nombres_materiales
    activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)

    assert "CUERO VACUNO" in activos
    assert "HILO PESPUNTE" not in activos
    assert "CUERO VACUNO" in todos
    assert "HILO PESPUNTE" in todos

    # Test cat_get_material_por_nombre
    ret1 = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert ret1.get("tipo_material") == "DIRECTO"
    assert ret1.get("unidad_default") == "DM"

    ret_nonexistent = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
    assert ret_nonexistent == {}


def test_cat_precarga_material(temp_db):
    mat_data = {
        "nombre": "PIEL OVAL",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
        "estatus": "ACTIVO",
    }
    modulo_catalogos.cat_guardar("materiales", mat_data)

    precarga = modulo_catalogos.cat_precarga_material("PIEL OVAL")
    assert precarga.get("tipo_ft") == "DIR"
    assert precarga.get("unidad") == "DM"
    assert precarga.get("departamento") == "CORTE"
    assert precarga.get("monitor") is True
    assert precarga.get("principal") is True


def test_ic_listar_estilos_pre_aggregation(temp_db):
    ok1, est_id1 = modulo_catalogos.ic_guardar_estilo("BOTIN_01", "CORTE", 25.0, "Nota 1")
    assert ok1 is True
    ok2, est_id2 = modulo_catalogos.ic_guardar_estilo("BOTIN_02", "PESPUNTE", 30.0, "Nota 2")
    assert ok2 is True

    # Add fractions for est_id1
    modulo_catalogos.ic_guardar_fraccion(est_id1, "CORTE CAPELLADA", 10.0, 1)
    modulo_catalogos.ic_guardar_fraccion(est_id1, "CORTE CHINELA", 15.0, 2)

    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    e1 = next(e for e in estilos if e["id"] == est_id1)
    e2 = next(e for e in estilos if e["id"] == est_id2)

    assert e1["n_frac"] == 2
    assert abs(e1["suma_frac"] - 25.0) < 1e-4

    assert e2["n_frac"] == 0
    assert abs(e2["suma_frac"] - 0.0) < 1e-4


def test_cat_buscar_empty_and_text(temp_db):
    trab1 = {"nombre": "JUAN PEREZ", "departamento": "CORTE", "estatus": "ACTIVO"}
    trab2 = {"nombre": "MARIA GOMEZ", "departamento": "PESPUNTE", "estatus": "INACTIVO"}
    modulo_catalogos.cat_guardar("trabajadores", trab1)
    modulo_catalogos.cat_guardar("trabajadores", trab2)

    # Search empty text
    rows_all = modulo_catalogos.cat_buscar("trabajadores", "", "TODOS")
    assert len(rows_all) == 2

    rows_active = modulo_catalogos.cat_buscar("trabajadores", "", "ACTIVO")
    assert len(rows_active) == 1
    assert rows_active[0][1] == "JUAN PEREZ"

    # Search with text filter
    rows_filter = modulo_catalogos.cat_buscar("trabajadores", "MARIA", "TODOS")
    assert len(rows_filter) == 1
    assert rows_filter[0][1] == "MARIA GOMEZ"
