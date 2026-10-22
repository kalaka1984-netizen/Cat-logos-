import os
import sqlite3
import pytest
import modulo_catalogos as mc

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    db_file = tmp_path / "test_catalogos.sqlite"
    old_db_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = str(db_file)
    mc.cat_init_db()
    yield db_file
    mc.CAT_DB_PATH = old_db_path


def test_cat_get_nombres_tabla():
    # Insert materials
    mc.cat_guardar("materiales", {"nombre": "Piel Vacuno", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "Hilo Nylon", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "Suela Goma Obsoleta", "estatus": "INACTIVO"})

    activos = mc.cat_get_nombres_materiales(solo_activos=True)
    todos = mc.cat_get_nombres_materiales(solo_activos=False)

    assert activos == ["HILO NYLON", "PIEL VACUNO"]
    assert todos == ["HILO NYLON", "PIEL VACUNO", "SUELA GOMA OBSOLETA"]


def test_cat_get_material_por_nombre():
    mc.cat_guardar("materiales", {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    })

    mat = mc.cat_get_material_por_nombre("CUERO VACUNO")
    assert mat.get("nombre") == "CUERO VACUNO"
    assert mat.get("tipo_material") == "DIRECTO"
    assert mat.get("unidad_default") == "DM"

    precarga = mc.cat_precarga_material("CUERO VACUNO")
    assert precarga["tipo_ft"] == "DIR"
    assert precarga["unidad"] == "DM"
    assert precarga["monitor"] is True

    non_existent = mc.cat_get_material_por_nombre("NON_EXISTENT")
    assert non_existent == {}


def test_cat_buscar_empty_text():
    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR A", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR B", "estatus": "INACTIVO"})

    res_activos = mc.cat_buscar("proveedores", "", "ACTIVO")
    assert len(res_activos) == 1
    assert res_activos[0][1] == "PROVEEDOR A"

    res_todos = mc.cat_buscar("proveedores", "  ", "TODOS")
    assert len(res_todos) == 2


def test_cat_get_nombres_invalid_tabla():
    assert mc._cat_get_nombres_tabla("invalid_table") == []
