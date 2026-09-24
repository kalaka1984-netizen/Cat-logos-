## 2025-02-23 - Direct Indexed SELECT vs. Fuzzy LIKE Query Scanning
**Learning:** Using `cat_buscar` (which performs a fuzzy `LIKE` comparison across both indexed columns and `datos_json` blobs) for exact name lookups like `cat_get_material_por_nombre` created a major bottleneck (~18.6x overhead) and forced full table scans.
**Action:** Perform direct equality matches (`WHERE nombre=?`) on indexed columns for single-entity lookups and bypass `LIKE` clauses when query strings are empty or whitespace-only.
