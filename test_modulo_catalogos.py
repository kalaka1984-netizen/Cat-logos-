import os
import sqlite3
from unittest.mock import MagicMock

import pytest

# Set a test database path before importing/running modulo_catalogos
import modulo_catalogos

TEST_DB_PATH = "test_catalogos_db.sqlite"
modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH

@pytest.fixture(autouse=True)
def setup_teardown_db():
    # Remove existing test db if any
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Initialize the tables
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    # Cleanup after test runs
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_database_initialization():
    """Verify that databases and tables are initialized correctly."""
    assert os.path.exists(TEST_DB_PATH)

    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()

    # Check that core tables exist
    for table in ("materiales", "trabajadores", "proveedores", "clientes", "proveedor_materiales", "ic_estilos", "ic_fracciones"):
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        assert cur.fetchone() is not None

    con.close()

def test_cat_buscar_empty_and_query():
    """Verify that cat_buscar retrieves all matching/filtered records."""
    # Pre-populate materials
    mat1 = {"nombre": "Goma Premium", "tipo_material": "DIRECTO", "estatus": "ACTIVO"}
    mat2 = {"nombre": "Hilo Rojo", "tipo_material": "INDIRECTO", "estatus": "INACTIVO"}

    res1, _id1 = modulo_catalogos.cat_guardar("materiales", mat1)
    res2, _id2 = modulo_catalogos.cat_guardar("materiales", mat2)

    assert res1 is True
    assert res2 is True

    # Empty query (TODOS) -> should return all materials
    rows = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(rows) == 2

    # Search specific query
    rows_hilo = modulo_catalogos.cat_buscar("materiales", "hilo", "TODOS")
    assert len(rows_hilo) == 1
    assert rows_hilo[0][1] == "HILO ROJO"  # uppercase formatting forced

    # Search with ACTIVO filter and empty query
    rows_activos = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
    assert len(rows_activos) == 1
    assert rows_activos[0][1] == "GOMA PREMIUM"

def test_cat_get_material_por_nombre():
    """Verify optimized exact lookup for materials."""
    mat_data = {"nombre": "Suela Confort", "tipo_material": "DIRECTO", "estatus": "ACTIVO"}
    res, _m_id = modulo_catalogos.cat_guardar("materiales", mat_data)
    assert res is True

    # Get by name
    res_data = modulo_catalogos.cat_get_material_por_nombre("Suela Confort")
    assert res_data != {}
    assert res_data["nombre"] == "SUELA CONFORT"  # saved as uppercase

    # Get by non-existing name
    res_none = modulo_catalogos.cat_get_material_por_nombre("Non Existent")
    assert res_none == {}

def test_ic_listar_estilos_pre_aggregation():
    """Verify pre-aggregation logic (n_frac and suma_frac) in ic_listar_estilos."""
    # 1. Add style
    style_name = "Nike Run"
    dept = "CORTE"
    precio_par = 12.50
    notas = "Runners"

    res_style, style_id = modulo_catalogos.ic_guardar_estilo(style_name, dept, precio_par, notas)
    assert res_style is True

    # 2. Assert n_frac and suma_frac are initially 0
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "NIKE RUN"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # 3. Add fractions
    res_f1, _f1_id = modulo_catalogos.ic_guardar_fraccion(style_id, "Fraccion Uno", 4.25, 1)
    res_f2, _f2_id = modulo_catalogos.ic_guardar_fraccion(style_id, "Fraccion Dos", 5.50, 2)

    assert res_f1 is True
    assert res_f2 is True

    # 4. Check list with aggregated results
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 1
    assert estilos[0]["n_frac"] == 2
    assert estilos[0]["suma_frac"] == 9.75  # 4.25 + 5.50

def test_ic_vista_refrescar_lista_mocked():
    """Verify that _refrescar_lista correctly maps aggregated fields and formats balance."""
    # Mock CTk variables
    mock_dep_filtro = MagicMock()
    mock_dep_filtro.get.return_value = "TODOS"

    mock_busq = MagicMock()
    mock_busq.get.return_value = "Adidas"

    # Populate mock styles/fractions in DB
    res_style, style_id = modulo_catalogos.ic_guardar_estilo("Adidas Ultra", "PESPUNTE", 20.0, "Super")
    assert res_style is True

    # Add fractions so n_frac = 2, suma_frac = 20.0 (cuadra!)
    modulo_catalogos.ic_guardar_fraccion(style_id, "Frac A", 10.0, 1)
    modulo_catalogos.ic_guardar_fraccion(style_id, "Frac B", 10.0, 2)

    # Mocking self for IC_Vista
    mock_self = MagicMock()
    mock_self._var_dep_filtro = mock_dep_filtro
    mock_self._var_busq = mock_busq

    # Mock frame list widget
    mock_frame = MagicMock()
    mock_frame.winfo_children.return_value = []
    mock_self._frame_lista = mock_frame

    # Mock tk.Frame and tk.Label creation inside the loop
    created_labels = []

    def dummy_label_init(parent, text=None, **kwargs):
        lbl = MagicMock()
        lbl.text = text
        lbl.fg = kwargs.get("fg")
        created_labels.append(lbl)
        return lbl

    class DummyFrame:
        def __init__(self, *args, **kwargs):
            pass
        def columnconfigure(self, *args, **kwargs):
            pass
        def pack(self, *args, **kwargs):
            pass
        def bind(self, *args, **kwargs):
            pass

    import tkinter as tk
    original_label = tk.Label
    original_frame = tk.Frame
    tk.Label = dummy_label_init
    tk.Frame = DummyFrame

    try:
        # Call the actual _refrescar_lista with mock self
        modulo_catalogos.IC_Vista._refrescar_lista(mock_self)
    finally:
        # Restore original tkinter classes
        tk.Label = original_label
        tk.Frame = original_frame

    # Check that labels were created for: style name, short dept name, price, n_frac, and balance text
    label_texts = [lbl.text for lbl in created_labels]
    assert "ADIDAS ULTRA" in label_texts
    assert "PES" in label_texts  # PESPUNTE[:3]
    assert "$20.00" in label_texts
    assert "2" in label_texts
    assert "✓ CUADRA" in label_texts
