## 2025-09-28 - Optimized Catalog Direct Lookup and Search
**Learning:** Calling generic search functions like `cat_buscar` with `texto=""` or for single-key lookups forces SQLite full table scans and `LIKE` pattern evaluations on large `datos_json` columns.
**Action:** Use direct `SELECT datos_json FROM table WHERE key=?` with indexed columns for single-key lookups, and bypass `LIKE` clauses when query strings are empty.
