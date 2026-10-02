## 2025-05-18 - Pre-aggregation in SQL JOINs eliminates N+1 query bottlenecks in UI lists
**Learning:** Querying child records inside a UI rendering loop for list views introduces an N+1 query bottleneck in SQLite. Using `LEFT JOIN` with `COUNT()` and `TOTAL()` in the main query returns pre-aggregated child counts and sums in a single database roundtrip without requiring additional Python-side computation.
**Action:** Always pre-aggregate child record counts and sums using SQL JOINs in listing functions rather than issuing per-row SQL queries during UI rendering.
