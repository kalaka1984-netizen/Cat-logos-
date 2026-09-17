## 2026-06-02 - Direct Exact SQL Lookups vs. LIKE Scanning
**Learning:** Functions doing exact string matches (e.g., `cat_get_material_por_nombre`) using generic `LIKE %text%` search functions cause O(N) full table scans and redundant JSON parsing in Python.
**Action:** Replace exact-match lookup calls with direct `SELECT ... WHERE column=?` queries using indexed columns.
