import os
import json
import sqlite3
import pytest
import modulo_catalogos

# Setup a temporary database path for testing
TEST_DB_PATH = "test_catalogos_db.sqlite"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Patch CAT_DB_PATH to use our test database
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", TEST_DB_PATH)

    # Initialize the database
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    # Cleanup database files after test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_cat_get_material_por_nombre():
    # Insert a dummy material
    datos = {
        "nombre": "CUERO PREMIUM",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }

    success, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert success is True

    # Check that lookup finds it and parses json properly
    retrieved = modulo_catalogos.cat_get_material_por_nombre("CUERO PREMIUM")
    assert retrieved != {}
    assert retrieved["tipo_material"] == "DIRECTO"
    assert retrieved["unidad_default"] == "DM"

    # Check case-insensitivity and whitespace handling
    retrieved_lower = modulo_catalogos.cat_get_material_por_nombre("  cuero premium  ")
    assert retrieved_lower != {}
    assert retrieved_lower["tipo_material"] == "DIRECTO"

    # Check lookup for non-existent material
    non_existent = modulo_catalogos.cat_get_material_por_nombre("NON-EXISTENT")
    assert non_existent == {}

def test_ic_listar_estilos_pre_aggregation():
    # Save a style
    success, estilo_id = modulo_catalogos.ic_guardar_estilo("ESTILO-123", "CORTE", 150.0, "Notas de prueba")
    assert success is True

    # Initially there are 0 fractions
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO-123")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # Add fractions
    success1, f1 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "CORTE FRACCION 1", 25.5, 1)
    success2, f2 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "CORTE FRACCION 2", 74.5, 2)
    assert success1 is True
    assert success2 is True

    # Query style and verify pre-aggregated fractions count and sum
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO-123")
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 100.0
