## 2024-05-15 - N+1 Query Resolution in Tkinter Desktop App
**Learning:** Resolving N+1 query loops using SQLite's `LEFT JOIN` and aggregate `TOTAL()` function significantly improves listing load performance while keeping database integrity intact.
**Action:** Use `TOTAL()` instead of `SUM()` in LEFT JOIN queries because `TOTAL()` always returns a float (even if no rows match, defaulting to 0.0), which prevents Python type errors and avoids handling `None` values.
