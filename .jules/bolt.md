## 2026-06-19 - [N+1 Query in IC_Vista._refrescar_lista]
**Learning:** Found an N+1 query pattern in `IC_Vista._refrescar_lista` where it fetches fractions for every style in a loop to calculate counts and sums. This can be optimized using a SQL JOIN and GROUP BY.
**Action:** Replace individual queries in the loop with a single aggregated JOIN query in `ic_listar_estilos`.
