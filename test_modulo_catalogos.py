import os
import sys
import time
import types
import pytest

# Create a mock customtkinter module with standard Python classes to avoid metaclass conflicts
mock_ctk = types.ModuleType("customtkinter")

class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs): pass
    def place(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass

class CTkFrame(DummyWidget): pass
class CTkLabel(DummyWidget): pass
class CTkButton(DummyWidget): pass
class CTkEntry(DummyWidget): pass
class CTkComboBox(DummyWidget): pass
class CTkTextbox(DummyWidget): pass
class CTkScrollableFrame(DummyWidget): pass
class CTkScrollbar(DummyWidget): pass
class CTkSegmentedButton(DummyWidget): pass
class CTkRadioButton(DummyWidget): pass
class CTkToplevel(DummyWidget): pass
class CTk(DummyWidget):
    def title(self, *args): pass
    def geometry(self, *args): pass
    def mainloop(self, *args): pass

mock_ctk.CTkFrame = CTkFrame
mock_ctk.CTkLabel = CTkLabel
mock_ctk.CTkButton = CTkButton
mock_ctk.CTkEntry = CTkEntry
mock_ctk.CTkComboBox = CTkComboBox
mock_ctk.CTkTextbox = CTkTextbox
mock_ctk.CTkScrollableFrame = CTkScrollableFrame
mock_ctk.CTkScrollbar = CTkScrollbar
mock_ctk.CTkSegmentedButton = CTkSegmentedButton
mock_ctk.CTkRadioButton = CTkRadioButton
mock_ctk.CTkToplevel = CTkToplevel
mock_ctk.CTk = CTk
mock_ctk.set_appearance_mode = lambda mode: None
mock_ctk.set_default_color_theme = lambda theme: None
mock_ctk.set_widget_scaling = lambda s: None
mock_ctk.set_window_scaling = lambda s: None

sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos

TEST_DB = "test_cat_temp.sqlite"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    orig_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    modulo_catalogos.cat_init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    modulo_catalogos.CAT_DB_PATH = orig_db

def test_cat_get_material_por_nombre_basic():
    # Insert material
    datos = {"nombre": "SUELA VANS", "unidad_default": "PAR", "departamento": "MONTADO"}
    ok, _ = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok is True

    # Test exact fetch
    res = modulo_catalogos.cat_get_material_por_nombre("SUELA VANS")
    assert res.get("nombre") == "SUELA VANS"
    assert res.get("unidad_default") == "PAR"
    assert res.get("departamento") == "MONTADO"

    # Test lowercase and leading/trailing spaces
    res2 = modulo_catalogos.cat_get_material_por_nombre("   suela vans  ")
    assert res2.get("nombre") == "SUELA VANS"

    # Test nonexistent
    res_none = modulo_catalogos.cat_get_material_por_nombre("NO_EXISTE")
    assert res_none == {}

    # Test empty / invalid inputs
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}
    assert modulo_catalogos.cat_get_material_por_nombre("   ") == {}

def test_benchmark_cat_get_material_por_nombre():
    # Populate with 300 materials
    for i in range(300):
        nm = f"MATERIAL_PRUEBA_{i}"
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": nm,
            "unidad_default": "DM",
            "departamento": "CORTE"
        })

    # Benchmark lookup
    target = "MATERIAL_PRUEBA_150"
    start = time.perf_counter()
    for _ in range(500):
        res = modulo_catalogos.cat_get_material_por_nombre(target)
        assert res.get("nombre") == target
    elapsed = time.perf_counter() - start

    print(f"\n[BENCHMARK] 500 lookups completed in {elapsed:.4f} seconds ({elapsed/500*1000:.3f} ms/query)")
    assert elapsed < 0.2  # Should be under 200ms for 500 queries
