## 2025-05-15 - N+1 Query in Engineering Costs
**Learning:** The Engineering Costs list view was performing a separate database query for every row to fetch and sum fraction data. For a list of 200 styles, this resulted in 201 queries.
**Action:** Use SQL `LEFT JOIN` and `GROUP BY` with aggregate functions like `COUNT()` and `TOTAL()` to pre-calculate these values in a single database round-trip. This resulted in a ~28x speedup in UI refresh times.

## 2025-05-15 - Exact Match vs. LIKE for Indexed Lookups
**Learning:** Using a generic search function that employs SQL `LIKE %text%` on JSON columns bypasses database indexes and forces full table scans.
**Action:** Implement dedicated lookup functions (e.g., `cat_get_material_por_nombre`) that use exact equality matches on indexed columns when the full identifier is known.
