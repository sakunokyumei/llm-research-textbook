"""Execute one chapter's cells like a fresh Colab session (used by verify.py).

    python runner.py cells.json result.json

Cells share one namespace, run in order, and each cell's stdout is captured.
Colab-only things are imitated: `!` shell lines, `google.colab.drive`, and
downloads are served from a local cache when the sandbox has no network.
"""
import ast
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache" / "downloads"
REPO_RAW = "https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/"
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, str(Path(__file__).parent / "fake_modules"))

# ---------------------------------------------------------------- downloads
_real_urlopen = urllib.request.urlopen


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _fetch(url):
    if url.startswith(REPO_RAW):
        return (ROOT / url[len(REPO_RAW):]).read_bytes()
    name = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if name.exists():
        return name.read_bytes()
    for path in CACHE.glob("*.txt"):  # files fetched by hand into the cache
        if url.endswith("/" + path.name):
            return path.read_bytes()
    data = _real_urlopen(url, timeout=60).read()
    CACHE.mkdir(parents=True, exist_ok=True)
    name.write_bytes(data)
    return data


def fake_urlopen(url, *args, **kwargs):
    if not isinstance(url, str):
        url = url.full_url
    return _Response(_fetch(url))


def fake_urlretrieve(url, filename=None, *args, **kwargs):
    filename = filename or url.rsplit("/", 1)[-1]
    Path(filename).write_bytes(_fetch(url))
    return filename, None


urllib.request.urlopen = fake_urlopen
urllib.request.urlretrieve = fake_urlretrieve


def shell(cmd):
    """Imitate a Colab `!command` line."""
    words = shlex.split(cmd)
    if not words:
        return
    if words[0] in {"pip", "nvidia-smi"} or words[:3] == ["python", "-m", "pip"] or words[:2] == ["uv", "pip"]:
        return
    if words[0] == "wget":
        url = next(w for w in words[1:] if w.startswith("http"))
        out = words[words.index("-O") + 1] if "-O" in words else url.rsplit("/", 1)[-1]
        Path(out).write_bytes(_fetch(url))
        return
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode:
        print(r.stderr, end="")


# ---------------------------------------------------------------- execution
def transform(code):
    lines = []
    for line in code.split("\n"):
        s = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        if s.startswith("!"):
            lines.append(f"{indent}__shell__({s[1:]!r})")
        elif s.startswith("%"):
            lines.append(f"{indent}pass")
        else:
            lines.append(line)
    return "\n".join(lines)


def run_cell(code, env):
    tree = ast.parse(code)
    last = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    exec(compile(tree, "<cell>", "exec"), env)
    if last is not None:
        value = eval(compile(last, "<cell>", "eval"), env)
        if value is not None:
            print(repr(value))


CURRENT_CELL = [0]


def _patch_matplotlib():
    """Save every figure shown by a cell to figs/cell{N}_{k}.png (used as book illustrations)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    counter = {}

    def show(*args, **kwargs):
        Path("figs").mkdir(exist_ok=True)
        for num in plt.get_fignums():
            fig = plt.figure(num)
            k = counter.get(CURRENT_CELL[0], 0)
            counter[CURRENT_CELL[0]] = k + 1
            fig.savefig(f"figs/cell{CURRENT_CELL[0]}_{k}.png", dpi=110, bbox_inches="tight")
        plt.close("all")
    plt.show = show


def main():
    _patch_matplotlib()
    cells = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_path = Path(sys.argv[2])
    env = {"__name__": "__main__", "__shell__": shell}
    results = []
    for i, cell in enumerate(cells):
        if cell.get("skip"):
            results.append({"index": i, "skipped": True})
            continue
        buf = io.StringIO()
        CURRENT_CELL[0] = i
        start = time.time()
        error = None
        try:
            with contextlib.redirect_stdout(buf):
                run_cell(transform(cell["code"]), env)
        except BaseException:  # report and stop like a failing notebook
            error = traceback.format_exc(limit=6)
        results.append({"index": i, "stdout": buf.getvalue(), "error": error, "seconds": round(time.time() - start, 2)})
        sys.stderr.write(f"cell {i}: {results[-1]['seconds']}s{' ERROR' if error else ''}\n")
        if error:
            break
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
