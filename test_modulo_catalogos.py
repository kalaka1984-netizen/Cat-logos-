import os
import sys
import sqlite3
from unittest.mock import MagicMock

# Define dummy classes to simulate tkinter and customtkinter widgets in a headless environment.
class DummyTk:
    def __init__(self, *args, **kwargs):
        pass
    def withdraw(self):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def destroy(self):
        pass

class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def winfo_toplevel(self):
        return self
    def after(self, *args, **kwargs):
        pass
    def after_cancel(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def pack_propagate(self, *args, **kwargs):
        pass

# Inject dummy components into sys.modules to prevent ImportError: No module named 'tkinter'
mock_tk = MagicMock()
mock_tk.Tk = DummyTk
mock_tk.Frame = DummyWidget
mock_tk.Label = DummyWidget
mock_tk.Canvas = DummyWidget

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

mock_ctk = MagicMock()
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkButton = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkScrollbar = DummyWidget
mock_ctk.CTkEntry = DummyWidget
mock_ctk.CTkOptionMenu = DummyWidget
mock_ctk.CTkTextbox = DummyWidget

sys.modules['customtkinter'] = mock_ctk

# Now it is safe to import modulo_catalogos
import pytest
import modulo_catalogos

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Fixture to redirect DB to a temporary file for clean testing."""
    test_db = "test_catalogos_db.sqlite"
    if os.path.exists(test_db):
        os.remove(test_db)

    # Override database path in the module
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", test_db)

    # Initialize DB tables
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield test_db

    # Teardown: close any active sqlite3 connections and clean up
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except PermissionError:
            pass

def test_db_initialization(setup_test_db):
    """Verify that all required tables and indexes are created successfully."""
    con = sqlite3.connect(setup_test_db)
    cur = con.cursor()

    # Check that ic_estilos and ic_fracciones tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('ic_estilos', 'ic_fracciones')")
    tables = [r[0] for r in cur.fetchall()]
    assert "ic_estilos" in tables
    assert "ic_fracciones" in tables

    # Verify the department index exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ic_estilos'")
    indexes = [r[0] for r in cur.fetchall()]
    assert "idx_ic_estilos_depto" in indexes

    con.close()

def test_guardar_y_listar_estilos_y_fracciones(setup_test_db):
    """Test saving styles and fractions and verify aggregation query accuracy in ic_listar_estilos."""
    # 1. Save style
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo(
        estilo="ESTILO-TEST",
        departamento="CORTE",
        precio_par=120.50,
        notas="Notas de prueba"
    )
    assert ok is True
    assert estilo_id is not None

    # 2. Save fractions
    ok1, msg1 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="Corte de Piel",
        precio=40.0,
        orden=1
    )
    ok2, msg2 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=estilo_id,
        nombre="Corte de Forro",
        precio=30.50,
        orden=2
    )
    assert ok1 is True
    assert ok2 is True

    # 3. Retrieve style using ic_listar_estilos and check pre-aggregation fields
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    style_row = estilos[0]
    assert style_row["estilo"] == "ESTILO-TEST"
    assert style_row["departamento"] == "CORTE"
    assert style_row["precio_par"] == 120.50
    assert style_row["n_frac"] == 2
    assert style_row["suma_frac"] == 70.50

def test_ic_listar_estilos_empty_and_filter(setup_test_db):
    """Test query behavior with different parameters: empty search, filtered department, or searched term."""
    # Save a style in CORTE and one in PESPUNTE
    _, corte_id = modulo_catalogos.ic_guardar_estilo("EST-CORTE", "CORTE", 100.0)
    _, pespunte_id = modulo_catalogos.ic_guardar_estilo("EST-PESP", "PESPUNTE", 150.0)

    # Save fractions for CORTE
    modulo_catalogos.ic_guardar_fraccion(corte_id, "FRAC-1", 50.0)

    # 1. List all (empty search)
    estilos = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
    assert len(estilos) == 2

    # 2. Filter by Department
    estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
    assert len(estilos_corte) == 1
    assert estilos_corte[0]["estilo"] == "EST-CORTE"
    assert estilos_corte[0]["n_frac"] == 1
    assert estilos_corte[0]["suma_frac"] == 50.0

    # 3. Search with string
    estilos_search = modulo_catalogos.ic_listar_estilos(buscar="CORTE", departamento="TODOS")
    assert len(estilos_search) == 1
    assert estilos_search[0]["estilo"] == "EST-CORTE"

def test_cat_buscar_empty_and_text(setup_test_db):
    """Verify cat_buscar retrieves catalog records correctly and handles bypass logic when search is empty."""
    # Save some materials
    ok1, mat_id1 = modulo_catalogos.cat_guardar("materiales", {
        "nombre": "PIEL TERNERA",
        "tipo_material": "DIRECTO",
        "estatus": "ACTIVO"
    })
    ok2, mat_id2 = modulo_catalogos.cat_guardar("materiales", {
        "nombre": "HILO NYLON",
        "tipo_material": "INDIRECTO",
        "estatus": "INACTIVO"
    })
    assert ok1 is True
    assert ok2 is True

    # 1. Empty search, status = TODOS
    res_todos = modulo_catalogos.cat_buscar("materiales", texto="", estatus="TODOS")
    assert len(res_todos) == 2
    assert res_todos[0][1] == "HILO NYLON"  # Sorted alphabetically
    assert res_todos[1][1] == "PIEL TERNERA"

    # 2. Empty search, status = ACTIVO
    res_activo = modulo_catalogos.cat_buscar("materiales", texto="", estatus="ACTIVO")
    assert len(res_activo) == 1
    assert res_activo[0][1] == "PIEL TERNERA"

    # 3. Text search
    res_text = modulo_catalogos.cat_buscar("materiales", texto="TERNERA", estatus="TODOS")
    assert len(res_text) == 1
    assert res_text[0][1] == "PIEL TERNERA"
