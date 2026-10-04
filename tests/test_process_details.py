import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from tools.build_docs import process_details

@pytest.fixture()
def docs_dir(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    return d

def test_process_details_basic(docs_dir):
    md = docs_dir / "test.md"
    md.write_text("<details>\n<summary>Test</summary>\nContent\n</details>", encoding="utf-8")
    
    process_details(docs_dir)
    
    result = md.read_text(encoding="utf-8")
    assert '<details markdown="1">' in result
    assert '<summary>Test</summary>' in result

def test_process_details_already_has_markdown(docs_dir):
    md = docs_dir / "test.md"
    md.write_text("<details markdown=\"1\">\n<summary>Test</summary>\n", encoding="utf-8")
    
    process_details(docs_dir)
    
    result = md.read_text(encoding="utf-8")
    assert "<details markdown=\"1\">" in result

def test_process_details_inside_fence(docs_dir):
    md = docs_dir / "test.md"
    md.write_text("```html\n<details>\n<summary>Code</summary>\n```", encoding="utf-8")
    
    process_details(docs_dir)
    
    result = md.read_text(encoding="utf-8")
    assert "```html\n<details>\n" in result

def test_process_details_open(docs_dir):
    md = docs_dir / "test.md"
    md.write_text("<details open>\n<summary>Test</summary>\n", encoding="utf-8")
    
    process_details(docs_dir)
    
    result = md.read_text(encoding="utf-8")
    assert '<details markdown="1" open>' in result
