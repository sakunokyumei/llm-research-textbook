"""Shared parsing for the book sources (used by build.py and verify.py).

A source file is Markdown. The first line may be a JSON object with metadata.
Fenced code blocks carry flags in the info string:

    ```python                      a Colab cell: shown, put in the notebook, verified
    ```python no-run               shown only (not in the notebook, not verified)
    ```python gpu-only             in the notebook, skipped by the CPU verifier
    ```python online               in the notebook, skipped (needs the Hugging Face Hub API)
    ```python colab-only           in the notebook, skipped (needs Colab itself, e.g. a public Gradio link)
    ```python test:A=>B|C=>D       verifier replaces text A with B (e.g. fewer steps)
    ```output                      real output of the previous cell (verified)
    ```output-example              illustrative output (not compared)
    ```bash / ```text / ```json    shown as is
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
FENCE = re.compile(r"^(`{3,})(.*)$")


def load_curriculum():
    return json.loads((BOOK / "curriculum.json").read_text(encoding="utf-8"))


def read_source(path):
    text = Path(path).read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    if first.startswith("{"):
        return json.loads(first), rest
    return {}, text


def parse_info(info):
    """Split a fence info string into (language, flags, test substitutions)."""
    info = info.strip()
    subs = []
    if " test:" in " " + info:
        head, _, tail = (" " + info).partition(" test:")
        info = head.strip()
        for pair in tail.split("|"):
            old, _, new = pair.partition("=>")
            subs.append((old.strip(), new.strip()))
    parts = info.split()
    lang = parts[0] if parts else ""
    return lang, set(parts[1:]), subs


def iter_fences(body):
    """Yield (lang, flags, subs, code) for every fenced block in order."""
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i].strip())
        if m:
            ticks, info = m.groups()
            j = i + 1
            while j < len(lines) and lines[j].strip() != ticks:
                j += 1
            lang, flags, subs = parse_info(info)
            yield lang, flags, subs, "\n".join(lines[i + 1:j])
            i = j + 1
        else:
            i += 1


def cells(body):
    """Python cells with their expected outputs, in document order."""
    result = []
    for lang, flags, subs, code in iter_fences(body):
        if lang == "python" and "no-run" not in flags:
            result.append({"code": code, "flags": sorted(flags), "subs": subs,
                           "expected": None, "example": None})
        elif lang == "output" and result:
            result[-1]["expected"] = code
        elif lang == "output-example" and result:
            result[-1]["example"] = code
    return result


def chapter_paths():
    cur = load_curriculum()
    for part in cur["parts"]:
        for slug in part["chapters"]:
            yield slug, BOOK / "chapters" / f"{slug}.md"


def appendix_paths():
    cur = load_curriculum()
    for slug in cur["appendix"] + cur.get("extra", []):
        yield slug, BOOK / "appendix" / f"{slug}.md"
