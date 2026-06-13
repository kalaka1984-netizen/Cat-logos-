## 2025-05-15 - [N+1 Query Bottleneck in IC Module]
**Learning:** Resolving N+1 query bottlenecks in list view refreshes by replacing individual child-record lookups in loops with a single SQL query using `LEFT JOIN` and `GROUP BY` to aggregate counts or sums significantly improves UI responsiveness. Using SQLite's `TOTAL()` function ensures a `0.0` result instead of `NULL`, simplifying Python-side handling.
**Action:** Always check for repeated database queries within loops during list retrieval and prioritize aggregated JOIN queries.
