## 2026-06-15 - [N+1 Query Resolution in SQLite]
**Learning:** In Tkinter applications with SQLite, performing individual child-record queries within a list rendering loop (N+1 problem) causes significant UI lag as the dataset grows. Using 'LEFT JOIN' with 'TOTAL()' and 'COUNT()' aggregates allows the database to handle the heavy lifting in a single pass.
**Action:** Always prefer pre-aggregating child record stats via JOINs when populating list views or tables.
