## 2025-02-16 - Pre-aggregate SQLite counts and sums with LEFT JOIN to eliminate N+1 UI queries

**Learning:** In desktop GUI list views backed by SQLite, querying child records inside a rendering loop creates severe N+1 query bottlenecks (~0.060s per refresh for 200 items). Using SQLite `LEFT JOIN` with `COUNT()` and `TOTAL()` pre-aggregates child count and sum fields in a single query (~0.0014s per refresh), providing a ~42x speedup.
**Action:** Always pre-aggregate child summary metrics in SQL JOINs when listing records for UI rendering.
