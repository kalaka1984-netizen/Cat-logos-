## 2026-06-02 - Direct SELECT and Column-Targeted Query Optimization for Catalog Lookups

**Learning:** Calling generic search functions like `cat_buscar` for exact lookups or list autocomplete causes expensive `LIKE` evaluations and unnecessary deserializations of large JSON columns (`datos_json`) for every row in SQLite tables. Using direct indexed `WHERE nombre = ?` or column-filtered `SELECT nombre FROM {tabla}` queries avoids O(N) full table scans and memory overhead.

**Action:** Replace helper wrappers that reuse generic `LIKE` search functions with direct, targeted SQL queries when exact matches or specific column lists are required. Ensure input parameters like table names are validated against strict whitelists when using parameterized table identifiers in helper methods.
