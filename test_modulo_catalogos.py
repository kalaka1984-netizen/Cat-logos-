import os
import sqlite3

import pytest

import modulo_catalogos as mc

TEST_DB = "test_catalogos_temp.sqlite"


@pytest.fixture(autouse=True)
def setup_teardown_db():
    old_db = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    mc.cat_init_db()
    mc.ic_init_db()
    yield
    mc.CAT_DB_PATH = old_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_cat_init_db_indexes():
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cur.fetchall()}
    con.close()

    assert "idx_materiales_nombre" in indexes
    assert "idx_materiales_estatus_nombre" in indexes
    assert "idx_ic_estilos_depto" in indexes


def test_cat_guardar_and_get_material_por_nombre():
    datos = {
        "nombre": "cuero vacuno",
        "unidad_default": "dm",
        "departamento": "corte",
    }
    status, registro_id = mc.cat_guardar("materiales", datos)
    assert status is True
    assert registro_id is not None

    # Verify direct lookup (returns uppercase values)
    material = mc.cat_get_material_por_nombre("cuero vacuno")
    assert material != {}
    assert material.get("nombre") == "CUERO VACUNO"
    assert material.get("unidad_default") == "DM"


def test_cat_buscar_empty_and_filtered():
    mc.cat_guardar("materiales", {"nombre": "SUELA HULE", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "HIPI DE CAJA", "estatus": "INACTIVO"})

    activos = mc.cat_buscar("materiales", "", "ACTIVO")
    assert len(activos) == 1
    assert activos[0][1] == "SUELA HULE"

    todos = mc.cat_buscar("materiales", "", "TODOS")
    assert len(todos) == 2

    busqueda = mc.cat_buscar("materiales", "SUELA", "TODOS")
    assert len(busqueda) == 1
    assert busqueda[0][1] == "SUELA HULE"


def test_ic_listar_estilos_preaggregation():
    ok_estilo, estilo_id = mc.ic_guardar_estilo("BOTA SADER", "CORTE", 120.0, "ESTILO DE PRUEBA")
    assert ok_estilo is True

    ok_f1, _ = mc.ic_guardar_fraccion(estilo_id, "CORTE PALA", 40.0, 1)
    ok_f2, _ = mc.ic_guardar_fraccion(estilo_id, "CORTE CHINELA", 80.0, 2)
    assert ok_f1 is True and ok_f2 is True

    estilos = mc.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos) == 1
    estilo = estilos[0]
    assert estilo["estilo"] == "BOTA SADER"
    assert estilo["precio_par"] == 120.0
    assert estilo["n_frac"] == 2
    assert abs(estilo["suma_frac"] - 120.0) < 1e-4

    # Test tarifa API
    tarifa = mc.ic_get_tarifa("BOTA SADER", "CORTE")
    assert tarifa["precio_par"] == 120.0
    assert tarifa["modo"] == "FRACCIONADO"
    assert len(tarifa["fracciones"]) == 2
