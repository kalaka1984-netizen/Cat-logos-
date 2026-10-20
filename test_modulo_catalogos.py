import os
import time
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
    # 1. Empty test
    estilos = mc.ic_listar_estilos()
    assert estilos == []

    # 2. Add style without fractions
    res, est1_id = mc.ic_guardar_estilo("ESTILO_A", "CORTE", 10.0, "Nota A")
    assert res is True

    # 3. Add style with fractions
    res, est2_id = mc.ic_guardar_estilo("ESTILO_B", "MONTADO", 25.0, "Nota B")
    assert res is True
    mc.ic_guardar_fraccion(est2_id, "Fraccion 1", 10.0, 1)
    mc.ic_guardar_fraccion(est2_id, "Fraccion 2", 15.0, 2)

    # List all
    lista = mc.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(lista) == 2

    # Map by id
    by_id = {item["id"]: item for item in lista}

    assert by_id[est1_id]["estilo"] == "ESTILO_A"
    assert by_id[est1_id]["n_frac"] == 0
    assert by_id[est1_id]["suma_frac"] == 0.0

    assert by_id[est2_id]["estilo"] == "ESTILO_B"
    assert by_id[est2_id]["n_frac"] == 2
    assert pytest.approx(by_id[est2_id]["suma_frac"]) == 25.0

    # Filter by department
    corte_list = mc.ic_listar_estilos(departamento="CORTE")
    assert len(corte_list) == 1
    assert corte_list[0]["estilo"] == "ESTILO_A"

    # Search term
    search_list = mc.ic_listar_estilos(buscar="Nota B")
    assert len(search_list) == 1
    assert search_list[0]["estilo"] == "ESTILO_B"


def test_ic_listar_estilos_performance_benchmark():
    # Seed 100 styles with 5 fractions each
    for i in range(100):
        _, est_id = mc.ic_guardar_estilo(f"STYLE_{i:03d}", "CORTE", 50.0)
        for j in range(5):
            mc.ic_guardar_fraccion(est_id, f"Frac_{j}", 10.0)

    # Benchmark optimized listing
    t0 = time.perf_counter()
    for _ in range(20):
        filas = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        assert len(filas) == 100
        for row in filas:
            assert row["n_frac"] == 5
            assert pytest.approx(row["suma_frac"]) == 50.0
    t1 = time.perf_counter()
    elapsed = t1 - t0

    # Ensure 20 listings of 100 items finish in less than 0.5 seconds
    assert elapsed < 0.5, f"Performance benchmark failed, took {elapsed:.4f}s"
