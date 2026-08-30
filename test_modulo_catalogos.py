import os
import time

import pytest

import modulo_catalogos as mc


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    # Set up isolated test DB
    test_db = str(tmp_path / "test_catalogos.sqlite")
    mc.CAT_DB_PATH = test_db
    mc.cat_init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


def test_cat_get_material_por_nombre_functional():
    datos = {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
    }
    ok, _mat_id = mc.cat_guardar("materiales", datos)
    assert ok is True

    # Case insensitive exact lookup
    res = mc.cat_get_material_por_nombre("cuero vacuno")
    assert res.get("nombre") == "CUERO VACUNO"
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Uppercase lookup
    res_up = mc.cat_get_material_por_nombre("CUERO VACUNO")
    assert res_up.get("nombre") == "CUERO VACUNO"

    # Non-existent material
    res_none = mc.cat_get_material_por_nombre("INEXISTENTE")
    assert res_none == {}

    # Empty string or spaces
    assert mc.cat_get_material_por_nombre("") == {}
    assert mc.cat_get_material_por_nombre("   ") == {}

def test_cat_get_material_por_nombre_performance():
    # Insert 1000 materials to test index performance
    for i in range(1000):
        d = {
            "nombre": f"MATERIAL_{i}",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ"
        }
        mc.cat_guardar("materiales", d)

    target_name = "MATERIAL_750"

    t0 = time.perf_counter()
    for _ in range(100):
        res = mc.cat_get_material_por_nombre(target_name)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    assert res.get("nombre") == target_name
    print(f"\n100 direct indexed material lookups executed in {elapsed:.4f}s")
    # 100 indexed queries in SQLite should take < 0.1s easily
    assert elapsed < 1.0
