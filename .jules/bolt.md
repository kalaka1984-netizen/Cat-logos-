## 2025-05-20 - Direct SELECT optimization for catalog lookups
**Learning:** Reusing full search function `cat_buscar` for autocomplete (`cat_get_nombres_*`) or exact item lookups (`cat_get_material_por_nombre`) causes full table scans, wildcard `LIKE` evaluations, and unnecessary deserialization of large `datos_json` blobs.
**Action:** Replace `cat_buscar` calls in lookup APIs with direct `SELECT` queries (`SELECT nombre FROM ...` or `SELECT datos_json FROM ... WHERE nombre=?`), utilizing indexed columns to achieve ~2.6x to ~4.8x speedups.
