## 2026-06-06 - SQL 'LIKE' on JSON blobs performance bottleneck
**Learning:** In this codebase, `cat_buscar` is used as a catch-all search function that performs SQL `LIKE` queries on a `datos_json` column. When looking up specific records by name or fetching lists of names for autocompletion, this triggers full table scans and redundant data loading (fetching large JSON strings just to extract names).
**Action:** Always prefer direct SQL queries on indexed columns (like `nombre`) and select only required columns when performing specific lookups or populating UI selectors.
