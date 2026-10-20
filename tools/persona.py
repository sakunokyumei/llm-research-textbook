"""Learner simulation: walk the book in order as the target learner and flag
what they would meet before it was taught, plus per-chapter load metrics.

    python tools/persona.py            # prints a report, writes verification/persona-metrics.json

The learner (see PERSONA) starts with what a first-year vocational student
in an AI engineering course knows: HTML/CSS, the very basics of Python, a
little Linux, flowcharts/tracing and Fundamental IT Engineer exam topics.
This is a mechanical check, not a substitute for a real reader; the
qualitative walk-through is recorded in book/appendix/i-simulation.md.
"""
from pathlib import Path
import ast
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import BOOK, ROOT, cells, chapter_paths, read_source  # noqa: E402

PERSONA = {
    "name": "専門学校1年・AIエンジニア専攻（2026年入学）",
    "knows": ["HTML", "CSS", "print", "変数", "if文", "フローチャート", "トレース", "2進数", "16進数",
              "文字コード", "浮動小数点", "Linux（cd・ls）", "基本情報のアルゴリズム（配列・ループ）"],
    "python_known": {"def_basic", "if", "print", "assign"},
    "hours_per_week": 5,
}

# Words the learner already knows (school, FE exam) or that are too generic to flag.
KNOWN_OR_GENERIC = {"確率", "平均", "バイト", "形", "ライセンス", "ダウンロード", "変数", "関数", "リスト", "辞書"}

# Where each Python construct is first explained in the chapters (None = never explained in a chapter).
PY_INTRO = {
    "genexp": "01-first-llm", "fstring": "01-first-llm", "ifexp": "01-first-llm", "def": "01-first-llm",
    "import": "01-first-llm", "list": "01-first-llm", "dict": "01-first-llm",
    "for": "02-tokens", "listcomp": "02-tokens", "set": "02-tokens", "join": "02-tokens",
    "with": "03-next-token", "starkwargs": "03-next-token",
    "slice": "04-bigram", "open": "04-bigram",
    "dictcomp": "06-tensors", "class": "09-mlp", "decorator": "09-mlp", "lambda": "14-bpe",
    "assert": "15-gpt2", "while": "14-bpe", "modulo": "07-gradient", "try": "23-agents",
    "isinstance": "12-transformer", "augassign": "03-next-token", "zip": "03-next-token",
    "enumerate": "02-tokens", "sorted": "02-tokens", "gather": "20-evaluation",
}


def constructs(code):
    """Python constructs used in a cell (shell lines removed)."""
    code = "\n".join("pass" if l.strip().startswith(("!", "%")) else l for l in code.split("\n"))
    found = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return found
    for n in ast.walk(tree):
        kind = {ast.GeneratorExp: "genexp", ast.JoinedStr: "fstring", ast.IfExp: "ifexp", ast.FunctionDef: "def",
                ast.ListComp: "listcomp", ast.DictComp: "dictcomp", ast.SetComp: "listcomp", ast.With: "with",
                ast.ClassDef: "class", ast.Lambda: "lambda", ast.Assert: "assert", ast.While: "while",
                ast.Try: "try", ast.For: "for", ast.AugAssign: "augassign", ast.Slice: "slice"}.get(type(n))
        if kind:
            found.add(kind)
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.decorator_list:
            found.add("decorator")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod):
            found.add("modulo")
        if isinstance(n, ast.Call):
            if any(k.arg is None for k in n.keywords):
                found.add("starkwargs")
            if isinstance(n.func, ast.Name) and n.func.id in {"isinstance", "zip", "enumerate", "sorted"}:
                found.add(n.func.id)
            if isinstance(n.func, ast.Attribute) and n.func.attr == "gather":
                found.add("gather")
    return found


def strip_for_terms(body):
    body = re.sub(r"```.*?```", " ", body, flags=re.S)                 # code
    body = re.sub(r":::deep .*?\n:::", " ", body, flags=re.S)         # optional deep dives
    return body


def main():
    glossary = json.loads((BOOK / "glossary.json").read_text(encoding="utf-8"))
    order = [slug for slug, _ in chapter_paths()]
    rank = {s: i for i, s in enumerate(order)}
    report = {"persona": {**PERSONA, "python_known": sorted(PERSONA["python_known"])}, "chapters": [], "issues": []}
    for slug, path in chapter_paths():
        meta, body = read_source(path)
        here = rank[slug]
        text = strip_for_terms(body)
        # the closing teaser (last sensei block) may name the next chapter's topic
        last = text.rfind(":::sensei")
        scan = text[:last] if last > len(text) * 0.8 else text
        early, previews = [], []
        if slug != "00-welcome":
            for t in glossary:
                if t["term"] in KNOWN_OR_GENERIC:
                    continue
                intro = t.get("chapter")
                if intro in rank and rank[intro] > here and t["term"] in scan:
                    # a forward mention is fine when the same sentence glosses it or points to its chapter
                    sentences = [x for x in re.split(r"[。\n]", scan) if t["term"] in x]
                    if all(re.search(r"第\d+章|次の章|後で|あとで|（|\(", x) for x in sentences):
                        previews.append(f'{t["term"]}（第{int(intro[:2])}章）')
                    else:
                        early.append(f'{t["term"]}（第{int(intro[:2])}章で説明）')
        new_terms = [t["term"] for t in glossary if t.get("chapter") == slug]
        used = set()
        for c in cells(body):
            used |= constructs(c["code"])
        early_py = sorted(k for k in used if PY_INTRO.get(k) is None or rank.get(PY_INTRO[k], 99) > here)
        new_py = sorted(k for k in used if PY_INTRO.get(k) == slug)
        prose = re.sub(r"```.*?```", "", body, flags=re.S)
        n_cells = len(cells(body))
        code_lines = sum(len(c["code"].split("\n")) for c in cells(body))
        talks = body.count(":::sensei") + body.count(":::minato")
        quizzes = body.count(":::quiz")
        outputs = body.count("```output")
        figures = body.count("](img/")
        # longest stretch of prose (characters) with no code, talk, quiz or figure in between
        stretches = re.split(r"```|:::sensei|:::minato|:::quiz|:::try|!\[", body)
        longest = max(len(re.sub(r"\s", "", s)) for s in stretches)
        minutes = len(re.sub(r"\s", "", prose)) / 500 + n_cells * 2.5
        risk = 0
        risk += len(new_terms) > 12
        risk += len(early) > 0
        risk += len(early_py) > 0
        risk += longest > 2500
        risk += meta.get("level", 1) >= 5
        risk += minutes > 180
        row = {"slug": slug, "title": meta["title"], "level": meta.get("level"), "env": meta.get("env"),
               "new_terms": len(new_terms), "new_python": new_py, "cells": n_cells, "code_lines": code_lines,
               "talks": talks, "quizzes": quizzes, "outputs": outputs, "figures": figures,
               "longest_prose_chars": longest, "est_minutes": round(minutes), "early_terms": early, "previews": previews,
               "early_python": early_py, "risk_flags": int(risk)}
        report["chapters"].append(row)
        for e in early:
            report["issues"].append(f"{slug}: 用語の先取り {e}")
        for e in early_py:
            report["issues"].append(f"{slug}: 未説明のPython構文 {e}")
        if longest > 2500:
            report["issues"].append(f"{slug}: 会話・コードのない地の文が {longest} 字続く")
    out = ROOT / "verification" / "persona-metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{'章':16s} 難 新用語 新Py セル 行  会話 クイズ 出力 図 最長地文 目安分 リスク")
    for r in report["chapters"]:
        print(f"{r['slug']:16s} {r['level']}  {r['new_terms']:4d} {len(r['new_python']):4d} {r['cells']:4d} {r['code_lines']:4d}"
              f" {r['talks']:4d} {r['quizzes']:4d} {r['outputs']:4d} {r['figures']:2d} {r['longest_prose_chars']:6d} {r['est_minutes']:5d}  {r['risk_flags']}")
    print(f"\n{len(report['issues'])} issue(s)")
    for i in report["issues"]:
        print(" -", i)
    return report


if __name__ == "__main__":
    main()
