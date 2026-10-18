import os
import tempfile
import time

import pytest

# Test setup for isolated temporary database
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "test_catalogos_temp.sqlite")

if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except OSError:
        pass

import modulo_catalogos

modulo_catalogos.CAT_DB_PATH = TEST_DB_FILE


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass
    modulo_catalogos.cat_init_db()
    yield
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass


def test_cat_init_db_and_guardar():
    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "CUERO VACUNO",
        "tipo": "DIRECTO",
        "unidad": "DM2",
        "estatus": "ACTIVO"
    })
    modulo_catalogos.cat_guardar("materiales", {
        "nombre": "SUELA INACTIVA",
        "tipo": "DIRECTO",
        "unidad": "PAR",
        "estatus": "INACTIVO"
    })

    mat = modulo_catalogos.cat_get_material_por_nombre("CUERO VACUNO")
    assert mat["nombre"] == "CUERO VACUNO"
    assert mat["tipo"] == "DIRECTO"
    assert mat["unidad"] == "DM2"

    mat_case = modulo_catalogos.cat_get_material_por_nombre("  cuero vacuno  ")
    assert mat_case["nombre"] == "CUERO VACUNO"

    mat_none = modulo_catalogos.cat_get_material_por_nombre("INEXISTENTE")
    assert mat_none == {}


def test_cat_get_nombres_tabla():
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})
    modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT C", "estatus": "ACTIVO"})

    activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
    assert activos == ["MAT A", "MAT C"]

    todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
    assert todos == ["MAT A", "MAT B", "MAT C"]

    with pytest.raises(ValueError, match="Tabla no permitida"):
        modulo_catalogos._cat_get_nombres_tabla("tabla_invalida")


def test_cat_get_nombres_trabajadores_proveedores_clientes():
    modulo_catalogos.cat_guardar("trabajadores", {"nombre": "JUAN PEREZ", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("proveedores", {"nombre": "PROVEEDOR X", "estatus": "ACTIVO"})
    modulo_catalogos.cat_guardar("clientes", {"nombre": "CLIENTE Y", "estatus": "ACTIVO"})

    assert modulo_catalogos.cat_get_nombres_trabajadores() == ["JUAN PEREZ"]
    assert modulo_catalogos.cat_get_nombres_proveedores() == ["PROVEEDOR X"]
    assert modulo_catalogos.cat_get_nombres_clientes() == ["CLIENTE Y"]


def test_performance_benchmark():
    # Insert 200 items into catalog
    for i in range(200):
        modulo_catalogos.cat_guardar("materiales", {
            "nombre": f"MATERIAL_{i:04d}",
            "tipo": "DIRECTO",
            "unidad": "MTS",
            "estatus": "ACTIVO" if i % 2 == 0 else "INACTIVO"
        })

    # Measure lookup speed
    t0 = time.perf_counter()
    for _ in range(100):
        res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_0100")
        assert res["nombre"] == "MATERIAL_0100"
    t1 = time.perf_counter()

    duration_ms = (t1 - t0) * 1000
    print(f"\n100 material lookups took {duration_ms:.2f} ms")
    # Assert 100 lookups complete in < 100ms
    assert duration_ms < 100.0
