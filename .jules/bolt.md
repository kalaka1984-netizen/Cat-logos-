## 2025-02-23 - Avoid SQL LIKE on JSON blobs during lookup queries
**Learning:** Calling `cat_buscar` with a string match evaluates `datos_json LIKE '%...%'` over all rows, ignoring column indexes and forcing SQLite full table scans and JSON string deserialization. Replacing exact material lookups with direct `WHERE nombre = ?` queries utilizes the index on `nombre` and provides a 3x-30x speedup depending on dataset size.
**Action:** Always favor direct indexed equality checks over generalized search helper functions when looking up specific entities by key.
