import os
import tempfile

import pytest

import modulo_catalogos as mc


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    original_db = mc.CAT_DB_PATH
    mc.CAT_DB_PATH = path
    mc.cat_init_db()
    mc.ic_init_db()
    yield path
    mc.CAT_DB_PATH = original_db
    if os.path.exists(path):
        os.remove(path)


def test_cat_init_db_indexes(temp_db):
    import sqlite3
    con = sqlite3.connect(temp_db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cur.fetchall()}
    con.close()

    for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
        assert f"idx_{tabla}_nombre" in indexes
        assert f"idx_{tabla}_estatus_nombre" in indexes


def test_cat_get_material_por_nombre(temp_db):
    data = {
        "nombre": "PIEL SINTETICA NEGRA",
        "tipo_material": "DIRECTO",
        "unidad_default": "DM",
        "departamento": "CORTE",
        "visible_monitor": "SÍ"
    }
    status, _ = mc.cat_guardar("materiales", data)
    assert status is True

    result = mc.cat_get_material_por_nombre("piel sintetica negra")
    assert result.get("nombre") == "PIEL SINTETICA NEGRA"
    assert result.get("departamento") == "CORTE"

    # Non-existent material should return empty dict
    assert mc.cat_get_material_por_nombre("MATERIAL INEXISTENTE") == {}


def test_cat_get_nombres_functions(temp_db):
    mc.cat_guardar("materiales", {"nombre": "SUELA HULE 01", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "SUELA HULE 02", "estatus": "INACTIVO"})

    mc.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "PROVEEDOR ALFA", "estatus": "ACTIVO"})
    mc.cat_guardar("clientes", {"nombre": "CLIENTE BETA", "estatus": "ACTIVO"})

    activos_mats = mc.cat_get_nombres_materiales(solo_activos=True)
    assert "SUELA HULE 01" in activos_mats
    assert "SUELA HULE 02" not in activos_mats

    todos_mats = mc.cat_get_nombres_materiales(solo_activos=False)
    assert "SUELA HULE 01" in todos_mats
    assert "SUELA HULE 02" in todos_mats

    assert "JUAN PEREZ" in mc.cat_get_nombres_trabajadores()
    assert "PROVEEDOR ALFA" in mc.cat_get_nombres_proveedores()
    assert "CLIENTE BETA" in mc.cat_get_nombres_clientes()


def test_cat_buscar(temp_db):
    mc.cat_guardar("materiales", {"nombre": "HILO ROJO", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "HILO AZUL", "estatus": "INACTIVO"})

    # Empty search query
    rows_empty_activo = mc.cat_buscar("materiales", "", "ACTIVO")
    assert len(rows_empty_activo) == 1
    assert rows_empty_activo[0][1] == "HILO ROJO"

    rows_empty_todos = mc.cat_buscar("materiales", "", "TODOS")
    assert len(rows_empty_todos) == 2

    # Specific search query
    rows_query = mc.cat_buscar("materiales", "AZUL", "TODOS")
    assert len(rows_query) == 1
    assert rows_query[0][1] == "HILO AZUL"


def test_ic_listar_estilos(temp_db):
    mc.ic_guardar_estilo("ESTILO_A", "CORTE", 10.0)
    mc.ic_guardar_estilo("ESTILO_B", "MONTADO", 12.5)

    estilos_todos = mc.ic_listar_estilos("", "TODOS")
    assert len(estilos_todos) == 2

    estilos_corte = mc.ic_listar_estilos("", "CORTE")
    assert len(estilos_corte) == 1
    assert estilos_corte[0]["estilo"] == "ESTILO_A"

    estilos_busqueda = mc.ic_listar_estilos("ESTILO_B", "TODOS")
    assert len(estilos_busqueda) == 1
    assert estilos_busqueda[0]["estilo"] == "ESTILO_B"
