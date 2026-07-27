## 2024-07-27 - [Metaclass Conflicts in Headless GUI Mocking & SQLite In-Memory Isolation]
**Learning:**
1. In headless automated testing environments, simply mocking GUI packages like `customtkinter` with basic `MagicMock()` causes severe Python metaclass conflicts if production classes inherit from mocked customtkinter classes (e.g., `class CatalogosFrame(CatalogosMixin, ctk.CTkFrame)`). This is because Python cannot resolve metaclasses when a parent is a MagicMock.
2. In SQLite, using `":memory:"` as a database path isolates each unique connection. Consecutive connect/close operations (e.g., first to initialize schema and then in a separate connection to query) operate on separate database instances, causing "no such table" errors.

**Action:**
1. Always mock `customtkinter` and `tkinter` using real Python dummy classes (with necessary dummy methods like `winfo_children()`, `pack()`, `after()`) for UI widgets used as base classes.
2. Use a distinct, temporary disk-backed SQLite database file (e.g., `test_catalogos.sqlite`) for testing database state transition functions across different connection handles, and clean it up in `tearDown`.
