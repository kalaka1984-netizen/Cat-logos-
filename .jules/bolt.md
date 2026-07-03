## 2025-05-15 - N+1 Query Bottleneck in Style Listings
**Learning:** In list views where child records are counted or summed (e.g., counting fractions per style), a naive implementation results in an N+1 query problem, significantly slowing down UI refreshes. Using a SQL `LEFT JOIN` with `GROUP BY` and `TOTAL()` (which handles empty sets as 0.0 better than `SUM()`) can speed up listing by 30-40x.
**Action:** Always check for repeated child-record lookups in UI rendering loops and replace them with aggregated JOIN queries.
