---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
# Testing Patterns

**Analysis Date:** 2026-09-25

## Test Framework

**Runner:**

- pytest (imported in `tests/test_parse_gdtf.py` line 6)
- No `pytest.ini` or `pyproject.toml` configuration file detected — pytest uses default configuration
- No test runner script detected

**Assertion Library:**

- Python's built-in `assert` statements (e.g., `assert result["Attr1"] == "Value1"`)
- pytest's exception testing via `pytest.raises()` context manager

**Run Commands:**

```bash
pytest tests/                    # Run all tests in tests directory
pytest tests/test_parse_gdtf.py  # Run specific test file
pytest -v                        # Verbose mode (not observed in config, but standard)
pytest --tb=short               # Show brief tracebacks (standard practice)
```

## Test File Organization

**Location:**

- Tests co-located in `tests/` directory parallel to source code
- Test file at `tests/test_parse_gdtf.py`
- Main source code in `BEtheLD` (no extension) at repo root and `blender_addon/__init__.py`

**Naming:**

- Test file: `test_parse_gdtf.py` following `test_*.py` pattern
- Test functions: `test_*` naming convention (e.g., `test_parse_gdtf_success`, `test_parse_gdtf_invalid_zip`)
- Test names are descriptive, indicating both the function tested and the scenario

**Structure:**

```
tests/
└── test_parse_gdtf.py
    ├── Imports + dynamic module loading (lines 1-14)
    ├── Helper function: build_gdtf_zip (lines 17-20)
    ├── Test suite for parse_gdtf function (lines 23-47)
    │   ├── test_parse_gdtf_success
    │   ├── test_parse_gdtf_invalid_zip
    │   └── test_parse_gdtf_malformed_xml
```

## Test Structure

**Suite Organization:**

```python

# Setup: Import module dynamically (no extension)

script_path = Path(__file__).resolve().parents[1] / "BEtheLD"
loader = importlib.machinery.SourceFileLoader("gdtf_module", str(script_path))
spec = importlib.util.spec_from_loader(loader.name, loader)
gdtf_module = importlib.util.module_from_spec(spec)
loader.exec_module(gdtf_module)
parse_gdtf = gdtf_module.parse_gdtf

# Helper function for test data setup

def build_gdtf_zip(path: Path, xml_content: str) -> None:
    """Create a minimal GDTF zip containing description.xml."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("description.xml", xml_content)

# Test function: Arrange-Act-Assert pattern

def test_parse_gdtf_success(tmp_path):
    # Arrange
    xml = '<Root Attr1="Value1"><Child Attr2="Value2" /></Root>'
    gdtf_file = tmp_path / "sample.gdtf"
    build_gdtf_zip(gdtf_file, xml)
    
    # Act
    result = parse_gdtf(str(gdtf_file))
    
    # Assert
    assert result["Attr1"] == "Value1"
    assert result["Attr2"] == "Value2"
```

**Patterns:**

- **Setup:** Test data created using `tmp_path` fixture before assertions
- **Teardown:** Implicit — pytest's `tmp_path` fixture auto-cleans temporary files
- **Assertion:** Simple `assert` statements comparing expected values
- **Error assertion:** `pytest.raises()` context manager captures expected exceptions

## Mocking

**Framework:** No external mocking framework used (no `unittest.mock` imports)

**Patterns:**

- No mock objects detected in tests
- Fixtures created as temporary files (`tmp_path`)
- Helper functions (`build_gdtf_zip`) used to prepare test data

**Example:**

```python
def build_gdtf_zip(path: Path, xml_content: str) -> None:
    """Create a minimal GDTF zip containing description.xml."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("description.xml", xml_content)
```

**What to Mock:** Currently nothing is mocked; tests work with actual file I/O and zip/XML libraries

**What NOT to Mock:** 

- Actual file system operations (intentional — testing real I/O)
- XML parsing library (testing actual parsing behavior)
- Zip file handling (testing real zip extraction)

## Fixtures and Factories

**Test Data:**

- Helper function `build_gdtf_zip()` creates GDTF file archives with specified XML content
- `tmp_path` pytest fixture provides temporary directories for file operations

**Location:**

- Helper function at module level in `tests/test_parse_gdtf.py` (lines 17-20)
- pytest fixtures (e.g., `tmp_path`) injected as function parameters

## Coverage

**Requirements:** No coverage requirements detected; no `.coveragerc` or coverage configuration present

**View Coverage:** Not configured; to enable:

```bash
pytest --cov=.          # Run with coverage (requires pytest-cov)
pytest --cov-report=html  # Generate HTML coverage report
```

## Test Types

**Unit Tests:**

- Scope: Testing `parse_gdtf()` function in isolation
- Approach: Direct function calls with known inputs (GDTF file archives)
- Tests verify: successful parsing, error handling for bad zip, error handling for malformed XML

**Integration Tests:**

- Not explicitly present; tests do exercise real zip and XML libraries (integration-like)

**E2E Tests:**

- Not present in repository
- GUI testing for `GDTFComparerApp` would require testing framework not currently in use

## Common Patterns

**Async Testing:**

- Not applicable — codebase uses no async/await

**Error Testing:**

```python
def test_parse_gdtf_invalid_zip(tmp_path):
    bad_zip = tmp_path / "invalid.gdtf"
    bad_zip.write_text("not a zip")

    with pytest.raises(zipfile.BadZipFile):
        parse_gdtf(str(bad_zip))

def test_parse_gdtf_malformed_xml(tmp_path):
    xml = "<Root><Child></Root>"  # malformed XML
    gdtf_file = tmp_path / "bad_xml.gdtf"
    build_gdtf_zip(gdtf_file, xml)

    with pytest.raises(ET.ParseError):
        parse_gdtf(str(gdtf_file))
```

**Test Data Builders:**

```python
def build_gdtf_zip(path: Path, xml_content: str) -> None:
    """Create a minimal GDTF zip containing description.xml."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("description.xml", xml_content)
```

## Test Coverage Status

**Current coverage:**

- `parse_gdtf()` function: 3 test cases
  - Happy path: successful parsing
  - Error path: invalid zip file
  - Error path: malformed XML

**Untested areas:**

- `GDTFComparerApp` class (no GUI tests)
- `main()` entry point
- `blender_addon/__init__.py` (register/unregister functions)
- File selection and UI interaction methods in `GDTFComparerApp`
- `run_comparison()` method

---

*Testing analysis: 2026-09-25*
