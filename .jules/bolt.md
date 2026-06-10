## 2025-05-15 - Exact match optimization for indexed columns
**Learning:** Using 'LIKE' on large JSON columns (datos_json) when an exact match on an indexed column (nombre) is possible causes unnecessary full table scans and Python-side filtering. Also, fetching large blobs when only the 'nombre' is needed wastes I/O.
**Action:** Use exact match queries for ID-like lookups and avoid selecting 'datos_json' when it's not required.
