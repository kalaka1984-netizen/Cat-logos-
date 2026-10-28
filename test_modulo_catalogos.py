"""
Unit tests for optimized functions in modulo_catalogos.py.
Tests cat_get_material_por_nombre, _cat_get_nombres_tabla, cat_get_nombres_*, and cat_buscar.
"""

import os
import tempfile

import pytest

import modulo_catalogos as mc

TEMP_DB = os.path.join(tempfile.gettempdir(), "test_catalogos_temp.sqlite")

@pytest.fixture(autouse=True)
def setup_teardown_db():
    # Save original DB path
    orig_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEMP_DB

    # Initialize clean DB
    if os.path.exists(TEMP_DB):
        os.remove(TEMP_DB)
    mc.cat_init_db()

    yield

    # Clean up temp DB and restore original path
    if os.path.exists(TEMP_DB):
        os.remove(TEMP_DB)
    mc.CAT_DB_PATH = orig_path

def test_cat_guardar_y_get_material_por_nombre():
    datos = {
        "nombre": "PIEL VACUNO",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "proveedor_ref": "PROV_A",
        "costo_ref": 150.0,
        "notas": "Piel para corte"
    }
    ok, mat_id = mc.cat_guardar("materiales", datos)
    assert ok is True
    assert mat_id is not None

    # Retrieve by name
    res = mc.cat_get_material_por_nombre("PIEL VACUNO")
    assert res.get("nombre") == "PIEL VACUNO"
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Non-existent material
    res_none = mc.cat_get_material_por_nombre("INEXISTENTE")
    assert res_none == {}

def test_cat_get_nombres_and_helper():
    mc.cat_guardar("materiales", {"nombre": "SUELA CAUCHO", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "HILO NYLON", "estatus": "INACTIVO"})
    mc.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR 1", "estatus": "ACTIVO"})
    mc.cat_guardar("clientes", {"nombre": "CLIENTE X", "estatus": "ACTIVO"})

    # Test _cat_get_nombres_tabla with active filter
    active_mats = mc._cat_get_nombres_tabla("materiales", solo_activos=True)
    assert "SUELA CAUCHO" in active_mats
    assert "HILO NYLON" not in active_mats

    # Test _cat_get_nombres_tabla without active filter
    all_mats = mc._cat_get_nombres_tabla("materiales", solo_activos=False)
    assert "SUELA CAUCHO" in all_mats
    assert "HILO NYLON" in all_mats

    # Test invalid table in helper
    invalid_res = mc._cat_get_nombres_tabla("tabla_falsa")
    assert invalid_res == []

    # Test public getter functions
    assert mc.cat_get_nombres_materiales(solo_activos=True) == ["SUELA CAUCHO"]
    assert mc.cat_get_nombres_trabajadores(solo_activos=True) == ["JUAN PEREZ"]
    assert mc.cat_get_nombres_proveedores(solo_activos=True) == ["PROVEEDOR 1"]
    assert mc.cat_get_nombres_clientes(solo_activos=True) == ["CLIENTE X"]

def test_cat_buscar_optimization():
    mc.cat_guardar("materiales", {"nombre": "FORRO CERDO", "notas": "Color negro", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "CASCO PLASTICO", "notas": "Talla M", "estatus": "INACTIVO"})

    # Empty text, ALL status
    all_rows = mc.cat_buscar("materiales", texto="", estatus="TODOS")
    assert len(all_rows) == 2

    # Empty text, ACTIVO status
    active_rows = mc.cat_buscar("materiales", texto="", estatus="ACTIVO")
    assert len(active_rows) == 1
    assert active_rows[0][1] == "FORRO CERDO"

    # Search with text in JSON or name
    searched_rows = mc.cat_buscar("materiales", texto="negro", estatus="TODOS")
    assert len(searched_rows) == 1
    assert searched_rows[0][1] == "FORRO CERDO"
