## 2024-06-11 - Optimized N+1 queries in Engineering Costs style list
**Learning:** The `IC_Vista._refrescar_lista` method was performing a database query for each style to fetch fraction counts and sums, resulting in an N+1 query bottleneck. Using a SQL `LEFT JOIN` with `GROUP BY` allowed fetching all necessary data in a single query.
**Action:** Always check for database queries inside loops, especially in list refreshing logic, and replace them with aggregated JOINs.
