import os
import sqlite3

import pytest

import modulo_catalogos

# Use a clean test database file for testing
TEST_DB = "test_catalogos_db.sqlite"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Fixture to redirect the database path to a test database and initialize it."""
    # Override CAT_DB_PATH with the test database path
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", TEST_DB)

    # Remove existing test DB if any
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

    # Initialize the tables and indexes
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    # Clean up test DB after each test
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

def test_database_initialization_and_indexes():
    """Verify that tables and crucial performance indexes are created properly."""
    assert os.path.exists(TEST_DB)

    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()

    # Check that indices exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cur.fetchall()]

    # Verify that the new department index exists on ic_estilos
    assert "idx_ic_estilos_depto" in indexes
    assert "idx_ic_estilo" in indexes
    assert "idx_materiales_nombre" in indexes

    con.close()

def test_cat_get_material_por_nombre_direct_select():
    """Verify that cat_get_material_por_nombre fetches correct material data directly."""
    # Guardar un material en el catálogo
    material_data = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "proveedor_ref": "PROV-A",
        "costo_ref": 150.0,
        "notas": "Piel premium"
    }

    ok, reg_id = modulo_catalogos.cat_guardar("materiales", material_data)
    assert ok is True
    assert reg_id is not None

    # Fetch material by name
    fetched = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert fetched != {}
    assert fetched["nombre"] == "CUERO VACUNO"
    assert fetched["tipo_material"] == "DIRECTO"
    assert fetched["unidad_default"] == "DM"
    assert fetched["costo_ref"] == 150.0

    # Non-existent material should return empty dict
    non_existent = modulo_catalogos.cat_get_material_por_nombre("NONEXISTENT")
    assert non_existent == {}

def test_ic_listar_estilos_pre_aggregation():
    """Verify that ic_listar_estilos returns correct pre-aggregated fraction count and sum."""
    # 1. Guardar un estilo
    ok_estilo, estilo_id = modulo_catalogos.ic_guardar_estilo(
        estilo="BOTA VAQUERA",
        departamento="PESPUNTE",
        precio_par=120.0,
        notas="Estilo invierno"
    )
    assert ok_estilo is True
    assert estilo_id is not None

    # Verify pre-aggregation values with no fractions
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "BOTA VAQUERA"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # 2. Guardar fracciones
    ok_frac1, _ = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="CORTAR CORREA",
        precio=15.50,
        orden=1
    )
    ok_frac2, _ = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="COSIDO LATERAL",
        precio=25.00,
        orden=2
    )
    assert ok_frac1 is True
    assert ok_frac2 is True

    # Verify pre-aggregation matches count and total sum of prices
    estilos_aggr = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos_aggr) == 1
    assert estilos_aggr[0]["estilo"] == "BOTA VAQUERA"
    assert estilos_aggr[0]["n_frac"] == 2
    assert estilos_aggr[0]["suma_frac"] == 40.50  # 15.50 + 25.00

def test_empty_search_fast_paths():
    """Verify that both cat_buscar and ic_listar_estilos work seamlessly with empty search inputs."""
    # Guardar algunos materiales para buscar
    modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO ESPAÑOL", "unidad_default": "m"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA COMODA", "unidad_default": "par"})

    # Empty query should return both
    results = modulo_catalogos.cat_buscar("materiales", texto="", estatus="ACTIVO")
    assert len(results) == 2
    names = [r[1] for r in results]
    assert "HILO ESPAÑOL" in names
    assert "SUELA COMODA" in names

    # Specific query
    specific_results = modulo_catalogos.cat_buscar("materiales", texto="HILO", estatus="ACTIVO")
    assert len(specific_results) == 1
    assert specific_results[0][1] == "HILO ESPAÑOL"

    # Test ic_listar_estilos search with empty and non-empty parameters
    modulo_catalogos.ic_guardar_estilo("TENIS DEPORTIVO", "MONTADO", 80.0)
    modulo_catalogos.ic_guardar_estilo("ZAPATO VESTIR", "MONTADO", 95.0)

    # Empty search should return both
    all_estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(all_estilos) == 2

    # Search by department filter
    montado_estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="MONTADO")
    assert len(montado_estilos) == 2

    # Non-empty keyword search
    vestir_estilos = modulo_catalogos.ic_listar_estilos(buscar="VESTIR", departamento="MONTADO")
    assert len(vestir_estilos) == 1
    assert vestir_estilos[0]["estilo"] == "ZAPATO VESTIR"
