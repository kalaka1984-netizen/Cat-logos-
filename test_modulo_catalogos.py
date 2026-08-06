import os
import sqlite3
import unittest

# Ensure we mock/override the database path during testing
import modulo_catalogos

TEST_DB_PATH = "test_catalogos_db.sqlite"


class TestModuloCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override the database path to a test database file
        modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        # Initialize database
        modulo_catalogos.ic_init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up the test database file
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except OSError:
                pass

    def setUp(self):
        # Clean database state before each test
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("DELETE FROM ic_fracciones")
        cur.execute("DELETE FROM ic_estilos")
        con.commit()
        con.close()

    def test_database_indices_created(self):
        # Verify that idx_ic_estilos_depto exists in the SQLite database
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = [r[0] for r in cur.fetchall()]
        con.close()

        self.assertIn("idx_ic_estilos_depto", indices)
        self.assertIn("idx_ic_estilo", indices)
        self.assertIn("idx_ic_frac_estilo", indices)

    def test_ic_listar_estilos_empty(self):
        # Verify listing on empty database
        res = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(res), 0)

    def test_ic_listar_estilos_pre_aggregation(self):
        # Create a style and multiple fractions
        success, _ = modulo_catalogos.ic_guardar_estilo(
            estilo="ESTILO-A",
            departamento="CORTADO",
            precio_par=150.0,
            notas="Some notes",
        )
        self.assertTrue(success)

        # Get the style ID
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id FROM ic_estilos WHERE estilo='ESTILO-A'")
        estilo_id = cur.fetchone()[0]
        con.close()

        # Add some fractions
        modulo_catalogos.ic_guardar_fraccion(
            ic_estilo_id=estilo_id,
            nombre="Fraccion 1",
            precio=45.5,
            orden=1,
        )
        modulo_catalogos.ic_guardar_fraccion(
            ic_estilo_id=estilo_id,
            nombre="Fraccion 2",
            precio=55.0,
            orden=2,
        )

        # Retrieve styles
        estilos = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(estilos), 1)

        style_entry = estilos[0]
        self.assertEqual(style_entry["estilo"], "ESTILO-A")
        self.assertEqual(style_entry["departamento"], "CORTADO")
        self.assertEqual(style_entry["precio_par"], 150.0)
        self.assertEqual(style_entry["n_frac"], 2)
        self.assertEqual(style_entry["suma_frac"], 100.5)

    def test_ic_listar_estilos_search_and_filter(self):
        # Create style A
        success, _ = modulo_catalogos.ic_guardar_estilo(
            estilo="ESTILO-A",
            departamento="CORTADO",
            precio_par=10.0,
            notas="Classic design",
        )
        self.assertTrue(success)

        # Create style B
        success, _ = modulo_catalogos.ic_guardar_estilo(
            estilo="ESTILO-B",
            departamento="PESPUNTE",
            precio_par=20.0,
            notas="Modern layout",
        )
        self.assertTrue(success)

        # 1. Filter by departamento "CORTADO"
        estilos_cortado = modulo_catalogos.ic_listar_estilos(
            departamento="CORTADO"
        )
        self.assertEqual(len(estilos_cortado), 1)
        self.assertEqual(estilos_cortado[0]["estilo"], "ESTILO-A")

        # 2. Filter by departamento "PESPUNTE"
        estilos_pespunte = modulo_catalogos.ic_listar_estilos(
            departamento="PESPUNTE"
        )
        self.assertEqual(len(estilos_pespunte), 1)
        self.assertEqual(estilos_pespunte[0]["estilo"], "ESTILO-B")

        # 3. Search by name/notes
        estilos_search_classic = modulo_catalogos.ic_listar_estilos(
            buscar="classic"
        )
        self.assertEqual(len(estilos_search_classic), 1)
        self.assertEqual(estilos_search_classic[0]["estilo"], "ESTILO-A")

        estilos_search_b = modulo_catalogos.ic_listar_estilos(buscar="b")
        self.assertEqual(len(estilos_search_b), 1)
        self.assertEqual(estilos_search_b[0]["estilo"], "ESTILO-B")

        # 4. Search and filter department combined
        estilos_combined = modulo_catalogos.ic_listar_estilos(
            buscar="classic", departamento="PESPUNTE"
        )
        self.assertEqual(len(estilos_combined), 0)
