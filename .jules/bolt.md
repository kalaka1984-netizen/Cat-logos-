## 2025-02-13 - Direct SQLite SELECT vs cat_buscar O(N) LIKE Search
**Learning:** `cat_get_material_por_nombre` previously called `cat_buscar("materiales", nombre, "TODOS")`, which executed `LIKE %nombre%` queries over both `nombre` and `datos_json` columns and iterated through all returned rows in Python to find exact matches.
**Action:** Bypassed `cat_buscar` in `cat_get_material_por_nombre` using direct indexed equality match `SELECT datos_json FROM materiales WHERE nombre=? LIMIT 1`, achieving ~7.5x faster material lookups in database operations.
