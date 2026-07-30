import sys
import os
import tempfile
from unittest.mock import MagicMock

# ── Mocking Tkinter and CustomTkinter to prevent headless environment crashes ──
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after(self, *args, **kwargs):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTk = MagicMock()
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()

# Setup tkinter mocks
mock_tk = MagicMock()
mock_tk_instance = MagicMock()
# Ensure return values are integers to prevent comparison/scaling TypeErrors
mock_tk_instance.winfo_screenwidth.return_value = 1920
mock_tk_instance.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_tk_instance

# Apply mocks to sys.modules
sys.modules["customtkinter"] = mock_ctk
sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()

import pytest

# ── Now we can safely import the module ──
import modulo_catalogos

@pytest.fixture(autouse=True)
def setup_test_db():
    """Sets up a temporary SQLite database for catalogos."""
    temp_dir = tempfile.TemporaryDirectory()
    temp_db_path = os.path.join(temp_dir.name, "test_catalogos_db.sqlite")

    # Override CAT_DB_PATH in modulo_catalogos
    original_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db_path

    # Initialize schema
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield temp_db_path

    # Cleanup
    modulo_catalogos.CAT_DB_PATH = original_db_path
    temp_dir.cleanup()

def test_cat_guardar_upper_formatting():
    """Asserts that cat_guardar forces uppercase formatting on string values."""
    datos = {
        "nombre": "hilo de nylon",
        "tipo_material": "directo",
        "unidad_default": "dm",
        "departamento": "corte",
        "visible_monitor": "sí",
        "notas": "alguna nota"
    }

    ok, registro_id = modulo_catalogos.cat_guardar("materiales", datos)
    assert ok is True
    assert registro_id is not None

    # Retrieve and verify uppercase formatting
    row = modulo_catalogos.cat_get_by_id("materiales", registro_id)
    assert row is not None
    assert row[1] == "HILO DE NYLON"  # Nombre should be uppercase

def test_ic_listar_estilos_n_plus_one_optimization():
    """
    Verifies that ic_listar_estilos LEFT JOINs and aggregates fractions correctly,
    eliminating the need for N+1 queries.
    """
    # 1. Create a style
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo(
        estilo="BOTA 500",
        departamento="PESPUNTE",
        precio_par=120.0,
        notas="Prueba de bota"
    )
    assert ok is True

    # 2. Add some fractions to this style
    ok1, msg1 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="Costura Tubo",
        precio=25.5,
        orden=1
    )
    ok2, msg2 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="Adorno Hebilla",
        precio=15.0,
        orden=2
    )
    assert ok1 is True
    assert ok2 is True

    # 3. Retrieve style list and assert pre-aggregated values
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
    assert len(estilos) == 1

    style_record = estilos[0]
    assert style_record["estilo"] == "BOTA 500"
    assert style_record["n_frac"] == 2
    assert style_record["suma_frac"] == 40.5

def test_ic_listar_estilos_empty_search():
    """Verifies that empty searches are handled correctly in ic_listar_estilos."""
    # 1. Insert multiple styles
    modulo_catalogos.ic_guardar_estilo("TENIS A", "CORTE", 80.0)
    modulo_catalogos.ic_guardar_estilo("TENIS B", "CORTE", 90.0)
    modulo_catalogos.ic_guardar_estilo("ZAPATO C", "ADORNO", 110.0)

    # 2. Test empty search for ALL departments
    estilos_todos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos_todos) == 3

    # 3. Test empty search for a specific department
    estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos_corte) == 2

    # 4. Test non-empty search
    estilos_search = modulo_catalogos.ic_listar_estilos(buscar="TENIS", departamento="TODOS")
    assert len(estilos_search) == 2
