---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
# Codebase Structure

**Analysis Date:** 2026-09-25

## Directory Layout

```
GDTFComparer/
├── BEtheLD                      # Main comparison app (no .py extension)
├── README.md                    # Project overview
├── LICENSE                      # License text
│
├── blender_addon/               # Blender addon scaffold
│   ├── __init__.py             # Addon entry point & metadata
│   └── README.md               # Addon documentation
│
├── tests/                       # Test suite
│   └── test_parse_gdtf.py      # Tests for GDTF parser
│
└── .planning/
    └── codebase/               # Architecture & structure docs
        ├── ARCHITECTURE.md
        └── STRUCTURE.md
```

## Directory Purposes

**Project Root:**

- Purpose: Top-level project files and entry points
- Contains: Main application (BEtheLD), README, LICENSE
- Key files: `BEtheLD` (main app), `README.md` (overview)

**`blender_addon/`:**

- Purpose: Blender addon structure for future MVR/GDTF import support
- Contains: Addon metadata, registration stubs, addon documentation
- Key files: `blender_addon/__init__.py` (bl_info, register/unregister)
- Status: Skeleton only; no operational code yet

**`tests/`:**

- Purpose: Pytest test suite for GDTF parsing functionality
- Contains: Test cases and fixtures
- Key files: `tests/test_parse_gdtf.py` (parse_gdtf() tests)

**`.planning/codebase/`:**

- Purpose: Architecture and structure documentation (this directory)
- Contains: ARCHITECTURE.md, STRUCTURE.md, TESTING.md (future), etc.

## Key File Locations

**Entry Points:**

- `BEtheLD`: Main executable script (no `.py` extension) - line 185-192
  - Creates Tkinter root window
  - Instantiates GDTFComparerApp
  - Starts event loop

**Core Logic:**

- `BEtheLD` (entire file):
  - `GDTFComparerApp` class: lines 11-128 (GUI, state, comparison workflow)
  - `parse_gdtf()` function: lines 131-182 (GDTF archive & XML parsing)

**Configuration:**

- `BEtheLD` lines 21-24: `attribute_categories` dict
  - Defines which GDTF attributes to display in comparison
  - Extensible; no external config files

**Testing:**

- `tests/test_parse_gdtf.py`:
  - Import mechanism: lines 1-14 (special loader for no-extension BEtheLD)
  - Helper: `build_gdtf_zip()` lines 17-20
  - Tests: lines 23-47 (3 test cases)

**Documentation:**

- `README.md`: Project overview and status
- `blender_addon/README.md`: Blender addon scope and roadmap

## Naming Conventions

**Files:**

- `BEtheLD` - No `.py` extension; intended as executable script (artist's initials/name convention)
- Test files: `test_*.py` - Pytest discovery pattern
- Addon: `blender_addon/` - Directory-based addon structure (Blender convention)

**Directories:**

- Lowercase with underscores: `blender_addon`, `tests`, `.planning`
- Follows Python package conventions

**Functions:**

- Snake_case: `parse_gdtf()`, `create_widgets()`, `select_target_file()`, `run_comparison()`
- Private methods: None marked with `_` prefix; all are class methods or free functions

**Variables:**

- Snake_case: `target_file`, `compare_files`, `attribute_categories`, `description_path`
- Class attributes: Prefixed with `self.` in GDTFComparerApp

**Types:**

- Dict[str, Any] for parsed GDTF attributes
- List[str] for file paths
- No type hints in code; documented in docstrings (see parse_gdtf)

## Where to Add New Code

**New Feature (e.g., export comparison to CSV):**

- Primary code: Add method to `GDTFComparerApp` class in `BEtheLD` or extract into separate module
- Tests: Add new test function to `tests/test_parse_gdtf.py` or create new `tests/test_*.py`
- Example: `def export_to_csv(self, filepath: str) -> None:` in GDTFComparerApp

**New Parsing Functionality (e.g., parse MVRDL or other formats):**

- Implementation: Create new function in `BEtheLD` or extract parsing logic to separate module (e.g., `gdtf_parser.py`)
- Pattern: Follow parse_gdtf() signature - takes file path, returns Dict[str, Any]
- Tests: Add test function to `tests/test_parse_gdtf.py` following existing pattern

**Blender Addon Implementation (future):**

- Addon operators: `blender_addon/operators.py` (new file)
- Import logic: `blender_addon/importer.py` (new file)
- Shared parsing: Can reuse parse_gdtf() from BEtheLD via import or refactor to standalone module
- Register operators in `blender_addon/__init__.py` register() function

**Utilities/Helpers:**

- Shared parsing logic: Move parse_gdtf() to `gdtf_parser.py` (new module in root)
- UI components: Create `ui_components.py` or `widgets.py` if expanding beyond single class
- Example: Extract attribute_categories to `config.py` or `constants.py`

## Special Directories

**`.planning/`:**

- Purpose: Project planning and documentation
- Generated: Yes (created by gsd-map-codebase or manual)
- Committed: Yes (version controlled)
- Contains: ARCHITECTURE.md, STRUCTURE.md, TESTING.md, CONCERNS.md (future phases)

**`.claude/`:**

- Purpose: Claude Code project configuration and agent definitions
- Generated: Yes (by Claude Code harness)
- Committed: Yes (project-specific settings)
- Contains: agents/, commands/, settings.local.json, etc.

**`.git/`:**

- Purpose: Git repository metadata
- Generated: Yes (by git init)
- Committed: No (git internals)

## File Extension Rationale

**BEtheLD (no .py):**

- Intentionally named without extension to be directly executable as script
- Python detected via shebang or explicit python invocation: `python BEtheLD`
- Tests use importlib to load: `SourceFileLoader("gdtf_module", str(script_path))`
- Rationale: Honors original artist/developer naming; works on Unix-like systems with shebang

## Module Organization

**Current (Monolithic):**

- `BEtheLD` contains both UI (GDTFComparerApp) and parsing (parse_gdtf)
- Tight coupling; all logic in one file (~190 lines)

**Recommended Future Organization:**

```
GDTFComparer/
├── gdtf_comparer/              # Package (future refactor)
│   ├── __init__.py
│   ├── parser.py               # parse_gdtf() and GDTF-specific logic
│   ├── app.py                  # GDTFComparerApp GUI class
│   ├── config.py               # Constants (attribute_categories)
│   └── utils.py                # Helper functions
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_app.py
│   └── fixtures.py
│
└── BEtheLD                      # Wrapper script (thin entry point)
    # imports and calls main()
```

This would allow `from gdtf_comparer.parser import parse_gdtf` in Blender addon.

---

*Structure analysis: 2026-09-25*
