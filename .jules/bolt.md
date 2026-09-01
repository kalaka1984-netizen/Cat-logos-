## 2025-09-01 - Direct SELECT vs LIKE on JSON Columns
**Learning:** Calling lookup functions like `cat_buscar` with full `LIKE %term%` queries over large JSON columns causes $O(N)$ full-table scans and deserialization overhead. Bypassing `cat_buscar` with a direct `SELECT datos_json FROM materiales WHERE nombre=? LIMIT 1` yields a ~23x performance boost.
**Action:** When performing exact material/entity lookups, use indexed direct equality queries rather than delegating to generic search functions that evaluate `LIKE` pattern matching on raw text/JSON columns.
