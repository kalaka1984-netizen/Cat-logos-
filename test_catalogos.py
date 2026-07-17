import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# --- Headless Mocking of GUI Packages ---
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def after(self, *args, **kwargs):
        return "after_id"
    def after_cancel(self, *args, **kwargs):
        pass
    def winfo_toplevel(self):
        return MagicMock()

# Register mocked modules in sys.modules before importing modulo_catalogos
mock_tk = MagicMock()
mock_tk.Tk.return_value.winfo_screenwidth.return_value = 1920
mock_tk.Tk.return_value.winfo_screenheight.return_value = 1080

mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkEntry = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkScrollableFrame = DummyCTkFrame
mock_ctk.CTkComboBox = MagicMock
mock_ctk.CTkTextbox = MagicMock
mock_ctk.CTkSegmentedButton = MagicMock
mock_ctk.CTkToplevel = DummyCTkFrame

sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["customtkinter"] = mock_ctk

# Now we can safely import and mock
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_db.sqlite")

@pytest.fixture(autouse=True)
def setup_test_db():
    # Remove test DB if exists
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    with patch("modulo_catalogos.CAT_DB_PATH", TEST_DB_PATH):
        import modulo_catalogos
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()
        yield

    # Clean up test DB
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

def test_cat_get_material_por_nombre():
    with patch("modulo_catalogos.CAT_DB_PATH", TEST_DB_PATH):
        import modulo_catalogos

        # Guardar algunos materiales de prueba
        datos_mat1 = {
            "nombre": "PIEL NAPA",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "costo_ref": 25.5
        }
        ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos_mat1)
        assert ok is True

        datos_mat2 = {
            "nombre": "HILO 40",
            "tipo_material": "INDIRECTO",
            "es_principal": "NO",
            "unidad_default": "m",
            "departamento": "PESPUNTE",
            "visible_monitor": "NO",
            "costo_ref": 5.0
        }
        ok2, mat_id2 = modulo_catalogos.cat_guardar("materiales", datos_mat2)
        assert ok2 is True

        # Exact match
        res1 = modulo_catalogos.cat_get_material_por_nombre("PIEL NAPA")
        assert res1 != {}
        assert res1.get("tipo_material") == "DIRECTO"
        assert res1.get("costo_ref") == 25.5

        # Lowercase and stripped match (now fully working thanks to our optimization!)
        res1_lower = modulo_catalogos.cat_get_material_por_nombre("  piel napa  ")
        assert res1_lower != {}
        assert res1_lower.get("tipo_material") == "DIRECTO"

        # Non-existent material
        res_none = modulo_catalogos.cat_get_material_por_nombre("PIEL INEXISTENTE")
        assert res_none == {}

def test_ic_listar_estilos_y_fracciones():
    with patch("modulo_catalogos.CAT_DB_PATH", TEST_DB_PATH):
        import modulo_catalogos

        # Guardar estilos
        ok1, est1_id = modulo_catalogos.ic_guardar_estilo("ESTILO-A", "PESPUNTE", 120.0, "Notas A")
        assert ok1 is True

        ok2, est2_id = modulo_catalogos.ic_guardar_estilo("ESTILO-B", "CORTE", 80.0, "Notas B")
        assert ok2 is True

        # Agregar fracciones para ESTILO-A
        f1_ok, f1_res = modulo_catalogos.ic_guardar_fraccion(est1_id, "COSTURA LATERAL", 50.0, 1)
        assert f1_ok is True
        f2_ok, f2_res = modulo_catalogos.ic_guardar_fraccion(est1_id, "REBOREDO", 70.0, 2)
        assert f2_ok is True

        # Listar estilos - todos
        estilos_todos = modulo_catalogos.ic_listar_estilos(buscar="")
        assert len(estilos_todos) == 2

        # Filtro por depto
        estilos_pespunte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
        assert len(estilos_pespunte) == 1
        assert estilos_pespunte[0]["estilo"] == "ESTILO-A"

        # Listar fracciones para ESTILO-A
        fracs = modulo_catalogos.ic_listar_fracciones(est1_id)
        assert len(fracs) == 2
        assert fracs[0]["nombre"] == "COSTURA LATERAL"
        assert fracs[0]["precio"] == 50.0
        assert fracs[1]["nombre"] == "REBOREDO"
        assert fracs[1]["precio"] == 70.0
