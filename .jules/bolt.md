## 2025-05-18 - Avoid SQL LIKE evaluations and full deserialization for exact name lookups

**Learning:** `cat_buscar` with empty search strings and `cat_get_material_por_nombre` were performing `LIKE '%query%'` comparisons against `datos_json` blobs. Doing direct equality `SELECT` on indexed columns and selecting only necessary columns bypasses `datos_json` deserialization and achieves ~6x speedups.

**Action:** When querying SQLite tables with JSON blob columns, always prefer direct equality lookups on indexed text columns and fetch only needed attributes.
