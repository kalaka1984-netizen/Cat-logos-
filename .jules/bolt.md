## 2025-05-20 - N+1 Query Aggregation in SQLite List Refreshes
**Learning:** In SQLite/desktop applications, calling child-record list queries inside list-render loops (N+1 queries) causes severe latency as dataset size grows. SQLite's `TOTAL()` aggregate function handles `LEFT JOIN` aggregations safely by returning `0.0` instead of `NULL` when no child records exist.
**Action:** Replace loop child queries with SQL `LEFT JOIN` and `GROUP BY e.id`, utilizing `TOTAL()` for sums to ensure type consistency and ~30x performance improvements.
