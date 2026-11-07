import os
import sqlite3

import pytest

import modulo_catalogos as mc

TEST_DB = "test_catalogos_temp.sqlite"


@pytest.fixture(autouse=True)
def setup_teardown_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    mc.CAT_DB_PATH = TEST_DB
    mc.ic_init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_ic_init_db_indexes():
    """Verify that indices on estilo and departamento are created."""
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()
    cur.execute("PRAGMA index_list('ic_estilos')")
    indexes = {row[1] for row in cur.fetchall()}
    con.close()
    assert "idx_ic_estilo" in indexes
    assert "idx_ic_estilos_depto" in indexes


def test_ic_listar_estilos_pre_aggregation():
    """Verify ic_listar_estilos aggregates fractions correctly without N+1 queries."""
    # 1. Empty test
    assert mc.ic_listar_estilos() == []

    # 2. Add styles in different departments
    ok1, id1 = mc.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 120.0, "Nota A")
    ok2, _id2 = mc.ic_guardar_estilo("ESTILO_B", "CORTE", 80.0, "Nota B")
    assert ok1 and ok2

    # Styles without fractions
    estilos = mc.ic_listar_estilos()
    assert len(estilos) == 2
    # Ordered by departamento, estilo: CORTE comes before PESPUNTE
    assert estilos[0]["estilo"] == "ESTILO_B"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    assert estilos[1]["estilo"] == "ESTILO_A"
    assert estilos[1]["n_frac"] == 0
    assert estilos[1]["suma_frac"] == 0.0

    # 3. Add fractions to ESTILO_A
    mc.ic_guardar_fraccion(id1, "FRAC_1", 50.0, orden=1)
    mc.ic_guardar_fraccion(id1, "FRAC_2", 70.0, orden=2)

    estilos_after = mc.ic_listar_estilos()
    estilo_a = next(e for e in estilos_after if e["estilo"] == "ESTILO_A")
    assert estilo_a["n_frac"] == 2
    assert estilo_a["suma_frac"] == 120.0

    estilo_b = next(e for e in estilos_after if e["estilo"] == "ESTILO_B")
    assert estilo_b["n_frac"] == 0
    assert estilo_b["suma_frac"] == 0.0


def test_ic_listar_estilos_filtering():
    """Verify filtering by departamento and search string."""
    mc.ic_guardar_estilo("BOTIN_NEGRO", "PESPUNTE", 100.0, "Piel vacuna")
    mc.ic_guardar_estilo("BOTIN_CAFE", "CORTE", 90.0, "Gamuza")
    mc.ic_guardar_estilo("ZAPATO_CLASICO", "PESPUNTE", 110.0, "Charol")

    # Filter by department
    pesp = mc.ic_listar_estilos(departamento="PESPUNTE")
    assert len(pesp) == 2
    assert all(e["departamento"] == "PESPUNTE" for e in pesp)

    corte = mc.ic_listar_estilos(departamento="CORTE")
    assert len(corte) == 1
    assert corte[0]["estilo"] == "BOTIN_CAFE"

    # Filter by search string
    busq_botin = mc.ic_listar_estilos(buscar="BOTIN")
    assert len(busq_botin) == 2

    busq_gamuza = mc.ic_listar_estilos(buscar="GAMUZA")
    assert len(busq_gamuza) == 1
    assert busq_gamuza[0]["estilo"] == "BOTIN_CAFE"

    busq_dep_and_search = mc.ic_listar_estilos(buscar="BOTIN", departamento="PESPUNTE")
    assert len(busq_dep_and_search) == 1
    assert busq_dep_and_search[0]["estilo"] == "BOTIN_NEGRO"
