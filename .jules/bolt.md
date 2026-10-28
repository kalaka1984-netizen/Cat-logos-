## 2026-03-31 - Indexed Exact Lookup and Selective Column Fetching
**Learning:** Full table scans via `cat_buscar` on large `datos_json` columns for single item point lookups (`cat_get_material_por_nombre`) or simple list name fetches (`cat_get_nombres_*`) incur high Python-side JSON parsing and `LIKE` evaluation overhead (~10x slowdown).
**Action:** Always write direct SQL queries targeting specific indexed columns (`WHERE nombre = ?`) and select only required columns (`SELECT nombre FROM ...`) when possible.
