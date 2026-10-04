#!/usr/bin/env python3
"""Prepare a docs folder from a notes directory for MkDocs."""

import argparse
import os
import re
import shutil
import textwrap
from pathlib import Path

# Directories / hidden-file patterns to skip when copying
SKIP_DIRS = {".git", ".github", "node_modules", "site", "docs"}
CODE_EXTENSIONS = {".cpp", ".c", ".h", ".hpp", ".py", ".java", ".js", ".go"}
LANG_MAP = {
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".go": "go",
}


def _is_hidden(name: str) -> bool:
    """Return True for dot-prefixed names (hidden files/folders)."""
    return name.startswith(".")


def _should_skip(name: str) -> bool:
    return _is_hidden(name) or name in SKIP_DIRS


def copy_notes(src: Path, dst: Path) -> None:
    """Recursively copy *src* → *dst*, skipping excluded entries."""
    for entry in sorted(src.iterdir()):
        if _should_skip(entry.name):
            continue
        target = dst / entry.name
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            copy_notes(entry, target)
        else:
            shutil.copy2(entry, target)


def _fence(code: str) -> str:
    """Return a fenced code block, using a longer fence if needed."""
    fence = "```"
    while fence in code:
        fence += "`"
    return fence


def generate_code_pages(docs_dir: Path) -> None:
    """For every source-code file, create a companion .md page."""
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in CODE_EXTENSIONS:
            continue

        md_name = f"{path.stem}-{ext.lstrip('.')}.md"
        md_path = path.parent / md_name

        if md_path.exists():
            continue  # never overwrite an existing .md

        code = path.read_text(encoding="utf-8", errors="replace")
        lang = LANG_MAP.get(ext, "")
        fence = _fence(code)
        content = f"# {path.name}\n\n{fence}{lang}\n{code}\n{fence}\n"
        md_path.write_text(content, encoding="utf-8")


def ensure_index(docs_dir: Path) -> None:
    """Make sure docs_dir has an index.md."""
    index = docs_dir / "index.md"
    if index.exists():
        return
    readme = docs_dir / "README.md"
    if readme.exists():
        shutil.copy2(readme, index)
        return
    site_name = os.environ.get("SITE_NAME", "My Notes")
    index.write_text(
        f"# {site_name}\n\nWelcome to **{site_name}**.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", required=True, help="Source notes directory")
    parser.add_argument("--out", required=True, help="Output build directory")
    parser.add_argument("--domain", required=True, help="Custom domain for CNAME")
    args = parser.parse_args()

    notes = Path(args.notes).resolve()
    out = Path(args.out).resolve()
    docs = out / "docs"

    # 1. Clean & recreate docs/
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)

    # 2. Copy notes → docs (filtered)
    copy_notes(notes, docs)

    # 3. Ensure an index.md exists
    ensure_index(docs)

    # 4. Generate .md pages for source-code files
    generate_code_pages(docs)

    # 5. Write CNAME
    (docs / "CNAME").write_text(args.domain, encoding="utf-8")

    # 6. Copy mkdocs.yml template into <out>/
    template = Path(__file__).resolve().parent.parent / "mkdocs.yml"
    shutil.copy2(template, out / "mkdocs.yml")

    print(f"[OK] docs prepared in {docs}  ({sum(1 for _ in docs.rglob('*') if _.is_file())} files)")


if __name__ == "__main__":
    main()
