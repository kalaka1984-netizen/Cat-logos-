import json
import os
import sqlite3
import sys
import tempfile
import time
from unittest import mock


class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass


mock_ctk = mock.MagicMock()
mock_ctk.CTkFrame = DummyWidget
mock_ctk.CTkLabel = DummyWidget
mock_ctk.CTkButton = DummyWidget

mock_tk = mock.MagicMock()
mock_root = mock.MagicMock()
mock_root.winfo_screenwidth.return_value = 1920
mock_root.winfo_screenheight.return_value = 1080
mock_tk.Tk.return_value = mock_root

sys.modules['customtkinter'] = mock_ctk
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.messagebox'] = mock.MagicMock()

import modulo_catalogos


class TestModuloCatalogos:

    def setup_method(self):
        # Setup temporary test database
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_catalogos.sqlite")
        self.orig_db_path = modulo_catalogos.CAT_DB_PATH
        modulo_catalogos.CAT_DB_PATH = self.db_path
        modulo_catalogos.cat_init_db()

    def teardown_method(self):
        modulo_catalogos.CAT_DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        if os.path.exists(self.tmp_dir):
            try:
                os.rmdir(self.tmp_dir)
            except OSError:
                pass

    def test_init_db_indexes(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        for tabla in ("materiales", "trabajadores", "proveedores", "clientes"):
            cur.execute(f"PRAGMA index_list({tabla})")
            indexes = [r[1] for r in cur.fetchall()]
            assert f"idx_{tabla}_nombre" in indexes
            assert f"idx_{tabla}_estatus_nombre" in indexes
        con.close()

    def test_cat_get_material_por_nombre(self):
        # Save sample materials via cat_guardar
        mat_data = {
            "nombre": "CUERO VACUNO",
            "tipo_material": "DIRECTO",
            "unidad_default": "dm",
            "departamento": "CORTE",
            "visible_monitor": "SÍ",
            "es_principal": "SÍ",
            "estatus": "ACTIVO",
        }
        ok, _ = modulo_catalogos.cat_guardar("materiales", mat_data)
        assert ok is True

        # Exact match (case insensitive)
        res = modulo_catalogos.cat_get_material_por_nombre("cuero vacuno")
        assert res["tipo_material"] == "DIRECTO"
        assert res["unidad_default"] == "DM"

        # Non-existent material
        res_empty = modulo_catalogos.cat_get_material_por_nombre("MATERIAL INEXISTENTE")
        assert res_empty == {}

        # Empty query
        assert modulo_catalogos.cat_get_material_por_nombre("") == {}

    def test_cat_get_nombres(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT A", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT B", "estatus": "INACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT C", "estatus": "ACTIVO"})

        activos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
        assert activos == ["MAT A", "MAT C"]

        todos = modulo_catalogos.cat_get_nombres_materiales(solo_activos=False)
        assert todos == ["MAT A", "MAT B", "MAT C"]

    def test_cat_buscar_empty_text(self):
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT 1", "estatus": "ACTIVO"})
        modulo_catalogos.cat_guardar("materiales", {"nombre": "MAT 2", "estatus": "INACTIVO"})

        # Search with empty string
        rows_all = modulo_catalogos.cat_buscar("materiales", "", "TODOS")
        assert len(rows_all) == 2

        rows_act = modulo_catalogos.cat_buscar("materiales", "   ", "ACTIVO")
        assert len(rows_act) == 1
        assert rows_act[0][1] == "MAT 1"

        # Search with actual query
        rows_search = modulo_catalogos.cat_buscar("materiales", "MAT 2", "TODOS")
        assert len(rows_search) == 1
        assert rows_search[0][1] == "MAT 2"

    def test_benchmark_performance(self):
        # Populate DB with 1000 items
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        mats = [(f"MATERIAL_{i}", json.dumps({"tipo_material": "DIRECTO", "unidad_default": "DM", "extra": "x" * 200}), "ACTIVO" if i % 2 == 0 else "INACTIVO", "2025-01-01", "2025-01-01") for i in range(1000)]
        cur.executemany("INSERT INTO materiales (nombre, datos_json, estatus, fecha_alta, fecha_mod) VALUES (?, ?, ?, ?, ?)", mats)
        con.commit()
        con.close()

        # Measure 100 get_material calls
        t0 = time.perf_counter()
        for _ in range(100):
            res = modulo_catalogos.cat_get_material_por_nombre("MATERIAL_500")
            assert res["unidad_default"] == "DM"
        t_lookup = time.perf_counter() - t0

        # Measure 100 get_nombres calls
        t0 = time.perf_counter()
        for _ in range(100):
            names = modulo_catalogos.cat_get_nombres_materiales(solo_activos=True)
            assert len(names) == 500
        t_nombres = time.perf_counter() - t0

        print(f"\n[BENCHMARK] 100 lookups: {t_lookup:.4f}s | 100 name list queries: {t_nombres:.4f}s")
        assert t_lookup < 0.1, f"Lookup took too long: {t_lookup:.4f}s"
        assert t_nombres < 0.2, f"Name listing took too long: {t_nombres:.4f}s"
