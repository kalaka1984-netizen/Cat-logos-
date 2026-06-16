## 2026-06-16 - Resolved N+1 query bottleneck in IC list view
**Learning:** List view refreshes in the Engineering of Costs (IC) module suffered from an N+1 query pattern, where each style record triggered additional synchronous SQLite queries to count and sum its fractions. This caused noticeable lag as the number of styles grew.
**Action:** Use SQL `LEFT JOIN` and aggregate functions (`COUNT`, `TOTAL`) to pre-calculate these values in a single query. Replace `SUM()` with `TOTAL()` in SQLite to ensure a float return value and avoid null-handling overhead in Python.
