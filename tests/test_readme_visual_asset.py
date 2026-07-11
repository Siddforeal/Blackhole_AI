from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "docs/assets/blackhole-demo-case-pack.svg"
README = ROOT / "README.md"


def test_demo_visual_asset_is_valid_svg() -> None:
    assert ASSET.is_file()
    assert ASSET.stat().st_size > 0
    root = ET.parse(ASSET).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 1200 600"
    assert "Blackhole Demo Case Pack" in ASSET.read_text()


def test_readme_references_demo_visual_asset() -> None:
    readme = README.read_text()
    assert "docs/assets/blackhole-demo-case-pack.svg" in readme
    assert "![Blackhole Demo Case Pack workflow]" in readme
