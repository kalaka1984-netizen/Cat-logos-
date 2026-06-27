## 2025-05-22 - SQL JOIN for N+1 Query Optimization
**Learning:** In SQLite-based Python applications with parent-child relationships (like styles and fractions), fetching child counts and sums in a loop creates an O(N) query bottleneck. Using `LEFT JOIN` with `COUNT()` and `TOTAL()` (which safely returns 0.0 for empty sets) allows O(1) retrieval of all data.
**Action:** Always check for loops that query child tables by foreign key and replace them with aggregated JOINs in the main query.
