# -*- coding: utf-8 -*-
import os
import sqlite3
import time
import pytest
import modulo_catalogos

# Use a temporary database for testing to prevent pollution
TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_catalogos_db.sqlite"
)

@pytest.fixture(autouse=True)
def setup_test_db():
    # Override database path
    old_db_path = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = TEST_DB_PATH

    # Initialize tables
    modulo_catalogos.cat_init_db()
    modulo_catalogos.ic_init_db()

    yield

    # Clean up test database file
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    modulo_catalogos.CAT_DB_PATH = old_db_path

def test_ic_index_exists():
    """Verifies that the index idx_ic_estilos_depto exists on the ic_estilos table."""
    con = sqlite3.connect(TEST_DB_PATH)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA index_list('ic_estilos')")
        indexes = [row[1] for row in cur.fetchall()]
        assert "idx_ic_estilos_depto" in indexes
    finally:
        con.close()

def test_ic_listar_estilos_empty():
    """Verifies style list on an empty database."""
    estilos = modulo_catalogos.ic_listar_estilos()
    assert estilos == []

def test_ic_listar_estilos_with_data():
    """Verifies styles are listed with correct pre-aggregated fraction count and sum."""
    # Guardar estilos
    ok1, res1 = modulo_catalogos.ic_guardar_estilo("ESTILO_A", "PESPUNTE", 100.0, "Notas A")
    ok2, res2 = modulo_catalogos.ic_guardar_estilo("ESTILO_B", "CORTADO", 150.0, "Notas B")
    assert ok1 is True
    assert ok2 is True

    # Get style ids
    estilos = modulo_catalogos.ic_listar_estilos()
    assert len(estilos) == 2

    id_a = next(e["id"] for e in estilos if e["estilo"] == "ESTILO_A")
    id_b = next(e["id"] for e in estilos if e["estilo"] == "ESTILO_B")

    # Guardar fracciones para ESTILO_A
    ok_f1, _ = modulo_catalogos.ic_guardar_fraccion(id_a, "FRAC_1", 20.0, 1)
    ok_f2, _ = modulo_catalogos.ic_guardar_fraccion(id_a, "FRAC_2", 30.5, 2)
    assert ok_f1 is True
    assert ok_f2 is True

    # Guardar fracciones para ESTILO_B (sin fracciones, should default to 0.0)

    # Refetch estilos and verify aggregates
    estilos_updated = modulo_catalogos.ic_listar_estilos()
    assert len(estilos_updated) == 2

    estilo_a_res = next(e for e in estilos_updated if e["estilo"] == "ESTILO_A")
    assert estilo_a_res["n_frac"] == 2
    assert pytest.approx(estilo_a_res["suma_frac"]) == 50.5

    estilo_b_res = next(e for e in estilos_updated if e["estilo"] == "ESTILO_B")
    assert estilo_b_res["n_frac"] == 0
    assert pytest.approx(estilo_b_res["suma_frac"]) == 0.0

def test_ic_listar_estilos_filter_and_search():
    """Verifies that search terms and department filtering work as expected with aggregates."""
    modulo_catalogos.ic_guardar_estilo("ESTILO_X", "PESPUNTE", 100.0, "Notas X")
    modulo_catalogos.ic_guardar_estilo("ESTILO_Y", "CORTADO", 200.0, "Notas Y")

    # Search with term
    res_search = modulo_catalogos.ic_listar_estilos(buscar="ESTILO_X")
    assert len(res_search) == 1
    assert res_search[0]["estilo"] == "ESTILO_X"

    # Search with department
    res_dept = modulo_catalogos.ic_listar_estilos(departamento="CORTADO")
    assert len(res_dept) == 1
    assert res_dept[0]["estilo"] == "ESTILO_Y"

def test_benchmark_performance_improvement():
    """Benchmarks the optimized ic_listar_estilos with LEFT JOIN vs mock legacy N+1 behavior."""
    # Insert 100 styles to simulate a moderately sized database
    num_estilos = 100
    style_ids = []
    for i in range(num_estilos):
        _, res = modulo_catalogos.ic_guardar_estilo(f"ESTILO_{i}", "PESPUNTE", 100.0 + i, f"Notas {i}")
        # Search to find the ID of the created style
        # (This is just a simple way to fetch the inserted ID)
        con = sqlite3.connect(TEST_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id FROM ic_estilos WHERE estilo = ?", (f"ESTILO_{i}",))
        style_ids.append(cur.fetchone()[0])
        con.close()

    # Insert 3 fractions for each style (total 300 fractions)
    for sid in style_ids:
        modulo_catalogos.ic_guardar_fraccion(sid, "FRAC_1", 10.0)
        modulo_catalogos.ic_guardar_fraccion(sid, "FRAC_2", 15.0)
        modulo_catalogos.ic_guardar_fraccion(sid, "FRAC_3", 20.0)

    # 1. Benchmark legacy N+1 style query logic
    t0_legacy = time.perf_counter()
    # Mock legacy N+1 loop
    # Simulate: fetch all styles, and then for each style, fetch fractions
    con = sqlite3.connect(TEST_DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, estilo, departamento, precio_par, notas, fecha_alta FROM ic_estilos")
    rows = cur.fetchall()
    legacy_results = []
    for r in rows:
        # Fetch fractions
        cur_f = con.cursor()
        cur_f.execute("SELECT id, nombre, precio, orden FROM ic_fracciones WHERE ic_estilo_id=?", (r[0],))
        fracs = cur_f.fetchall()
        n_frac = len(fracs)
        suma_frac = sum(fr[2] for fr in fracs)
        legacy_results.append({
            "id": r[0], "estilo": r[1], "departamento": r[2],
            "precio_par": r[3], "notas": r[4], "fecha_alta": r[5],
            "n_frac": n_frac, "suma_frac": suma_frac
        })
    con.close()
    duration_legacy = time.perf_counter() - t0_legacy

    # 2. Benchmark optimized LEFT JOIN query logic
    t0_opt = time.perf_counter()
    opt_results = modulo_catalogos.ic_listar_estilos()
    duration_opt = time.perf_counter() - t0_opt

    # Print results to console during test execution
    print(f"\n[BENCHMARK] Legacy N+1 logic query duration for {num_estilos} styles: {duration_legacy:.6f}s")
    print(f"[BENCHMARK] Optimized SQL JOIN logic query duration for {num_estilos} styles: {duration_opt:.6f}s")

    speedup = duration_legacy / max(duration_opt, 1e-9)
    print(f"[BENCHMARK] Speedup factor: {speedup:.2f}x")

    # Sort results by ID to ensure exact element-wise comparison
    opt_sorted = sorted(opt_results, key=lambda x: x["id"])
    legacy_sorted = sorted(legacy_results, key=lambda x: x["id"])

    # Assert correctness
    assert len(opt_sorted) == len(legacy_sorted)
    for opt_row, leg_row in zip(opt_sorted, legacy_sorted):
        assert opt_row["id"] == leg_row["id"]
        assert opt_row["n_frac"] == leg_row["n_frac"]
        assert pytest.approx(opt_row["suma_frac"]) == leg_row["suma_frac"]

    # We expect the JOIN optimization to be significantly faster (at least 2x faster, often much more)
    assert duration_opt < duration_legacy
