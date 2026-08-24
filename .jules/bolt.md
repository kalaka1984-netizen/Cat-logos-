## 2025-08-24 - Direct Indexed Lookups vs Generic LIKE Searching
**Learning:** Functions like `cat_get_material_por_nombre` that look up a specific record by exact key name should never call generic search helpers like `cat_buscar` which execute `LIKE %...%` across large JSON blob columns (`datos_json`) and deserialize all candidate rows.
**Action:** Use direct parameterized SQL equality queries (`SELECT ... WHERE key = ?`) to leverage single-row index lookups in SQLite and bypass O(N) Python-side filtering.
