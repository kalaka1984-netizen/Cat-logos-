import os
import sqlite3

import pytest

import modulo_catalogos


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    # Setup temporary database path for isolation
    temp_db = os.path.join(tmp_path, "test_catalogos_db.sqlite")
    old_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db

    # Initialize DB
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield temp_db

    # Restore original path
    modulo_catalogos.CAT_DB_PATH = old_path

def test_ic_init_db_creates_index(setup_temp_db):
    """Verifies that the database index idx_ic_estilos_depto is successfully created."""
    con = sqlite3.connect(setup_temp_db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ic_estilos'")
    indices = [r[0] for r in cur.fetchall()]
    con.close()

    assert "idx_ic_estilos_depto" in indices
    assert "idx_ic_estilo" in indices

def test_cat_guardar_uppercase_formatting():
    """Checks that string values stored via cat_guardar are automatically converted to uppercase."""
    datos = {
        "nombre": "hilo nylon",
        "tipo_material": "directo",
        "unidad_default": "dm",
        "departamento": "corte"
    }
    success, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert success is True

    # Get by id and check fields are uppercase
    row = modulo_catalogos.cat_get_by_id("materiales", reg_id)
    assert row is not None
    assert row[1] == "HILO NYLON"  # nombre column

    import json
    datos_stored = json.loads(row[2])
    assert datos_stored["tipo_material"] == "DIRECTO"
    assert datos_stored["unidad_default"] == "DM"
    assert datos_stored["departamento"] == "CORTE"

def test_cat_buscar_empty_optimization():
    """Verifies empty search string bypass for cat_buscar and exact search filters."""
    # Seed data
    modulo_catalogos.cat_guardar("materiales", {"nombre": "PIEL VACUNA", "tipo": "DIR"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "FORRO CERDO", "tipo": "DIR"})

    # Empty query (bypass LIKE)
    results = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(results) == 2
    assert results[0][1] == "FORRO CERDO"
    assert results[1][1] == "PIEL VACUNA"

    # Active only
    results_active = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
    assert len(results_active) == 2

    # Specific search query
    results_filtered = modulo_catalogos.cat_buscar("materiales", "forro", "TODOS")
    assert len(results_filtered) == 1
    assert results_filtered[0][1] == "FORRO CERDO"

def test_ic_listar_estilos_pre_aggregation():
    """Verifies style listings return correct pre-aggregated fraction count and sum total."""
    # 1. Create a style
    success_e1, est_id1 = modulo_catalogos.ic_guardar_estilo(
        estilo="BOTA VAQUERA",
        departamento="CORTE",
        precio_par=120.0,
        notas="Estilo bota clasica"
    )
    assert success_e1 is True

    # 2. Create another style (no fractions)
    success_e2, est_id2 = modulo_catalogos.ic_guardar_estilo(
        estilo="ZAPATO CASUAL",
        departamento="CORTE",
        precio_par=85.0,
        notas="Zapato de diario"
    )
    assert success_e2 is True

    # 3. Add fractions for style 1
    success_f1, _ = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=est_id1,
        nombre="CORTAR CHINELA",
        precio=12.50,
        orden=1
    )
    success_f2, _ = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=est_id1,
        nombre="CORTAR TALON",
        precio=8.25,
        orden=2
    )
    assert success_f1 is True
    assert success_f2 is True

    # 4. List styles and verify pre-aggregated fields
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos) == 2

    # Style 1 (BOTA VAQUERA) - sorted alphabetically by estilo
    bota = next(e for e in estilos if e["id"] == est_id1)
    assert bota["estilo"] == "BOTA VAQUERA"
    assert bota["n_frac"] == 2
    assert bota["suma_frac"] == 20.75  # 12.50 + 8.25

    # Style 2 (ZAPATO CASUAL)
    zapato = next(e for e in estilos if e["id"] == est_id2)
    assert zapato["estilo"] == "ZAPATO CASUAL"
    assert zapato["n_frac"] == 0
    assert zapato["suma_frac"] == 0.0  # default total aggregate for no records

def test_ic_listar_estilos_empty_optimization():
    """Verifies search bypass and department filtering for ic_listar_estilos."""
    modulo_catalogos.ic_guardar_estilo("TENIS DEPORTIVO", "MONTADO", 45.0)
    modulo_catalogos.ic_guardar_estilo("BOTA TRABAJO", "CORTE", 95.0)

    # Empty query, TODOS departments
    estilos_all = modulo_catalogos.ic_listar_estilos("", "TODOS")
    assert len(estilos_all) == 2

    # Empty query, specific department
    estilos_corte = modulo_catalogos.ic_listar_estilos("", "CORTE")
    assert len(estilos_corte) == 1
    assert estilos_corte[0]["estilo"] == "BOTA TRABAJO"

    # With query, specific department
    estilos_search = modulo_catalogos.ic_listar_estilos("TRABAJO", "CORTE")
    assert len(estilos_search) == 1
    assert estilos_search[0]["estilo"] == "BOTA TRABAJO"
