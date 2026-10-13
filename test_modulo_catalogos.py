"""
Tests for modulo_catalogos performance optimizations and functional correctness.
Mocks GUI dependencies (tkinter, customtkinter) for headless environments.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock


# Dummy classes for customtkinter mocking
class DummyCTkFrame:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass

    def place(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def winfo_children(self):
        return []

    def columnconfigure(self, *args, **kwargs):
        pass


class DummyCTkLabel:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass


class DummyCTkButton:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass


# Mock customtkinter module before importing modulo_catalogos
mock_ctk = MagicMock()
mock_ctk.CTkFrame = DummyCTkFrame
mock_ctk.CTkLabel = DummyCTkLabel
mock_ctk.CTkButton = DummyCTkButton
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.set_widget_scaling = MagicMock()
mock_ctk.set_window_scaling = MagicMock()
sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos
from modulo_catalogos import (
    cat_get_material_por_nombre,
    cat_get_nombres_clientes,
    cat_get_nombres_materiales,
    cat_get_nombres_proveedores,
    cat_get_nombres_trabajadores,
    cat_guardar,
    cat_init_db,
)


class TestModuloCatalogosOptimizations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tf:
            cls.temp_db_path = tf.name

        # Override DB path for tests
        modulo_catalogos.CAT_DB_PATH = cls.temp_db_path
        cat_init_db()

        # Seed sample data
        cat_guardar('materiales', {
            'nombre': 'CUERO BOVINO',
            'tipo_material': 'DIRECTO',
            'unidad_default': 'DM',
            'departamento': 'CORTE',
            'visible_monitor': 'SÍ',
            'es_principal': 'SÍ',
            'estatus': 'ACTIVO',
        })
        cat_guardar('materiales', {
            'nombre': 'HILO SINTETICO',
            'tipo_material': 'INDIRECTO',
            'unidad_default': 'MTS',
            'departamento': 'PESPUNTE',
            'visible_monitor': 'NO',
            'es_principal': 'NO',
            'estatus': 'INACTIVO',
        })

        cat_guardar('trabajadores', {'nombre': 'JUAN PEREZ', 'estatus': 'ACTIVO'})
        cat_guardar('trabajadores', {'nombre': 'MARIA GOMEZ', 'estatus': 'INACTIVO'})

        cat_guardar('proveedores', {'nombre': 'PROVEEDOR A', 'estatus': 'ACTIVO'})
        cat_guardar('proveedores', {'nombre': 'PROVEEDOR B', 'estatus': 'INACTIVO'})

        cat_guardar('clientes', {'nombre': 'CLIENTE X', 'estatus': 'ACTIVO'})
        cat_guardar('clientes', {'nombre': 'CLIENTE Y', 'estatus': 'INACTIVO'})

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            os.remove(cls.temp_db_path)

    def test_cat_get_material_por_nombre_existing(self):
        mat = cat_get_material_por_nombre('CUERO BOVINO')
        self.assertEqual(mat.get('nombre'), 'CUERO BOVINO')
        self.assertEqual(mat.get('tipo_material'), 'DIRECTO')
        self.assertEqual(mat.get('unidad_default'), 'DM')

    def test_cat_get_material_por_nombre_whitespace_and_case(self):
        mat = cat_get_material_por_nombre('   cuero bovino  ')
        self.assertEqual(mat.get('nombre'), 'CUERO BOVINO')

    def test_cat_get_material_por_nombre_nonexistent(self):
        mat = cat_get_material_por_nombre('INEXISTENTE')
        self.assertEqual(mat, {})

    def test_cat_get_material_por_nombre_empty(self):
        mat = cat_get_material_por_nombre('')
        self.assertEqual(mat, {})

    def test_cat_get_nombres_materiales(self):
        activos = cat_get_nombres_materiales(solo_activos=True)
        self.assertEqual(activos, ['CUERO BOVINO'])

        todos = cat_get_nombres_materiales(solo_activos=False)
        self.assertEqual(sorted(todos), ['CUERO BOVINO', 'HILO SINTETICO'])

    def test_cat_get_nombres_trabajadores(self):
        activos = cat_get_nombres_trabajadores(solo_activos=True)
        self.assertEqual(activos, ['JUAN PEREZ'])

        todos = cat_get_nombres_trabajadores(solo_activos=False)
        self.assertEqual(sorted(todos), ['JUAN PEREZ', 'MARIA GOMEZ'])

    def test_cat_get_nombres_proveedores(self):
        activos = cat_get_nombres_proveedores(solo_activos=True)
        self.assertEqual(activos, ['PROVEEDOR A'])

        todos = cat_get_nombres_proveedores(solo_activos=False)
        self.assertEqual(sorted(todos), ['PROVEEDOR A', 'PROVEEDOR B'])

    def test_cat_get_nombres_clientes(self):
        activos = cat_get_nombres_clientes(solo_activos=True)
        self.assertEqual(activos, ['CLIENTE X'])

        todos = cat_get_nombres_clientes(solo_activos=False)
        self.assertEqual(sorted(todos), ['CLIENTE X', 'CLIENTE Y'])

if __name__ == '__main__':
    unittest.main()
