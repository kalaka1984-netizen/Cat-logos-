## 2025-05-18 - Pre-aggregation in SQL JOIN vs N+1 queries in UI lists
**Learning:** Calling child record query functions in UI render loops causes N+1 database queries, slowing list refreshes significantly. Using `LEFT JOIN` and `TOTAL()`/`COUNT()` in `ic_listar_estilos` aggregates counts and sums in a single SQL query pass.
**Action:** When retrieving parent-child records for UI display, use `LEFT JOIN` with SQLite `TOTAL()` and `COUNT()` pre-aggregations to return all summary metrics in 1 query.
