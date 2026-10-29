# -*- coding: utf-8 -*-
"""
Tests for modulo_catalogos.py optimizations and core functionality.
"""
import os
import sqlite3
import pytest
import unittest.mock as mock

# Safely mock customtkinter and tkinter prior to importing modulo_catalogos
import sys
if "customtkinter" not in sys.modules:
    mock_ctk = mock.MagicMock()
    # Dummy classes for inheritance if needed
    class DummyFrame:
        def __init__(self, *args, **kwargs): pass
    mock_ctk.CTkFrame = DummyFrame
    sys.modules["customtkinter"] = mock_ctk

import modulo_catalogos as mc

TEST_DB_PATH = "test_catalogos_suite.sqlite"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    old_path = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    mc.cat_init_db()

    yield

    mc.CAT_DB_PATH = old_path
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def test_cat_init_db_indexes():
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        cur.execute(f"PRAGMA index_list({tabla})")
        indexes = [r[1] for r in cur.fetchall()]
        assert f"idx_{tabla}_nombre" in indexes
        assert f"idx_{tabla}_estatus_nombre" in indexes
    con.close()


def test_cat_get_nombres_functions():
    mc.cat_guardar("materiales", {"nombre": "SUELA DE GOMA", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "PIEL VACUNO", "estatus": "INACTIVO"})

    mats_activos = mc.cat_get_nombres_materiales(solo_activos=True)
    mats_todos = mc.cat_get_nombres_materiales(solo_activos=False)

    assert mats_activos == ["SUELA DE GOMA"]
    assert set(mats_todos) == {"SUELA DE GOMA", "PIEL VACUNO"}

    mc.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    trab_activos = mc.cat_get_nombres_trabajadores(solo_activos=True)
    assert trab_activos == ["JUAN PEREZ"]

    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR S.A.", "estatus": "ACTIVO"})
    prov_activos = mc.cat_get_nombres_proveedores(solo_activos=True)
    assert prov_activos == ["PROVEEDOR S.A."]

    mc.cat_guardar("clientes", {"nombre": "CLIENTE X", "estatus": "ACTIVO"})
    cli_activos = mc.cat_get_nombres_clientes(solo_activos=True)
    assert cli_activos == ["CLIENTE X"]


def test_cat_buscar_empty_text():
    mc.cat_guardar("materiales", {"nombre": "Hilo Rojo", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "Hilo Azul", "estatus": "ACTIVO"})

    res = mc.cat_buscar("materiales", "", "ACTIVO")
    assert len(res) == 2
    nombres = [r[1] for r in res]
    assert "HILO ROJO" in nombres
    assert "HILO AZUL" in nombres
