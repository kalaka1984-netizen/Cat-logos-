## 2025-03-03 - SQLite Covering Index and Direct Lookups for Catalog Tables
**Learning:** Functions doing `WHERE nombre LIKE '%name%' OR datos_json LIKE '%name%'` incur O(N) full table scans and text evaluation overhead across all rows. Creating a composite covering index `(estatus, nombre)` allows index-only scans for name listing, and direct `WHERE nombre=?` exact match bypasses `cat_buscar` text scan resulting in ~41x faster lookups.
**Action:** Favor exact indexed equality lookups and covering index scans over generic `LIKE` queries on JSON columns.
