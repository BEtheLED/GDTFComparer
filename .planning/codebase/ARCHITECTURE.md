---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
<!-- refreshed: 2026-09-25 -->

# Architecture

**Analysis Date:** 2026-09-25

## System Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                   Tkinter GUI Layer                          │
│            GDTFComparerApp (BEtheLD)                          │
│  `BEtheLD` - File selection, UI widgets, comparison display  │
└─────────────────┬────────────────────────┬──────────────────┘
                  │                        │
        ┌─────────▼─────────┐    ┌────────▼──────────┐
        │  File Selection   │    │  Data Display     │
        │  UI Components    │    │  TreeView Output  │
        └─────────┬─────────┘    └───────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────┐
│                   GDTF Parsing Layer                         │
│                  parse_gdtf()                                │
│  `BEtheLD` - Archive extraction & XML parsing                │
└─────────────────┬────────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  Zip Handler     │  │  XML Parser      │
│  zipfile module  │  │  ElementTree API │
│  tempfile mgmt   │  │  Attribute ext.  │
└──────────────────┘  └──────────────────┘
        │                    │
        └─────────┬──────────┘
                  ▼
┌──────────────────────────────────────────────────────────────┐
│            Output: Flat Attribute Dictionary                 │
│         Dict[str, Any] - All extracted attributes            │
└──────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| GDTFComparerApp | GUI initialization, widget creation, event handling | `BEtheLD` (lines 11-128) |
| parse_gdtf() | Archive extraction, XML parsing, attribute extraction | `BEtheLD` (lines 131-182) |
| Blender Addon Skeleton | Addon registration and structure | `blender_addon/__init__.py` |
| Tests | Validation of parse_gdtf() behavior | `tests/test_parse_gdtf.py` |

## Pattern Overview

**Overall:** Two-layer application with a Tkinter-based GUI frontend and a standalone parsing utility backend.

**Key Characteristics:**

- Monolithic design with GUI tightly coupled to business logic
- Single-entry-point CLI application (BEtheLD script)
- Functional parsing module (parse_gdtf) that can be imported independently
- Separate Blender addon structure for future extension
- No explicit MVC pattern; UI logic and data processing mixed in GDTFComparerApp

## Layers

**Presentation Layer:**

- Purpose: Display file selection UI and comparison results
- Location: `BEtheLD` (lines 30-128) - `GDTFComparerApp.create_widgets()` and `run_comparison()`
- Contains: Tkinter widgets (Entry, Button, Listbox, Treeview), event handlers
- Depends on: parse_gdtf() for data extraction; os module for file handling
- Used by: main() entry point

**Parsing & Extraction Layer:**

- Purpose: Extract and parse GDTF archive contents
- Location: `BEtheLD` (lines 131-182) - parse_gdtf() function
- Contains: Zip file extraction, XML parsing, attribute collection
- Depends on: zipfile, xml.etree.ElementTree, tempfile, shutil, os
- Used by: GDTFComparerApp.run_comparison()

**Infrastructure/Setup Layer:**

- Purpose: Standalone Blender addon scaffold
- Location: `blender_addon/__init__.py`
- Contains: Blender addon metadata (bl_info), register/unregister stubs
- Depends on: None (not yet integrated)
- Used by: Blender addon system (not yet active)

## Data Flow

### Primary Request Path (Comparison Workflow)

1. User launches application (`BEtheLD` main, line 185-192)
   - Creates Tkinter root window
   - Instantiates GDTFComparerApp

2. User selects target GDTF file (lines 74-80)
   - filedialog.askopenfilename() → select_target_file()
   - File path stored in self.target_file

3. User adds comparison files (lines 82-88)
   - filedialog.askopenfilenames() → select_compare_files()
   - File paths appended to self.compare_files list

4. User clicks "Run Comparison" (lines 97-128)
   - run_comparison() is invoked
   - Validation: ensure target_file and compare_files are set

5. Parse target and comparison files (lines 111-112)
   - parse_gdtf(self.target_file) → target_data (Dict[str, Any])
   - parse_gdtf() for each file in self.compare_files → list of dicts

6. Render results in TreeView (lines 114-128)
   - Construct columns from file names
   - Iterate attribute_categories, build rows from parsed data
   - Insert rows into ttk.Treeview

### GDTF Parsing Flow (parse_gdtf)

1. Create temporary directory (line 142)
   - tempfile.mkdtemp() for isolated extraction

2. Copy and extract GDTF zip (lines 145-152)
   - shutil.copyfile() - copy to temp location
   - zipfile.ZipFile.extractall() - extract archive
   - Catch BadZipFile, propagate to caller

3. Locate description.xml (lines 154-162)
   - os.walk() through extracted directory
   - Case-insensitive search for "description.xml"

4. Parse XML and extract attributes (lines 167-178)
   - ET.parse() - load XML document
   - root.iter() - walk all elements
   - Collect all element.attrib into flat dict

5. Cleanup and return (lines 181-182)
   - shutil.rmtree() - clean temporary directory (in finally block)
   - Return parsed_data dict

**State Management:**

- GDTFComparerApp maintains state: target_file, compare_files, attribute_categories, selected_attributes
- parse_gdtf() is stateless; uses temporary directory isolated from app state
- TreeView is cleared and repopulated on each comparison run

## Key Abstractions

**GDTFComparerApp (class):**

- Purpose: Encapsulates GUI state and comparison logic
- Examples: `BEtheLD` lines 11-128
- Pattern: Object-oriented state container; not a classic MVC controller
- Manages: file lists, UI widgets, comparison execution

**parse_gdtf (function):**

- Purpose: Generic GDTF archive parser; decoupled from UI
- Examples: Used in tests (`tests/test_parse_gdtf.py`), app workflow
- Pattern: Pure function for side effects (temp file cleanup happens in finally)
- Contract: Takes file path string, returns Dict[str, Any] or raises (BadZipFile, ParseError)

**attribute_categories (dict):**

- Purpose: Define which attributes are displayed in comparison
- Location: `BEtheLD` lines 21-24
- Pattern: Simple configuration dict mapping category names to attribute lists
- Extensible: New categories/attributes can be added without code changes

## Entry Points

**BEtheLD Script:**

- Location: `BEtheLD` (root of repo, no extension)
- Triggers: Directly invoked as Python script (`python BEtheLD`)
- Responsibilities: 
  - Creates Tkinter root window (line 186)
  - Instantiates GDTFComparerApp (line 187)
  - Starts event loop (line 188)

**Blender Addon (future):**

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

**What happens:** GDTFComparerApp.run_comparison() directly calls parse_gdtf() and manipulates TreeView; no separation between parsing and presentation.

**Why it's wrong:** Changes to GDTF parsing require modifying GUI code. UI cannot be tested without Tkinter. Makes the parser harder to reuse.

**Do this instead:** Extract comparison logic into a separate Comparator class or service that takes file paths and returns structured comparison results. GDTFComparerApp becomes a thin view layer that calls this service.

```python

# Better pattern:

class GDTFComparator:
    def compare(self, target_file: str, compare_files: list) -> ComparisonResult:
        target = parse_gdtf(target_file)
        comparisons = [parse_gdtf(f) for f in compare_files]
        return ComparisonResult(target, comparisons)

class GDTFComparerApp:
    def __init__(self, master, comparator: GDTFComparator):
        self.comparator = comparator  # Inject dependency
        # ... UI only
```

### No Error Messages to User

**What happens:** messagebox import on line 100 is referenced but never imported; if bad zip or malformed XML occurs during comparison, the app crashes without user feedback.

**Why it's wrong:** Parsing errors (BadZipFile, ParseError) propagate uncaught. Users have no context for failures.

**Do this instead:** Wrap parse_gdtf() calls in try/except in run_comparison(); display user-friendly messagebox errors.

```python
from tkinter import messagebox

def run_comparison(self):
    try:
        target_data = parse_gdtf(self.target_file)
    except zipfile.BadZipFile:
        messagebox.showerror("Error", "Target file is not a valid GDTF")
        return
```

## Error Handling

**Strategy:** Exceptions propagate to caller for explicit handling.

**Patterns:**

- parse_gdtf() raises zipfile.BadZipFile and xml.etree.ElementTree.ParseError without catching
- Tests explicitly assert these exceptions (lines 37-47 in test_parse_gdtf.py)
- GDTFComparerApp.run_comparison() has validation for empty file lists but no exception handling

## Cross-Cutting Concerns

**Logging:** None. No logging framework present. Failures are silent or raise exceptions.

**Validation:** Minimal. Checks for non-empty target_file and compare_files before comparison. No schema validation on GDTF or XML.

**Authentication:** Not applicable. Standalone desktop app; no auth layer.

---

*Architecture analysis: 2026-09-25*
