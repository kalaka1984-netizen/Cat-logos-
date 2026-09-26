"""
Tests for modulo_catalogos optimizations and core functions.
"""

import json
import os
import sqlite3
import sys
import time
from unittest.mock import MagicMock

# Inject dummy customtkinter/tkinter to prevent GUI instantiation in headless environment
dummy_ctk = MagicMock()
dummy_ctk.set_appearance_mode = MagicMock()
dummy_ctk.set_default_color_theme = MagicMock()
dummy_ctk.CTkFrame = type("CTkFrame", (object,), {"__init__": lambda self, *a, **k: None})
dummy_ctk.CTkLabel = type("CTkLabel", (object,), {"__init__": lambda self, *a, **k: None})
dummy_ctk.CTkButton = type("CTkButton", (object,), {"__init__": lambda self, *a, **k: None})

sys.modules["customtkinter"] = dummy_ctk

import modulo_catalogos

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_catalogos_temp.sqlite")


def setup_module():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH
    modulo_catalogos.cat_init_db()


def teardown_module():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_cat_get_material_por_nombre_lookup():
    """Verify cat_get_material_por_nombre retrieves exact material data correctly."""
    # Insert test materials
    mat_data = {
        "nombre": "PIEL VACUNA NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ",
    }
    ok, _mat_id = modulo_catalogos.cat_guardar("materiales", mat_data)
    assert ok is True

    res = modulo_catalogos.cat_get_material_por_nombre("piel vacuna negra")
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"
    assert res.get("departamento") == "CORTE"

    # Test non-existent material
    non_existent = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE 999")
    assert non_existent == {}


def test_cat_get_material_por_nombre_performance():
    """Benchmark performance over 1,000 records."""
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()

    # Seed 1,000 materials
    bulk_records = []
    for i in range(1000):
        d = {
            "nombre": f"MATERIAL BENCH {i:04d}",
            "tipo_material": "DIRECTO" if i % 2 == 0 else "INDIRECTO",
            "unidad_default": "M",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "NO",
        }
        bulk_records.append((
            f"MATERIAL BENCH {i:04d}",
            json.dumps(d),
            "ACTIVO",
            "2025-01-01",
            "2025-01-01",
        ))

    cur.executemany(
        "INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)",
        bulk_records,
    )
    con.commit()
    con.close()

    target_name = "MATERIAL BENCH 0500"

    t0 = time.perf_counter()
    for _ in range(200):
        data = modulo_catalogos.cat_get_material_por_nombre(target_name)
        assert data.get("departamento") == "CORTE"
    t1 = time.perf_counter()

    elapsed = t1 - t0
    # 200 queries should easily run under 0.1 seconds with indexed SELECT
    assert elapsed < 0.2, f"Lookup too slow: {elapsed:.4f}s for 200 iterations"
