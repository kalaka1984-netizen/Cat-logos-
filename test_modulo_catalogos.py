import sys
from unittest import mock

import pytest

# Ensure headless test environment by creating mock customtkinter module if needed
try:
    import customtkinter  # noqa: F401
except ImportError:
    sys.modules['customtkinter'] = mock.MagicMock()

import modulo_catalogos


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """Fixture that redirects CAT_DB_PATH to a temporary database file."""
    db_file = str(tmp_path / "test_catalogos_db.sqlite")
    orig_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = db_file

    # Initialize DB schema
    modulo_catalogos.cat_init_db()

    yield db_file

    modulo_catalogos.CAT_DB_PATH = orig_db_path


def test_cat_get_material_por_nombre_existing():
    """Test retrieving existing material data by exact and case-insensitive name."""
    material_data = {
        "nombre": "CUERO VACUNO BLACK",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
    }
    ok, _ = modulo_catalogos.cat_guardar("materiales", material_data)
    assert ok is True

    # Test exact uppercase search
    res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO BLACK")
    assert res["nombre"] == "CUERO VACUNO BLACK"
    assert res["tipo_material"] == "DIRECTO"
    assert res["unidad_default"] == "DM"

    # Test lowercase with whitespace search
    res_lower = modulo_catalogos.cat_get_material_por_nombre("  cuero vacuno black  ")
    assert res_lower["nombre"] == "CUERO VACUNO BLACK"
    assert res_lower["unidad_default"] == "DM"


def test_cat_get_material_por_nombre_non_existent():
    """Test retrieving a material name that does not exist in the database."""
    res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_INEXISTENTE")
    assert res == {}


def test_cat_get_material_por_nombre_empty():
    """Test calling cat_get_material_por_nombre with empty string or whitespace."""
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}
    assert modulo_catalogos.cat_get_material_por_nombre("   ") == {}
    assert modulo_catalogos.cat_get_material_por_nombre(None) == {}


def test_cat_precarga_material_integration():
    """Test integration with cat_precarga_material helper."""
    material_data = {
        "nombre": "FORRO CERDO",
        "tipo_material": "DIRECTO",
        "es_principal": "NO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
    }
    modulo_catalogos.cat_guardar("materiales", material_data)

    precarga = modulo_catalogos.cat_precarga_material("forro cerdo")
    assert precarga == {
        "tipo_ft": "DIR",
        "unidad": "DM",
        "departamento": "CORTE",
        "monitor": True,
        "principal": False,
    }
