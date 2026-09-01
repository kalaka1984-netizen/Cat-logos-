import sys
from unittest.mock import MagicMock

import pytest


# Dummy classes for GUI mocking in headless test environments
class DummyCTkWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkWidget
mock_ctk.CTkLabel = DummyCTkWidget
mock_ctk.CTkButton = DummyCTkWidget
mock_ctk.CTkEntry = DummyCTkWidget
mock_ctk.CTkOptionMenu = DummyCTkWidget
mock_ctk.CTkScrollableFrame = DummyCTkWidget

mock_tk = MagicMock()
mock_root = MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root

sys.modules['tkinter'] = mock_tk
sys.modules['customtkinter'] = mock_ctk

import modulo_catalogos


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Set up temporary database for testing catalog functions."""
    test_db = str(tmp_path / "test_catalogos.sqlite")
    old_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = test_db
    modulo_catalogos.cat_init_db()

    yield test_db

    modulo_catalogos.CAT_DB_PATH = old_db


def test_cat_get_material_por_nombre():
    # Insert test material
    mat_data = {
        "nombre": "PIEL VACUNO NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "visible_monitor": "SÍ",
        "es_principal": "SÍ"
    }
    ok, _ = modulo_catalogos.cat_guardar("materiales", mat_data)
    assert ok is True

    # Test exact query
    res = modulo_catalogos.cat_get_material_por_nombre("PIEL VACUNO NEGRA")
    assert res.get("unidad_default") == "DM"
    assert res.get("departamento") == "CORTE"

    # Test case insensitivity & whitespace trimming
    res_case = modulo_catalogos.cat_get_material_por_nombre("  piel vacuno negra  ")
    assert res_case.get("unidad_default") == "DM"

    # Test non-existent material
    res_none = modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
    assert res_none == {}

    # Test empty query
    assert modulo_catalogos.cat_get_material_por_nombre("") == {}


def test_cat_buscar_empty_and_text_queries():
    # Insert materials
    mats = [
        {"nombre": "SUELA CAUCHO", "estatus": "ACTIVO", "notas": "SUELA DE GOMA"},
        {"nombre": "SUELA PU", "estatus": "INACTIVO", "notas": "POLIURETANO"},
        {"nombre": "CINTA ADHESIVA", "estatus": "ACTIVO", "notas": "CONSUMIBLE"}
    ]
    for m in mats:
        modulo_catalogos.cat_guardar("materiales", m)

    # Empty search with "TODOS" status
    all_mats = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
    assert len(all_mats) == 3

    # Empty search with "ACTIVO" status
    active_mats = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
    assert len(active_mats) == 2
    names = [row[1] for row in active_mats]
    assert "SUELA CAUCHO" in names
    assert "CINTA ADHESIVA" in names

    # Text search with specific query
    suela_mats = modulo_catalogos.cat_buscar("materiales", "SUELA", "TODOS")
    assert len(suela_mats) == 2

    # Text search in datos_json notes
    goma_mats = modulo_catalogos.cat_buscar("materiales", "GOMA", "TODOS")
    assert len(goma_mats) == 1
    assert goma_mats[0][1] == "SUELA CAUCHO"
