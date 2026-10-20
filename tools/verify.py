"""Verify the book: run every chapter's code, compare outputs, check links.

    python tools/verify.py                  # everything
    python tools/verify.py --only 04-bigram # one chapter (comma separated)
    python tools/verify.py --update         # write real outputs into ```output blocks
    python tools/verify.py --links-only     # only check links in docs/

Each chapter runs in a fresh folder, like a new Colab session. Hugging Face
model names are swapped for tiny local stand-ins (tools/testkit/make_fakes.py)
because the verification machine cannot download real models: this proves
the code runs with the real libraries, not that the real models answer well.
Cells marked gpu-only are skipped on CPU; `test:` substitutions shrink loops.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import BOOK, ROOT, cells, chapter_paths, read_source, FENCE, parse_info  # noqa: E402

FAKES = ROOT / ".cache" / "fakes"
HF_IDS = {
    "Qwen/Qwen2.5-0.5B-Instruct": FAKES / "Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-0.5B": FAKES / "Qwen2.5-0.5B",
    "Qwen/Qwen2.5-1.5B-Instruct": FAKES / "Qwen2.5-1.5B-Instruct",
    "intfloat/multilingual-e5-small": FAKES / "multilingual-e5-small",
    "gpt2": FAKES / "gpt2",
}


def prepare(cell, full=False):
    code = cell["code"]
    for old, new in ([] if full else cell["subs"]):
        if old not in code:
            raise SystemExit(f"test substitution not found: {old!r}\n---\n{code}")
        code = code.replace(old, new)
    for hub, local in HF_IDS.items():
        code = code.replace(f'"{hub}"', f'"{local}"').replace(f"'{hub}'", f"'{local}'")
    # gpu-only: needs CUDA; online: needs the Hugging Face Hub API (both skipped by the CPU sandbox)
    return {"code": code, "skip": "gpu-only" in cell["flags"] or "online" in cell["flags"]}


def normalize(text):
    return "\n".join(line.rstrip() for line in text.strip("\n").split("\n")).strip()


def run_chapter(slug, path, timeout, full=False):
    meta, body = read_source(path)
    cs = cells(body)
    if not cs:
        return None
    work = ROOT / ".verify" / slug
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "cells.json").write_text(json.dumps([prepare(c, full) for c in cs], ensure_ascii=False), encoding="utf-8")
    try:
        proc = subprocess.run([sys.executable, str(ROOT / "tools/testkit/runner.py"), "cells.json", "result.json"],
                              cwd=work, capture_output=True, text=True, timeout=timeout)
        stderr = proc.stderr
    except subprocess.TimeoutExpired:
        return {"slug": slug, "cells": len(cs), "failures": [f"timeout after {timeout}s"], "results": []}
    result_file = work / "result.json"
    results = json.loads(result_file.read_text(encoding="utf-8")) if result_file.exists() else []
    failures = []
    if not result_file.exists():
        failures.append("runner crashed: " + stderr[-1500:])
    diverged = False   # after a shrunken (test:) cell, later outputs legitimately differ
    for r in results:
        if cs[r["index"]]["subs"] and not full:
            diverged = True
        r["comparable"] = not diverged and not r.get("skipped")
        if r.get("error"):
            failures.append(f"cell {r['index']} raised:\n{r['error'][-1500:]}\n--- code ---\n{cs[r['index']]['code'][:600]}")
        elif r["comparable"] and cs[r["index"]]["expected"] is not None:
            want, got = normalize(cs[r["index"]]["expected"]), normalize(r["stdout"])
            if want != got:
                failures.append(f"cell {r['index']} output differs\n--- expected ---\n{want[:800]}\n--- actual ---\n{got[:800]}")
    if len(results) < len(cs) and not failures:
        failures.append(f"only {len(results)} of {len(cs)} cells ran")
    return {"slug": slug, "cells": len(cs), "skipped": sum(1 for r in results if r.get("skipped")),
            "seconds": round(sum(r.get("seconds", 0) for r in results), 1), "failures": failures, "results": results}


def update_outputs(path, results):
    """Replace ```output blocks after each python cell with the real stdout."""
    meta_line, _, _ = path.read_text(encoding="utf-8").partition("\n")
    lines = path.read_text(encoding="utf-8").split("\n")
    by_index = {r["index"]: r for r in results}
    i, cell_no, last_cell = 0, -1, None
    out = []
    while i < len(lines):
        m = FENCE.match(lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        ticks, info = m.groups()
        j = i + 1
        while j < len(lines) and lines[j].strip() != ticks:
            j += 1
        lang, flags, subs = parse_info(info)
        block = lines[i:j + 1]
        if lang == "python" and "no-run" not in flags:
            cell_no += 1
            last_cell = cell_no
        elif lang == "output" and last_cell is not None:
            r = by_index.get(last_cell)
            if r and r.get("comparable") and not r.get("error"):
                text = r["stdout"].rstrip("\n")
                block = [lines[i]] + (text.split("\n") if text else ["(何も表示されない)"]) + [lines[j]]
            last_cell = None
        else:
            last_cell = None if lang not in {"output-example"} else last_cell
        out.extend(block)
        i = j + 1
    path.write_text("\n".join(out), encoding="utf-8")


def check_minigpt():
    """code/minigpt.py must contain exactly the classes written in chapter 12."""
    import ast
    lib = {n.name: ast.dump(n) for n in ast.parse((ROOT / "code/minigpt.py").read_text(encoding="utf-8")).body
           if isinstance(n, ast.ClassDef)}
    _, body = read_source(BOOK / "chapters" / "12-transformer.md")
    book = {}
    for c in cells(body):
        for n in ast.parse(c["code"]).body:
            if isinstance(n, ast.ClassDef):
                book[n.name] = ast.dump(n)
    problems = [f"minigpt.py class {k} differs from chapter 12" for k in lib if book.get(k) != lib[k]]
    return problems + [f"chapter 12 class {k} missing from minigpt.py" for k in book if k not in lib]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.links.append(a[k])


def check_links(site):
    pages, failures = {}, []
    for f in site.glob("*.html"):
        p = Links()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f.resolve()] = p
        if re.search(r"(?m)^:::|BLOCKPH\d|MATHPH[0-9a-f]{16}X", f.read_text(encoding="utf-8")):
            failures.append(f"unrendered marker in {f.name}")
    for f, p in pages.items():
        for link in p.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or link.startswith("mailto:"):
                continue
            target = (f.parent / unquote(u.path)).resolve() if u.path else f
            if not target.exists():
                failures.append(f"broken link {f.name} -> {link}")
            elif u.fragment and target in pages and u.fragment not in pages[target].ids:
                failures.append(f"missing anchor {f.name} -> {link}")
    return len(pages), failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--links-only", action="store_true")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--full", action="store_true", help="ignore test: substitutions (slow, real outputs)")
    a = ap.parse_args()
    report = {"date": datetime.date.today().isoformat(), "python": sys.version.split()[0], "chapters": [], "link_failures": []}
    try:
        import torch, transformers  # noqa: E401
        report["torch"], report["transformers"] = torch.__version__, transformers.__version__
    except ImportError:
        pass
    all_failures = []
    if not a.links_only:
        only = set(a.only.split(",")) if a.only else None
        for slug, path in chapter_paths():
            if only and slug not in only:
                continue
            r = run_chapter(slug, path, a.timeout, a.full)
            if r is None:
                continue
            status = "OK" if not r["failures"] else "FAIL"
            print(f"{status:4} {slug}: {r['cells']} cells, {r.get('skipped', 0)} skipped (gpu-only), {r.get('seconds', 0)}s", flush=True)
            for f in r["failures"]:
                print("    " + f.replace("\n", "\n    "))
            if a.update and r["results"]:
                update_outputs(path, r["results"])
            figs = ROOT / ".verify" / slug / "figs"
            if figs.exists() and not r["failures"]:
                dest = ROOT / "site" / "img" / "figs" / slug
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(figs, dest)
            all_failures += r["failures"]
            report["chapters"].append({k: v for k, v in r.items() if k != "results"})
    consistency = check_minigpt()
    for f in consistency:
        print("CODE " + f)
    all_failures += consistency
    n, link_failures = check_links(ROOT / "docs")
    report["html_pages"], report["link_failures"] = n, link_failures
    for f in link_failures:
        print("LINK " + f)
    all_failures += link_failures
    if not a.only and not a.links_only:
        (ROOT / "verification").mkdir(exist_ok=True)
        (ROOT / "verification" / "code-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("ALL OK" if not all_failures else f"{len(all_failures)} problem(s)")
    sys.exit(1 if all_failures else 0)


if __name__ == "__main__":
    main()
