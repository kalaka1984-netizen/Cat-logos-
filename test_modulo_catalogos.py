# -*- coding: utf-8 -*-
"""
Unit tests and performance benchmark verification for modulo_catalogos optimizations.
"""

import sys
import unittest
from unittest.mock import MagicMock

# Dummy custom classes for CustomTkinter widgets to avoid metaclass conflicts
class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs):
        pass
    def grid(self, *args, **kwargs):
        pass
    def place(self, *args, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass
    def unbind(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        pass
    def config(self, *args, **kwargs):
        pass
    def destroy(self):
        pass
    def winfo_children(self):
        return []
    def winfo_height(self):
        return 1000
    def winfo_width(self):
        return 1000
    def winfo_screenwidth(self):
        return 1920
    def winfo_screenheight(self):
        return 1080
    def winfo_toplevel(self):
        return self
    def winfo_exists(self):
        return True
    def after(self, ms, func=None, *args):
        return "timer_1"
    def after_cancel(self, timer_id):
        pass

class DummyCTkFrame(DummyWidget):
    pass

class DummyCTkLabel(DummyWidget):
    pass

class DummyCTkButton(DummyWidget):
    pass

class DummyCTkEntry(DummyWidget):
    pass

class DummyCTkScrollableFrame(DummyWidget):
    pass

class DummyCTkToplevel(DummyWidget):
    def resizable(self, *args, **kwargs):
        pass
    def lift(self, *args, **kwargs):
        pass
    def grab_set(self, *args, **kwargs):
        pass
    def grab_release(self, *args, **kwargs):
        pass
    def geometry(self, *args, **kwargs):
        pass

class DummyCTk:
    def set_appearance_mode(self, mode):
        pass
    def set_default_color_theme(self, theme):
        pass
    def set_widget_scaling(self, scaling):
        pass
    def set_window_scaling(self, scaling):
        pass

mock_ctk = MagicMock()
mock_ctk.set_appearance_mode = lambda m: None
mock_ctk.set_default_color_theme = lambda t: None
mock_ctk.set_widget_scaling = lambda s: None
mock_ctk.set_window_scaling = lambda s: None
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkLabel
mock_ctk.CTkButton = DummyCTkButton
mock_ctk.CTkEntry = DummyCTkEntry
mock_ctk.CTkScrollableFrame = DummyCTkScrollableFrame
mock_ctk.CTkToplevel = DummyCTkToplevel
sys.modules['customtkinter'] = mock_ctk

import os # noqa: E402
import tempfile # noqa: E402

# Override DB path for testing
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "test_catalogos_temp.sqlite")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

import modulo_catalogos # noqa: E402
modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH


class TestModuloCatalogosOptimizations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_cat_get_material_por_nombre(self):
        # Save a material
        datos = {
            "nombre": "CUERO VACUNO 1.8MM",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ"
        }
        ok, mat_id = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        # Retrieve material
        res = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO 1.8MM")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")
        self.assertEqual(res.get("unidad_default"), "DM")

        # Retrieve non-existent material
        empty_res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_INEXISTENTE")
        self.assertEqual(empty_res, {})

    def test_ic_listar_estilos_pre_agregacion(self):
        # Save style and fractions
        ok, est_id = modulo_catalogos.ic_guardar_estilo("ESTILO_TEST_01", "PESPUNTE", 100.0)
        self.assertTrue(ok)

        modulo_catalogos.ic_guardar_fraccion(est_id, "COSTURA LATERAL", 30.0, 1)
        modulo_catalogos.ic_guardar_fraccion(est_id, "COSTURA TRASERA", 70.0, 2)

        estilos = modulo_catalogos.ic_listar_estilos("ESTILO_TEST_01", "PESPUNTE")
        self.assertEqual(len(estilos), 1)
        st = estilos[0]
        self.assertEqual(st["estilo"], "ESTILO_TEST_01")
        self.assertEqual(st["n_frac"], 2)
        self.assertAlmostEqual(st["suma_frac"], 100.0)

    def test_ic_listar_estilos_index_filtering(self):
        # Save style in another department
        ok, est_id = modulo_catalogos.ic_guardar_estilo("ESTILO_CORTE_01", "CORTE", 50.0)
        self.assertTrue(ok)

        # Query by department using idx_ic_estilos_depto
        estilos_corte = modulo_catalogos.ic_listar_estilos("", "CORTE")
        self.assertTrue(any(e["estilo"] == "ESTILO_CORTE_01" for e in estilos_corte))
        self.assertFalse(any(e["estilo"] == "ESTILO_TEST_01" for e in estilos_corte))


if __name__ == "__main__":
    unittest.main()
