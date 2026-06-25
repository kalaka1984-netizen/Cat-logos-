## 2024-10-27 - [N+1 query in Ingeniería de Costos]
**Learning:** The 'Ingeniería de Costos' module was suffering from an N+1 query problem when listing styles, as it queried for the fractions of each style individually inside a loop. This can be optimized by using a single SQL query with a `LEFT JOIN` and `GROUP BY` to aggregate the count and sum of fractions.
**Action:** Use SQL JOINs and aggregation functions like `COUNT()` and `TOTAL()` to fetch child record summaries in a single query when rendering lists.

## 2024-10-27 - [Headless environment mocking]
**Learning:** Testing GUI-related Python modules in a headless environment requires careful mocking of 'tkinter' and 'customtkinter'. Simple mocks may fail if the module performs operations on the mock's return values (like screen width comparisons) or if there are metaclass conflicts during inheritance.
**Action:** Provide realistic return values for common winfo methods in mocks (e.g., screen dimensions as integers) and ensure base classes in mocks are sufficient to avoid metaclass issues.
