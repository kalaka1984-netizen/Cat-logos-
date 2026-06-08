## 2025-05-15 - Headless GUI Imports and Metaclass Conflicts
**Learning:** Importing a module that creates a `tkinter.Tk` instance or uses `customtkinter` on import will fail in headless environments. Mocking `customtkinter` classes (like `CTkFrame`) with just `MagicMock` can lead to metaclass conflicts if the code uses multiple inheritance with real classes.
**Action:** Use a real base class for mocks of GUI components and mock `tkinter.Tk` to return a mock with appropriate screen dimensions to satisfy scaling calculations.

## 2025-05-15 - SQL Performance on JSON Columns
**Learning:** Generic search functions using `LIKE` on JSON columns are extremely inefficient for exact lookups or empty searches.
**Action:** Implement shortcuts for empty search strings and use indexed equality lookups for exact matches. Always select specific columns instead of full rows containing large JSON blobs when only metadata is needed.
