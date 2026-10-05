#!/usr/bin/env python3
"""Tests for sidebar CSS copying in build_docs.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from tools.build_docs import main as build_main


@pytest.fixture()
def workspace(tmp_path):
    """Yield (notes_dir, out_dir) and a helper to run the build."""
    notes = tmp_path / "notes"
    notes.mkdir()
    out = tmp_path / "out"

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


class TestSidebarCSS:
    """Verify that sb-extra.css is copied into docs/stylesheets/."""

    def test_css_copied(self, workspace):
        """sb-extra.css should appear in docs/stylesheets/ after build."""
        notes, run_build = workspace
        (notes / "page.md").write_text("# Page\n", encoding="utf-8")

        docs = run_build()

        css = docs / "stylesheets" / "sb-extra.css"
        assert css.exists(), "docs/stylesheets/sb-extra.css was not created"

        # Verify the file has real content (not empty)
        content = css.read_text(encoding="utf-8")
        assert "Sidebar polish" in content

    def test_notes_not_modified(self, workspace):
        """Original notes files must not be altered by the build."""
        notes, run_build = workspace
        original = "# My Page\n\nSome content.\n"
        (notes / "page.md").write_text(original, encoding="utf-8")

        run_build()

        # The source note must be untouched
        assert (notes / "page.md").read_text(encoding="utf-8") == original
