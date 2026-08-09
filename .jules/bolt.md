## 2025-08-09 - N+1 Query in Style Listing Refreshes
**Learning:** Calling `ic_listar_fracciones` in a loop inside `_refrescar_lista` creates an N+1 query problem, causing substantial lag when many styles exist. Pre-aggregating these fields (`n_frac`, `suma_frac`) via a single SQL query with a `LEFT JOIN` and SQLite `TOTAL()` avoids Python-side aggregation and excessive DB connections.
**Action:** Avoid querying child records in a loop; always use SQL LEFT JOINs with GROUP BY and aggregate functions like `COUNT()` and `TOTAL()` to load everything in one go.

## 2025-08-09 - Exact Match Database Lookup Overuse of LIKE
**Learning:** Relying on `cat_buscar` with the SQLite `LIKE` operator to retrieve a single record by its exact name forces O(N) full-table scans and unnecessary deserialization overhead, particularly on JSON columns.
**Action:** Query indexed columns directly with equality operators (`=`) and select only required columns to improve query performance significantly.
