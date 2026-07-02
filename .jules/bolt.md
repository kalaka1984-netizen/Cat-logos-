## 2025-05-15 - N+1 Query Optimization in Style Listings

**Learning:** The 'ic_listar_estilos' function was causing an N+1 query pattern in the UI refresh loop by calling 'ic_listar_fracciones' for every style record. This resulted in significant overhead as the number of styles grew. Using a SQL 'LEFT JOIN' with 'GROUP BY' allows pre-calculating counts and sums in a single query.

**Action:** Replace individual child-record lookups in loops with aggregated JOIN queries. Use SQLite's 'TOTAL()' function instead of 'SUM()' to ensure a float (0.0) is returned when no child records exist, avoiding NULL handling issues in Python.

## 2025-05-15 - Redundant Variable Detection

**Learning:** The 'modo' variable in 'IC_Vista._refrescar_lista' was defined but unused (verified by Ruff F841 and manual code trace), likely a leftover from a previous version where 'bal_txt' replaced its functionality for the 'MODO' column.

**Action:** Always trust linting tools like Ruff to identify dead code, but perform an exhaustive trace of variable usage before removal to ensure no legacy UI components or late-bound lambdas depend on it.
