## 2025-05-22 - SQL JOIN for N+1 query optimization in style listing
**Learning:** The IC_Vista._refrescar_lista function was performing a separate SQL query for each style to count and sum its fractions, creating an N+1 performance bottleneck. Using a LEFT JOIN with GROUP BY in ic_listar_estilos allows fetching all necessary data in a single query.
**Action:** Always check for UI loops that perform database queries. Aggregate data in the initial fetch whenever possible.
