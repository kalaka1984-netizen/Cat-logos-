import os
import unittest

import modulo_catalogos as mc


class TestModuloCatalogos(unittest.TestCase):
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

    def test_ic_init_db_indexes(self):
        """Verify indexes exist on ic_estilos and ic_fracciones."""
        con = mc.sqlite3.connect(self.test_db)
        cur = con.cursor()
        cur.execute("PRAGMA index_list('ic_estilos')")
        indexes = {r[1] for r in cur.fetchall()}
        self.assertIn("idx_ic_estilo", indexes)
        self.assertIn("idx_ic_estilos_depto", indexes)

        cur.execute("PRAGMA index_list('ic_fracciones')")
        frac_indexes = {r[1] for r in cur.fetchall()}
        self.assertIn("idx_ic_frac_estilo", frac_indexes)
        con.close()

    def test_ic_listar_estilos_aggregation(self):
        """Verify ic_listar_estilos precomputes n_frac and suma_frac correctly."""
        # 1. Add estilo without fractions
        ok1, _est1_id = mc.ic_guardar_estilo("BOTA_01", "CORTE", 25.50, "Bota de trabajo")
        self.assertTrue(ok1)

        # 2. Add estilo with 3 fractions
        ok2, est2_id = mc.ic_guardar_estilo("ZAPATO_02", "PESPUNTE", 18.00, "Zapato vestir")
        self.assertTrue(ok2)

        mc.ic_guardar_fraccion(est2_id, "COSTURA_LATERAL", 5.00, 1)
        mc.ic_guardar_fraccion(est2_id, "VIVO", 4.50, 2)
        mc.ic_guardar_fraccion(est2_id, "TALON", 8.50, 3)

        # Query all
        estilos = mc.ic_listar_estilos("", "TODOS")
        self.assertEqual(len(estilos), 2)

        est_map = {e["estilo"]: e for e in estilos}

        # Style 1: no fractions
        self.assertEqual(est_map["BOTA_01"]["n_frac"], 0)
        self.assertEqual(est_map["BOTA_01"]["suma_frac"], 0.0)
        self.assertEqual(est_map["BOTA_01"]["departamento"], "CORTE")
        self.assertEqual(est_map["BOTA_01"]["precio_par"], 25.50)

        # Style 2: 3 fractions summing to 18.00
        self.assertEqual(est_map["ZAPATO_02"]["n_frac"], 3)
        self.assertAlmostEqual(est_map["ZAPATO_02"]["suma_frac"], 18.00, places=2)
        self.assertEqual(est_map["ZAPATO_02"]["departamento"], "PESPUNTE")
        self.assertEqual(est_map["ZAPATO_02"]["precio_par"], 18.00)

        # Query filtered by department
        pespunte_estilos = mc.ic_listar_estilos("", "PESPUNTE")
        self.assertEqual(len(pespunte_estilos), 1)
        self.assertEqual(pespunte_estilos[0]["estilo"], "ZAPATO_02")

        # Query filtered by search keyword
        search_estilos = mc.ic_listar_estilos("BOTA", "TODOS")
        self.assertEqual(len(search_estilos), 1)
        self.assertEqual(search_estilos[0]["estilo"], "BOTA_01")


if __name__ == "__main__":
    unittest.main()
