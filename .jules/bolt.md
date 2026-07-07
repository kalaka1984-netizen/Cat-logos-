## 2025-05-15 - N+1 Query Bottleneck in SQLite-backed GUI Lists
**Learning:** Rendering lists where each row requires an additional database lookup (e.g., child record counts or sums) causes significant performance degradation as the dataset grows (N+1 problem). SQLite is fast, but multiple round-trips from a Python loop are much slower than a single JOIN query.
**Action:** Use SQL `LEFT JOIN` and aggregate functions (`COUNT`, `TOTAL`) with `GROUP BY` to retrieve all necessary data in one query.
