import os
import unittest
import modulo_catalogos


class TestModuloCatalogosPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override database path to use a temporary test database
        cls.test_db_path = "test_catalogos_db.sqlite"
        modulo_catalogos.CAT_DB_PATH = cls.test_db_path

        # Ensure no residual test database exists from previous runs
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        # Initialize the test database tables
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    @classmethod
    def tearDownClass(cls):
        # Remove the temporary test database to keep repository clean
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        # Clear/Truncate tables before each test for clean test isolation
        import sqlite3
        con = sqlite3.connect(self.test_db_path)
        cur = con.cursor()
        cur.execute("DELETE FROM ic_estilos")
        cur.execute("DELETE FROM ic_fracciones")
        con.commit()
        con.close()

    def test_ic_listar_estilos_pre_aggregation(self):
        """
        Verifies that `ic_listar_estilos` correctly returns the count of fractions (n_frac)
        and sum of fraction prices (suma_frac) using optimized LEFT JOIN and TOTAL().
        """
        # 1. Create a style
        ok, estilo_id = modulo_catalogos.ic_guardar_estilo(
            estilo="ESTILO-A",
            departamento="CORTE",
            precio_par=150.50,
            notas="Test style"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(estilo_id)

        # 2. Verify initial pre-aggregation (0 fractions)
        estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO-A")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["n_frac"], 0)
        self.assertEqual(estilos[0]["suma_frac"], 0.0)

        # 3. Add fractions
        ok1, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id, "OP1", 10.25, 1)
        ok2, _ = modulo_catalogos.ic_guardar_fraccion(estilo_id, "OP2", 20.75, 2)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # 4. Verify aggregated fields are correct
        estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO-A")
        self.assertEqual(len(estilos), 1)
        self.assertEqual(estilos[0]["n_frac"], 2)
        self.assertEqual(estilos[0]["suma_frac"], 31.0)  # 10.25 + 20.75

    def test_ic_listar_estilos_empty_search_optimization(self):
        """
        Verifies that `ic_listar_estilos` works correctly when empty strings or
        whitespace are provided as search terms, ensuring we hit the optimized fast-path.
        """
        # Save style 1
        modulo_catalogos.ic_guardar_estilo("ESTILO-A", "PESPUNTE", 80.0)
        # Save style 2
        modulo_catalogos.ic_guardar_estilo("ESTILO-B", "PESPUNTE", 90.0)

        # Empty search should return all styles in department
        estilos_all = modulo_catalogos.ic_listar_estilos(buscar="")
        self.assertEqual(len(estilos_all), 2)

        estilos_all_space = modulo_catalogos.ic_listar_estilos(buscar="   ")
        self.assertEqual(len(estilos_all_space), 2)

        # Non-empty search should filter
        estilos_filtered = modulo_catalogos.ic_listar_estilos(buscar="ESTILO-A")
        self.assertEqual(len(estilos_filtered), 1)
        self.assertEqual(estilos_filtered[0]["estilo"], "ESTILO-A")

    def test_ic_listar_estilos_department_filters(self):
        """
        Verifies that department-specific filtering behaves correctly with pre-aggregation.
        """
        ok1, id1 = modulo_catalogos.ic_guardar_estilo("STYLE-1", "CORTE", 100.0)
        ok2, id2 = modulo_catalogos.ic_guardar_estilo("STYLE-2", "PESPUNTE", 200.0)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # Add a fraction to STYLE-1
        modulo_catalogos.ic_guardar_fraccion(id1, "FRAC1", 5.0, 1)

        # Filter by CORTE
        estilos_corte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
        self.assertEqual(len(estilos_corte), 1)
        self.assertEqual(estilos_corte[0]["estilo"], "STYLE-1")
        self.assertEqual(estilos_corte[0]["n_frac"], 1)
        self.assertEqual(estilos_corte[0]["suma_frac"], 5.0)

        # Filter by PESPUNTE
        estilos_pespunte = modulo_catalogos.ic_listar_estilos(buscar="", departamento="PESPUNTE")
        self.assertEqual(len(estilos_pespunte), 1)
        self.assertEqual(estilos_pespunte[0]["estilo"], "STYLE-2")
        self.assertEqual(estilos_pespunte[0]["n_frac"], 0)
        self.assertEqual(estilos_pespunte[0]["suma_frac"], 0.0)


if __name__ == "__main__":
    unittest.main()
