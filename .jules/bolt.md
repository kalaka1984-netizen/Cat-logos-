## 2024-07-29 - SQLite N+1 JOIN and TOTAL() Pre-aggregation
**Learning:** Resolving N+1 query bottlenecks in SQLite list refreshes via a SQL LEFT JOIN is highly performant (~8x-37x faster), but using `SUM()` can return `NULL` for styles without fractions, leading to Python `TypeError` in UI loops. SQLite's `TOTAL()` aggregate function always returns a float (defaulting to `0.0` if no matching rows exist), perfectly safeguarding against type errors.
**Action:** Always favor `TOTAL()` over `SUM()` in SQLite left joins to compute sums safely.

## 2024-07-29 - SQLite LIKE Bypassing and Indexed O(1) Searches
**Learning:** Searching using wildcard `LIKE` (e.g., `%%`) forces SQLite to sequentially scan the entire table and deserialize/parse large columns (like text or JSON `datos_json` fields), transforming a basic list load into an expensive O(N) sequential scan. Adding an empty-query fast path avoids `LIKE` completely. Furthermore, bypassing a generic search helper with sequential scans (e.g., `cat_buscar`) in favor of a direct O(1) query on an indexed column (e.g., `nombre`) yields immediate massive speedups.
**Action:** Avoid wildcard `LIKE '%%'` queries for default empty searches and always run exact direct indexed SELECTs where applicable.
