## 2025-02-14 - [SQLite N+1 Query & Headless GUI Testing Patterns]
**Learning:**
1. Database N+1 queries in loop iterations severely degrade GUI rendering performance in SQLite. Using aggregate functions like `COUNT` and `TOTAL` combined with a `LEFT JOIN` and `GROUP BY` allows the entire list and its metrics to be fetched in a single query, resulting in a ~37x speedup.
2. The SQLite `LIKE` operator causes full scans when evaluating empty search strings. Explicitly checking for empty search inputs and executing direct scans without pattern matching bypasses this CPU bottleneck.
3. Testing Python desktop applications in headless CI/CD environments requires mocking `tkinter` and `customtkinter`. Simple `MagicMock` base classes trigger metaclass conflict errors when standard classes inherit from them. Creating dummy Python classes for frames/windows completely bypasses this. Additionally, screen scaling logic comparing dimensions requires mocked measurement functions to return integer values instead of mock objects to avoid comparison `TypeError` crashes.

**Action:**
1. Always replace loops calling lookups with pre-aggregated SQL JOIN queries.
2. Explicitly guard `LIKE` clauses with checking if search string has characters.
3. Mock GUI components with dummy Python classes as base classes and configure `winfo` methods to return dummy integers.
