import os
import unittest

import modulo_catalogos as mc

TEST_DB = "test_catalogos_temp.sqlite"

class TestModuloCatalogos(unittest.TestCase):
    def setUp(self):
        self.original_db_path = mc.CAT_DB_PATH
        mc.CAT_DB_PATH = TEST_DB
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        mc.ic_init_db()

    def tearDown(self):
        mc.CAT_DB_PATH = self.original_db_path
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_ic_listar_estilos_and_fracciones(self):
        ok, est1_id = mc.ic_guardar_estilo("ESTILO_001", "PESPUNTE", 50.0)
        self.assertTrue(ok)
        ok, est2_id = mc.ic_guardar_estilo("ESTILO_002", "CORTE", 30.0)
        self.assertTrue(ok)

        # Add fractions for ESTILO_001
        mc.ic_guardar_fraccion(est1_id, "FRAC_1", 20.0, 1)
        mc.ic_guardar_fraccion(est1_id, "FRAC_2", 30.0, 2)

        estilos = mc.ic_listar_estilos(buscar="", departamento="TODOS")
        self.assertEqual(len(estilos), 2)

        # Check pre-aggregated fields
        est1 = next(e for e in estilos if e["id"] == est1_id)
        est2 = next(e for e in estilos if e["id"] == est2_id)

        self.assertEqual(est1["n_frac"], 2)
        self.assertAlmostEqual(est1["suma_frac"], 50.0)
        self.assertEqual(est2["n_frac"], 0)
        self.assertAlmostEqual(est2["suma_frac"], 0.0)

if __name__ == "__main__":
    unittest.main()
