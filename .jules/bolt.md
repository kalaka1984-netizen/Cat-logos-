## 2025-05-22 - Avoid SQLite LIKE Wildcards on Unindexed and JSON Columns

**Learning:** Using `WHERE column LIKE '%...' OR datos_json LIKE '%...'` forces SQLite to perform O(N) full-table scans, string scanning every row even when the search query string is empty (`""`). Furthermore, using `cat_buscar` to look up specific items by exact key causes unnecessary deserialization and O(N) filtering in Python.
**Action:** Always check if the search string is empty before constructing `LIKE` queries to bypass wildcard matching, and use direct indexed `WHERE key=?` queries for exact item lookups.
