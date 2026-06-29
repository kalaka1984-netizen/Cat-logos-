## 2025-05-15 - N+1 Query in Style Listing
**Learning:** The style listing in Engineering of Costs was performing a separate query for each row to count fractions and sum prices, leading to O(N) database calls.
**Action:** Use SQL `LEFT JOIN` and aggregation (`COUNT`, `TOTAL`) to pre-calculate these values in a single query. `TOTAL()` is preferred over `SUM()` in SQLite to ensure a float result (0.0 instead of NULL) for empty sets.
