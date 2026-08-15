## 2025-08-15 - Fast Exact Match for Material Lookups
**Learning:** `cat_buscar` does full-table scans using SQL `LIKE` on both `nombre` and `datos_json` columns, causing significant performance overhead when querying specific single entities.
**Action:** Bypassed `cat_buscar` in single-item lookup functions like `cat_get_material_por_nombre` by performing direct SQL `SELECT` queries on indexed exact-match columns (e.g. `WHERE nombre = ?`), resulting in a ~17x lookup speedup.
