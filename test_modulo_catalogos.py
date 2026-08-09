import os
import sqlite3
import sys
import types

import pytest

# Create a robust mock customtkinter module to prevent display & metaclass conflicts in headless environments
ctk_mock = types.ModuleType("customtkinter")
ctk_mock.set_appearance_mode = lambda mode: None
ctk_mock.set_default_color_theme = lambda theme: None
ctk_mock.set_widget_scaling = lambda scaling: None
ctk_mock.set_window_scaling = lambda scaling: None

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
    def after(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return None
    def update_idletasks(self):
        pass
    def winfo_width(self):
        return 1920
    def winfo_height(self):
        return 1080
    def winfo_exists(self):
        return True

ctk_mock.CTkFrame = DummyWidget
ctk_mock.CTkLabel = DummyWidget
ctk_mock.CTkButton = DummyWidget
ctk_mock.CTkScrollableFrame = DummyWidget
ctk_mock.CTkComboBox = DummyWidget
ctk_mock.CTkEntry = DummyWidget
ctk_mock.CTkTextbox = DummyWidget
ctk_mock.CTkSegmentedButton = DummyWidget
ctk_mock.CTkScrollbar = DummyWidget
ctk_mock.CTkToplevel = DummyWidget
ctk_mock.CTkRadioButton = DummyWidget
ctk_mock.CTk = DummyWidget

sys.modules["customtkinter"] = ctk_mock

import modulo_catalogos

# Set temporary database path for testing
TEST_DB_PATH = "test_catalogos_db.sqlite"
modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH


@pytest.fixture(autouse=True)
def db_session():
    # Setup: Clean up and initialize fresh test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    # Teardown: Clean up database file after test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_ic_listar_estilos_pre_aggregation():
    # 1. Guardar un estilo
    ok, estilo_id = modulo_catalogos.ic_guardar_estilo("ESTILO-TEST-1", "PESPUNTE", 150.00, "NOTAS TEST")
    assert ok is True
    assert estilo_id is not None

    # Listar y verificar pre-agregados iniciales (0 fracciones, 0.0 suma)
    estilos = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
    assert len(estilos) == 1
    assert estilos[0]["estilo"] == "ESTILO-TEST-1"
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # 2. Agregar fracciones
    ok_f1, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRACCION-A", 45.50, 1)
    ok_f2, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id, "FRACCION-B", 54.50, 2)
    assert ok_f1 is True
    assert ok_f2 is True

    # Listar y verificar pre-agregados actualizados (2 fracciones, 100.0 suma)
    estilos_actualizados = modulo_catalogos.ic_listar_estilos("", "PESPUNTE")
    assert len(estilos_actualizados) == 1
    assert estilos_actualizados[0]["n_frac"] == 2
    assert estilos_actualizados[0]["suma_frac"] == 100.0


def test_idx_ic_estilos_depto_index_exists():
    # Verificar que el índice de departamento exista en la base de datos
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA index_list('ic_estilos')")
    indexes = cur.fetchall()
    con.close()

    index_names = [idx[1] for idx in indexes]
    assert "idx_ic_estilos_depto" in index_names


def test_cat_get_material_por_nombre_exact_match():
    # 1. Guardar material en el catálogo
    material_data = {
        "nombre": "PIEL FLOTER NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "estatus": "ACTIVO"
    }
    ok, _mat_id = modulo_catalogos.cat_guardar("materiales", material_data)
    assert ok is True

    # 2. Obtener por nombre exacto (y asegurar que no tiene que usar LIKE)
    res = modulo_catalogos.cat_get_material_por_nombre("PIEL FLOTER NEGRA")
    assert res != {}
    assert res["nombre"] == "PIEL FLOTER NEGRA"
    assert res["tipo_material"] == "DIRECTO"
    assert res["unidad_default"] == "DM"  # Se fuerza a mayúsculas al guardar

    # 3. Consultar nombre inexistente
    res_not_found = modulo_catalogos.cat_get_material_por_nombre("PIEL INEXISTENTE")
    assert res_not_found == {}


def test_cat_buscar_bypass_like():
    # Guardar un par de materiales
    modulo_catalogos.cat_guardar("materiales", {"nombre": "SUELA TR", "tipo_material": "DIRECTO", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "HILO NYLON", "tipo_material": "INDIRECTO", "estatus": "ACTIVO"})

    # Buscar con texto vacío (debe retornar todos sin hacer LIKE)
    rows_empty = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(rows_empty) == 2

    # Buscar con filtro de texto específico
    rows_filter = modulo_catalogos.cat_buscar("materiales", "SUELA", "TODOS")
    assert len(rows_filter) == 1
    assert rows_filter[0][1] == "SUELA TR"
