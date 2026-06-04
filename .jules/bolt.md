## 2025-05-14 - [Inefficient generic search for exact matches and full listings]
**Learning:** Generic search functions using `LIKE %text%` on JSON fields are significantly slower than exact matches on indexed columns. Functions like `cat_get_material_por_nombre` were performing O(N) Python-side filtering instead of utilizing SQL indexes.
**Action:** Use exact SQL queries (`WHERE nombre = ?`) for lookups by name and skip `LIKE` clauses when search text is empty to improve full listing performance.
