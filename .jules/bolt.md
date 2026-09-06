## 2026-06-02 - Direct Indexed Lookups vs Generic Full Table Search

**Learning:** Delegating point lookups by key/name (e.g., `cat_get_material_por_nombre`) to generic search functions like `cat_buscar` forces SQLite to perform O(N) full table scans with wildcard `LIKE %...%` filters over JSON text columns (`datos_json`). Direct `SELECT datos_json FROM table WHERE nombre=?` leverages SQLite indexes and bypasses unnecessary row deserializations, achieving over 4x speedup.

**Action:** When implementing point lookups for specific records by exact indexed fields, always use direct SQL point queries instead of generic wildcard search functions.
