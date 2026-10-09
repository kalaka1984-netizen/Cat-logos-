## 2025-10-09 - Direct Column Selection for Catalog Autocomplete Lookups

**Learning:** Delegation of simple column lookups (e.g. `nombre`) to full search helpers like `cat_buscar()` forces SQLite full-row scans and unnecessary JSON deserialization (`datos_json`), adding ~3x latency overhead on autocomplete queries.
**Action:** Use direct targeted `SELECT col FROM table` queries with explicit table name whitelist validation for simple lookup functions.
