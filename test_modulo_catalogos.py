# -*- coding: utf-8 -*-
"""
Tests unitarios para modulo_catalogos.py
Verifica la optimización SQL de ic_listar_estilos (pre-agregación y eliminación de N+1 queries).
"""

import os
import sqlite3
import pytest
import modulo_catalogos as mc

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_catalogos_temp.sqlite"
)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Configura una base de datos temporal para los tests y la limpia al finalizar."""
    original_db = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB_PATH

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    mc.cat_init_db()
    mc.ic_init_db()

    yield

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    mc.CAT_DB_PATH = original_db


def test_ic_listar_estilos_pre_aggregation():
    """Verifica que ic_listar_estilos retorne pre-agregaciones n_frac y suma_frac correctamente."""
    # Guardar estilo A con 2 fracciones
    ok, est1_id = mc.ic_guardar_estilo("ESTILO_001", "PESPUNTE", 100.0, "Nota A")
    assert ok is True
    mc.ic_guardar_fraccion(est1_id, "COSTURA_1", 35.0, 1)
    mc.ic_guardar_fraccion(est1_id, "COSTURA_2", 65.0, 2)

    # Guardar estilo B sin fracciones
    ok, est2_id = mc.ic_guardar_estilo("ESTILO_002", "CORTE", 45.0, "Nota B")
    assert ok is True

    # Consultar todos los estilos
    estilos = mc.ic_listar_estilos("", "TODOS")
    assert len(estilos) == 2

    # Map por id
    mapa = {e["id"]: e for e in estilos}

    # Verificar pre-agregación para estilo 1
    row1 = mapa[est1_id]
    assert row1["estilo"] == "ESTILO_001"
    assert row1["departamento"] == "PESPUNTE"
    assert row1["precio_par"] == 100.0
    assert row1["n_frac"] == 2
    assert pytest.approx(row1["suma_frac"]) == 100.0

    # Verificar pre-agregación para estilo 2 (sin fracciones)
    row2 = mapa[est2_id]
    assert row2["estilo"] == "ESTILO_002"
    assert row2["departamento"] == "CORTE"
    assert row2["precio_par"] == 45.0
    assert row2["n_frac"] == 0
    assert row2["suma_frac"] == 0.0


def test_ic_listar_estilos_filtrado_departamento():
    """Verifica el filtrado por departamento usando el índice idx_ic_estilos_depto."""
    mc.ic_guardar_estilo("ESTILO_PESP", "PESPUNTE", 80.0)
    mc.ic_guardar_estilo("ESTILO_CORT", "CORTE", 50.0)

    res_pesp = mc.ic_listar_estilos("", "PESPUNTE")
    assert len(res_pesp) == 1
    assert res_pesp[0]["estilo"] == "ESTILO_PESP"

    res_cort = mc.ic_listar_estilos("", "CORTE")
    assert len(res_cort) == 1
    assert res_cort[0]["estilo"] == "ESTILO_CORT"


def test_ic_index_created():
    """Verifica que el índice idx_ic_estilos_depto existe en la base de datos."""
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_ic_estilos_depto'")
    idx = cur.fetchone()
    con.close()
    assert idx is not None
