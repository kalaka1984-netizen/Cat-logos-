## 2025-05-20 - Fast Direct SQL Selection for Catalog Lookups
**Learning:** Reusing general search functions (`cat_buscar`) with `LIKE` filters for exact lookups or list retrieval causes unnecessary full table scans and Python JSON deserialization overhead.
**Action:** Use targeted `SELECT` queries with indexed column matches (`WHERE nombre = ?`) or specific column lists (`SELECT nombre ...`) for lookup APIs to achieve up to 17x faster database queries.
