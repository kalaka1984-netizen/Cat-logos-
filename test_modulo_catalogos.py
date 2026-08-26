import os
import sqlite3
import time
import modulo_catalogos as mc
import pytest

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_catalogos_db.sqlite")


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Fixture to set up a clean temporary SQLite database for testing."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    monkeypatch.setattr(mc, "CAT_DB_PATH", TEST_DB)
    mc.cat_init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_database_initialization_indexes():
    """Verify that composite index idx_materiales_estatus_nombre and standard tables exist."""
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [r[0] for r in cur.fetchall()]
    con.close()
    assert "idx_materiales_nombre" in indexes
    assert "idx_materiales_estatus_nombre" in indexes
    assert "idx_trabajadores_estatus_nombre" in indexes


def test_cat_guardar_and_buscar():
    """Test saving catalog items and retrieving them via cat_buscar."""
    ok, mat_id = mc.cat_guardar("materiales", {
        "nombre": "piel vacuno cafe",
        "tipo_material": "DIRECTO",
        "unidad_default": "dm",
        "departamento": "CORTE",
        "estatus": "ACTIVO"
    })
    assert ok is True
    assert isinstance(mat_id, int)

    # Empty search string should bypass LIKE evaluations
    all_active = mc.cat_buscar("materiales", "", "ACTIVO")
    assert len(all_active) == 1
    assert all_active[0][1] == "PIEL VACUNO CAFE"

    # Specific search string
    filtered = mc.cat_buscar("materiales", "VACUNO", "ACTIVO")
    assert len(filtered) == 1
    assert filtered[0][1] == "PIEL VACUNO CAFE"


def test_cat_get_material_por_nombre():
    """Test exact material retrieval by name using direct SELECT."""
    mc.cat_guardar("materiales", {
        "nombre": "suela ranurada",
        "tipo_material": "DIRECTO",
        "unidad_default": "par",
        "departamento": "MONTADO",
        "visible_monitor": "SÍ"
    })

    mat = mc.cat_get_material_por_nombre("suela ranurada")
    assert mat.get("nombre") == "SUELA RANURADA"
    assert mat.get("unidad_default") == "PAR"
    assert mat.get("departamento") == "MONTADO"

    # Non-existent material
    assert mc.cat_get_material_por_nombre("invalido") == {}
    assert mc.cat_get_material_por_nombre("") == {}


def test_cat_get_nombres_functions():
    """Test optimized index-only name retrieval functions for materials, workers, suppliers, and clients."""
    mc.cat_guardar("materiales", {"nombre": "hilo 30", "estatus": "ACTIVO"})
    mc.cat_guardar("materiales", {"nombre": "clavos 1/2", "estatus": "INACTIVO"})

    mc.cat_guardar("trabajadores", {"nombre": "juan perez", "estatus": "ACTIVO"})
    mc.cat_guardar("proveedores", {"nombre": "proveedor alfa", "estatus": "ACTIVO"})
    mc.cat_guardar("clientes", {"nombre": "calzados beta", "estatus": "ACTIVO"})

    activos_mats = mc.cat_get_nombres_materiales(solo_activos=True)
    assert activos_mats == ["HILO 30"]

    todos_mats = mc.cat_get_nombres_materiales(solo_activos=False)
    assert todos_mats == ["CLAVOS 1/2", "HILO 30"]

    assert mc.cat_get_nombres_trabajadores(solo_activos=True) == ["JUAN PEREZ"]
    assert mc.cat_get_nombres_proveedores(solo_activos=True) == ["PROVEEDOR ALFA"]
    assert mc.cat_get_nombres_clientes(solo_activos=True) == ["CALZADOS BETA"]


def test_performance_benchmark():
    """Benchmark direct indexed search against O(N) full LIKE search."""
    # Populate DB with 1000 items
    for i in range(1000):
        mc.cat_guardar("materiales", {
            "nombre": f"MATERIAL MODELO {i:04d}",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "notas": "Texto largo de notas para abultar json " * 5,
            "estatus": "ACTIVO" if i % 2 == 0 else "INACTIVO"
        })

    target_name = "MATERIAL MODELO 0500"

    t0 = time.perf_counter()
    for _ in range(50):
        res1 = mc.cat_get_material_por_nombre(target_name)
    t1 = time.perf_counter()
    new_time = (t1 - t0) / 50

    assert res1.get("nombre") == target_name
    # Direct lookup should be fast (< 5ms per query on 1000 rows)
    assert new_time < 0.005
