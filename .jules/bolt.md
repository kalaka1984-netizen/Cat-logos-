## 2025-01-24 - N+1 Query Bottleneck in SQLite UI Lists
**Learning:** Calling `SELECT` for child records (e.g., `ic_listar_fracciones`) inside a loop while rendering a UI list (e.g., `_refrescar_lista`) causes an N+1 query problem, which is significantly slower than using a single `LEFT JOIN` with aggregate functions like `COUNT()` and `TOTAL()`. In this case, a ~30x speedup was achieved for 200 records.
**Action:** Always prefer SQL joins and pre-aggregation for list views involving child record metadata.

## 2025-01-24 - Repository Hygiene: Binary Artifacts
**Learning:** Running benchmarks often generates transient files like `catalogos_db.sqlite` and `__pycache__/` directories. If not deleted, these can be accidentally included in the PR, bloating the repository.
**Action:** Explicitly delete all benchmark-generated files and build artifacts before requesting code review or submitting.
