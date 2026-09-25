---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
# Technology Stack

**Analysis Date:** 2026-09-25

## Languages

**Primary:**

- Python 3.7+ - Core application logic, GDTF parsing, GUI development

**Secondary:**

- Python (Blender API subset) - Blender addon module in `blender_addon/`

## Runtime

**Environment:**

- Python 3.7 or higher
- No external runtime required for core application

**Package Manager:**

- pip (implicit - no lockfile or requirements.txt present)
- Blender's embedded Python for addon execution

## Frameworks

**Core:**

- tkinter (Python standard library) - GUI framework for GDTF Comparer application, used in `BEtheLD`
  - Widgets: `tk.Label`, `tk.Entry`, `tk.Button`, `tk.Listbox`, `ttk.Treeview`
  - Dialog functions: `filedialog.askopenfilename`, `filedialog.askopenfilenames`

**Testing:**

- pytest - Test runner for `tests/test_parse_gdtf.py`

**Blender Integration:**

- Blender 2.80+ - Required for addon execution
  - Addon version: 0.1.0
  - No external API calls; operates within Blender's Python environment

## Key Dependencies

**Standard Library (No External Packages Required):**

- `zipfile` - Handles GDTF file extraction (ZIP archive format)
- `xml.etree.ElementTree` - XML parsing for `description.xml` extraction
- `os` - File system operations
- `shutil` - Directory operations (copy, remove)
- `tempfile` - Temporary directory creation for extraction
- `tkinter` - GUI components (part of Python standard library)
- `typing` - Type hints for function signatures

**Testing (Development Only):**

- `pytest` - Test framework for `tests/test_parse_gdtf.py`
- `importlib` - Dynamic module loading for test fixture (standard library)

## Configuration

**Environment:**

- No environment variables required
- No configuration files detected (`.env`, `.ini`, `.toml`, `.yaml`)

**Build:**

- No build configuration detected (no `setup.py`, `pyproject.toml`, `Makefile`, or build scripts)
- Direct Python execution via `python BEtheLD` or Blender addon loader

## Platform Requirements

**Development:**

- Python 3.7+ interpreter
- pytest (for running tests)
- Blender 2.80+ (for addon development/testing)

**Production:**

- Python 3.7+ interpreter
- tkinter (included with Python on most distributions)
- For addon: Blender 2.80+ application

**Operating Systems:**

- Linux, macOS, Windows (all support Python 3.7+ and tkinter)

## File Format Support

**Primary Formats:**

- GDTF (`.gdtf` files) - ZIP archives containing `description.xml`
- MVR (referenced in `blender_addon/` but not yet implemented)

---

*Stack analysis: 2026-09-25*
