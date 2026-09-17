import os
import sys
import json
import sqlite3
import time
import pytest
from unittest.mock import MagicMock

# ── Mock tkinter & customtkinter prior to importing modulo_catalogos ────────────
mock_ctk = MagicMock()
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []

mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkComboBox = DummyWidget
mock_ctk.CTkTextbox = DummyWidget
mock_ctk.CTkScrollableFrame = DummyWidget
mock_ctk.CTkSegmentedButton = DummyWidget
mock_ctk.CTkScrollbar = DummyWidget

sys.modules['customtkinter'] = mock_ctk
sys.modules['darkdetect'] = MagicMock()

import modulo_catalogos

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_temp.sqlite")

@pytest.fixture(autouse=True)
def setup_teardown_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    original_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH

    modulo_catalogos.cat_init_db()

    yield

    modulo_catalogos.CAT_DB_PATH = original_db
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_cat_get_material_por_nombre_lookup():
    """Verify that cat_get_material_por_nombre returns correct JSON data or empty dict."""
    mat_data = {
        "nombre": "PIEL FLOR ENTERA",
        "tipo_material": "DIRECTO",
        "es_principal": "SÍ",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "notas": "TEST MAT"
    }

    ok, res_id = modulo_catalogos.cat_guardar("materiales", mat_data)
    assert ok is True

    # Exact lookup
    retrieved = modulo_catalogos.cat_get_material_por_nombre("PIEL FLOR ENTERA")
    assert retrieved.get("unidad_default") == "DM"
    assert retrieved.get("departamento") == "CORTE"

    # Lowercase / stripped lookup
    retrieved_case = modulo_catalogos.cat_get_material_por_nombre("  piel flor entera  ")
    assert retrieved_case.get("unidad_default") == "DM"

    # Non-existent material
    non_existent = modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
    assert non_existent == {}

    # Empty string
    empty_res = modulo_catalogos.cat_get_material_por_nombre("")
    assert empty_res == {}


def test_cat_get_material_por_nombre_performance_benchmark():
    """Benchmark direct lookup against population of materials."""
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()

    batch = []
    for i in range(1000):
        data = {
            "nombre": f"MAT_{i}",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE"
        }
        batch.append((f"MAT_{i}", json.dumps(data), "ACTIVO", "2026-01-01", "2026-01-01"))

    cur.executemany("INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)", batch)
    con.commit()
    con.close()

    t0 = time.perf_counter()
    for _ in range(200):
        res = modulo_catalogos.cat_get_material_por_nombre("MAT_750")
        assert res.get("unidad_default") == "DM"
    t1 = time.perf_counter()

    total_time = t1 - t0
    # 200 lookups on 1000 items should take well under 0.25s with indexed SELECT
    assert total_time < 0.25, f"Performance regression: 200 lookups took {total_time:.4f}s"
