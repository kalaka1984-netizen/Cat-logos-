import sys
from unittest.mock import MagicMock

# Define dummy classes for Tkinter/Customtkinter components to avoid metaclass inheritance issues
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass
    def winfo_children(self):
        return []
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def after(self, *args, **kwargs):
        pass
    def after_cancel(self, *args, **kwargs):
        pass

class DummyCTkToplevel:
    def __init__(self, *args, **kwargs):
        pass
    def grab_release(self):
        pass
    def destroy(self):
        pass

class DummyTkFrame(DummyCTkFrame):
    pass

class DummyTkLabel:
    def __init__(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass

# Ensure winfo_screenwidth and winfo_screenheight return integer values to prevent TypeErrors in scaling functions
class DummyTk:
    def withdraw(self):
        pass
    def destroy(self):
        pass
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080

# Create mock modules
mock_tkinter = MagicMock()
mock_tkinter.Frame = DummyTkFrame
mock_tkinter.Label = DummyTkLabel
mock_tkinter.Tk = DummyTk
mock_tkinter.StringVar = MagicMock
mock_tkinter.DoubleVar = MagicMock
mock_tkinter.IntVar = MagicMock
mock_tkinter.BooleanVar = MagicMock

mock_customtkinter = MagicMock()
mock_customtkinter.CTkFrame = DummyCTkFrame
mock_customtkinter.CTkToplevel = DummyCTkToplevel
mock_customtkinter.CTkButton = MagicMock
mock_customtkinter.CTkLabel = MagicMock
mock_customtkinter.CTkEntry = MagicMock
mock_customtkinter.set_appearance_mode = MagicMock
mock_customtkinter.set_default_color_theme = MagicMock

sys.modules['tkinter'] = mock_tkinter
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['customtkinter'] = mock_customtkinter
sys.modules['darkdetect'] = MagicMock()

# Now import modulo_catalogos and run tests
import os  # noqa: E402
import sqlite3  # noqa: E402
import pytest  # noqa: E402
import modulo_catalogos  # noqa: E402

@pytest.fixture(autouse=True)
def setup_teardown_db():
    original_db_path = modulo_catalogos.CAT_DB_PATH
    temp_db_path = "test_catalogos_db.sqlite"
    modulo_catalogos.CAT_DB_PATH = temp_db_path

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass

    # Initialize DB
    modulo_catalogos.ic_init_db()

    yield

    # Clean up test DB
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass

    modulo_catalogos.CAT_DB_PATH = original_db_path

def test_ic_listar_estilos_empty_db():
    res = modulo_catalogos.ic_listar_estilos()
    assert res == []

def test_ic_listar_estilos_with_data():
    con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
    cur = con.cursor()

    # Style 1: CORTE, price 20.0
    cur.execute(
        "INSERT INTO ic_estilos (estilo, departamento, precio_par, notas, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
        ("ALPHA", "CORTE", 20.0, "Some notes", "2023-01-01", "2023-01-01")
    )
    style1_id = cur.lastrowid

    # Style 2: COSTURA, price 30.0
    cur.execute(
        "INSERT INTO ic_estilos (estilo, departamento, precio_par, notas, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
        ("BETA", "COSTURA", 30.0, "Beta notes", "2023-01-01", "2023-01-01")
    )

    # Fractions for Style 1: 2 fractions (10.5 and 9.5, total = 20.0)
    cur.execute(
        "INSERT INTO ic_fracciones (ic_estilo_id, nombre, precio, orden, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
        (style1_id, "FRAC_1", 10.5, 1, "2023-01-01", "2023-01-01")
    )
    cur.execute(
        "INSERT INTO ic_fracciones (ic_estilo_id, nombre, precio, orden, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?, ?)",
        (style1_id, "FRAC_2", 9.5, 2, "2023-01-01", "2023-01-01")
    )

    # Fractions for Style 2: 0 fractions

    con.commit()
    con.close()

    # Test 1: List all styles
    res = modulo_catalogos.ic_listar_estilos()
    assert len(res) == 2

    assert res[0]["estilo"] == "ALPHA"
    assert res[0]["departamento"] == "CORTE"
    assert res[0]["n_frac"] == 2
    assert res[0]["suma_frac"] == 20.0

    assert res[1]["estilo"] == "BETA"
    assert res[1]["departamento"] == "COSTURA"
    assert res[1]["n_frac"] == 0
    assert res[1]["suma_frac"] == 0.0

    # Test 2: Filter by department (CORTE)
    res_corte = modulo_catalogos.ic_listar_estilos(departamento="CORTE")
    assert len(res_corte) == 1
    assert res_corte[0]["estilo"] == "ALPHA"

    # Test 3: Search with empty string
    res_empty_search = modulo_catalogos.ic_listar_estilos(buscar="  ")
    assert len(res_empty_search) == 2

    # Test 4: Search matching ALPHA
    res_search_alpha = modulo_catalogos.ic_listar_estilos(buscar="alpha")
    assert len(res_search_alpha) == 1
    assert res_search_alpha[0]["estilo"] == "ALPHA"

    # Test 5: Search matching BETA
    res_search_beta = modulo_catalogos.ic_listar_estilos(buscar="beta")
    assert len(res_search_beta) == 1
    assert res_search_beta[0]["estilo"] == "BETA"

    # Test 6: Search with no matches
    res_no_match = modulo_catalogos.ic_listar_estilos(buscar="gamma")
    assert len(res_no_match) == 0
