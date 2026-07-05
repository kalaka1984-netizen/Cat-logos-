## 2025-05-15 - N+1 Query in Style Listing
**Learning:** The 'ic_listar_estilos' function was causing an N+1 query bottleneck by fetching related fractions for each style in a loop during UI refresh. This significantly slowed down the application as the number of styles grew.
**Action:** Use SQL JOINs and aggregate functions (COUNT, TOTAL) to fetch all required data in a single query. Always use 'TOTAL()' instead of 'SUM()' in SQLite to ensure a float result and avoid NULLs.
>>>>>>> REPLACE
