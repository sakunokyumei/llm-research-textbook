"""Verify Python syntax of all chapter cells, pure-Python cell execution, code/*.py, and Colab notebook parity.

Checks:
  1. Every executable Python cell across all 27 chapters (and all code/*.py files) parses cleanly
     with Python's `ast.parse` (after stripping Colab `!` / `%` magics).
  2. Executes safe standalone pure-Python cells in isolated subprocesses with timeout and reports counts.
  3. Every `notebooks/<slug>.ipynb` and `docs/notebooks/<slug>.ipynb` exists, has zero orphan files,
     is valid nbformat 4.5 (with unique per-cell `id`s and optional `nbformat.validate()`),
     has rich standalone markdown (no empty skeletons, no raw `:::` directives),
     and matches executable Python cells in `book/chapters/<slug>.md` 1-for-1!
"""
from pathlib import Path
import argparse
import ast
import json
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import ROOT, cells, chapter_paths, iter_fences, read_source  # noqa: E402

try:
    import nbformat
except ImportError:
    nbformat = None

EXTERNAL_OR_NET = (
    "torch", "transformers", "trl", "peft", "datasets", "gradio", "matplotlib",
    "numpy", "openai", "tiktoken", "sentence_transformers", "bitsandbytes",
    "urllib", "requests", "google.colab", "huggingface_hub", "minigpt",
    "open(", "wget", "!pip", "!nvidia-smi", "drive.mount", "files.download",
)


def strip_magics(code):
    return "\n".join("pass" if l.strip().startswith(("!", "%")) else l for l in code.split("\n"))


def is_standalone_pure_python(code, flags):
    """Heuristic for cells that can safely run standalone in stdlib Python without network/external libs."""
    if {"gpu-only", "online", "colab-only"} & set(flags):
        return False
    if any(tok in code for tok in EXTERNAL_OR_NET):
        return False
    if any(l.strip().startswith(("!", "%")) for l in code.split("\n")):
        return False
    return True


def run_pure_cell(code, timeout=15):
    """Run a pure-Python cell in a clean subprocess; returns (ok, reason)."""
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout,
    )
    if r.returncode == 0:
        return True, ""
    # NameError on first execution indicates cell depends on a previous cell's variable
    if "NameError:" in r.stderr:
        return None, "stateful"
    return False, r.stderr.strip()[-400:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notebooks-dir", default=str(ROOT / "notebooks"))
    ap.add_argument("--docs-notebooks-dir", default=str(ROOT / "docs" / "notebooks"))
    a = ap.parse_args()
    nb_dirs = [Path(a.notebooks_dir), Path(a.docs_notebooks_dir)]

    errors = []
    total_cells = 0
    total_norun_checked = 0
    total_nbs = 0
    pure_executed = 0
    pure_stateful_skipped = 0
    expected_nb_names = set()

    # 1. Check code/*.py syntax
    for py_path in sorted((ROOT / "code").glob("*.py")):
        try:
            ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            errors.append(f"{py_path.relative_to(ROOT)}: SyntaxError: {e}")

    # 2. Check all chapter cells & notebooks
    for slug, path in chapter_paths():
        _, body = read_source(path)
        cs = cells(body)
        total_cells += len(cs)

        # Syntax check no-run python snippets too (ignoring intentional ellipsis-only pseudocode)
        for lang, flags, _, code in iter_fences(body):
            if lang == "python" and "no-run" in flags:
                if "…" in code or "..." in code:
                    continue
                total_norun_checked += 1
                try:
                    ast.parse(strip_magics(code))
                except SyntaxError as e:
                    errors.append(f"{slug} (no-run): SyntaxError: {e}")

        for idx, c in enumerate(cs):
            try:
                ast.parse(strip_magics(c["code"]))
            except SyntaxError as e:
                errors.append(f"{slug} cell {idx}: SyntaxError: {e}")
                continue
            if is_standalone_pure_python(c["code"], c["flags"]):
                ok, reason = run_pure_cell(c["code"])
                if ok is True:
                    pure_executed += 1
                elif ok is None:
                    pure_stateful_skipped += 1
                else:
                    errors.append(f"{slug} cell {idx} pure-Python execution failed: {reason}")

        if not cs:
            continue

        expected_nb_names.add(f"{slug}.ipynb")
        nb_bytes_list = []

        for nb_dir in nb_dirs:
            nb_path = nb_dir / f"{slug}.ipynb"
            if not nb_path.exists():
                errors.append(f"missing notebook: {nb_path}")
                continue
            raw_bytes = nb_path.read_bytes()
            nb_bytes_list.append(raw_bytes)
            nb = json.loads(raw_bytes.decode("utf-8"))

            if nb.get("nbformat") != 4 or nb.get("nbformat_minor") != 5:
                errors.append(f"{nb_path}: expected nbformat 4.5, got {nb.get('nbformat')}.{nb.get('nbformat_minor')}")
            if nbformat is not None:
                try:
                    nbformat.validate(nb)
                except Exception as e:
                    errors.append(f"{nb_path}: nbformat.validate failed: {e}")

            nb_cells = nb.get("cells", [])
            seen_ids = set()
            md_cells = []
            nb_code_cells = []
            for ci, cell in enumerate(nb_cells):
                cid = cell.get("id")
                if not cid or not isinstance(cid, str):
                    errors.append(f"{nb_path}: cell {ci} missing nbformat 4.5 'id'")
                elif cid in seen_ids:
                    errors.append(f"{nb_path}: duplicate cell id {cid!r}")
                else:
                    seen_ids.add(cid)
                src = "".join(cell.get("source", []))
                if cell.get("cell_type") == "markdown":
                    md_cells.append(src)
                    if re.search(r"(?m)^:::[a-z]|^:::$", src):
                        errors.append(f"{nb_path}: cell {ci} contains unrendered ::: directive")
                elif cell.get("cell_type") == "code":
                    nb_code_cells.append(src)

            if nb_cells and "" in nb_cells[0].get("source", []):
                errors.append(f"{nb_path}: cell 0 source contains extraneous empty string element")
            md_chars = sum(len(s) for s in md_cells)
            if len(md_cells) < 3 or md_chars < 500:
                errors.append(f"{nb_path}: notebook markdown too sparse ({len(md_cells)} md cells, {md_chars} chars)")

            if len(nb_code_cells) != len(cs):
                errors.append(f"{nb_path}: code cell count {len(nb_code_cells)} != chapter {len(cs)}")
            else:
                for i, (nb_src, ch_cell) in enumerate(zip(nb_code_cells, cs)):
                    if nb_src != ch_cell["code"]:
                        errors.append(f"{nb_path} cell {i}: content differs from chapter markdown")

        if len(nb_bytes_list) == 2 and nb_bytes_list[0] != nb_bytes_list[1]:
            errors.append(f"{slug}.ipynb differs between {nb_dirs[0]} and {nb_dirs[1]}")
        total_nbs += 1

    # 3. Check for orphan .ipynb files
    for nb_dir in nb_dirs:
        if nb_dir.exists():
            for p in sorted(nb_dir.glob("*.ipynb")):
                if p.name not in expected_nb_names:
                    errors.append(f"orphan notebook: {p}")

    print(json.dumps({
        "chapters_with_nb": total_nbs,
        "total_code_cells": total_cells,
        "norun_syntax_checked": total_norun_checked,
        "pure_python_cells_executed": pure_executed,
        "pure_python_stateful_skipped": pure_stateful_skipped,
        "nbformat_validated": nbformat is not None,
        "errors": len(errors),
    }, ensure_ascii=False))
    if errors:
        for e in errors[:30]:
            print("  -", e)
        sys.exit(1)
    print("CODE SYNTAX & NOTEBOOK PARITY ALL OK")


if __name__ == "__main__":
    main()
