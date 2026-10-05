#!/usr/bin/env python3
"""Tests for front-matter title injection in build_docs.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from tools.build_docs import inject_titles, _title_from_filename


@pytest.fixture()
def docs_dir(tmp_path):
    """Return a temporary docs directory for inject_titles."""
    d = tmp_path / "docs"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Unit tests for _title_from_filename
# ---------------------------------------------------------------------------

class TestTitleFromFilename:
    # --- no-space names: underscores/hyphens become spaces ----------------
    def test_underscores_replaced(self):
        assert _title_from_filename("My_Notes.md") == "My Notes"

    def test_hyphens_replaced(self):
        assert _title_from_filename("hello-world.md") == "hello world"

    def test_number_prefix_kept_underscore(self):
        """Leading number prefixes are preserved."""
        assert _title_from_filename("01_Level_1_Core_OOP.md") == "01 Level 1 Core OOP"

    def test_event_driven_notes(self):
        assert _title_from_filename("event-driven-notes.md") == "event driven notes"

    def test_preserves_capitalisation(self):
        assert _title_from_filename("MyGreatPage.md") == "MyGreatPage"

    # --- names that already contain a space: used verbatim ----------------
    def test_space_name_intro(self):
        assert _title_from_filename(
            "01 - Introduction, Servers, Deployment & Metrics.md"
        ) == "01 - Introduction, Servers, Deployment & Metrics"

    def test_space_name_monolithic(self):
        assert _title_from_filename(
            "04 - Monolithic vs Microservices Architecture.md"
        ) == "04 - Monolithic vs Microservices Architecture"

    def test_space_name_keeps_hyphens(self):
        """Hyphens inside a name that contains spaces are preserved."""
        assert _title_from_filename(
            "02 - Scaling & Back-of-the-Envelope Estimation.md"
        ) == "02 - Scaling & Back-of-the-Envelope Estimation"


# ---------------------------------------------------------------------------
# Integration tests for inject_titles
# ---------------------------------------------------------------------------

class TestNoFrontMatter:
    """A .md file with no front matter at all gets a new block prepended."""

    def test_title_inserted(self, docs_dir):
        md = docs_dir / "My_Notes.md"
        md.write_text("# Hello\n\nSome content.\n", encoding="utf-8")

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert result.startswith("---\ntitle: \"My Notes\"\n---\n")
        assert "# Hello" in result
        assert "Some content." in result

    def test_number_prefix_kept(self, docs_dir):
        """Number prefix is preserved in the generated title."""
        md = docs_dir / "01_Level_1_Core_OOP.md"
        md.write_text("# OOP Basics\n", encoding="utf-8")

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert result.startswith("---\ntitle: \"01 Level 1 Core OOP\"\n---\n")

    def test_root_index_skipped(self, docs_dir):
        """Root index.md must never be touched."""
        original = "# Home\n"
        md = docs_dir / "index.md"
        md.write_text(original, encoding="utf-8")

        inject_titles(docs_dir)

        assert md.read_text(encoding="utf-8") == original

    def test_original_notes_untouched(self, tmp_path):
        """Source notes should never be modified – only docs copies."""
        notes = tmp_path / "notes"
        notes.mkdir()
        original = "# Original\n"
        src = notes / "page.md"
        src.write_text(original, encoding="utf-8")

        docs = tmp_path / "docs"
        docs.mkdir()
        dst = docs / "page.md"
        dst.write_text(original, encoding="utf-8")

        inject_titles(docs)

        # docs copy should be modified
        assert dst.read_text(encoding="utf-8").startswith("---\ntitle:")
        # source should be untouched
        assert src.read_text(encoding="utf-8") == original


class TestExistingFrontMatterWithoutTitle:
    """Front matter exists but has no title key → title is added."""

    def test_title_added(self, docs_dir):
        md = docs_dir / "Design_Patterns.md"
        md.write_text(
            "---\ntags: [python, design]\n---\n# Design Patterns\n\nBody.\n",
            encoding="utf-8",
        )

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        # Must contain both the original key and the new title
        assert "tags: [python, design]" in result
        assert 'title: "Design Patterns"' in result
        # Title should be inside the front-matter block
        lines = result.split("\n")
        # First line is ---, last of front matter is ---
        assert lines[0] == "---"
        fm_end = lines.index("---", 1)
        fm_block = "\n".join(lines[1:fm_end])
        assert 'title: "Design Patterns"' in fm_block

    def test_multiple_keys_preserved(self, docs_dir):
        md = docs_dir / "Arch.md"
        md.write_text(
            "---\ndate: 2024-01-01\nauthor: Alice\n---\n# Arch\n",
            encoding="utf-8",
        )

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert "date: 2024-01-01" in result
        assert "author: Alice" in result
        assert 'title: "Arch"' in result


class TestExistingTitle:
    """Front matter already contains a title → file is left untouched."""

    def test_not_modified(self, docs_dir):
        original = "---\ntitle: Custom Title\n---\n# Heading\n\nBody.\n"
        md = docs_dir / "My_Page.md"
        md.write_text(original, encoding="utf-8")

        inject_titles(docs_dir)

        assert md.read_text(encoding="utf-8") == original

    def test_title_with_other_keys(self, docs_dir):
        original = (
            "---\ntags: [web]\ntitle: Already Set\ndate: 2024-06-01\n---\n"
            "# Content\n"
        )
        md = docs_dir / "Web_Dev.md"
        md.write_text(original, encoding="utf-8")

        inject_titles(docs_dir)

        assert md.read_text(encoding="utf-8") == original

    def test_existing_front_matter_title_respected(self, docs_dir):
        """Files with an explicit title in front matter must never be overwritten."""
        original = '---\ntitle: "My Custom Title"\n---\n# Whatever\n'
        md = docs_dir / "01_Level_1_Core_OOP.md"
        md.write_text(original, encoding="utf-8")

        inject_titles(docs_dir)

        assert md.read_text(encoding="utf-8") == original


class TestSubfolderIndex:
    """Non-root index.md derives title from parent folder name."""

    def test_no_front_matter(self, docs_dir):
        sub = docs_dir / "PlacementNotes"
        sub.mkdir()
        md = sub / "index.md"
        md.write_text("# Welcome\n\nSome content.\n", encoding="utf-8")

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert result.startswith('---\ntitle: "PlacementNotes"\n---\n')
        assert "# Welcome" in result

    def test_existing_title_untouched(self, docs_dir):
        sub = docs_dir / "PlacementNotes"
        sub.mkdir()
        original = "---\ntitle: My Custom Title\n---\n# Welcome\n"
        md = sub / "index.md"
        md.write_text(original, encoding="utf-8")

        inject_titles(docs_dir)

        assert md.read_text(encoding="utf-8") == original

    def test_number_prefix_kept_in_folder(self, docs_dir):
        """Folder name number prefix is preserved in the derived title."""
        sub = docs_dir / "01-Getting_Started"
        sub.mkdir()
        md = sub / "index.md"
        md.write_text("# Intro\n", encoding="utf-8")

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert result.startswith('---\ntitle: "01 Getting Started"\n---\n')


class TestTitleCharacters:
    """Test that special characters in titles are safely quoted."""

    def test_special_characters(self, docs_dir, monkeypatch):
        import tools.build_docs
        monkeypatch.setattr(tools.build_docs, "_title_from_filename", lambda x: "Symbols & : # [ ] \"quotes\"")
        
        md = docs_dir / "Symbols.md"
        md.write_text("# Hello\n", encoding="utf-8")

        inject_titles(docs_dir)

        result = md.read_text(encoding="utf-8")
        assert "title: \"Symbols & : # [ ] \\\"quotes\\\"\"" in result
