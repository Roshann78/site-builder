#!/usr/bin/env python3
"""Tests for README → index.md promotion in build_docs.py."""

import os
import shutil
import sys
import textwrap
from pathlib import Path

# Ensure the tools package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from tools.build_docs import main as build_main


@pytest.fixture()
def workspace(tmp_path):
    """Yield (notes_dir, out_dir) and a helper to run the build."""
    notes = tmp_path / "notes"
    notes.mkdir()
    out = tmp_path / "out"

    # The build copies mkdocs.yml from repo root – place a stub so it
    # doesn't fail.
    repo_root = Path(__file__).resolve().parent.parent
    mkdocs_src = repo_root / "mkdocs.yml"
    # We'll monkey-patch sys.argv to call main()

    def run_build():
        sys.argv = [
            "build_docs.py",
            "--notes", str(notes),
            "--out",   str(out),
            "--domain", "example.com",
        ]
        build_main()
        return out / "docs"

    yield notes, run_build


class TestReadmeMd:
    """Fixture 1: root contains ``Readme.md`` (mixed case)."""

    def test_promoted_to_index(self, workspace):
        notes, run_build = workspace
        readme_content = "# Hello from Readme.md\n\nBody text.\n"
        (notes / "Readme.md").write_text(readme_content, encoding="utf-8")

        docs = run_build()

        # index.md should exist with the readme's content
        index = docs / "index.md"
        assert index.exists(), "docs/index.md was not created"
        assert index.read_text(encoding="utf-8") == readme_content

        # The original Readme.md should NOT be present in docs/
        assert not (docs / "Readme.md").exists(), \
            "Readme.md was copied into docs/ (duplicate)"


class TestREADMEMd:
    """Fixture 2: root contains ``README.md`` (all-caps)."""

    def test_promoted_to_index(self, workspace):
        notes, run_build = workspace
        readme_content = "# Hello from README.md\n\nAll caps readme.\n"
        (notes / "README.md").write_text(readme_content, encoding="utf-8")

        docs = run_build()

        index = docs / "index.md"
        assert index.exists(), "docs/index.md was not created"
        assert index.read_text(encoding="utf-8") == readme_content

        # The original README.md should NOT be present in docs/
        assert not (docs / "README.md").exists(), \
            "README.md was copied into docs/ (duplicate)"


class TestNoReadme:
    """Fixture 3: root has no readme at all – fallback placeholder."""

    def test_fallback_placeholder(self, workspace, monkeypatch):
        notes, run_build = workspace
        # Put a dummy file so the folder isn't empty
        (notes / "notes.md").write_text("# Notes\n", encoding="utf-8")
        monkeypatch.setenv("SITE_NAME", "Test Site")

        docs = run_build()

        index = docs / "index.md"
        assert index.exists(), "docs/index.md was not created"
        content = index.read_text(encoding="utf-8")
        assert "# Test Site" in content
        assert "Welcome to **Test Site**" in content

        # notes.md should still be there (not excluded)
        assert (docs / "notes.md").exists()
