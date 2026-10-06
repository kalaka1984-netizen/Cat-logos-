## 2026-06-02 - SQL JOIN Pre-Aggregation Eliminates N+1 Queries in UI List Refreshes
**Learning:** Calling child-record database query functions (like `ic_listar_fracciones`) inside a loop during UI list rendering creates an N+1 query bottleneck that scales linearly with dataset size (~37ms down to ~1ms for 200 items).
**Action:** Use SQL `LEFT JOIN` with `COUNT()` and `TOTAL()` pre-aggregation in list fetch functions (`ic_listar_estilos`) to compute summary fields in a single query.
