## 2025-05-18 - SQLite Pre-aggregation for N+1 Query Prevention in UI List Rendering
**Learning:** Performing per-row child queries (`ic_listar_fracciones`) inside UI loop renders (`IC_Vista._refrescar_lista`) creates severe N+1 bottlenecks. SQLite `LEFT JOIN` combined with `COUNT()` and `TOTAL()` allows single-query retrieval of row counts and sums without raising `NoneType` errors for empty child sets.
**Action:** Always pre-aggregate child table metrics in SQL list queries using `LEFT JOIN` and `GROUP BY` when building desktop UI list components.
