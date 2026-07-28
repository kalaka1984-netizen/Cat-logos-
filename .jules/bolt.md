## 2024-07-28 - [N+1 Query Resolution & Aggregation Optimization]
**Learning:** Resolving N+1 database queries in desktop list views using SQL `LEFT JOIN` and SQLite `TOTAL()` aggregates is highly efficient. When grouping by style ID, using `TOTAL()` instead of `SUM()` ensures we safely return a float defaulting to `0.0` even when no matching rows exist, preventing type errors in Python. Also, we can bypass expensive wildcard `LIKE` operations with simple empty search-string checks.
**Action:** Always replace loop-level queries in table/list views with aggregated queries using `LEFT JOIN` + `GROUP BY` and use SQLite's robust `TOTAL()` function for numeric aggregations.

## 2024-07-28 - [Pipx pytest vs. System python3 -m pytest]
**Learning:** In headless sandbox environments with pre-installed tkinter wrappers, executing tests with global `pytest` may fail with `ModuleNotFoundError: No module named 'tkinter'` if the pipx virtual environment is isolated from the system Python.
**Action:** Always use `python3 -m pytest` to run the test suite using the system Python interpreter which has access to tkinter/customtkinter.
