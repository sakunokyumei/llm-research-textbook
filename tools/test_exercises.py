"""Strict validator for book/exercises/*.json and rendered exercise HTML.

Checks:
  1. Fails hard when book/exercises/ is missing/empty, any chapter lacks an exercise bank,
     or docs/ is missing when --no-docs is not passed.
  2. JSON schema completeness (reasoning, steps, altExample, wrongReason, level 1..5,
     progressive hints[] schema, strict numeric value/tolerance types, valid ^#sN anchor).
  3. Choice/numeric/predict answer consistency & anti-skew check (MCQ answers not >60% one letter).
  4. Executes ALL pure-Python `predict` code snippets (including choice-predict with options)
     and `code` exercises (`solutionCode` + `colabCheck`), plus `ast.parse` on ALL code fields.
  5. Cross-checks single-line and multi-line `:::exercise` references in book/chapters/*.md
     against JSON banks and detects duplicate placements in the same chapter.
  6. Detects blatant exact-answer leaks in hints[0] / hint.
  7. When docs/ is checked, verifies every `sectionAnchor` exists in its HTML page,
     JSON embeds parse cleanly without unrendered MATHPH, and no duplicate exercise DOM IDs exist.
  8. `--self-test` runs fault-injection tests in a temporary directory to prove the validator
     rejects missing dirs, bad JSON, duplicate IDs, answer mismatches, missing embeds, and bad anchors.
"""
from html.parser import HTMLParser
from pathlib import Path
import argparse
import ast
import contextlib
import io
import json
import math
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import BOOK, ROOT, chapter_paths, extract_exercise_refs, read_source  # noqa: E402

VALID_TYPES = {"choice", "numeric", "predict", "code", "explain"}
EXTERNAL_MODS = (
    "torch", "transformers", "trl", "peft", "datasets", "gradio",
    "matplotlib", "numpy", "openai", "tiktoken", "sentence_transformers", "bitsandbytes",
)
ANCHOR_RE = re.compile(r"^#s\d+(?:-\d+)?$")


def strip_magics(code):
    return "\n".join("pass" if l.strip().startswith(("!", "%")) else l for l in code.split("\n"))


def is_pure_python(code):
    if not code:
        return False
    for mod in EXTERNAL_MODS:
        if re.search(rf"\b(?:import\s+{mod}|from\s+{mod}\b|{mod}\.)", code):
            return False
    if re.search(r"\b(chat|model|tok|tokenizer|trainer|pipe)\b", code):
        return False
    return True


def run_snippet(code):
    buf = io.StringIO()
    env = {"__name__": "__main__"}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<exercise>", "exec"), env)
    return buf.getvalue().strip()


def _check_hint_leak(ex_type, v, hint0):
    """Detect blatant exact-answer leaks in Stage-1 hint."""
    if not hint0:
        return None
    if ex_type == "choice":
        ans_id = v.get("answer")
        for o in v.get("options", []):
            if o.get("id") == ans_id:
                otext = str(o.get("text", "")).strip()
                if len(otext) >= 14 and otext in hint0:
                    return f"hint[0] leaks exact correct option text: {otext[:40]!r}"
        if re.search(rf"(?:正解は|答えは)\s*[「『`]?{re.escape(str(ans_id))}[」』`]?(?:\s|です|。|$)", hint0):
            return f"hint[0] explicitly states correct option {ans_id!r}"
    elif ex_type == "numeric":
        ans = v.get("answer")
        if isinstance(ans, dict) and isinstance(ans.get("value"), (int, float)) and not isinstance(ans.get("value"), bool):
            val = ans["value"]
            val_strs = {str(val)}
            if isinstance(val, float) and val.is_integer():
                val_strs.add(str(int(val)))
            for vs in val_strs:
                if re.search(rf"(?:=|≈|≒|答えは|正解は)\s*{re.escape(vs)}(?:\s*です|\s*！|\s*。|$)", hint0):
                    return f"hint[0] leaks exact numeric answer {vs!r}"
    return None


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.ex_ids = []
        self.in_ex_json = False
        self.cur_json = []
        self.ex_jsons = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "section" and a.get("data-exercise-id"):
            self.ex_ids.append(a["data-exercise-id"])
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


def validate_all(check_docs=True, book_dir=None, docs_dir=None, chapters_iter=None, quiet=False):
    book_root = Path(book_dir) if book_dir is not None else BOOK
    ex_dir = book_root / "exercises"
    docs_root = Path(docs_dir) if docs_dir is not None else (ROOT / "docs")
    chapters = list(chapters_iter) if chapters_iter is not None else list(chapter_paths())

    errors = []
    stats = {
        "files": 0, "exercises": 0, "variants": 0,
        "exec_predict": 0, "exec_code": 0, "mcq_answer_dist": {},
    }
    all_ids = set()
    by_chapter = {}
    parsed_by_slug = {}

    if not ex_dir.exists():
        errors.append(f"exercises directory not found: {ex_dir}")
        if not quiet:
            print(f"FAILED with {len(errors)} error(s):\n  - {errors[0]}")
        return 1

    json_files = sorted(ex_dir.glob("*.json"))
    if not json_files:
        errors.append(f"no exercise JSON files found in {ex_dir}")

    for path in json_files:
        stats["files"] += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{path.name}: malformed JSON: {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.name}: top-level JSON must be an object")
            continue
        slug = data.get("chapter") or path.stem
        if data.get("chapter") and data["chapter"] != path.stem:
            errors.append(f"{path.name}: 'chapter' field {data['chapter']!r} != filename stem {path.stem!r}")
        items = data.get("exercises", [])
        if not isinstance(items, list) or not items:
            errors.append(f"{path.name}: 'exercises' must be a non-empty list")
            continue
        parsed_by_slug[slug] = items
        by_chapter[slug] = [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]

        for item in items:
            if not isinstance(item, dict):
                errors.append(f"{path.name}: exercise entry must be an object")
                continue
            stats["exercises"] += 1
            eid = item.get("id")
            if not eid or not isinstance(eid, str):
                errors.append(f"{path.name}: missing/invalid exercise id")
                continue
            if eid in all_ids:
                errors.append(f"{path.name}: duplicate exercise id {eid}")
            all_ids.add(eid)

            ex_type = item.get("type")
            if ex_type not in VALID_TYPES:
                errors.append(f"{eid}: invalid type {ex_type!r}")
            lvl = item.get("level")
            if not isinstance(lvl, int) or isinstance(lvl, bool) or not (1 <= lvl <= 5):
                errors.append(f"{eid}: invalid level {lvl!r}")
            for req in ("concept", "conceptLabel", "section", "sectionAnchor"):
                if not item.get(req):
                    errors.append(f"{eid}: missing {req}")
            anc = item.get("sectionAnchor", "")
            if anc and not ANCHOR_RE.match(str(anc)):
                errors.append(f"{eid}: sectionAnchor {anc!r} must match ^#s\\d+(-\\d+)?$")

            variants = item.get("variants", [])
            if not isinstance(variants, list) or not variants:
                errors.append(f"{eid}: must have at least 1 variant")
                continue

            for vi, v in enumerate(variants):
                stats["variants"] += 1
                tag = f"{eid}[v{vi}]"
                if not isinstance(v, dict):
                    errors.append(f"{tag}: variant must be an object")
                    continue
                if not v.get("prompt"):
                    errors.append(f"{tag}: missing prompt")
                if not v.get("reasoning"):
                    errors.append(f"{tag}: missing reasoning")
                if not v.get("steps") or not isinstance(v["steps"], list):
                    errors.append(f"{tag}: missing steps list")
                if not v.get("altExample"):
                    errors.append(f"{tag}: missing altExample")

                # Validate progressive hints[] schema if present, and check Stage-1 leak
                if "hints" in v:
                    if not isinstance(v["hints"], list) or len(v["hints"]) < 2 or not all(isinstance(h, str) and h.strip() for h in v["hints"]):
                        errors.append(f"{tag}: 'hints' must be a list of >= 2 non-empty strings")
                hint0 = v["hints"][0] if (isinstance(v.get("hints"), list) and v["hints"]) else v.get("hint", "")
                leak = _check_hint_leak(ex_type, v, hint0)
                if leak:
                    errors.append(f"{tag}: {leak}")

                # Syntax-check ALL code fields regardless of external dependencies
                for cfield in ("code", "starterCode", "solutionCode", "colabCheck"):
                    src = v.get(cfield)
                    if src:
                        try:
                            ast.parse(strip_magics(src))
                        except SyntaxError as e:
                            errors.append(f"{tag}: {cfield} SyntaxError: {e}")

                if ex_type == "choice" or (ex_type == "predict" and v.get("options")):
                    opts = v.get("options", [])
                    if not isinstance(opts, list) or len(opts) < 3:
                        errors.append(f"{tag}: choice needs at least 3 options")
                    else:
                        opt_ids = [o.get("id") for o in opts]
                        if len(opt_ids) != len(set(opt_ids)):
                            errors.append(f"{tag}: duplicate option ids")
                        ans = v.get("answer")
                        if ans not in opt_ids:
                            errors.append(f"{tag}: answer {ans!r} not in options {opt_ids}")
                        else:
                            stats["mcq_answer_dist"][str(ans)] = stats["mcq_answer_dist"].get(str(ans), 0) + 1
                        for o in opts:
                            if o.get("id") != ans and not o.get("wrongReason"):
                                errors.append(f"{tag}: wrong option {o.get('id')!r} missing wrongReason")

                if ex_type == "numeric":
                    ans = v.get("answer")
                    if not isinstance(ans, dict) or "value" not in ans:
                        errors.append(f"{tag}: numeric answer must be dict with 'value'")
                    else:
                        val = ans["value"]
                        if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(val):
                            errors.append(f"{tag}: numeric answer 'value' must be finite int/float, got {val!r}")
                        if "tolerance" in ans:
                            tol = ans["tolerance"]
                            if not isinstance(tol, (int, float)) or isinstance(tol, bool) or tol < 0 or not math.isfinite(tol):
                                errors.append(f"{tag}: numeric 'tolerance' must be finite >= 0, got {tol!r}")

                if ex_type == "predict":
                    if not v.get("options"):
                        acc = v.get("accept")
                        if not isinstance(acc, list) or not acc:
                            errors.append(f"{tag}: text predict needs non-empty 'accept' list")
                    if v.get("code") and is_pure_python(v["code"]):
                        try:
                            actual = run_snippet(v["code"])
                            stats["exec_predict"] += 1
                            if not v.get("options"):
                                norm_acc = [str(a).strip() for a in v.get("accept", [])]
                                if actual not in norm_acc:
                                    errors.append(f"{tag}: code stdout {actual!r} != accept {norm_acc!r}")
                        except Exception as e:
                            errors.append(f"{tag}: predict code raised {e}")

                if ex_type == "code":
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

                if ex_type == "explain":
                    if not v.get("modelAnswer") or not v.get("selfCheckCriteria"):
                        errors.append(f"{tag}: explain exercise needs modelAnswer and selfCheckCriteria")

    # Anti-skew check on MCQ answer distribution across corpus
    total_mcq = sum(stats["mcq_answer_dist"].values())
    if total_mcq >= 20:
        for opt_id, cnt in stats["mcq_answer_dist"].items():
            ratio = cnt / total_mcq
            if ratio > 0.60:
                errors.append(f"MCQ answer distribution heavily skewed: option {opt_id!r} is {cnt}/{total_mcq} ({ratio:.1%}) > 60%")

    # Cross-check references in markdown chapters (must have bank for every chapter!)
    for slug, cpath in chapters:
        if slug not in by_chapter:
            errors.append(f"{slug}: missing exercise bank book/exercises/{slug}.json")
        if not Path(cpath).exists():
            errors.append(f"{slug}: chapter markdown missing at {cpath}")
            continue
        _, body = read_source(cpath)
        ref_pairs = extract_exercise_refs(body)
        refs = [eid for _, eid in ref_pairs]
        seen_in_ch = set()
        for ln, r in ref_pairs:
            if r in seen_in_ch:
                errors.append(f"{slug}.md:{ln}: duplicate :::exercise placement for {r}")
            seen_in_ch.add(r)
            if r not in all_ids:
                errors.append(f"{slug}.md:{ln}: references undefined exercise {r}")
        for d in by_chapter.get(slug, []):
            if d not in seen_in_ch:
                errors.append(f"{slug}.json: exercise {d} is never placed via :::exercise in {slug}.md")

    # Check rendered docs/ HTML
    if check_docs:
        if not docs_root.exists():
            errors.append(f"docs directory missing: {docs_root} (pass --no-docs to skip HTML checks)")
        else:
            for slug, items in parsed_by_slug.items():
                html_path = docs_root / f"{slug}.html"
                if not html_path.exists():
                    errors.append(f"docs/{slug}.html missing")
                    continue
                p = AnchorParser()
                p.feed(html_path.read_text(encoding="utf-8"))
                if len(p.ex_ids) != len(set(p.ex_ids)):
                    errors.append(f"docs/{slug}.html: duplicate exercise DOM IDs")
                for raw in p.ex_jsons:
                    try:
                        obj = json.loads(raw)
                        if "MATHPH" in raw or "DOLLARPHX" in raw:
                            errors.append(f"docs/{slug}.html: unrendered placeholder inside exercise {obj.get('id')}")
                    except Exception as e:
                        errors.append(f"docs/{slug}.html: invalid embedded exercise JSON: {e}")
                for item in items:
                    anchor = item.get("sectionAnchor", "")
                    if not ANCHOR_RE.match(str(anchor)) or anchor[1:] not in p.ids:
                        errors.append(f"{item['id']}: sectionAnchor {anchor!r} not found in docs/{slug}.html")

    if not quiet:
        print(json.dumps(stats, ensure_ascii=False))
        if errors:
            print(f"FAILED with {len(errors)} error(s):")
            for e in errors[:50]:
                print("  -", e)
        else:
            print("EXERCISES ALL OK")
    return 1 if errors else 0


def run_self_test():
    """Fault-injection self-test proving validate_all catches every critical failure mode."""
    def base_ex(eid="ch00-q01", ans="4", code="print(2 + 2)", anchor="#s1"):
        return {
            "id": eid, "chapter": "00-test", "section": "Sec 1", "sectionAnchor": anchor,
            "concept": "add", "conceptLabel": "Addition", "level": 1, "type": "predict",
            "variants": [{
                "prompt": "What prints?", "code": code, "accept": [ans],
                "hint": "Think about addition.", "hints": ["Think about addition.", "Add the two numbers."],
                "reasoning": "2 + 2 = 4", "steps": ["Compute 2 + 2"], "altExample": "1 + 1 = 2",
            }],
        }

    cases = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # Case 1: Missing exercises dir -> must fail (1)
        rc = validate_all(check_docs=False, book_dir=td / "empty_book", chapters_iter=[], quiet=True)
        cases.append(("missing_exercises_dir", rc == 1))

        # Helper to build a valid minimal fixture
        def make_fixture(name, ex_list=None, raw_json=None, md_text=None, with_docs=False, html_text=None):
            b = td / name / "book"
            (b / "exercises").mkdir(parents=True)
            (b / "chapters").mkdir(parents=True)
            ch_md = b / "chapters" / "00-test.md"
            ch_md.write_text(md_text if md_text is not None else '{"title":"t"}\n## Sec 1\n\n:::exercise ch00-q01\n:::\n', encoding="utf-8")
            ex_p = b / "exercises" / "00-test.json"
            if raw_json is not None:
                ex_p.write_text(raw_json, encoding="utf-8")
            else:
                ex_p.write_text(json.dumps({"chapter": "00-test", "exercises": ex_list}, ensure_ascii=False), encoding="utf-8")
            d = td / name / "docs"
            if with_docs:
                d.mkdir(parents=True)
                (d / "00-test.html").write_text(html_text or '<h2 id="s1">Sec 1</h2>', encoding="utf-8")
            return b, d, [("00-test", ch_md)]

        # Case 2: Valid baseline -> must pass (0)
        b, d, chs = make_fixture("ok", ex_list=[base_ex()], with_docs=True)
        cases.append(("valid_baseline", validate_all(check_docs=True, book_dir=b, docs_dir=d, chapters_iter=chs, quiet=True) == 0))

        # Case 3: Malformed JSON -> must fail (1)
        b, d, chs = make_fixture("bad_json", raw_json="{invalid json")
        cases.append(("malformed_json", validate_all(check_docs=False, book_dir=b, chapters_iter=chs, quiet=True) == 1))

        # Case 4: Duplicate exercise ID -> must fail (1)
        b, d, chs = make_fixture("dup_id", ex_list=[base_ex("ch00-q01"), base_ex("ch00-q01")])
        cases.append(("duplicate_id", validate_all(check_docs=False, book_dir=b, chapters_iter=chs, quiet=True) == 1))

        # Case 5: Predict code stdout mismatch -> must fail (1)
        b, d, chs = make_fixture("bad_ans", ex_list=[base_ex(ans="999")])
        cases.append(("predict_answer_mismatch", validate_all(check_docs=False, book_dir=b, chapters_iter=chs, quiet=True) == 1))

        # Case 6: Missing :::exercise embed -> must fail (1)
        b, d, chs = make_fixture("missing_embed", ex_list=[base_ex()], md_text='{"title":"t"}\n## Sec 1\nNo embed here.\n')
        cases.append(("missing_embed", validate_all(check_docs=False, book_dir=b, chapters_iter=chs, quiet=True) == 1))

        # Case 7: Missing docs/ when check_docs=True -> must fail (1)
        b, d, chs = make_fixture("missing_docs", ex_list=[base_ex()], with_docs=False)
        cases.append(("missing_docs_dir", validate_all(check_docs=True, book_dir=b, docs_dir=d, chapters_iter=chs, quiet=True) == 1))

        # Case 8: Invalid sectionAnchor without '#' -> must fail (1)
        b, d, chs = make_fixture("bad_anchor", ex_list=[base_ex(anchor="s1")], with_docs=True)
        cases.append(("bad_section_anchor", validate_all(check_docs=True, book_dir=b, docs_dir=d, chapters_iter=chs, quiet=True) == 1))

    failed = [name for name, ok in cases if not ok]
    print(json.dumps({"self_test_cases": len(cases), "passed": len(cases) - len(failed), "failed": failed}))
    if failed:
        print("SELF-TEST FAILED:", failed)
        return 1
    print("SELF-TEST ALL OK")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-docs", action="store_true")
    ap.add_argument("--docs-dir", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(run_self_test())
    sys.exit(validate_all(check_docs=not a.no_docs, docs_dir=a.docs_dir))


if __name__ == "__main__":
    main()
