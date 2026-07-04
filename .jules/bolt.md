## 2026-07-04 - Resolve N+1 query bottleneck in Engineering of Costs list
**Learning:** Identifying and resolving N+1 query patterns in list refreshes significantly improves UI responsiveness. Using SQL `LEFT JOIN` and `GROUP BY` with `TOTAL()` allowed consolidating aggregate data retrieval into a single query.
**Action:** Always check for repeated database calls inside loops, especially in UI refresh methods. Use SQL aggregation to pre-calculate values like counts and sums.
