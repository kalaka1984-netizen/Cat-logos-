## 2026-05-30 - Catalog Database Lookup & Scan Optimization
**Learning:** In SQLite databases storing JSON blobs in text columns (`datos_json`), `cat_buscar` and autocomplete lookups was executing `WHERE nombre LIKE '%' OR datos_json LIKE '%'` for exact searches and empty queries. This forced full table scans and string evaluation over JSON text blobs.
**Action:** Use direct `WHERE nombre=? LIMIT 1` queries for exact item lookups, bypass `LIKE` when search text is empty, and add composite indexes `(estatus, nombre)` to enable Index-Only scans for autocomplete queries.
