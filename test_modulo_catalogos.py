# -*- coding: utf-8 -*-
"""
Unit tests for modulo_catalogos.py database and lookup optimizations.
"""

import os
import unittest
import modulo_catalogos

class TestModuloCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_catalogos_temp.sqlite"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        # Override DB path for test isolation
        modulo_catalogos.CAT_DB_PATH = cls.test_db
        modulo_catalogos.cat_init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_01_cat_guardar_and_get_material_por_nombre(self):
        mat_data = {
            "nombre": "piel vacuno negra",
            "tipo_material": "DIRECTO",
            "es_principal": "SÍ",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "proveedor_ref": "PROVEEDOR TEST",
            "costo_ref": "120.50",
            "notas": "Piel de alta calidad",
        }
        ok, res_id = modulo_catalogos.cat_guardar("materiales", mat_data)
        self.assertTrue(ok)
        self.assertIsInstance(res_id, int)

        # Retrieve material using cat_get_material_por_nombre
        fetched = modulo_catalogos.cat_get_material_por_nombre("piel vacuno negra")
        self.assertIsInstance(fetched, dict)
        self.assertEqual(fetched.get("nombre"), "PIEL VACUNO NEGRA")
        self.assertEqual(fetched.get("unidad_default"), "DM")
        self.assertEqual(fetched.get("departamento"), "CORTE")

        # Test non-existent material lookup
        non_existent = modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
        self.assertEqual(non_existent, {})

    def test_02_cat_buscar(self):
        # Insert additional records
        mats = [
            {"nombre": "HILO ROJO", "tipo_material": "INDIRECTO", "departamento": "PESPUNTE"},
            {"nombre": "SUELA GOMA", "tipo_material": "DIRECTO", "departamento": "MONTADO"},
        ]
        for m in mats:
            ok, _ = modulo_catalogos.cat_guardar("materiales", m)
            self.assertTrue(ok)

        # Test empty string search (should return all active materials without LIKE clause error)
        all_rows = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
        self.assertGreaterEqual(len(all_rows), 3)

        # Test filtered search
        filtered_rows = modulo_catalogos.cat_buscar("materiales", "SUELA", "TODOS")
        self.assertEqual(len(filtered_rows), 1)
        self.assertEqual(filtered_rows[0][1], "SUELA GOMA")

if __name__ == "__main__":
    unittest.main()
