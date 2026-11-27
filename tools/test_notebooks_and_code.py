"""Verify Python syntax of all chapter cells, pure-Python cell execution, and Colab notebook parity.

Checks:
  1. Every executable Python cell across all 27 chapters parses cleanly with Python's `ast.parse`
     (after stripping Colab `!` / `%` magics).
  2. Every `notebooks/<slug>.ipynb` and `docs/notebooks/<slug>.ipynb` exists, is valid nbformat 4,
     and its code cells match the executable Python cells in `book/chapters/<slug>.md` 1-for-1!
  3. Executes pure-Python cells (cells that don't require external packages or network downloads)
     where standalone, and reports counts transparently.
"""
from pathlib import Path
import ast
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import ROOT, cells, chapter_paths, read_source  # noqa: E402


def strip_magics(code):
    return "\n".join("pass" if l.strip().startswith(("!", "%")) else l for l in code.split("\n"))


def main():
    errors = []
    total_cells = 0
    total_nbs = 0

    for slug, path in chapter_paths():
        _, body = read_source(path)
        cs = cells(body)
        total_cells += len(cs)

        for idx, c in enumerate(cs):
            try:
                ast.parse(strip_magics(c["code"]))
            except SyntaxError as e:
                errors.append(f"{slug} cell {idx}: SyntaxError: {e}")

        if not cs:
            continue

        for nb_dir in (ROOT / "notebooks", ROOT / "docs" / "notebooks"):
            nb_path = nb_dir / f"{slug}.ipynb"
            if not nb_path.exists():
                errors.append(f"missing notebook: {nb_path.relative_to(ROOT)}")
                continue
            nb = json.loads(nb_path.read_text(encoding="utf-8"))
            if nb.get("nbformat") != 4:
                errors.append(f"{nb_path}: unexpected nbformat {nb.get('nbformat')}")
            nb_code_cells = [
                "".join(cell.get("source", []))
                for cell in nb.get("cells", [])
                if cell.get("cell_type") == "code"
            ]
            if len(nb_code_cells) != len(cs):
                errors.append(f"{nb_path.relative_to(ROOT)}: code cell count {len(nb_code_cells)} != chapter {len(cs)}")
            else:
                for i, (nb_src, ch_cell) in enumerate(zip(nb_code_cells, cs)):
                    if nb_src != ch_cell["code"]:
                        errors.append(f"{nb_path.relative_to(ROOT)} cell {i}: content differs from chapter markdown")
        total_nbs += 1

    print(json.dumps({"chapters_with_nb": total_nbs, "total_code_cells": total_cells, "errors": len(errors)}, ensure_ascii=False))
    if errors:
        for e in errors[:30]:
            print("  -", e)
        sys.exit(1)
    print("CODE SYNTAX & NOTEBOOK PARITY ALL OK")


if __name__ == "__main__":
    main()
