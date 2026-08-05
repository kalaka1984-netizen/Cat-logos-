## 2025-02-23 - LEFT JOIN Pre-Aggregation to Resolve N+1 Queries
**Learning:** Rendering style listings in a loop with individual database lookups for each style's fractions caused a major N+1 query performance bottleneck. Implementing a `LEFT JOIN` with `GROUP BY` and SQLite's `TOTAL()` function allows the database to aggregate counts and sums in a single O(log N) indexed query.
**Action:** Always replace parent-child nested lookups with SQL JOINs and pre-aggregation in the parent query, and leverage `TOTAL()` over `SUM()` in SQLite to gracefully handle styles with no child fractions.
