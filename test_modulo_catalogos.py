import os
import sys
import tempfile
import time
from unittest.mock import MagicMock

import pytest

# Inject dummy customtkinter if needed
try:
    import customtkinter  # noqa: F401
except ImportError:
    mock_ctk = MagicMock()
    sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


@pytest.fixture(autouse=True)
def setup_temp_db():
    # Setup temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        temp_db = tmp.name

    old_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db
    modulo_catalogos.cat_init_db()

    yield temp_db

    modulo_catalogos.CAT_DB_PATH = old_db
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
        except OSError:
            pass


def test_cat_guardar_and_get_material_por_nombre():
    datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
        "estatus": "ACTIVO"
    }
    ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok is True
    assert isinstance(mat_id, int)

    res = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
    assert res.get("nombre") == "CUERO VACUNO"
    assert res.get("unidad_default") == "DM"
    assert res.get("tipo_material") == "DIRECTO"

    # Non-existent material
    empty = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
    assert empty == {}


def test_cat_buscar_empty_query():
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT C", "estatus": "ACTIVO"})

    activos = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
    nombres_activos = [r[1] for r in activos]
    assert nombres_activos == ["MAT A", "MAT C"]

    todos = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    nombres_todos = [r[1] for r in todos]
    assert nombres_todos == ["MAT A", "MAT B", "MAT C"]


def test_cat_get_nombres():
    modulo_catalogos.cat_guardar("materiales", {"nombre": "ZAPATO A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "ZAPATO B", "estatus": "INACTIVO"})

    mats_activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert mats_activos == ["ZAPATO A"]

    mats_todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert mats_todos == ["ZAPATO A", "ZAPATO B"]


def test_cat_precarga_material():
    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    })

    precarga = modulo_catalogos.cat_precarga_material("cuero vacuno")
    assert precarga["tipo_ft"] == "DIR"
    assert precarga["unidad"] == "DM"
    assert precarga["departamento"] == "CORTE"
    assert precarga["monitor"] is True
    assert precarga["principal"] is True

    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "HILO NYLON",
        "tipo_material": "INDIRECTO",
        "unidad_default": "MTS",
        "departamento": "PESPUNTE",
        "visible_monitor": "NO",
        "es_principal": "NO"
    })

    precarga_ind = modulo_catalogos.cat_precarga_material("hilo nylon")
    assert precarga_ind["tipo_ft"] == "IND"


def test_performance_direct_lookup():
    # Insert multiple items
    for i in range(100):
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": f"MAT_{i:04d}",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "notas": "TESTING PERFORMANCE " * 5
        })

    t0 = time.perf_counter()
    for _ in range(50):
        res = modulo_catalogos.cat_get_material_por_nombre("MAT_0050")
        assert res.get("nombre") == "MAT_0050"
    t1 = time.perf_counter()

    elapsed = (t1 - t0) / 50
    # Lookup should be under 2 milliseconds per call
    assert elapsed < 0.002
