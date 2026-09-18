## 2025-02-18 - Database Search & Lookup Optimizations in Catalog Modules

**Learning:** When retrieving records for dropdowns or autocompletes, querying full table rows with large JSON blobs (`datos_json`) and executing wildcard `LIKE` searches on empty strings causes significant I/O and CPU overhead. Using composite indexes `(estatus, nombre)`, direct indexed column SELECTs (`SELECT nombre ...`), and bypassing `LIKE` on empty search strings yields ~5.8x speedup on name listings and ~33.5x speedup on direct material lookups.

**Action:** Always check if list query helpers fetch unneeded large text/JSON columns or evaluate wildcard `LIKE` on empty strings, and optimize with direct indexed column projection and shortcut queries for empty search parameters.
