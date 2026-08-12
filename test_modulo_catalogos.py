import sys


# Create mock for customtkinter and inject it into sys.modules
class MockCTk:
    def set_appearance_mode(self, mode): pass
    def set_default_color_theme(self, theme): pass
    def set_widget_scaling(self, scale): pass
    def set_window_scaling(self, scale): pass

    # Base classes
    class CTkFrame:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def winfo_children(self): return []
        def after(self, *args, **kwargs): pass
        def after_cancel(self, *args, **kwargs): pass
        def grid(self, *args, **kwargs): pass
        def columnconfigure(self, *args, **kwargs): pass
    class CTkScrollableFrame(CTkFrame): pass
    class CTkLabel:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def configure(self, *args, **kwargs): pass
    class CTkButton:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def configure(self, *args, **kwargs): pass
    class CTkEntry:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
    class CTkComboBox:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
    class CTkTextbox:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
    class CTkSegmentedButton:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
    class CTkToplevel:
        def __init__(self, *args, **kwargs): pass
    class CTkRadioButton:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass

sys.modules["customtkinter"] = MockCTk()

import os

import pytest

import modulo_catalogos

# Override database path for testing
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_db.sqlite")
modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH

@pytest.fixture(autouse=True)
def setup_teardown_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    modulo_catalogos.ic_init_db()
    modulo_catalogos.cat_init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_ic_listar_estilos_aggregation():
    # 1. Guardar un estilo
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 150.0, "NOTAS A")
    assert ok is True
    assert estilo_id is not None

    # Listar sin fracciones
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "ESTILO_A"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # 2. Agregar fracciones
    ok2, _msg2 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRAC_1", 50.0, 1)
    assert ok2 is True
    ok3, _msg3 = modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRAC_2", 100.0, 2)
    assert ok3 is True

    # Listar con fracciones (agregado)
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "ESTILO_A"
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 150.0

def test_ic_empty_search_bypass():
    # Insert multiple styles
    modulo_catalogos.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 10.0)
    modulo_catalogos.ic_guardar_estilo("ESTILO_B", "PESPUNTE", 20.0)

    # Test empty search (bypasses LIKE)
    estilos = modulo_catalogos.ic_listar_estilos(buscar="")
    assert len(estilos) == 2

    # Test with search
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_A")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "ESTILO_A"

def test_cat_buscar_empty_search_bypass():
    # Initialize DB for general catalogs
    modulo_catalogos.cat_init_db()

    # Insert general catalog entry
    ok, _reg_id = modulo_catalogos.cat_guardar("materiales", {
        "nombre": "CUERO VACUNO",
        "tipo_material": "DIRECTO"
    })
    assert ok is True

    # Search all
    res = modulo_catalogos.cat_buscar("materiales", "")
    assert len(res) == 1
    assert res[0][1] == "CUERO VACUNO"
