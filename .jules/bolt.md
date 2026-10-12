## 2025-10-12 - Eliminate N+1 SQL queries in ic_listar_estilos with LEFT JOIN aggregation

**Learning:** Calling `ic_listar_fracciones` in a loop inside `IC_Vista._refrescar_lista` introduced an N+1 query pattern (1 query for styles + N queries for fractions). In SQLite, using `LEFT JOIN ic_fracciones f ON e.id = f.ic_estilo_id` and `GROUP BY e.id` with aggregate functions `COUNT(f.id)` and `TOTAL(f.precio)` pre-calculates fraction count and total price in a single SQL query. Note that SQLite's `TOTAL()` function is preferred over `SUM()` because `TOTAL()` returns `0.0` when no rows match instead of `NULL`.

**Action:** Whenever listing parent records that display child record counts or sums in UI tables, pre-aggregate child metrics in the initial parent SQL query using `LEFT JOIN`, `GROUP BY`, and `TOTAL()`.
