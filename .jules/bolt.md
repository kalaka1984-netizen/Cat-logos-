## 2025-05-14 - IC Styles N+1 Query Optimization
**Learning:** The Engineering of Costs (IC) module's style list had a significant performance bottleneck due to an N+1 query pattern: for every style fetched, a separate query was made to count and sum its fractions. This resulted in O(N) database trips, causing noticeable UI lag as the dataset grew.

**Action:** Resolved by using a single SQL query with a `LEFT JOIN` and `GROUP BY` to aggregate fraction counts (`COUNT`) and sums (`TOTAL`) in one trip. This achieved a ~30x speedup for 200 records (from ~0.07s to ~0.002s). SQLite's `TOTAL()` was preferred over `SUM()` as it handles nulls gracefully by returning 0.0.
