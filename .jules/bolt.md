## 2025-10-03 - Indexed Column Lookups vs. Wildcard Full-Table LIKE
**Learning:** Functions like `cat_get_material_por_nombre` that search for exact records were executing full-table scans via `cat_buscar`, performing SQL `LIKE` on large JSON blobs (`datos_json`) and deserializing all rows in Python before filtering. Using direct `WHERE nombre=?` queries leverages SQLite's index on `nombre` for ~16x speedup.
**Action:** When looking up individual records by unique or indexed attributes, query the indexed column directly instead of delegating to general-purpose search functions.
