## 2024-05-15 - N+1 Query in Style Listing
**Learning:** Found a classic N+1 query bottleneck in `IC_Vista._refrescar_lista` where `ic_listar_fracciones` was called for every row returned by `ic_listar_estilos`. This resulted in significant UI lag when the number of styles grew.
**Action:** Replaced the individual queries with a single `LEFT JOIN` and SQL aggregates (`COUNT`, `TOTAL`) in `ic_listar_estilos`. This improved performance by ~30-40x for 200 records.

## 2024-05-15 - Unused UI Variable `modo`
**Learning:** The `modo` variable in `_refrescar_lista` was being calculated but was redundant because `bal_txt` (the high-fidelity status) was already being mapped to the "MODO" column in the UI. Ruff correctly identified it as an unused variable (F841).
**Action:** Removed the `modo` calculation to clean up the code and resolve the linting error.
