"""Strict validator for book/exercises/*.json and rendered exercise HTML.

Checks:
  1. JSON schema completeness (reasoning, steps, altExample, wrongReason, level 1..5).
  2. Choice/numeric/predict answer consistency.
  3. Executes pure-Python `predict` code snippets and checks stdout matches expected answer!
  4. Executes pure-Python `code` exercises (`solutionCode` + `colabCheck`) to verify assertions pass!
  5. Cross-checks `:::exercise` references in book/chapters/*.md against JSON banks.
  6. When docs/ is built, checks every `sectionAnchor` exists in its HTML page and JSON embeds parse cleanly.
"""
from html.parser import HTMLParser
from pathlib import Path
import contextlib
import io
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import BOOK, ROOT, chapter_paths, read_source  # noqa: E402

VALID_TYPES = {"choice", "numeric", "predict", "code", "explain"}
EXTERNAL_MODS = ("torch", "transformers", "trl", "peft", "datasets", "gradio", "matplotlib", "numpy", "openai", "tiktoken")


def is_pure_python(code):
    if not code:
        return False
    for mod in EXTERNAL_MODS:
        if re.search(rf"\b(?:import\s+{mod}|from\s+{mod}\b|{mod}\.)", code):
            return False
    # Skip snippets referencing chapter runtime variables like tok, model, chat, logits, probs
    if re.search(r"\b(chat|model|tok|tokenizer|trainer|pipe)\b", code):
        return False
    return True


def run_snippet(code):
    buf = io.StringIO()
    env = {"__name__": "__main__"}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<exercise>", "exec"), env)
    return buf.getvalue().strip()


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.in_ex_json = False
        self.cur_json = []
        self.ex_jsons = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "script" and a.get("class") == "ex-data":
            self.in_ex_json = True
            self.cur_json = []

    def handle_endtag(self, tag):
        if tag == "script" and self.in_ex_json:
            self.in_ex_json = False
            self.ex_jsons.append("".join(self.cur_json))

    def handle_data(self, data):
        if self.in_ex_json:
            self.cur_json.append(data)


def validate_all(check_docs=True):
    ex_dir = BOOK / "exercises"
    errors = []
    stats = {"files": 0, "exercises": 0, "variants": 0, "exec_predict": 0, "exec_code": 0}
    all_ids = set()
    by_chapter = {}

    if not ex_dir.exists():
        print("No book/exercises directory found.")
        return 0

    for path in sorted(ex_dir.glob("*.json")):
        stats["files"] += 1
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = data.get("chapter") or path.stem
        items = data.get("exercises", [])
        by_chapter[slug] = [item["id"] for item in items]

        for item in items:
            stats["exercises"] += 1
            eid = item.get("id", "<missing-id>")
            if eid in all_ids:
                errors.append(f"{path.name}: duplicate exercise id {eid}")
            all_ids.add(eid)

            if item.get("type") not in VALID_TYPES:
                errors.append(f"{eid}: invalid type {item.get('type')!r}")
            lvl = item.get("level")
            if not isinstance(lvl, int) or not (1 <= lvl <= 5):
                errors.append(f"{eid}: invalid level {lvl!r}")
            for req in ("concept", "conceptLabel", "section", "sectionAnchor"):
                if not item.get(req):
                    errors.append(f"{eid}: missing {req}")
            variants = item.get("variants", [])
            if not variants:
                errors.append(f"{eid}: must have at least 1 variant")

            for vi, v in enumerate(variants):
                stats["variants"] += 1
                tag = f"{eid}[v{vi}]"
                if not v.get("prompt"):
                    errors.append(f"{tag}: missing prompt")
                if not v.get("reasoning"):
                    errors.append(f"{tag}: missing reasoning")
                if not v.get("steps") or not isinstance(v["steps"], list):
                    errors.append(f"{tag}: missing steps list")
                if not v.get("altExample"):
                    errors.append(f"{tag}: missing altExample")

                t = item.get("type")
                if t == "choice" or (t == "predict" and v.get("options")):
                    opts = v.get("options", [])
                    if len(opts) < 3:
                        errors.append(f"{tag}: choice needs at least 3 options")
                    opt_ids = [o.get("id") for o in opts]
                    if len(opt_ids) != len(set(opt_ids)):
                        errors.append(f"{tag}: duplicate option ids")
                    if v.get("answer") not in opt_ids:
                        errors.append(f"{tag}: answer {v.get('answer')!r} not in options {opt_ids}")
                    for o in opts:
                        if o.get("id") != v.get("answer") and not o.get("wrongReason"):
                            errors.append(f"{tag}: wrong option {o.get('id')!r} missing wrongReason")
                elif t == "numeric":
                    ans = v.get("answer")
                    if not isinstance(ans, dict) or "value" not in ans:
                        errors.append(f"{tag}: numeric answer must be dict with 'value'")
                elif t == "predict":
                    acc = v.get("accept")
                    if not isinstance(acc, list) or not acc:
                        errors.append(f"{tag}: text predict needs non-empty 'accept' list")
                    if v.get("code") and is_pure_python(v["code"]):
                        try:
                            actual = run_snippet(v["code"])
                            stats["exec_predict"] += 1
                            norm_acc = [a.strip() for a in acc]
                            if actual not in norm_acc:
                                errors.append(f"{tag}: code stdout {actual!r} != accept {norm_acc!r}")
                        except Exception as e:
                            errors.append(f"{tag}: predict code raised {e}")
                elif t == "code":
                    if not v.get("starterCode") or not v.get("solutionCode") or not v.get("colabCheck"):
                        errors.append(f"{tag}: code exercise needs starterCode, solutionCode, and colabCheck")
                    if not v.get("selfCheckCriteria"):
                        errors.append(f"{tag}: code exercise needs selfCheckCriteria")
                    combo = (v.get("solutionCode", "") + "\n" + v.get("colabCheck", "")).strip()
                    if is_pure_python(combo) and not item.get("skipExec"):
                        try:
                            run_snippet(combo)
                            stats["exec_code"] += 1
                        except Exception as e:
                            errors.append(f"{tag}: solutionCode + colabCheck failed: {e}")
                elif t == "explain":
                    if not v.get("modelAnswer") or not v.get("selfCheckCriteria"):
                        errors.append(f"{tag}: explain exercise needs modelAnswer and selfCheckCriteria")

    # Cross-check references in markdown chapters
    for slug, cpath in chapter_paths():
        _, body = read_source(cpath)
        refs = []
        for m in re.finditer(r"(?m)^:::exercise\s+(.+)$", body):
            refs.extend(tok.strip() for tok in m.group(1).replace(",", " ").split() if tok.strip())
        defined = by_chapter.get(slug, [])
        for r in refs:
            if r not in all_ids:
                errors.append(f"{slug}.md: references undefined exercise {r}")
        for d in defined:
            if d not in refs:
                errors.append(f"{slug}.json: exercise {d} is never placed via :::exercise in {slug}.md")

    # Check rendered docs/ HTML
    docs_dir = ROOT / "docs"
    if check_docs and docs_dir.exists():
        for slug, ids in by_chapter.items():
            html_path = docs_dir / f"{slug}.html"
            if not html_path.exists():
                errors.append(f"docs/{slug}.html missing")
                continue
            p = AnchorParser()
            p.feed(html_path.read_text(encoding="utf-8"))
            for raw in p.ex_jsons:
                try:
                    obj = json.loads(raw)
                    if "MATHPH" in raw:
                        errors.append(f"docs/{slug}.html: unrendered MATHPH inside exercise {obj.get('id')}")
                except Exception as e:
                    errors.append(f"docs/{slug}.html: invalid embedded exercise JSON: {e}")
            data = json.loads((ex_dir / f"{slug}.json").read_text(encoding="utf-8"))
            for item in data.get("exercises", []):
                anchor = item.get("sectionAnchor", "")
                if anchor.startswith("#") and anchor[1:] not in p.ids:
                    errors.append(f"{item['id']}: sectionAnchor {anchor} not found in docs/{slug}.html")

    print(json.dumps(stats, ensure_ascii=False))
    if errors:
        print(f"FAILED with {len(errors)} error(s):")
        for e in errors[:50]:
            print("  -", e)
        return 1
    print("EXERCISES ALL OK")
    return 0


if __name__ == "__main__":
    no_docs = "--no-docs" in sys.argv
    sys.exit(validate_all(check_docs=not no_docs))
