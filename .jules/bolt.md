## 2025-05-14 - Pre-aggregating SQLite child records for UI lists
**Learning:** Calling `ic_listar_fracciones` in a loop inside `IC_Vista._refrescar_lista` introduced an N+1 query overhead. Refactoring `ic_listar_estilos` with a `LEFT JOIN` and `COUNT`/`TOTAL` aggregations reduces 200 list item loads from ~58.5ms to ~1.9ms (~30x speedup).
**Action:** When populating list views with child record summaries, always pre-aggregate count and totals using SQL `LEFT JOIN` and `GROUP BY`.
