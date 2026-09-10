## 2026-03-10 - Direct SQLite Indexed Column Query vs Full-Table Scan LIKE

**Learning:** When retrieving records by unique or indexed text keys (such as `nombre` in catalog tables), delegating to a generic `cat_buscar` search function that uses `LIKE %key%` on large JSON text columns causes O(N) full table scans and unnecessary JSON deserialization. Replacing `cat_buscar` with a direct `SELECT datos_json FROM table WHERE nombre=?` query utilizes SQLite's B-Tree index on `nombre`, reducing 500-lookup time from ~48ms to ~4ms (~12x speedup).

**Action:** Whenever exact lookup functions are called frequently (such as autocomplete or pre-populating form fields), bypass generic search functions and query the indexed key column directly.
