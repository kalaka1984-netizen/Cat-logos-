## 2025-05-24 - N+1 Query in SQLite JOIN vs. Manual Loop
**Learning:** In `modulo_catalogos.py`, the style list view was performing a separate SQL query to count and sum fractions for every style fetched, leading to O(N) queries. Replacing this with a single `LEFT JOIN` and aggregate functions (`COUNT`, `TOTAL`) reduced query time from ~60ms to ~1.8ms for 200 records. Using SQLite's `TOTAL()` is better than `SUM()` as it returns `0.0` instead of `NULL` for empty joins.
**Action:** Always look for loops that perform database queries per item and replace them with set-based SQL operations (JOINs/GROUP BY) to minimize I/O overhead.

## 2025-05-24 - GUI Mocking in Headless Environments
**Learning:** Testing or importing modules that instantiate `tkinter` or `customtkinter` components at the top level or during class definition fails in headless environments. Simple `MagicMock` may cause `TypeError` in scaling logic if integer values are expected, or `TypeError: metaclass conflict` if inheritance from mocked classes is used.
**Action:** Use a more robust mock that provides real base classes and returns valid integers for winfo methods when testing GUI-heavy Python modules.
