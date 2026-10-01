## 2025-05-20 - N+1 Query Aggregation in SQLite List Refresh
**Learning:** Calling child record query functions (e.g., `ic_listar_fracciones`) inside a loop over parent rows (`ic_listar_estilos`) introduces a severe N+1 database bottleneck during UI rendering (~22x slower for 500 rows). Using `LEFT JOIN` and SQLite aggregation functions `COUNT(f.id)` and `TOTAL(f.precio)` with `GROUP BY` pre-calculates child metrics in a single query.
**Action:** When fetching list views with associated child counts or sums, aggregate in SQL rather than loop-fetching in Python or UI code.
