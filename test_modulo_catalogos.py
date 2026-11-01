"""Unit tests for modulo_catalogos.py performance optimizations and correctness."""

import os
import sys
import tempfile
import time
from unittest.mock import MagicMock


# ── Mock GUI components for headless testing ─────────────────────────────────
class DummyCTkWidget:
    def winfo_children(self):
        return []

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def pack(self, *args, **kwargs):
        pass

    def place(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def after(self, ms, func=None, *args):
        if func:
            func()
        return "after_id"

    def after_cancel(self, id_):
        pass


ctk_mock = MagicMock()
for widget_cls in [
    "CTkFrame",
    "CTkToplevel",
    "CTkEntry",
    "CTkButton",
    "CTkLabel",
    "CTkOptionMenu",
    "CTkComboBox",
    "CTkScrollableFrame",
    "CTkTabview",
    "CTk",
]:
    setattr(ctk_mock, widget_cls, DummyCTkWidget)

tk_mock = MagicMock()
root_mock = MagicMock()
root_mock.winfo_screenwidth.return_value = 1920
root_mock.winfo_screenheight.return_value = 1080
tk_mock.Tk.return_value = root_mock

sys.modules["tkinter"] = tk_mock
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["customtkinter"] = ctk_mock
sys.modules["darkdetect"] = MagicMock()

import modulo_catalogos


def test_ic_listar_estilos_pre_aggregation():
    """Verify that ic_listar_estilos accurately calculates n_frac and suma_frac via LEFT JOIN."""
    db_fd, temp_db = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)
    original_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db

    try:
        modulo_catalogos.ic_init_db()

        # Insert 1 style with 2 fractions
        ok1, est1_id = modulo_catalogos.ic_guardar_estilo(
            "ESTILO_ALPHA", "CORTE", 150.0, "Nota Alpha"
        )
        assert ok1, "Failed to insert style 1"
        modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE TAPA", 50.0, 1)
        modulo_catalogos.ic_guardar_fraccion(est1_id, "CORTE CHINELA", 100.0, 2)

        # Insert 1 style with 0 fractions
        ok2, _ = modulo_catalogos.ic_guardar_estilo(
            "ESTILO_BETA", "PESPUNTE", 80.0, "Nota Beta"
        )
        assert ok2, "Failed to insert style 2"

        # List all styles
        rows = modulo_catalogos.ic_listar_estilos(buscar="", departamento="TODOS")
        assert len(rows) == 2

        alpha = next(r for r in rows if r["estilo"] == "ESTILO_ALPHA")
        assert alpha["n_frac"] == 2
        assert abs(alpha["suma_frac"] - 150.0) < 1e-4
        assert alpha["precio_par"] == 150.0

        beta = next(r for r in rows if r["estilo"] == "ESTILO_BETA")
        assert beta["n_frac"] == 0
        assert beta["suma_frac"] == 0.0
        assert beta["precio_par"] == 80.0

        # Filter by department
        corte_rows = modulo_catalogos.ic_listar_estilos(buscar="", departamento="CORTE")
        assert len(corte_rows) == 1
        assert corte_rows[0]["estilo"] == "ESTILO_ALPHA"

    finally:
        modulo_catalogos.CAT_DB_PATH = original_db
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_ic_listar_estilos_benchmark():
    """Benchmark ic_listar_estilos performance with 200 items."""
    db_fd, temp_db = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)
    original_db = modulo_catalogos.CAT_DB_PATH
    modulo_catalogos.CAT_DB_PATH = temp_db

    try:
        modulo_catalogos.ic_init_db()

        # Populate 200 styles with 5 fractions each
        for i in range(200):
            ok, est_id = modulo_catalogos.ic_guardar_estilo(
                f"ESTILO_{i:03d}",
                "CORTE" if i % 2 == 0 else "PESPUNTE",
                100.0 + i,
            )
            assert ok
            for j in range(5):
                modulo_catalogos.ic_guardar_fraccion(
                    est_id, f"FRAC_{j}", 20.0 + (i % 5)
                )

        start = time.perf_counter()
        for _ in range(10):
            rows = modulo_catalogos.ic_listar_estilos()
            assert len(rows) == 200
        elapsed_ms = ((time.perf_counter() - start) / 10) * 1000

        print(
            f"\n[BENCHMARK] ic_listar_estilos for 200 styles: {elapsed_ms:.2f} ms per call"
        )
        # Ensure execution is well under 15ms for 200 records
        assert elapsed_ms < 15.0, f"Query took too long: {elapsed_ms:.2f} ms"

    finally:
        modulo_catalogos.CAT_DB_PATH = original_db
        if os.path.exists(temp_db):
            os.remove(temp_db)
