import os
import unittest
import sys
from unittest.mock import MagicMock

# Inject dummy customtkinter if needed
if "customtkinter" not in sys.modules:
    dummy_ctk = MagicMock()
    class DummyWidget:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def place(self, *args, **kwargs): pass
        def grid(self, *args, **kwargs): pass
        def winfo_children(self): return []
        def destroy(self): pass
        def after(self, *args, **kwargs): pass
        def after_cancel(self, *args, **kwargs): pass
        def bind(self, *args, **kwargs): pass
        def configure(self, *args, **kwargs): pass
        def lift(self): pass
        def lower(self): pass

    dummy_ctk.CTkFrame = DummyWidget
    dummy_ctk.CTkLabel = DummyWidget
    dummy_ctk.CTkButton = DummyWidget
    dummy_ctk.CTkEntry = DummyWidget
    dummy_ctk.CTkComboBox = DummyWidget
    sys.modules["customtkinter"] = dummy_ctk

import modulo_catalogos as mc

class TestModuloCatalogosOptimizations(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_catalogos_temp.sqlite"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        mc.CAT_DB_PATH = self.test_db
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_ic_listar_estilos_pre_aggregation(self):
        # 1. Test empty list
        self.assertEqual(mc.ic_listar_estilos(), [])

        # 2. Add style A (with 2 fractions) and style B (with 0 fractions)
        ok1, id_a = mc.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 100.0)
        self.assertTrue(ok1)
        ok2, id_b = mc.ic_guardar_estilo("ESTILO_B", "CORTE", 50.0)
        self.assertTrue(ok2)

        mc.ic_guardar_fraccion(id_a, "FRAC_1", 40.0, orden=1)
        mc.ic_guardar_fraccion(id_a, "FRAC_2", 60.0, orden=2)

        estilos = mc.ic_listar_estilos()
        self.assertEqual(len(estilos), 2)

        # Order by departamento: CORTE then PESPUNTE
        est_b = estilos[0]
        self.assertEqual(est_b["estilo"], "ESTILO_B")
        self.assertEqual(est_b["n_frac"], 0)
        self.assertEqual(est_b["suma_frac"], 0.0)

        est_a = estilos[1]
        self.assertEqual(est_a["estilo"], "ESTILO_A")
        self.assertEqual(est_a["n_frac"], 2)
        self.assertEqual(est_a["suma_frac"], 100.0)

    def test_ic_listar_estilos_filtering(self):
        mc.ic_guardar_estilo("SUELA_X", "PESPUNTE", 10.0)
        mc.ic_guardar_estilo("PIEL_Y", "CORTE", 20.0)

        res_p = mc.ic_listar_estilos(departamento="PESPUNTE")
        self.assertEqual(len(res_p), 1)
        self.assertEqual(res_p[0]["estilo"], "SUELA_X")

        res_s = mc.ic_listar_estilos(buscar="PIEL")
        self.assertEqual(len(res_s), 1)
        self.assertEqual(res_s[0]["estilo"], "PIEL_Y")

    def test_cat_get_material_por_nombre(self):
        datos = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad": "DM",
            "departamento": "CORTE"
        }
        ok, mat_id = mc.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        # Lookup with exact match and case/whitespace variations
        res1 = mc.cat_get_material_por_nombre("CUERO VACUNO")
        self.assertEqual(res1.get("tipo_material"), "DIRECTO")

        res2 = mc.cat_get_material_por_nombre(" cuero vacuno ")
        self.assertEqual(res2.get("tipo_material"), "DIRECTO")

        # Non-existent material
        res3 = mc.cat_get_material_por_nombre("NO EXISTE")
        self.assertEqual(res3, {})

if __name__ == "__main__":
    unittest.main()
