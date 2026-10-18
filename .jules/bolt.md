## 2025-02-23 - Direct SQLite Index Scan vs. Full Table Wildcard Scan

**Learning:** Calling generic search functions like `cat_buscar` to retrieve single exact matches or column lists performs an $O(N)$ full table scan with `LIKE %query%` on unparsed `datos_json` columns. Bypassing generic search with direct indexed `SELECT` queries on indexed `nombre` achieves up to ~43.5x speedup for exact lookups and ~3.6x speedup for column listings.

**Action:** When querying catalog tables for specific fields or exact row matches, write direct parameterized SQL queries on indexed columns rather than reusing full-text table search helpers.
