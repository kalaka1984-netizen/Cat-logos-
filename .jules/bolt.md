## 2026-06-02 - Direct SELECT and Composite Indexing for Catalog Autocomplete
**Learning:** Fetching full catalog rows via `cat_buscar` to extract only names introduces severe SQL scan and Python deserialization overhead. Using direct `SELECT nombre` queries with a composite index on `(estatus, nombre)` speeds up list retrieval queries by ~3x while avoiding unnecessary memory allocations for large JSON blobs.
**Action:** Always project specific required columns for autocomplete/list helpers instead of reusing general search routines that load entire rows and JSON data.
