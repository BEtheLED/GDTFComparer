<!-- GSD:project-start source:PROJECT.md -->

## Project

**GDTF Comparer**

A desktop application for lighting/AV professionals that compares GDTF (General Device Type Format) fixture files side-by-side, showing which attributes differ between a target fixture and one or more comparison fixtures. Originally prototyped with ChatGPT as a Tkinter script; this milestone rebuilds it into a polished, standalone application that runs without a Python install, for the creator and other lighting/AV professionals to use.

**Core Value:** You can pick a target GDTF file and any number of comparison files and immediately see which fixture attributes actually differ — without needing Python, dependencies, or command-line knowledge to run the tool.

### Constraints

- **Tech stack**: Python-based today; open to swapping the GUI framework as part of the "better UI" work, but MVRxchange integration and standalone packaging need to work from whatever stack is chosen.
- **Distribution**: Must produce installable/runnable standalone builds for both macOS and Windows with no separate Python install required by the end user.
- **Compatibility**: Must continue to correctly read `.gdtf` (zip+XML) fixture files; MVRxchange integration must not break basic file-based comparison for users who aren't networked.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.7+ - Core application logic, GDTF parsing, GUI development
- Python (Blender API subset) - Blender addon module in `blender_addon/`

## Runtime

- Python 3.7 or higher
- No external runtime required for core application
- pip (implicit - no lockfile or requirements.txt present)
- Blender's embedded Python for addon execution

## Frameworks

- tkinter (Python standard library) - GUI framework for GDTF Comparer application, used in `BEtheLD`
- pytest - Test runner for `tests/test_parse_gdtf.py`
- Blender 2.80+ - Required for addon execution

## Key Dependencies

- `zipfile` - Handles GDTF file extraction (ZIP archive format)
- `xml.etree.ElementTree` - XML parsing for `description.xml` extraction
- `os` - File system operations
- `shutil` - Directory operations (copy, remove)
- `tempfile` - Temporary directory creation for extraction
- `tkinter` - GUI components (part of Python standard library)
- `typing` - Type hints for function signatures
- `pytest` - Test framework for `tests/test_parse_gdtf.py`
- `importlib` - Dynamic module loading for test fixture (standard library)

## Configuration

- No environment variables required
- No configuration files detected (`.env`, `.ini`, `.toml`, `.yaml`)
- No build configuration detected (no `setup.py`, `pyproject.toml`, `Makefile`, or build scripts)
- Direct Python execution via `python BEtheLD` or Blender addon loader

## Platform Requirements

- Python 3.7+ interpreter
- pytest (for running tests)
- Blender 2.80+ (for addon development/testing)
- Python 3.7+ interpreter
- tkinter (included with Python on most distributions)
- For addon: Blender 2.80+ application
- Linux, macOS, Windows (all support Python 3.7+ and tkinter)

## File Format Support

- GDTF (`.gdtf` files) - ZIP archives containing `description.xml`
- MVR (referenced in `blender_addon/` but not yet implemented)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Snake case with no extension for main scripts (e.g., `BEtheLD`)
- Lowercase `.py` extension for modules and packages (e.g., `blender_addon/__init__.py`)
- Test files follow `test_*.py` pattern (e.g., `test_parse_gdtf.py`)
- Snake case for all functions (e.g., `parse_gdtf()`, `create_widgets()`, `select_target_file()`)
- Descriptive verb-noun patterns preferred (e.g., `select_target_file`, `run_comparison`)
- Snake case for all variable names (e.g., `target_file`, `compare_files`, `temp_dir`, `tree_scrollbar`)
- Instance attributes prefixed with `self.` (e.g., `self.master`, `self.target_entry`)
- Classes use PascalCase (e.g., `GDTFComparerApp`)
- Type hints in function signatures using `typing` module (e.g., `Dict[str, Any]`, `str`)
- Dictionary keys appear to use camelCase for attribute names (e.g., `'BeamAngle'`, `'PowerConsumption'`)
- Dictionary structure constants use lowercase names (e.g., `self.attribute_categories`)

## Code Style

- No explicit formatter configured (no `.flake8`, `.pylintrc`, or `pyproject.toml`)
- Standard Python conventions appear to be followed implicitly
- 4-space indentation used throughout
- Line length varies, with typical lengths between 80-120 characters
- No linting configuration detected
- Code uses type hints from `typing` module, suggesting type checking may be desired
- Standard library imports first: `os`, `zipfile`, `xml.etree.ElementTree`, `typing`, `shutil`, `tempfile`, `tkinter`
- Third-party/conditional imports follow (though minimal third-party dependencies present)
- One import per line is the standard, except for related tkinter submodules
- Imports organized by: standard library → third-party → local

## Error Handling

- Specific exception types caught and re-raised to allow caller handling (e.g., `zipfile.BadZipFile`, `xml.etree.ElementTree.ParseError`)
- Exception context preserved when re-raising (uses `raise exc` to maintain traceback)
- Try/finally blocks used for resource cleanup (e.g., temporary directory cleanup)
- Comments explain exception handling intent:

## Logging

- Error messages displayed via `messagebox.showerror()` in GUI context
- No structured logging framework (no logging module usage detected)
- Errors are raised to caller rather than logged

## Comments

- Comments explain intent, not implementation (e.g., "Propagate the error so callers can handle it")
- Comments placed at line or block level where behavior needs clarification
- Minimal inline comments; prefer self-documenting code
- Docstrings present on public functions using triple-quoted format
- DocString style: descriptive summary with Parameters and Returns sections
- Example from `BEtheLD` lines 131-141:

## Function Design

- Type hints used in function signatures
- Default values not extensively used
- `self` is first parameter for methods
- File paths pass as strings, not Path objects (though `Path` is available in test utilities)
- Functions either return a single value or `None`
- Type hints specify return type (e.g., `-> Dict[str, Any]`, `-> None`)
- Empty dict `{}` returned when resource not found (e.g., when description.xml missing)

## Module Design

- Main entry point via `if __name__ == "__main__":` block (e.g., `BEtheLD` line 191)
- Blender addon defines `register()` and `unregister()` as public entry points for addon system
- Functions like `parse_gdtf()` and `main()` are public module functions
- Blender addon uses `__init__.py` for package metadata and entry points (lines 1-21)
- No barrel-style re-exports detected

## Class Design

- `__init__()` method first, defining all instance attributes
- `create_widgets()` method early, handling initialization
- Action methods grouped logically (select/file operations, then run operations)
- Related methods kept together (e.g., file selection methods)

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| GDTFComparerApp | GUI initialization, widget creation, event handling | `BEtheLD` (lines 11-128) |
| parse_gdtf() | Archive extraction, XML parsing, attribute extraction | `BEtheLD` (lines 131-182) |
| Blender Addon Skeleton | Addon registration and structure | `blender_addon/__init__.py` |
| Tests | Validation of parse_gdtf() behavior | `tests/test_parse_gdtf.py` |

## Pattern Overview

- Monolithic design with GUI tightly coupled to business logic
- Single-entry-point CLI application (BEtheLD script)
- Functional parsing module (parse_gdtf) that can be imported independently
- Separate Blender addon structure for future extension
- No explicit MVC pattern; UI logic and data processing mixed in GDTFComparerApp

## Layers

- Purpose: Display file selection UI and comparison results
- Location: `BEtheLD` (lines 30-128) - `GDTFComparerApp.create_widgets()` and `run_comparison()`
- Contains: Tkinter widgets (Entry, Button, Listbox, Treeview), event handlers
- Depends on: parse_gdtf() for data extraction; os module for file handling
- Used by: main() entry point
- Purpose: Extract and parse GDTF archive contents
- Location: `BEtheLD` (lines 131-182) - parse_gdtf() function
- Contains: Zip file extraction, XML parsing, attribute collection
- Depends on: zipfile, xml.etree.ElementTree, tempfile, shutil, os
- Used by: GDTFComparerApp.run_comparison()
- Purpose: Standalone Blender addon scaffold
- Location: `blender_addon/__init__.py`
- Contains: Blender addon metadata (bl_info), register/unregister stubs
- Depends on: None (not yet integrated)
- Used by: Blender addon system (not yet active)

## Data Flow

### Primary Request Path (Comparison Workflow)

### GDTF Parsing Flow (parse_gdtf)

- GDTFComparerApp maintains state: target_file, compare_files, attribute_categories, selected_attributes
- parse_gdtf() is stateless; uses temporary directory isolated from app state
- TreeView is cleared and repopulated on each comparison run

## Key Abstractions

- Purpose: Encapsulates GUI state and comparison logic
- Examples: `BEtheLD` lines 11-128
- Pattern: Object-oriented state container; not a classic MVC controller
- Manages: file lists, UI widgets, comparison execution
- Purpose: Generic GDTF archive parser; decoupled from UI
- Examples: Used in tests (`tests/test_parse_gdtf.py`), app workflow
- Pattern: Pure function for side effects (temp file cleanup happens in finally)
- Contract: Takes file path string, returns Dict[str, Any] or raises (BadZipFile, ParseError)
- Purpose: Define which attributes are displayed in comparison
- Location: `BEtheLD` lines 21-24
- Pattern: Simple configuration dict mapping category names to attribute lists
- Extensible: New categories/attributes can be added without code changes

## Entry Points

- Location: `BEtheLD` (root of repo, no extension)
- Triggers: Directly invoked as Python script (`python BEtheLD`)
- Responsibilities: 
- Location: `blender_addon/__init__.py`
- Triggers: Blender addon system on load
- Responsibilities: Currently stubbed with register()/unregister() (lines 12-17)
- Status: Skeleton only; no implementation yet

## Architectural Constraints

- **Threading:** Single-threaded event loop (Tkinter mainloop). GDTF parsing blocks UI.
- **Global state:** None enforced in modules. GDTFComparerApp instance holds all session state.
- **Circular imports:** Not present; linear dependency: BEtheLD → tkinter + builtin modules; parse_gdtf is independent.
- **GUI blocking:** Comparison runs synchronously; large GDTF files or many comparisons will freeze UI.
- **Temp file cleanup:** Guaranteed via try/finally in parse_gdtf(); survives exceptions.
- **File permissions:** Relies on OS for file read access; no error handling for permission denied.

## Anti-Patterns

### Tightly Coupled GUI and Business Logic

```python

```

### No Error Messages to User

```python

```

## Error Handling

- parse_gdtf() raises zipfile.BadZipFile and xml.etree.ElementTree.ParseError without catching
- Tests explicitly assert these exceptions (lines 37-47 in test_parse_gdtf.py)
- GDTFComparerApp.run_comparison() has validation for empty file lists but no exception handling

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
