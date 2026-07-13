## 2025-05-15 - N+1 Query Optimization in Style Listings
**Learning:** Resolving N+1 query bottlenecks in list view refreshes by replacing individual child-record lookups in loops with a single SQL query using `LEFT JOIN` and `GROUP BY` to aggregate counts or sums. In SQLite, `TOTAL()` is preferred over `SUM()` because it returns 0.0 instead of NULL when no rows match, avoiding potential Python type errors.
**Action:** Always look for loops that execute database queries and refactor them into a single JOIN-based query with pre-aggregation.

## 2025-05-15 - Redundant Variable Removal
**Learning:** In `IC_Vista._refrescar_lista`, the `bal_txt` variable provides a high-fidelity status (e.g., '✓ CUADRA', 'FALTA $...') and is mapped to the 'MODO' column in the UI, rendering the generic `modo` variable redundant.
**Action:** Use linting tools like `ruff` to identify and safely remove unused local variables (F841) during refactoring.
