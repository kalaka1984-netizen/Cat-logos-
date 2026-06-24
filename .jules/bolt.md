## 2025-05-15 - SQL JOIN vs N+1 in Style Listings
**Learning:** Listing records that require aggregated data from child tables (e.g., counting fractions for a style) is a major bottleneck when performed iteratively in Python. A single SQL query using `LEFT JOIN` and `GROUP BY` is significantly faster.
**Action:** Always look for loops that perform database queries per-item and replace them with aggregated JOINs.

## 2025-05-15 - Headless GUI Testing
**Learning:** Modules that initialize GUI components or calculate screen scaling on import will crash in headless environments. Mocking `tkinter` and `customtkinter` is required, and screen dimensions must be mocked as integers to avoid `TypeError` in comparison logic.
**Action:** Use a robust mock setup for `tkinter` before importing any UI modules in tests.

## 2025-05-15 - SQLite Aggregate Safety
**Learning:** In SQLite, `SUM()` returns `NULL` if no rows match, while `TOTAL()` returns `0.0`. Using `TOTAL()` is safer for Python math operations and prevents `TypeError` when a parent has no children.
**Action:** Prefer `TOTAL()` for price/quantity sums in SQLite aggregate queries.
