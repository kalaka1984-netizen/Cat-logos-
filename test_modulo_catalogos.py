import os
import sys
from unittest.mock import MagicMock

# Create dummy classes to avoid metaclass conflicts when inheriting from CTkFrame/CTkCanvas/etc.
class DummyCTkClass:
    def __init__(self, *args, **kwargs):
        pass

mock_tk = MagicMock()
mock_tk.Tk().winfo_screenwidth.return_value = 1920
mock_tk.Tk().winfo_screenheight.return_value = 1080

class MockCustomTkinter:
    CTk = DummyCTkClass
    CTkFrame = DummyCTkClass
    CTkCanvas = DummyCTkClass
    CTkLabel = DummyCTkClass
    CTkButton = DummyCTkClass
    CTkEntry = DummyCTkClass
    CTkComboBox = DummyCTkClass
    CTkCheckBox = DummyCTkClass
    CTkTabview = DummyCTkClass
    CTkScrollableFrame = DummyCTkClass
    CTkFont = DummyCTkClass
    CTkImage = DummyCTkClass
    CTkToplevel = DummyCTkClass
    CTkSegmentedButton = DummyCTkClass
    set_appearance_mode = MagicMock()
    set_default_color_theme = MagicMock()

mock_ctk = MockCustomTkinter()

sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["customtkinter"] = mock_ctk

import pytest  # noqa: E402
import modulo_catalogos as mc  # noqa: E402


@pytest.fixture(autouse=True)
def setup_tmp_db(tmp_path):
    db_file = tmp_path / "test_catalogos.sqlite"
    mc.CAT_DB_PATH = str(db_file)
    mc.cat_init_db()
    yield
    if os.path.exists(mc.CAT_DB_PATH):
        try:
            os.remove(mc.CAT_DB_PATH)
        except Exception:
            pass


def test_cat_get_material_por_nombre_success():
    datos_mat = {
        "nombre": "CUERO VACUNO NEGRO",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ"
    }
    mc.cat_guardar("materiales", datos_mat)

    # Test exact match
    res = mc.cat_get_material_por_nombre("CUERO VACUNO NEGRO")
    assert res.get("tipo_material") == "DIRECTO"
    assert res.get("unidad_default") == "DM"

    # Test case insensitivity and whitespace strip
    res_case = mc.cat_get_material_por_nombre("  cuero vacuno negro  ")
    assert res_case.get("tipo_material") == "DIRECTO"


def test_cat_get_material_por_nombre_not_found():
    assert mc.cat_get_material_por_nombre("MATERIAL INEXISTENTE") == {}
    assert mc.cat_get_material_por_nombre("") == {}
    assert mc.cat_get_material_por_nombre(None) == {}


def test_cat_precarga_material():
    datos_mat = {
        "nombre": "FORRO SINTETICO",
        "tipo_material": "INDIRECTO",
        "unidad_default": "MTS",
        "departamento": "PESPUNTE",
        "visible_monitor": "NO",
        "es_principal": "SÍ"
    }
    mc.cat_guardar("materiales", datos_mat)

    precarga = mc.cat_precarga_material("  forro sintetico ")
    assert precarga["tipo_ft"] == "IND"
    assert precarga["unidad"] == "MTS"
    assert precarga["departamento"] == "PESPUNTE"
    assert precarga["monitor"] is False
    assert precarga["principal"] is True
