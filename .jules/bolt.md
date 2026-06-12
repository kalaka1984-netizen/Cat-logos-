# Bolt's Journal - Critical Learnings

## 2025-05-15 - Mocking GUI for Headless Verification
**Learning:** This codebase heavily depends on `tkinter` and `customtkinter`, which attempt to initialize GUI components on import. In a headless environment, this causes `TclError` or `ModuleNotFoundError`.
**Action:** When writing verification scripts or tests, mock `tkinter` and `customtkinter` before importing any module from the codebase.
