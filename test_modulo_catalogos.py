import os
import unittest

import modulo_catalogos


class TestModuloCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override the database path to a test database
        cls.orig_db_path = modulo_catalogos.CAT_DB_PATH
        cls.test_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_catalogos_db.sqlite"
        )
        modulo_catalogos.CAT_DB_PATH = cls.test_db_path

    @classmethod
    def tearDownClass(cls):
        # Restore the database path
        modulo_catalogos.CAT_DB_PATH = cls.orig_db_path
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except OSError:
                pass

    def setUp(self):
        # Always start with a fresh/empty database for each test
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

    def test_ic_guardar_y_listar_estilos(self):
        # Check initially empty
        estilos = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(estilos), 0)

        # Save style 1
        ok, res_id = modulo_catalogos.ic_guardar_estilo(
            estilo="estilo_a", departamento="corte", precio_par=15.50, notas="Estilo de prueba A"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(res_id)

        # Save style 2
        ok, _res_id2 = modulo_catalogos.ic_guardar_estilo(
            estilo="estilo_b", departamento="pespunte", precio_par=25.00, notas="Estilo de prueba B"
        )
        self.assertTrue(ok)

        # List all styles
        estilos = modulo_catalogos.ic_listar_estilos()
        self.assertEqual(len(estilos), 2)

        # Verify fields of style 1
        estilo_a = next(e for e in estilos if e["estilo"] == "ESTILO_A")
        self.assertEqual(estilo_a["departamento"], "CORTE")
        self.assertEqual(estilo_a["precio_par"], 15.50)
        self.assertEqual(estilo_a["notas"], "ESTILO DE PRUEBA A")

        # Test search
        estilos_search = modulo_catalogos.ic_listar_estilos(buscar="PRUEBA B")
        self.assertEqual(len(estilos_search), 1)
        self.assertEqual(estilos_search[0]["estilo"], "ESTILO_B")

        # Test filtering by depto
        estilos_depto = modulo_catalogos.ic_listar_estilos(departamento="CORTE")
        self.assertEqual(len(estilos_depto), 1)
        self.assertEqual(estilos_depto[0]["estilo"], "ESTILO_A")

    def test_ic_fracciones_y_tarifa(self):
        # Save a style
        _, est_id = modulo_catalogos.ic_guardar_estilo(
            estilo="estilo_x", departamento="montado", precio_par=30.00, notas="Prueba Fracciones"
        )

        # Verify no fractions initially
        fracs = modulo_catalogos.ic_listar_fracciones(est_id)
        self.assertEqual(len(fracs), 0)

        # Add fractions
        ok1, _ = modulo_catalogos.ic_guardar_fraccion(
            ic_estilo_id=est_id, nombre="frac1", precio=12.50, orden=1
        )
        self.assertTrue(ok1)

        ok2, _ = modulo_catalogos.ic_guardar_fraccion(
            ic_estilo_id=est_id, nombre="frac2", precio=17.50, orden=2
        )
        self.assertTrue(ok2)

        # Verify fractions are returned correctly
        fracs = modulo_catalogos.ic_listar_fracciones(est_id)
        self.assertEqual(len(fracs), 2)
        self.assertEqual(fracs[0]["nombre"], "FRAC1")
        self.assertEqual(fracs[0]["precio"], 12.50)
        self.assertEqual(fracs[1]["nombre"], "FRAC2")
        self.assertEqual(fracs[1]["precio"], 17.50)

        # Test get_tarifa
        tarifa = modulo_catalogos.ic_get_tarifa("estilo_x", "montado")
        self.assertEqual(tarifa["precio_par"], 30.00)
        self.assertEqual(tarifa["modo"], "FRACCIONADO")
        self.assertEqual(len(tarifa["fracciones"]), 2)

        # Delete one fraction
        modulo_catalogos.ic_eliminar_fraccion(fracs[0]["id"])
        fracs = modulo_catalogos.ic_listar_fracciones(est_id)
        self.assertEqual(len(fracs), 1)
        self.assertEqual(fracs[0]["nombre"], "FRAC2")

if __name__ == "__main__":
    unittest.main()
