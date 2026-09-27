import os
import sys
import time
from unittest.mock import MagicMock

# Set up dummy customtkinter / tkinter in sys.modules before importing modulo_catalogos if needed
if "customtkinter" not in sys.modules:
    dummy_ctk = MagicMock()
    class DummyFrame:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def grid(self, *args, **kwargs): pass
        def winfo_children(self): return []
        def after(self, *args, **kwargs): return "timer_1"
        def after_cancel(self, *args, **kwargs): pass
    dummy_ctk.CTkFrame = DummyFrame
    dummy_ctk.CTk = DummyFrame
    dummy_ctk.CTkLabel = DummyFrame
    dummy_ctk.CTkButton = DummyFrame
    dummy_ctk.CTkEntry = DummyFrame
    sys.modules["customtkinter"] = dummy_ctk

import pytest

import modulo_catalogos


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_catalogos_temp.sqlite")
    old_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = db_file
    modulo_catalogos.cat_init_db()
    yield db_file
    modulo_catalogos.CAT_DB_PATH = old_db_path


def test_cat_guardar_y_get_material_por_nombre(temp_db):
    datos_mat = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    success, res_id = modulo_catalogos.cat_guardar("materiales", datos_mat)
    assert success is True
    assert isinstance(res_id, int)

    res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert res.get("NOMBRE") == "CUERO VACUNO" or res.get("nombre") == "CUERO VACUNO"
    assert res.get("TIPO_MATERIAL") == "DIRECTO" or res.get("tipo_material") == "DIRECTO"

    # Test non-existent lookup returns empty dict
    assert modulo_catalogos.cat_get_material_por_nombre("NO_EXISTE") == {}


def test_cat_buscar_empty_and_filtered(temp_db):
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA 1", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA 2", "estatus": "INACTIVO"})

    # Empty search query
    activos = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
    assert len(activos) == 1
    assert activos[0][1] == "SUELA 1"

    todos = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(todos) == 2

    # Search query
    filtered = modulo_catalogos.cat_buscar("materiales", "SUELA 2", "TODOS")
    assert len(filtered) == 1
    assert filtered[0][1] == "SUELA 2"


def test_cat_get_nombres_helper(temp_db):
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})

    nombres_activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert nombres_activos == ["MAT A"]

    nombres_todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert nombres_todos == ["MAT A", "MAT B"]


def test_performance_direct_lookup(temp_db):
    # Populate DB with 500 records
    for i in range(500):
        nombre = f"MATERIAL_{i:04d}"
        datos = {
            "nombre": nombre,
            "tipo_material": "DIRECTO" if i % 2 == 0 else "INDIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "notas": "Texto de prueba " * 10
        }
        modulo_catalogos.cat_guardar("materiales", datos)

    # Measure lookup speed
    t0 = time.perf_counter()
    for _ in range(100):
        res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_0250")
        assert res.get("NOMBRE") == "MATERIAL_0250" or res.get("nombre") == "MATERIAL_0250"
    t1 = time.perf_counter()

    elapsed = t1 - t0
    # 100 lookups should take well under 0.1 seconds with indexed direct SELECT
    assert elapsed < 0.2
