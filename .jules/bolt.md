## 2025-02-23 - Catalog Table Name Listing Index-Only Scan Optimization
**Learning:** Using `cat_buscar()` for name listings (`cat_get_nombres_*`) loaded all columns including `datos_json` blobs and evaluated `LIKE '%%'` string matching on JSON strings, causing unneeded disk I/O and CPU deserialization overhead. Direct `SELECT nombre` queries backed by `(estatus, nombre)` composite indexes allow SQLite covering index scans with a 4.2x speedup.
**Action:** Always select only required indexed columns when fetching lookup/autocomplete name lists instead of delegating to generic search routines.
