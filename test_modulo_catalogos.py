import os
import tempfile

import modulo_catalogos
import pytest

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    old_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = db_path
    modulo_catalogos.cat_init_db()

    yield db_path

    modulo_catalogos.CAT_DB_PATH = old_path
    if os.path.exists(db_path):
        os.remove(db_path)

def test_cat_guardar_and_get_material_por_nombre(temp_db):
    datos = {
        "nombre": "PIEL VACUNO NEGRO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    success, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert success is True
    assert reg_id > 0

    # Fetch material by exact name
    result = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRO")
    assert result.get("nombre") == "PIEL VACUNO NEGRO"
    assert result.get("unidad_default") == "DM"
    assert result.get("departamento") == "CORTE"

    # Fetch with lowercase and leading/trailing whitespace
    result_lower = modulo_catalogos.cat_get_material_por_nombre("  piel vacuno negro  ")
    assert result_lower.get("nombre") == "PIEL VACUNO NEGRO"
    assert result_lower.get("unidad_default") == "DM"

    # Non-existent or empty material
    empty_res = modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT")
    assert empty_res == {}

    empty_str_res = modulo_catalogos.cat_get_material_por_nombre("   ")
    assert empty_str_res == {}

def test_cat_buscar_empty_and_query_text(temp_db):
    for i in range(5):
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": f"MATERIAL_{i}",
            "tipo_material": "DIRECTO",
            "estatus": "ACTIVO" if i < 3 else "INACTIVO"
        })

    # Search with empty string and TODOS
    all_mats = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(all_mats) == 5

    # Search with whitespace string and ACTIVO
    active_mats = modulo_catalogos.cat_buscar("materiales", "   ", "ACTIVO")
    assert len(active_mats) == 3

    # Search with query string
    query_mats = modulo_catalogos.cat_buscar("materiales", "MATERIAL_1", "TODOS")
    assert len(query_mats) == 1
    assert query_mats[0][1] == "MATERIAL_1"
