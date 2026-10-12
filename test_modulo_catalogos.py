import os

import pytest

import modulo_catalogos as mc

TEST_DB = "test_catalogos_temp.sqlite"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    original_db = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    mc.cat_init_db()
    mc.ic_init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    mc.CAT_DB_PATH = original_db

def test_ic_listar_estilos_pre_aggregation():
    ok, estilo1_id = mc.ic_guardar_estilo("ESTILO_A", "CORTE", 100.0)
    assert ok
    ok, _estilo2_id = mc.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 150.0)
    assert ok

    # Add fractions to estilo 1
    mc.ic_guardar_fraccion(estilo1_id, "FRAC_1", 30.0)
    mc.ic_guardar_fraccion(estilo1_id, "FRAC_2", 70.0)

    estilos = mc.ic_listar_estilos()
    assert len(estilos) == 2

    # Check estilo A
    e_a = next(e for e in estilos if e["estilo"] == "ESTILO_A")
    assert e_a["precio_par"] == 100.0
    assert e_a["n_frac"] == 2
    assert e_a["suma_frac"] == 100.0

    # Check estilo B (no fractions)
    e_b = next(e for e in estilos if e["estilo"] == "ESTILO_B")
    assert e_b["precio_par"] == 150.0
    assert e_b["n_frac"] == 0
    assert e_b["suma_frac"] == 0.0

def test_ic_listar_estilos_department_filter():
    mc.ic_guardar_estilo("ESTILO_CORTE_1", "CORTE", 50.0)
    mc.ic_guardar_estilo("ESTILO_CORTE_2", "CORTE", 60.0)
    mc.ic_guardar_estilo("ESTILO_PESPUNTE_1", "PESPUNTE", 70.0)

    corte_estilos = mc.ic_listar_estilos(departamento="CORTE")
    assert len(corte_estilos) == 2
    for e in corte_estilos:
        assert e["departamento"] == "CORTE"

    pespunte_estilos = mc.ic_listar_estilos(departamento="PESPUNTE")
    assert len(pespunte_estilos) == 1
    assert pespunte_estilos[0]["estilo"] == "ESTILO_PESPUNTE_1"
