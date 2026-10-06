import os

import pytest

import modulo_catalogos as mc

TEST_DB = "test_catalogos_temp.sqlite"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    mc.CAT_DB_PATH = TEST_DB
    mc.cat_init_db()
    mc.ic_init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_cat_buscar_and_material_lookup():
    # Insert materials
    m1 = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    m2 = {
        "nombre": "PEGAMENTO AMARILLO",
        "tipo_material": "INDIRECTO",
        "unidad_default": "LTS",
        "departamento": "MONTADO",
        "visible_monitor": "NO",
        "es_principal": "NO"
    }
    mc.cat_guardar("materiales", m1)
    mc.cat_guardar("materiales", m2)

    # Test cat_buscar with empty text
    todos = mc.cat_buscar("materiales", "", "TODOS")
    assert len(todos) == 2
    assert todos[0][1] == "CUERO VACUNO"
    assert todos[1][1] == "PEGAMENTO AMARILLO"

    # Test cat_get_material_por_nombre
    res_m1 = mc.cat_get_material_por_nombre("CUERO VACUNO")
    assert res_m1["nombre"] == "CUERO VACUNO"
    assert res_m1["tipo_material"] == "DIRECTO"

    res_m2 = mc.cat_get_material_por_nombre("PEGAMENTO AMARILLO")
    assert res_m2["nombre"] == "PEGAMENTO AMARILLO"
    assert res_m2["tipo_material"] == "INDIRECTO"

    assert mc.cat_get_material_por_nombre("NONEXISTENT") == {}

def test_cat_precarga_material():
    m1 = {
        "nombre": "PIEL NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    m2 = {
        "nombre": "HILO NYLON",
        "tipo_material": "INDIRECTO",
        "unidad_default": "MTS",
        "departamento": "PESPUNTE",
        "visible_monitor": "NO",
        "es_principal": "NO"
    }
    mc.cat_guardar("materiales", m1)
    mc.cat_guardar("materiales", m2)

    prec_m1 = mc.cat_precarga_material("PIEL NEGRA")
    assert prec_m1["tipo_ft"] == "DIR"
    assert prec_m1["unidad"] == "DM"
    assert prec_m1["departamento"] == "CORTE"
    assert prec_m1["monitor"] is True
    assert prec_m1["principal"] is True

    prec_m2 = mc.cat_precarga_material("HILO NYLON")
    assert prec_m2["tipo_ft"] == "IND"
    assert prec_m2["unidad"] == "MTS"
    assert prec_m2["departamento"] == "PESPUNTE"
    assert prec_m2["monitor"] is False
    assert prec_m2["principal"] is False

def test_ic_listar_estilos_pre_aggregation():
    # Save a style
    status, est_id = mc.ic_guardar_estilo("ESTILO 101", "PESPUNTE", 25.50, "MOCASIN")
    assert status is True

    # Add fractions
    mc.ic_guardar_fraccion(est_id, "CORTE DE PIEL", 10.00, 1)
    mc.ic_guardar_fraccion(est_id, "PESPUNTE LATERAL", 15.50, 2)

    # Save another style without fractions
    status2, _ = mc.ic_guardar_estilo("ESTILO 102", "CORTE", 30.00, "BOTIN")
    assert status2 is True

    # List styles
    estilos = mc.ic_listar_estilos("", "TODOS")
    assert len(estilos) == 2

    e102 = next(e for e in estilos if e["estilo"] == "ESTILO 102")
    assert e102["n_frac"] == 0
    assert e102["suma_frac"] == 0.0

    e101 = next(e for e in estilos if e["estilo"] == "ESTILO 101")
    assert e101["n_frac"] == 2
    assert e101["suma_frac"] == 25.50

    # Test department filter
    pespunte_estilos = mc.ic_listar_estilos("", "PESPUNTE")
    assert len(pespunte_estilos) == 1
    assert pespunte_estilos[0]["estilo"] == "ESTILO 101"

    # Test search query
    search_estilos = mc.ic_listar_estilos("BOTIN", "TODOS")
    assert len(search_estilos) == 1
    assert search_estilos[0]["estilo"] == "ESTILO 102"
