import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import importlib.machinery
import importlib.util
import pytest

# Import parse_gdtf from the BEtheLD script (which lacks a .py extension)
script_path = Path(__file__).resolve().parents[1] / "BEtheLD"
loader = importlib.machinery.SourceFileLoader("gdtf_module", str(script_path))
spec = importlib.util.spec_from_loader(loader.name, loader)
gdtf_module = importlib.util.module_from_spec(spec)
loader.exec_module(gdtf_module)
parse_gdtf = gdtf_module.parse_gdtf


def build_gdtf_zip(path: Path, xml_content: str) -> None:
    """Create a minimal GDTF zip containing description.xml."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("description.xml", xml_content)


def test_parse_gdtf_success(tmp_path):
    xml = '<Root Attr1="Value1"><Child Attr2="Value2" /></Root>'
    gdtf_file = tmp_path / "sample.gdtf"
    build_gdtf_zip(gdtf_file, xml)

    result = parse_gdtf(str(gdtf_file))
    assert result["Attr1"] == "Value1"
    assert result["Attr2"] == "Value2"


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
