# -*- coding: utf-8 -*-
"""
Pruebas unitarias para modulo_catalogos.py
Verifica inicialización de BD, operaciones CRUD, optimizaciones de consultas y pre-agregación.
"""

import os
import unittest
import sqlite3

# En entorno headless, aseguramos que modulo_catalogos se importe sin errores de Tk/ctk
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_temp.sqlite")

import modulo_catalogos as mc  # noqa: E402

class TestModuloCatalogos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mc.CAT_DB_PATH = TEST_DB_PATH

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        mc.cat_init_db()
        mc.ic_init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_cat_init_db_and_indexes(self):
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {r[0] for r in cur.fetchall()}
        con.close()

        self.assertIn("idx_materiales_nombre", indexes)
        self.assertIn("idx_trabajadores_nombre", indexes)
        self.assertIn("idx_proveedores_nombre", indexes)
        self.assertIn("idx_clientes_nombre", indexes)
        self.assertIn("idx_ic_estilo", indexes)
        self.assertIn("idx_ic_estilos_depto", indexes)
        self.assertIn("idx_ic_frac_estilo", indexes)

    def test_cat_guardar_and_direct_material_lookup(self):
        datos_mat = {
            "nombre": "piel vacuna cafe",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE"
        }
        ok, reg_id = mc.cat_guardar("materiales", datos_mat)
        self.assertTrue(ok)

        # cat_guardar fuerza mayúsculas
        res = mc.cat_get_material_por_nombre("piel vacuna cafe")
        self.assertEqual(res.get("nombre"), "PIEL VACUNA CAFE")
        self.assertEqual(res.get("tipo_material"), "DIRECTO")

        # Inexistente
        res_empty = mc.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
        self.assertEqual(res_empty, {})

    def test_cat_get_nombres_tabla_helper(self):
        mc.cat_guardar("materiales", {"nombre": "ZETA MATERIAL", "estatus": "ACTIVO"})
        mc.cat_guardar("materiales", {"nombre": "ALPHA MATERIAL", "estatus": "ACTIVO"})
        mc.cat_guardar("materiales", {"nombre": "INACTIVO MATERIAL", "estatus": "INACTIVO"})

        activos = mc.cat_get_nombres_materiales(solo_activos=True)
        self.assertEqual(activos, ["ALPHA MATERIAL", "ZETA MATERIAL"])

        todos = mc.cat_get_nombres_materiales(solo_activos=False)
        self.assertEqual(todos, ["ALPHA MATERIAL", "INACTIVO MATERIAL", "ZETA MATERIAL"])

    def test_ic_listar_estilos_preaggregation(self):
        # Crear estilo
        ok, est_id = mc.ic_guardar_estilo("ESTILO_001", "PESPUNTE", 200.0, "Nota de prueba")
        self.assertTrue(ok)

        # Crear fracciones
        mc.ic_guardar_fraccion(est_id, "COSTURA LATERAL", 50.0, 1)
        mc.ic_guardar_fraccion(est_id, "TALONERA", 150.0, 2)

        estilos = mc.ic_listar_estilos(buscar="ESTILO_001")
        self.assertEqual(len(estilos), 1)
        row = estilos[0]
        self.assertEqual(row["estilo"], "ESTILO_001")
        self.assertEqual(row["departamento"], "PESPUNTE")
        self.assertEqual(row["n_frac"], 2)
        self.assertEqual(row["suma_frac"], 200.0)

    def test_ic_listar_estilos_sin_fracciones(self):
        ok, est_id = mc.ic_guardar_estilo("ESTILO_SIMPLE", "CORTE", 80.0)
        self.assertTrue(ok)

        estilos = mc.ic_listar_estilos(buscar="ESTILO_SIMPLE")
        self.assertEqual(len(estilos), 1)
        row = estilos[0]
        self.assertEqual(row["n_frac"], 0)
        self.assertEqual(row["suma_frac"], 0.0)

if __name__ == "__main__":
    unittest.main()
