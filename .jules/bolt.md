# Bolt's Performance Journal

## 2026-06-02 - N+1 Query Aggregation with SQLite in Cost Engineering List View
**Learning:** In desktop GUI apps (Tkinter/CustomTkinter), list views that query child records in a loop (e.g. `ic_listar_fracciones` per style to calculate count and sum) cause severe UI lag on search input or tab switching due to N+1 SQLite queries. Using `LEFT JOIN` with `GROUP BY` and SQLite's `TOTAL()` aggregate (which always yields a float and defaults to 0.0 rather than NULL like `SUM()`) allows precomputing aggregates in a single database trip (~30x faster) without breaking downstream data contracts.
**Action:** When populating list components with summary statistics of child records, aggregate in SQL via `LEFT JOIN` + `GROUP BY` instead of making per-item database queries in Python loops.
