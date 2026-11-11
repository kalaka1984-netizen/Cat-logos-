# Bolt's Performance Journal

## 2026-06-02 - Direct Indexed Lookup vs Full-Table LIKE Scan in Catalog Lookups
**Learning:** `cat_buscar()` performs a full-table scan using SQL `LIKE` on both `nombre` and the unbounded `datos_json` column. Delegating single-entity lookups (like `cat_get_material_por_nombre`) to `cat_buscar` caused O(N) database reads and subsequent Python-level deserialization and string matching, ignoring the existing B-tree index `idx_materiales_nombre`.
**Action:** When querying records by unique or indexed identifiers like `nombre`, use direct equality matching (`SELECT datos_json FROM materiales WHERE nombre = ? LIMIT 1`) to leverage existing table indexes (`idx_<table>_nombre`) and eliminate table scans on large JSON fields.
