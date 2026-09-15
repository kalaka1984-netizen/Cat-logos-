# -*- coding: utf-8 -*-
import os
import sqlite3
import pytest
import modulo_catalogos

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_catalogos_temp.sqlite"
)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Overrides CAT_DB_PATH to point to a temporary test database file."""
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", TEST_DB_PATH)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_ic_listar_estilos_aggregation():
    """Verify that ic_listar_estilos correctly aggregates n_frac and suma_frac in a single query."""
    ok, est1_id = modulo_catalogos.ic_guardar_estilo("ESTILO_A", "CORTE", 100.0)
    assert ok

    ok, est2_id = modulo_catalogos.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 150.0)
    assert ok

    # Add fractions to ESTILO_A
    modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE 1", 30.0, orden=1)
    modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE 2", 70.0, orden=2)

    # Fetch all styles
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    # Map by style ID
    est_map = {e["id"]: e for e in estilos}

    # ESTILO_A should have 2 fractions summing to 100.0
    assert est_map[est1_id]["n_frac"] == 2
    assert est_map[est1_id]["suma_frac"] == 100.0

    # ESTILO_B should have 0 fractions summing to 0.0
    assert est_map[est2_id]["n_frac"] == 0
    assert est_map[est2_id]["suma_frac"] == 0.0

def test_ic_listar_estilos_filtrado():
    """Verify department and search query filtering in ic_listar_estilos."""
    modulo_catalogos.ic_guardar_estilo("ALPHA", "CORTE", 50.0, notas="PRIMERA VUELTA")
    modulo_catalogos.ic_guardar_estilo("BETA", "PESPUNTE", 75.0, notas="SEGUNDA VUELTA")

    # Filter by department
    corte_estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(corte_estilos) == 1
    assert corte_estilos[0]["estilo"] == "ALPHA"

    # Filter by search string
    vueltas = modulo_catalogos.ic_listar_estilos(buscar="VUELTA", departamento="TODOS")
    assert len(vueltas) == 2
