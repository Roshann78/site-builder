#!/usr/bin/env python3
"""Tests for MathJax JS copying in build_docs.py."""

import shutil
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


class TestMathJax:
    """Verify that sb-mathjax.js is copied into docs/javascripts/."""

    def test_js_copied_and_delimiters_preserved(self, workspace):
        """sb-mathjax.js should appear in docs/javascripts/ with double-backslash delimiters."""
        notes, run_build = workspace
        (notes / "page.md").write_text("# Page\n\nSome math $x$.\n", encoding="utf-8")

        docs = run_build()

        js_file = docs / "javascripts" / "sb-mathjax.js"
        assert js_file.exists(), "docs/javascripts/sb-mathjax.js was not created"

        content = js_file.read_text(encoding="utf-8")

        # Confirm the double-backslash delimiters are preserved exactly
        assert r'inlineMath: [["\\(", "\\)"]]' in content
        assert r'displayMath: [["\\[", "\\]"]]' in content
        assert r"\\(" in content
        assert r"\\)" in content
        assert r"\\[" in content
        assert r"\\]" in content
        assert 'ignoreHtmlClass: ".*|"' in content
        assert 'processHtmlClass: "arithmatex"' in content
        assert "MathJax.typesetPromise()" in content

    def test_notes_not_modified(self, workspace):
        """Original notes files must not be altered by the build."""
        notes, run_build = workspace
        original = "# My Math Page\n\n$$E = mc^2$$\n\nInline $x^2$ and plain $5.\n"
        (notes / "page.md").write_text(original, encoding="utf-8")

        run_build()

        assert (notes / "page.md").read_text(encoding="utf-8") == original

    def test_user_file_not_overwritten(self, workspace):
        """Never overwrite an existing user file in docs/javascripts/sb-mathjax.js."""
        notes, run_build = workspace
        user_js_dir = notes / "javascripts"
        user_js_dir.mkdir(parents=True)
        user_js_content = "// Custom user MathJax config\nconsole.log('user custom');\n"
        (user_js_dir / "sb-mathjax.js").write_text(user_js_content, encoding="utf-8")

        docs = run_build()

        copied = docs / "javascripts" / "sb-mathjax.js"
        assert copied.exists()
        assert copied.read_text(encoding="utf-8") == user_js_content

    def test_missing_source_warns_and_continues(self, workspace, monkeypatch, capsys):
        """If assets/sb-mathjax.js is missing, print a warning and continue."""
        notes, run_build = workspace
        (notes / "page.md").write_text("# Page\n", encoding="utf-8")

        # Temporarily mock non-existent source file
        fake_path = Path("non_existent_sb_mathjax.js")
        monkeypatch.setattr(Path, "is_file", lambda self: False if self.name == "sb-mathjax.js" else Path.is_file.__wrapped__(self) if hasattr(Path.is_file, "__wrapped__") else False)

        docs = run_build()
        captured = capsys.readouterr()
        assert "[WARN] MathJax JS not found:" in captured.out
        assert not (docs / "javascripts" / "sb-mathjax.js").exists()

    def test_mathjax_mkdocs_build_rendering(self, workspace):
        """Real mkdocs build verifying arithmatex rendering, plain text, and script tags."""
        import subprocess

        notes, run_build = workspace
        fixture_content = (
            "# Math Fixture\n\n"
            "$$\n"
            "\\frac{a}{b} = c\n"
            "$$\n\n"
            "Here is an inline equation: $x^2$.\n\n"
            "A plain item costs $5 in text.\n\n"
            "```text\n"
            "$x$\n"
            "```\n"
        )
        (notes / "fixture.md").write_text(fixture_content, encoding="utf-8")

        docs = run_build()
        out = docs.parent

        res = subprocess.run(
            [sys.executable, "-m", "mkdocs", "build"],
            cwd=str(out),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"mkdocs build failed: {res.stderr}\n{res.stdout}"

        page_html = (out / "site" / "fixture" / "index.html").read_text(encoding="utf-8")

        # Confirm elements with class "arithmatex" for both math cases:
        # Block math:
        assert '<div class="arithmatex">' in page_html
        assert r"\[" in page_html and r"\frac{a}{b} = c" in page_html
        # Inline math:
        assert '<span class="arithmatex">' in page_html
        assert r"\(" in page_html and "x^2" in page_html

        # Confirm exactly 2 arithmatex occurrences (one div for block, one span for inline)
        assert page_html.count('class="arithmatex"') == 2

        # Confirm "$5" text and the code block content are NOT turned into math
        assert "costs $5" in page_html
        assert "$x$" in page_html
        assert '<span class="arithmatex">$5</span>' not in page_html
        assert '<span class="arithmatex">$x$</span>' not in page_html
        assert '<span class="arithmatex">x</span>' not in page_html

        # Confirm the built page links both scripts
        assert 'src="../javascripts/sb-mathjax.js"' in page_html or 'src="javascripts/sb-mathjax.js"' in page_html
        assert "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" in page_html

