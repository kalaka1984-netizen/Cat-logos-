## 2026-03-20 - Substring Inclusion Bug in Material Type Check
**Learning:** `cat_precarga_material` previously checked `"DIRECTO" in tipo_raw`, which evaluated to `True` for both `"DIRECTO"` and `"INDIRECTO"` due to substring matching.
**Action:** When matching category strings that contain common sub-words (like "DIRECTO" and "INDIRECTO"), check for the unique/distinct prefix or substring first (e.g. `"IND" in tipo_raw`).
