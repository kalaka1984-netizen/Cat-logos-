## 2025-02-18 - Pre-aggregating Child Records in SQLite JOINs
**Learning:** Performing per-row child queries in SQLite list rendering loops creates a severe N+1 bottleneck. Using `LEFT JOIN` with `COUNT(f.id)` and `TOTAL(f.precio)` returns pre-aggregated child counts and sums in a single pass while correctly handling zero-child cases (defaulting to 0.0 without NULL).
**Action:** Always pre-aggregate child metrics using SQL `GROUP BY` and `TOTAL()` for UI list views.
