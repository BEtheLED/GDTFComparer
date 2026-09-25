---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
# Coding Conventions

**Analysis Date:** 2026-09-25

## Naming Patterns

**Files:**

- Snake case with no extension for main scripts (e.g., `BEtheLD`)
- Lowercase `.py` extension for modules and packages (e.g., `blender_addon/__init__.py`)
- Test files follow `test_*.py` pattern (e.g., `test_parse_gdtf.py`)

**Functions:**

- Snake case for all functions (e.g., `parse_gdtf()`, `create_widgets()`, `select_target_file()`)
- Descriptive verb-noun patterns preferred (e.g., `select_target_file`, `run_comparison`)

**Variables:**

- Snake case for all variable names (e.g., `target_file`, `compare_files`, `temp_dir`, `tree_scrollbar`)
- Instance attributes prefixed with `self.` (e.g., `self.master`, `self.target_entry`)

**Types:**

- Classes use PascalCase (e.g., `GDTFComparerApp`)
- Type hints in function signatures using `typing` module (e.g., `Dict[str, Any]`, `str`)

**Constants:**

- Dictionary keys appear to use camelCase for attribute names (e.g., `'BeamAngle'`, `'PowerConsumption'`)
- Dictionary structure constants use lowercase names (e.g., `self.attribute_categories`)

## Code Style

**Formatting:**

- No explicit formatter configured (no `.flake8`, `.pylintrc`, or `pyproject.toml`)
- Standard Python conventions appear to be followed implicitly
- 4-space indentation used throughout
- Line length varies, with typical lengths between 80-120 characters

**Linting:**

- No linting configuration detected
- Code uses type hints from `typing` module, suggesting type checking may be desired

**Import Organization:**

- Standard library imports first: `os`, `zipfile`, `xml.etree.ElementTree`, `typing`, `shutil`, `tempfile`, `tkinter`
- Third-party/conditional imports follow (though minimal third-party dependencies present)
- One import per line is the standard, except for related tkinter submodules
- Imports organized by: standard library → third-party → local

Example from `BEtheLD`:

```python
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, ttk
```

## Error Handling

**Patterns:**

- Specific exception types caught and re-raised to allow caller handling (e.g., `zipfile.BadZipFile`, `xml.etree.ElementTree.ParseError`)
- Exception context preserved when re-raising (uses `raise exc` to maintain traceback)
- Try/finally blocks used for resource cleanup (e.g., temporary directory cleanup)
- Comments explain exception handling intent:
  ```python
  except zipfile.BadZipFile as exc:
      # Propagate the error so callers can handle it (e.g. tests)
      raise exc
  ```

**Example from `BEtheLD` lines 147-152:**

```python
try:
    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
except zipfile.BadZipFile as exc:
    raise exc
```

## Logging

**Framework:** No logging framework configured; `tkinter` messagebox used for UI errors

**Patterns:**

- Error messages displayed via `messagebox.showerror()` in GUI context
- No structured logging framework (no logging module usage detected)
- Errors are raised to caller rather than logged

## Comments

**When to Comment:**

- Comments explain intent, not implementation (e.g., "Propagate the error so callers can handle it")
- Comments placed at line or block level where behavior needs clarification
- Minimal inline comments; prefer self-documenting code

**Docstrings:**

- Docstrings present on public functions using triple-quoted format
- DocString style: descriptive summary with Parameters and Returns sections
- Example from `BEtheLD` lines 131-141:
  ```python
  def parse_gdtf(file_path: str) -> Dict[str, Any]:
      """Parse a GDTF file.

      Parameters:
          file_path: Path to the ``.gdtf`` file to parse.

      Returns:
          Dictionary of attributes extracted from ``description.xml`` inside the
          archive. If ``description.xml`` is not found, an empty dictionary is
          returned.
      """
  ```

## Function Design

**Size:** Functions are typically 10-40 lines, with `run_comparison()` being one of the larger methods at ~25 lines

**Parameters:** 

- Type hints used in function signatures
- Default values not extensively used
- `self` is first parameter for methods
- File paths pass as strings, not Path objects (though `Path` is available in test utilities)

**Return Values:**

- Functions either return a single value or `None`
- Type hints specify return type (e.g., `-> Dict[str, Any]`, `-> None`)
- Empty dict `{}` returned when resource not found (e.g., when description.xml missing)

## Module Design

**Exports:**

- Main entry point via `if __name__ == "__main__":` block (e.g., `BEtheLD` line 191)
- Blender addon defines `register()` and `unregister()` as public entry points for addon system
- Functions like `parse_gdtf()` and `main()` are public module functions

**Barrel Files:**

- Blender addon uses `__init__.py` for package metadata and entry points (lines 1-21)
- No barrel-style re-exports detected

## Class Design

**Organization:**

- `__init__()` method first, defining all instance attributes
- `create_widgets()` method early, handling initialization
- Action methods grouped logically (select/file operations, then run operations)
- Related methods kept together (e.g., file selection methods)

**Example from `GDTFComparerApp` organization in `BEtheLD`:**

1. `__init__()` - initialization
2. `create_widgets()` - UI setup
3. File selection methods - `select_target_file()`, `select_compare_files()`, `remove_selected_files()`
4. Action methods - `run_comparison()`

---

*Convention analysis: 2026-09-25*
