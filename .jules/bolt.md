# Bolt's Journal

## 2025-02-18 - Database Query and N+1 Bottleneck Optimization
**Learning:** Found that SQLite query performance is significantly degraded when executing `LIKE` queries against large JSON or text columns (like `datos_json`) with empty search values (`%%`). This causes full-table scans. Additionally, nested per-row subqueries (such as calling `ic_listar_fracciones` inside a list iteration in `_refrescar_lista`) produce severe N+1 query overhead that can be avoided by pre-aggregating child fields using a LEFT JOIN with `COUNT()` and `TOTAL()` on SQLite.
**Action:** Always verify if a search string is empty to bypass expensive `LIKE` scans, perform direct exact match SELECTs when query parameters allow, and use LEFT JOIN with SQLite `TOTAL()` aggregation to resolve N+1 query bottlenecks in list renders.
