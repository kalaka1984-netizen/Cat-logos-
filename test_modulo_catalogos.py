"""Unit tests for database query optimizations and operations in modulo_catalogos.py."""

import os
import sqlite3
import tempfile
import unittest

# Temporary database path for testing
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".sqlite")
os.close(temp_db_fd)

import modulo_catalogos

modulo_catalogos.CAT_DB_PATH = temp_db_path


class TestModuloCatalogosOptimizations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        modulo_catalogos.cat_init_db()
        modulo_catalogos.ic_init_db()

    def setUp(self):
        # Clean tables between tests
        con = sqlite3.connect(modulo_catalogos.CAT_DB_PATH)
        cur = con.cursor()
        for tbl in [
            "materiales",
            "trabajadores",
            "proveedores",
            "clientes",
            "ic_estilos",
            "ic_fracciones",
        ]:
            cur.execute(f"DELETE FROM {tbl}")
        con.commit()
        con.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

    def test_cat_guardar_and_cat_get_material_por_nombre(self):
        """Test direct SELECT optimization for cat_get_material_por_nombre."""
        datos = {
            "nombre": "Piel Vacuna Negra",
            "tipo_material": "DIRECTO",
            "unidad_default": "DM",
            "departamento": "CORTE",
            "costo_ref": 12.50,
        }
        ok, reg_id = modulo_catalogos.cat_guardar("materiales", datos)
        self.assertTrue(ok)
        self.assertIsInstance(reg_id, int)

        # Retrieve material by exact name (case-insensitive search)
        mat = modulo_catalogos.cat_get_material_por_nombre("piel vacuna negra")
        self.assertEqual(mat.get("nombre"), "PIEL VACUNA NEGRA")
        self.assertEqual(mat.get("unidad_default"), "DM")
        self.assertEqual(mat.get("costo_ref"), 12.50)

        # Retrieve non-existent material
        empty_mat = modulo_catalogos.cat_get_material_por_nombre("PIEL INEXISTENTE")
        self.assertEqual(empty_mat, {})

        # Empty string lookup
        empty_str_mat = modulo_catalogos.cat_get_material_por_nombre("   ")
        self.assertEqual(empty_str_mat, {})

    def test_cat_buscar_empty_and_non_empty(self):
        """Test cat_buscar optimization for empty vs non-empty search strings."""
        datos1 = {"nombre": "Hilo Pespunte Red", "estatus": "ACTIVO"}
        datos2 = {"nombre": "Suela Goma Black", "estatus": "INACTIVO"}
        modulo_catalogos.cat_guardar("materiales", datos1)
        modulo_catalogos.cat_guardar("materiales", datos2)

        # Search with empty string and TODOS status
        res_all = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
        self.assertEqual(len(res_all), 2)

        # Search with empty string and ACTIVO status
        res_active = modulo_catalogos.cat_buscar("materiales", "", "ACTIVO")
        self.assertEqual(len(res_active), 1)
        self.assertEqual(res_active[0][1], "HILO PESPUNTE RED")

        # Search with keyword
        res_kw = modulo_catalogos.cat_buscar("materiales", "GOMA", "TODOS")
        self.assertEqual(len(res_kw), 1)
        self.assertEqual(res_kw[0][1], "SUELA GOMA BLACK")

    def test_ic_listar_estilos_pre_aggregation(self):
        """Test IC pre-aggregation in ic_listar_estilos (N+1 query optimization)."""
        ok1, est1_id = modulo_catalogos.ic_guardar_estilo(
            "ESTILO_001", "CORTE", 100.0
        )
        self.assertTrue(ok1)

        ok2, est2_id = modulo_catalogos.ic_guardar_estilo(
            "ESTILO_002", "PESPUNTE", 150.0
        )
        self.assertTrue(ok2)

        # Add fractions for ESTILO_001
        modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE DE PIEL", 40.0, 1)
        modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE DE FORRO", 60.0, 2)

        # List all styles
        estilos = modulo_catalogos.ic_listar_estilos("", "TODOS")
        self.assertEqual(len(estilos), 2)

        # Check pre-aggregated fields
        est1_data = next(e for e in estilos if e["id"] == est1_id)
        self.assertEqual(est1_data["n_frac"], 2)
        self.assertAlmostEqual(est1_data["suma_frac"], 100.0)

        # Style without fractions
        est2_data = next(e for e in estilos if e["id"] == est2_id)
        self.assertEqual(est2_data["n_frac"], 0)
        self.assertAlmostEqual(est2_data["suma_frac"], 0.0)

        # Department filter test
        estilos_corte = modulo_catalogos.ic_listar_estilos("", "CORTE")
        self.assertEqual(len(estilos_corte), 1)
        self.assertEqual(estilos_corte[0]["estilo"], "ESTILO_001")


if __name__ == "__main__":
    unittest.main()
