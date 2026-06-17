## 2025-05-15 - N+1 Query in IC Module
**Learning:** The Engineering of Costs (IC) module list view suffered from an N+1 query bottleneck, fetching fractions for each style in a loop.
**Action:** Use SQL JOINs and GROUP BY with aggregate functions (COUNT, TOTAL) to fetch all required metrics in a single query.

## 2025-05-15 - Repository Hygiene
**Learning:** Automated code review flagged binary `.pyc` files in the patch.
**Action:** Always clear `__pycache__` and delete temporary benchmark scripts before submitting.
