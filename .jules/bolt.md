## 2025-05-15 - N+1 Query in GUI List Refresh
**Learning:** In applications using SQLite for GUI list rendering, fetching child record counts/sums in a loop (N+1 queries) causes noticeable UI lag as the dataset grows. JOINing and aggregating in a single SQL query using `COUNT()` and `TOTAL()` is significantly faster.
**Action:** Always prefer SQL aggregation for list view metadata (like counts/sums of child records) instead of individual queries in a loop.

## 2025-05-15 - Ruff --fix risk in legacy code
**Learning:** Running `ruff --fix` on large files with non-standard formatting (e.g., multiple statements on one line using semicolons or colons) can lead to accidental deletions of required logic if not carefully reviewed.
**Action:** Manually review every change made by automated formatters in large legacy files, or avoid `--fix` on unowned code sections.
