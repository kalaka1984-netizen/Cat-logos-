import sqlite3
import pytest
import modulo_catalogos

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    # Use a temporary file path for the test database
    test_db = str(tmp_path / "test_catalogos_db.sqlite")
    monkeypatch.setattr(modulo_catalogos, "CAT_DB_PATH", test_db)

    # Initialize DB tables
    modulo_catalogos.ic_init_db()

    yield test_db

def test_ic_init_db_creates_indices(setup_test_db):
    test_db = setup_test_db
    con = sqlite3.connect(test_db)
    cur = con.cursor()

    # Verify tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert "ic_estilos" in tables
    assert "ic_fracciones" in tables

    # Verify index idx_ic_estilos_depto exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indices = [r[0] for r in cur.fetchall()]
    assert "idx_ic_estilos_depto" in indices
    assert "idx_ic_estilo" in indices

    con.close()

def test_ic_listar_estilos_pre_aggregation(setup_test_db):
    # Create style 1
    ok1, res1 = modulo_catalogos.ic_guardar_estilo(
        estilo="ESTILO_A",
        departamento="DEPTO_X",
        precio_par=150.0,
        notas="Test note style A"
    )
    assert ok1 is True

    # Let's get the style ID by listing styles
    estilos = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_A", departamento="DEPTO_X")
    assert len(estilos) == 1
    est_id = estilos[0]["id"]
    assert estilos[0]["n_frac"] == 0
    assert estilos[0]["suma_frac"] == 0.0

    # Add fractions to style 1
    ok_f1, res_f1 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=est_id,
        nombre="FRAC1",
        precio=45.5,
        orden=1
    )
    assert ok_f1 is True

    ok_f2, res_f2 = modulo_catalogos.ic_guardar_fraccion(
        ic_estilo_id=est_id,
        nombre="FRAC2",
        precio=54.5,
        orden=2
    )
    assert ok_f2 is True

    # Fetch styles again and check pre-aggregation
    estilos_updated = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_A")
    assert len(estilos_updated) == 1
    assert estilos_updated[0]["n_frac"] == 2
    assert estilos_updated[0]["suma_frac"] == 100.0  # 45.5 + 54.5

    # Create style 2 (no fractions)
    ok2, res2 = modulo_catalogos.ic_guardar_estilo(
        estilo="ESTILO_B",
        departamento="DEPTO_Y",
        precio_par=200.0,
        notas="Style B without fractions"
    )
    assert ok2 is True

    # Fetch all styles (departamento="TODOS")
    todos_estilos = modulo_catalogos.ic_listar_estilos(buscar="")
    assert len(todos_estilos) == 2

    # Verify Style B details
    style_b = next(e for e in todos_estilos if e["estilo"] == "ESTILO_B")
    assert style_b["n_frac"] == 0
    assert style_b["suma_frac"] == 0.0

def test_ic_get_tarifa(setup_test_db):
    # Save a style with fractions
    ok, res = modulo_catalogos.ic_guardar_estilo("ESTILO_C", "DEPTO_Z", 100.0)
    assert ok is True

    estilos = modulo_catalogos.ic_listar_estilos("ESTILO_C", "DEPTO_Z")
    est_id = estilos[0]["id"]

    modulo_catalogos.ic_guardar_fraccion(est_id, "FRAC_C", 50.0)

    # Test ic_get_tarifa with fractions
    tarifa_c = modulo_catalogos.ic_get_tarifa("ESTILO_C", "DEPTO_Z")
    assert tarifa_c["precio_par"] == 100.0
    assert tarifa_c["modo"] == "FRACCIONADO"
    assert len(tarifa_c["fracciones"]) == 1
    assert tarifa_c["fracciones"][0]["nombre"] == "FRAC_C"

    # Test ic_get_tarifa without fractions
    modulo_catalogos.ic_guardar_estilo("ESTILO_D", "DEPTO_Z", 80.0)
    tarifa_d = modulo_catalogos.ic_get_tarifa("ESTILO_D", "DEPTO_Z")
    assert tarifa_d["precio_par"] == 80.0
    assert tarifa_d["modo"] == "PAR"
    assert len(tarifa_d["fracciones"]) == 0

    # Test non-existing style
    tarifa_none = modulo_catalogos.ic_get_tarifa("UNKNOWN", "DEPTO_Z")
    assert tarifa_none["precio_par"] == 0.0
    assert tarifa_none["modo"] == "SIN_TARIFA"
