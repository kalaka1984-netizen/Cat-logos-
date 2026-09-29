## 2026-09-29 - Avoid SQL LIKE on JSON Columns for Exact Matches & Name Listings

**Learning:** Using generic `LIKE '%query%'` queries across large `datos_json` columns forces SQLite into O(N) full table scans and unnecessary JSON deserialization overhead, even when searching for exact indexed column matches (such as `nombre`) or retrieving names for autocomplete.

**Action:** Replace `cat_buscar` calls in exact lookups with `SELECT datos_json FROM table WHERE nombre=?`, query `SELECT nombre` directly for autocomplete lists with composite `(estatus, nombre)` indexes, and bypass `LIKE` clause construction when search strings are empty.
