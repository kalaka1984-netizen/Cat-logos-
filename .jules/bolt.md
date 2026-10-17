## 2025-02-22 - Pre-aggregation with SQLite TOTAL() to Eliminate N+1 Queries
**Learning:** In SQLite, performing `LEFT JOIN` on child tables and using `TOTAL()` (instead of `SUM()`) prevents `NULL` return values when no child rows exist, allowing pre-aggregated counts and totals in a single query without Python type errors.
**Action:** When populating list views with child aggregate data (e.g. fraction count and price sum per style), use `LEFT JOIN` with `TOTAL()` and `GROUP BY` in `ic_listar_estilos` instead of querying child records inside the rendering loop.
