from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_schema_files_exist_and_parse() -> None:
    schema_paths = [
        ROOT / "schemas" / "config_v1.schema.json",
        ROOT / "schemas" / "flash_report_v1.schema.json",
        ROOT / "schemas" / "test_report_v1.schema.json",
    ]
    for path in schema_paths:
        assert path.exists(), f"Missing schema file: {path}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"].startswith("https://json-schema.org/")
        assert "required" in payload


@pytest.mark.unit
def test_compatibility_matrix_scaffold_shape() -> None:
    matrix_path = ROOT / "fixtures" / "compatibility" / "matrix.v1.json"
    payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "compat_matrix_v1"
    assert isinstance(payload["entries"], list)


@pytest.mark.unit
def test_hil_fixture_readme_exists() -> None:
    readme = ROOT / "fixtures" / "hil" / "runs" / "README.md"
    assert readme.exists()
    text = readme.read_text(encoding="utf-8")
    assert "manifest.json" in text
