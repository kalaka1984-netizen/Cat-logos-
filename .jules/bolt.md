## 2026-03-31 - Direct SQL Lookup Optimization for Catalog Lookups
**Learning:** Replaces `LIKE` operations over `datos_json` columns in `cat_buscar` with indexed direct `SELECT` queries when looking up exact names (`cat_get_material_por_nombre`) to bypass full table scans and O(N) `json.loads` calls.
**Action:** Always favor indexed column lookups over pattern-matching search abstractions when looking up specific entities by key/name.
