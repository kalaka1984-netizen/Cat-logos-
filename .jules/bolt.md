## 2026-03-09 - Direct Indexed Query Optimization for Exact Column Lookups
**Learning:** Using generic search functions (`cat_buscar`) that execute SQL `LIKE '%term%'` patterns on large `datos_json` columns triggers full table scans ($O(N)$ complexity) and forces unnecessary JSON deserialization for every candidate row.
**Action:** Always write targeted SQL queries (`SELECT col FROM tbl WHERE indexed_col=?`) for exact match lookups to leverage SQLite's B-Tree index, bypassing full-table scans.
