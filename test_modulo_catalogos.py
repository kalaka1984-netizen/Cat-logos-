import os
import sys
import json
import time
import sqlite3
import pytest

# Ensure modulo_catalogos uses a test DB file
TEST_DB = "test_catalogos_benchmark.sqlite"

def setup_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    import modulo_catalogos
    modulo_catalogos.CAT_DB_PATH = TEST_DB
    modulo_catalogos.cat_init_db()

    # Populate DB with 1000 items
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()
    for i in range(1000):
        d = json.dumps({
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ" if i % 2 == 0 else "NO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "proveedor_ref": f"PROVEEDOR_{i}",
            "costo_ref": 15.5 + i
        })
        cur.execute(
            "INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)",
            (f"MATERIAL_{i:04d}", d, "ACTIVO" if i % 10 != 0 else "INACTIVO", "2025-01-01", "2025-01-01")
        )
    con.commit()
    con.close()

def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_cat_get_material_por_nombre_correctness():
    import modulo_catalogos
    res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_0042")
    assert res is not None
    assert res.get("proveedor_ref") == "PROVEEDOR_42"
    assert res.get("unidad_default") == "dm"

    # Case insensitive lookups
    res_lower = modulo_catalogos.cat_get_material_por_nombre("material_0042")
    assert res_lower.get("proveedor_ref") == "PROVEEDOR_42"

    # Non-existent material
    res_nonexistent = modulo_catalogos.cat_get_material_por_nombre("NON_EXISTENT_MATERIAL")
    assert res_nonexistent == {}

    # Empty material
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}

def test_cat_get_material_por_nombre_benchmark():
    import modulo_catalogos
    # Perform 500 lookups
    t0 = time.perf_counter()
    for i in range(500):
        target = f"MATERIAL_{(i * 2) % 1000:04d}"
        res = modulo_catalogos.cat_get_material_por_nombre(target)
        assert res.get("proveedor_ref") == f"PROVEEDOR_{(i * 2) % 1000}"
    t1 = time.perf_counter()

    elapsed = t1 - t0
    print(f"\n[Benchmark] 500 lookups completed in {elapsed:.4f}s ({elapsed / 500 * 1000:.3f}ms per lookup)")
    # Should be well under 0.1s for 500 lookups
    assert elapsed < 0.2
