import os
import unittest

import modulo_catalogos as mc


class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/test_cat_temp.sqlite"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.orig_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = self.db_path
        mc.cat_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_cat_get_material_por_nombre(self):
        datos = {
            "nombre": "CUERO VACUNO NEGRO",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
        }
        ok, _ = mc.cat_guardar("materiales", datos)
        self.assertTrue(ok)

        # Exact match case insensitive
        res = mc.cat_get_material_por_nombre("cuero vacuno negro")
        self.assertEqual(res.get("nombre"), "CUERO VACUNO NEGRO")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")

        # Non-existent
        res_none = mc.cat_get_material_por_nombre("NO EXISTE")
        self.assertEqual(res_none, {})

    def test_cat_precarga_material(self):
        datos = {
            "nombre": "PIEL FLOR",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ",
        }
        mc.cat_guardar("materiales", datos)
        precarga = mc.cat_precarga_material("PIEL FLOR")
        self.assertEqual(precarga.get("tipo_ft"), "DIR")
        self.assertEqual(precarga.get("unidad"), "DM")
        self.assertTrue(precarga.get("monitor"))
        self.assertTrue(precarga.get("principal"))


if __name__ == "__main__":
    unittest.main()
