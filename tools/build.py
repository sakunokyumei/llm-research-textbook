"""Build the static site into docs/ (GitHub Pages) and notebooks/ (Colab).

    python tools/build.py            # writes docs/ and notebooks/
    python tools/build.py --out dist # preview build elsewhere

Math ($...$, $$...$$) is rendered at build time with the vendored KaTeX
(needs Node.js). Rendered math is cached in book/.mathcache.json so the site
can be rebuilt without Node as long as the formulas did not change.
"""
from html import escape
from pathlib import Path
import argparse
import hashlib
import json
import keyword
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent))
try:
    from markdown_it import MarkdownIt
except ImportError:
    from mdfallback import MarkdownIt  # noqa: E402
from bookparse import BOOK, ROOT, load_curriculum, read_source, parse_info, cells, iter_fences  # noqa: E402

args = argparse.ArgumentParser()
args.add_argument("--out", default="docs")
args.add_argument("--notebooks", default="notebooks")
args.add_argument("--no-write-cache", action="store_true",
                  help="Do not modify book/.mathcache.json (useful for isolated/read-only builds)")
args.add_argument("--allow-raw-math", action="store_true",
                  help="Allow fallback raw TeX in HTML if Node.js is unavailable (never cached)")
opts = args.parse_args()
OUT = ROOT / opts.out
NB_OUT = ROOT / opts.notebooks
CUR = load_curriculum()
REPO = CUR["repo"]
SITE_TITLE = CUR["title"]

# ---------------------------------------------------------------- math
MATH_CACHE_PATH = BOOK / ".mathcache.json"
math_cache = json.loads(MATH_CACHE_PATH.read_text(encoding="utf-8")) if MATH_CACHE_PATH.exists() else {}
# Discard any accidentally poisoned entries on load
math_cache = {k: v for k, v in math_cache.items() if "math-raw" not in v and not v.startswith("ERROR:")}
math_ephemeral = {}
math_used = set()
math_pending = {}


def math_key(tex, display):
    return hashlib.sha1(((("D" if display else "I") + tex)).encode()).hexdigest()[:16]


def math_placeholder(tex, display):
    key = math_key(tex, display)
    math_used.add(key)
    if key not in math_cache and key not in math_ephemeral:
        math_pending[key] = (tex, display)
    return f"MATHPH{key}X"


def flush_math():
    if not math_pending:
        return
    items = list(math_pending.items())
    try:
        r = subprocess.run(["node", str(ROOT / "tools/katex/render.js")],
                           input=json.dumps([v for _, v in items]), capture_output=True,
                           text=True, encoding="utf-8", check=True)
        rendered = json.loads(r.stdout)
    except (OSError, subprocess.CalledProcessError) as e:
        if not opts.allow_raw_math:
            raise SystemExit(f"KaTeX rendering failed (Node.js required for {len(items)} uncached formula(s)): {e}")
        print("warning: KaTeX unavailable, math left as TeX (not cached):", e, file=sys.stderr)
        rendered = [None] * len(items)
    for (key, (tex, display)), html in zip(items, rendered):
        if html is None:
            # Never poison book/.mathcache.json with raw TeX fallback
            math_ephemeral[key] = f'<code class="math-raw">{escape(tex)}</code>'
        elif html.startswith("ERROR:"):
            raise SystemExit(f"KaTeX error in {tex!r}: {html}")
        else:
            math_cache[key] = html
    math_pending.clear()


def _normalize_cjk_bold_line(line):
    """Convert **...** outside inline code into <strong>...</strong> so CommonMark CJK punctuation boundaries work identically across markdown-it-py and mdfallback."""
    stash = {}

    def _stash_code(m):
        k = f"\x00CS{len(stash)}X\x00"
        stash[k] = m.group(0)
        return k

    masked = re.sub(r"(`+[^`\n]*?`+)", _stash_code, line)
    masked = re.sub(
        r"(?<!\*)\*\*(?!\s)([^\n*]+?(?:\*[^\n*]+?)*?)(?<!\s)\*\*(?!\*)",
        r"<strong>\1</strong>",
        masked,
    )
    for k, v in stash.items():
        masked = masked.replace(k, v)
    return masked


def normalize_cjk_bold(text):
    """Apply CJK-safe bold normalization outside fenced code blocks."""
    lines = text.split("\n")
    out = []
    fence = None
    for line in lines:
        s = line.strip()
        mf = re.match(r"^(`{3,}|~{3,})", s)
        if fence:
            if s.startswith(fence) and s.strip(fence[0]) == "":
                fence = None
            out.append(line)
            continue
        if mf:
            fence = mf.group(1)
            out.append(line)
            continue
        out.append(_normalize_cjk_bold_line(line))
    return "\n".join(out)


def protect_math(text):
    """Replace $$..$$ and $..$ outside fenced code blocks and inline code with placeholders."""
    lines = text.split("\n")
    out_lines = []
    fence = None
    for line in lines:
        s = line.strip()
        mf = re.match(r"^(`{3,}|~{3,})", s)
        if fence:
            if s.startswith(fence) and s.strip(fence[0]) == "":
                fence = None
            out_lines.append(("fence", line))
            continue
        if mf:
            fence = mf.group(1)
            out_lines.append(("fence", line))
            continue
        out_lines.append(("text", line))

    # Group consecutive text/fence lines so display math $$...$$ can span multiple lines
    grouped = []
    for kind, line in out_lines:
        if grouped and grouped[-1][0] == kind:
            grouped[-1][1].append(line)
        else:
            grouped.append((kind, [line]))

    result = []
    for kind, glines in grouped:
        chunk = "\n".join(glines)
        if kind == "fence":
            result.append(chunk)
            continue
        pieces = re.split(r"(`+[^`\n]*?`+)", chunk)
        out = []
        for piece in pieces:
            if piece.startswith("`"):
                out.append(piece)
                continue
            piece = piece.replace(r"\$", "DOLLARPHX")
            piece = re.sub(
                r"\$\$(.+?)\$\$",
                lambda m: "\n\n<div class=\"math-display\">" + math_placeholder(m[1].strip(), True) + "</div>\n\n",
                piece,
                flags=re.S,
            )
            piece = re.sub(
                r"(?<![\w$])\$([^$\n]+?)\$(?![\w$])",
                lambda m: math_placeholder(m[1], False),
                piece,
            )
            out.append(piece)
        result.append("".join(out))
    return "\n".join(result)


def restore_math(html):
    html = html.replace("DOLLARPHX", "$")
    return re.sub(
        r"MATHPH([0-9a-f]{16})X",
        lambda m: math_cache.get(m[1], math_ephemeral.get(m[1], m[0])),
        html,
    )


def _tex_to_plain(tex):
    """Convert simple inline TeX into readable plain Unicode text (for tooltips / aria-labels)."""
    s = tex.strip()
    s = re.sub(r"\\(?:text|mathrm|operatorname|mathbf|mathit)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    repls = [
        (r"\mid", "|"), (r"\|", "||"), (r"\times", "×"), (r"\cdot", "·"),
        (r"\approx", "≈"), (r"\le", "≤"), (r"\ge", "≥"), (r"\ne", "≠"),
        (r"\to", "→"), (r"\rightarrow", "→"), (r"\sum", "Σ"), (r"\prod", "Π"),
        (r"\nabla", "∇"), (r"\partial", "∂"), (r"\infty", "∞"),
        (r"\mu", "μ"), (r"\sigma", "σ"), (r"\alpha", "α"), (r"\beta", "β"),
        (r"\theta", "θ"), (r"\lambda", "λ"), (r"\pi", "π"), (r"\epsilon", "ε"),
        (r"\log", "log"), (r"\ln", "ln"), (r"\exp", "exp"), (r"\max", "max"),
        (r"\min", "min"), (r"\,", " "), (r"\;", " "), (r"\!", ""), (r"\ ", " "),
    ]
    for old, new in repls:
        s = s.replace(old, new)
    s = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", s)
    s = re.sub(r"_\{([^{}]+)\}", r"_\1", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def clean_plain_text(text):
    """Strip inline Markdown and convert TeX to clean plain Unicode text."""
    if not text:
        return ""
    s = str(text)
    s = re.sub(r"`([^`\n]+)`", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\$\$(.+?)\$\$", lambda m: _tex_to_plain(m.group(1)), s, flags=re.S)
    s = re.sub(r"(?<![\w$])\$([^$\n]+?)\$(?![\w$])", lambda m: _tex_to_plain(m.group(1)), s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- code highlighting
BUILTINS = {"print", "len", "range", "list", "dict", "set", "tuple", "int", "float", "str", "bool",
            "sorted", "sum", "max", "min", "enumerate", "zip", "open", "isinstance", "type", "abs",
            "round", "map", "filter", "any", "all", "reversed", "super", "input", "repr", "iter", "next",
            "format", "ord", "chr", "hex", "bin", "divmod", "pow", "vars", "getattr", "setattr", "hasattr"}
TOKEN = re.compile(r"""(?P<shell>^[ \t]*[!%].*$)|(?P<comment>\#[^\n]*)|(?P<string>(?:[rRbBfFuU]{1,2})?(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(?P<number>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)|(?P<deco>@[A-Za-z_][\w.]*)|(?P<name>[A-Za-z_]\w*)""", re.M)


def highlight_python(code):
    out, pos, prev_kw = [], 0, ""
    for m in TOKEN.finditer(code):
        out.append(escape(code[pos:m.start()]))
        kind, text = m.lastgroup, m[0]
        cls = None
        if kind == "name":
            if keyword.iskeyword(text) or text in {"self"}:
                cls = "kw" if text != "self" else "self"
            elif prev_kw in {"def", "class"}:
                cls = "fn"
            elif text in BUILTINS:
                cls = "bi"
            prev_kw = text
        else:
            cls = {"shell": "sh", "comment": "cm", "string": "st", "number": "nu", "deco": "de"}[kind]
            prev_kw = ""
        out.append(f'<span class="{cls}">{escape(text)}</span>' if cls else escape(text))
        pos = m.end()
    out.append(escape(code[pos:]))
    return "".join(out)


def highlight_shell(code):
    lines = []
    for line in code.split("\n"):
        if line.lstrip().startswith("#"):
            lines.append(f'<span class="cm">{escape(line)}</span>')
        else:
            lines.append(escape(line))
    return "\n".join(lines)


CODE_LABELS = {
    "python": "Python（Colabのセルに貼って実行）",
    "bash": "ターミナル（黒い画面）に入力",
    "sh": "ターミナル（黒い画面）に入力",
    "powershell": "PowerShell（Windows）に入力",
    "output": "出力",
    "output-example": "出力の例（数値や文章は実行ごとに変わってOK）",
    "text": "テキスト",
    "json": "JSON",
    "jsonl": "JSONL（1行に1件のJSON）",
    "html": "HTML",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "css": "CSS",
}


def render_fence(self, tokens, idx, options, env):
    token = tokens[idx]
    lang, flags, _ = parse_info(token.info)
    code = token.content.rstrip("\n")
    label = CODE_LABELS.get(lang, lang or "コード")
    if lang == "python" and "no-run" in flags:
        label = "Python（読むだけ・実行しなくてOK）"
    if lang == "python" and "gpu-only" in flags:
        label = "Python（GPUのランタイムで実行）"
    if lang == "python" and "online" in flags:
        label = "Python（Hugging Faceにつないで実行）"
    if lang == "python" and "colab-only" in flags:
        label = "Python（Colabで実行）"
    if lang == "python":
        body = highlight_python(code)
    elif lang in {"bash", "sh", "powershell"}:
        body = highlight_shell(code)
    else:
        body = escape(code)
    kind = "output" if lang.startswith("output") else "code"
    copy = '' if kind == "output" else '<button type="button" class="copy" aria-label="コードをコピー">コピー</button>'
    return (f'<div class="codeblock {kind} lang-{escape(lang or "plain")}"><div class="code-head"><span>{escape(label)}</span>{copy}</div>'
            f'<pre><code>{body}</code></pre></div>\n')


md = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
md.add_render_rule("fence", render_fence)

# ---------------------------------------------------------------- custom blocks
BLOCK_OPEN = re.compile(r"^:::([a-z][\w-]*)(?:\s+(.*))?$")
AVATARS = {"sensei": ("ボンゴ先生", "img/bongo.svg"), "minato": ("ミナト", "img/minato.svg")}
BOX = {
    "theory": ("理論の小部屋", "theory"),
    "try": ("やってみよう", "try"),
    "warn": ("つまずき注意", "warn"),
    "tip": ("コツ", "tip"),
    "goal": ("この章でつくるもの", "goal"),
    "recap": ("まとめ", "recap"),
    "math": ("数学の道具箱", "mathbox"),
    "python": ("Pythonの道具箱", "pybox"),
    "fe": ("基本情報とつながる", "fe"),
    "free": ("0円のコツ", "free"),
    "review-bridge": ("これまでの復習とつながり", "review-bridge"),
}
widget_pages = set()
EXERCISES_DIR = BOOK / "exercises"
EXERCISES_BY_CHAPTER = {}
EXERCISES_BY_ID = {}


def load_exercises():
    EXERCISES_BY_CHAPTER.clear()
    EXERCISES_BY_ID.clear()
    if not EXERCISES_DIR.exists():
        return
    for path in sorted(EXERCISES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = data.get("chapter") or path.stem
        items = data.get("exercises", [])
        EXERCISES_BY_CHAPTER[slug] = items
        for item in items:
            item.setdefault("chapter", slug)
            EXERCISES_BY_ID[item["id"]] = item


def render_inline_deferred(text):
    """Render inline markdown + math placeholders (restored in final HTML pass)."""
    if not text:
        return ""
    return md.renderInline(normalize_cjk_bold(protect_math(str(text))))


def render_inline_rich(text):
    """Render inline markdown + math (restored from cache on second pass before JSON serialization)."""
    if not text:
        return ""
    return restore_math(render_inline_deferred(text))


def render_exercise_payload(item):
    """Prepare a JSON-serializable copy of an exercise with KaTeX math placeholders rendered."""
    out = {
        "id": item["id"],
        "chapter": item["chapter"],
        "section": item.get("section", ""),
        "sectionAnchor": item.get("sectionAnchor", ""),
        "concept": item.get("concept", ""),
        "conceptLabel": item.get("conceptLabel", item.get("concept", "")),
        "level": int(item.get("level", 1)),
        "type": item.get("type", "choice"),
        "course": item.get("course", "all"),
        "reviewOf": item.get("reviewOf", []),
        "variants": [],
    }
    for v in item.get("variants", []):
        raw_hints = v.get("hints")
        if isinstance(raw_hints, list) and raw_hints:
            rendered_hints = [render_inline_rich(h) for h in raw_hints if str(h).strip()]
            hint_single = rendered_hints[0] if rendered_hints else render_inline_rich(v.get("hint", ""))
        else:
            hint_single = render_inline_rich(v.get("hint", ""))
            rendered_hints = [hint_single] if hint_single else []
        rv = {
            "prompt": render_inline_rich(v.get("prompt", "")),
            "hint": hint_single,
            "hints": rendered_hints,
            "reasoning": render_inline_rich(v.get("reasoning", "")),
            "steps": [render_inline_rich(s) for s in v.get("steps", [])],
            "altExample": render_inline_rich(v.get("altExample", "")),
        }
        if v.get("code"):
            rv["code"] = v["code"]
            rv["codeHtml"] = highlight_python(v["code"])
        if v.get("options"):
            rv["options"] = [
                {
                    "id": o["id"],
                    "text": render_inline_rich(o["text"]),
                    "wrongReason": render_inline_rich(o.get("wrongReason", "")),
                }
                for o in v["options"]
            ]
        if "answer" in v:
            rv["answer"] = v["answer"]
        if v.get("accept"):
            rv["accept"] = v["accept"]
        if v.get("placeholder"):
            rv["placeholder"] = v["placeholder"]
        if v.get("unit"):
            rv["unit"] = v["unit"]
        if v.get("starterCode"):
            rv["starterCode"] = v["starterCode"]
            rv["starterCodeHtml"] = highlight_python(v["starterCode"])
        if v.get("solutionCode"):
            rv["solutionCode"] = v["solutionCode"]
            rv["solutionCodeHtml"] = highlight_python(v["solutionCode"])
        if v.get("colabCheck"):
            rv["colabCheck"] = v["colabCheck"]
            rv["colabCheckHtml"] = highlight_python(v["colabCheck"])
        if v.get("modelAnswer"):
            rv["modelAnswer"] = render_inline_rich(v["modelAnswer"])
        if v.get("selfCheckCriteria"):
            rv["selfCheckCriteria"] = [render_inline_rich(c) for c in v["selfCheckCriteria"]]
        out["variants"].append(rv)
    return out


def split_blocks(text):
    """Find top-level ::: blocks outside code fences. Returns list of str | (name, arg, inner)."""
    lines = text.split("\n")
    out, buf, i = [], [], 0
    fence = None
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        m_f = re.match(r"^(`{3,})", stripped)
        if fence:
            if stripped == fence:
                fence = None
            buf.append(line)
            i += 1
            continue
        if m_f:
            fence = m_f[1]
            buf.append(line)
            i += 1
            continue
        m = BLOCK_OPEN.match(stripped)
        if m and m[1] != "answer":
            name, arg = m[1], (m[2] or "").strip()
            depth, j, inner, ifence = 1, i + 1, [], None
            while j < len(lines):
                s = lines[j].strip()
                f2 = re.match(r"^(`{3,})", s)
                if ifence:
                    if s == ifence:
                        ifence = None
                elif f2:
                    ifence = f2[1]
                elif BLOCK_OPEN.match(s) and BLOCK_OPEN.match(s)[1] != "answer":
                    depth += 1
                elif s == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                inner.append(lines[j])
                j += 1
            if depth:
                raise SystemExit(f"unclosed block :::{name} near: {line}")
            out.append("\n".join(buf))
            buf = []
            out.append((name, arg, "\n".join(inner)))
            i = j + 1
            continue
        buf.append(line)
        i += 1
    out.append("\n".join(buf))
    return out


def wrap_tables(html):
    """Wrap rendered <table>...</table> elements in a scrollable container for mobile & a11y."""
    return re.sub(
        r"(?<!<div class=\"table-wrap\">)(<table\b[^>]*>.*?</table>)",
        r'<div class="table-wrap">\1</div>',
        html,
        flags=re.S,
    )


def render_markdown(text, ctx):
    html_parts = {}
    pieces = []
    for piece in split_blocks(text):
        if isinstance(piece, str):
            pieces.append(normalize_cjk_bold(protect_math(piece)))
        else:
            key = f"BLOCKPH{len(html_parts)}X"
            html_parts[key] = render_block(*piece, ctx)
            pieces.append(f"\n\n<div>{key}</div>\n\n")
    html = md.render("\n".join(pieces))
    html = wrap_tables(html)
    for key, value in html_parts.items():
        html = html.replace(f"<div>{key}</div>", value)
    return html


def render_exercise_html(ex_id, ctx):
    item = EXERCISES_BY_ID.get(ex_id)
    if not item:
        raise SystemExit(f"unknown exercise id: {ex_id} in {ctx.get('slug')}")
    ctx["exercise"] = ctx.get("exercise", 0) + 1
    payload = render_exercise_payload(item)
    payload["num"] = ctx["exercise"]
    raw_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    v0 = payload["variants"][0] if payload["variants"] else {}
    noscript_prompt = v0.get("prompt", "")
    return (
        f'<section class="exercise" id="ex-{escape(ex_id)}" data-exercise-id="{escape(ex_id)}" '
        f'data-chapter="{escape(payload["chapter"])}" data-concept="{escape(payload["concept"])}" '
        f'data-level="{payload["level"]}" data-type="{escape(payload["type"])}" '
        f'data-course="{escape(payload["course"])}">'
        f'<script type="application/json" class="ex-data">{raw_json}</script>'
        f'<noscript><div class="ex-noscript"><p><b>確認問題 {ctx["exercise"]}</b>：{noscript_prompt}</p>'
        f'<p>自動採点・ヒント・解説の表示にはJavaScriptを有効にしてください。</p></div></noscript>'
        f'</section>\n'
    )


def render_block(name, arg, inner, ctx):
    if name in AVATARS:
        who, img = AVATARS[name]
        return (f'<div class="talk talk-{name}"><img class="avatar" src="{img}" alt="" width="56" height="56">'
                f'<div class="bubble"><p class="who">{who}</p>{render_markdown(inner, ctx)}</div></div>\n')
    if name == "quiz":
        question, _, answer = inner.partition("\n:::answer\n")
        if not answer:
            raise SystemExit(f"quiz without :::answer: {arg}")
        ctx["quiz"] += 1
        qtitle = "：" + render_inline_deferred(arg) if arg else ""
        return (f'<section class="quiz"><p class="quiz-label">クイズ {ctx["quiz"]}{qtitle}</p>'
                f'{render_markdown(question, ctx)}<details><summary>答えを見る（まず自分で考えてから！）</summary>'
                f'{render_markdown(answer, ctx)}</details></section>\n')
    if name == "exercise":
        ids = [tok.strip() for tok in (arg + " " + inner).replace(",", " ").split() if tok.strip()]
        if not ids:
            raise SystemExit(f"empty :::exercise block in {ctx.get('slug')}")
        return "".join(render_exercise_html(eid, ctx) for eid in ids)
    if name == "scaffold":
        stitle = render_inline_deferred(arg or "じっくり確認しよう")
        return (f'<details class="scaffold" open><summary><span class="sc-badge">基礎の補足</span>{stitle}</summary>'
                f'<div class="scaffold-body">{render_markdown(inner, ctx)}</div></details>\n')
    if name == "deep":
        dtitle = render_inline_deferred(arg)
        return (f'<details class="deep"><summary><span>もっと深く</span>{dtitle}</summary>'
                f'{render_markdown(inner, ctx)}</details>\n')
    if name == "checklist":
        items = [l[2:].strip() for l in inner.strip().split("\n") if l.startswith("- ")]
        lis = "".join(f'<li><label><input type="checkbox" data-check="{ctx["slug"]}:{n}"> <span>{render_inline_deferred(t)}</span></label></li>'
                      for n, t in enumerate(items))
        return f'<section class="checklist"><p class="box-title">できたらチェック</p><ul>{lis}</ul></section>\n'
    if name == "widget":
        widget_pages.add(ctx["slug"])
        wname, _, mode = arg.partition(" ")
        mode_attr = f' data-mode="{escape(mode)}"' if mode else ""
        return f'<div class="widget" data-widget="{escape(wname)}"{mode_attr}><noscript>このデモはJavaScriptを有効にすると動きます。</noscript></div>\n'
    if name in BOX:
        title, cls = BOX[name]
        heading_html = f'{title}{"：" + render_inline_deferred(arg) if arg else ""}'
        aria_label = f'{title}{"：" + clean_plain_text(arg) if arg else ""}'
        return (f'<div class="box box-{cls}" role="note" aria-label="{escape(aria_label, quote=True)}">'
                f'<p class="box-title">{heading_html}</p>{render_markdown(inner, ctx)}</div>\n')
    raise SystemExit(f"unknown block :::{name}")


# ---------------------------------------------------------------- glossary
GLOSSARY = json.loads((BOOK / "glossary.json").read_text(encoding="utf-8")) if (BOOK / "glossary.json").exists() else []
CHAPTER_ORDER = [s for p in CUR["parts"] for s in p["chapters"]]


def term_id(term):
    return "t-" + hashlib.sha1(term["term"].encode()).hexdigest()[:8]


def link_terms(html, slug):
    """Link the first use of glossary terms learned in earlier chapters (a memory aid)."""
    if slug not in CHAPTER_ORDER:
        return html
    here = CHAPTER_ORDER.index(slug)
    learned = [t for t in GLOSSARY if t.get("chapter") in CHAPTER_ORDER and CHAPTER_ORDER.index(t["chapter"]) < here]
    learned.sort(key=lambda t: -len(t["term"]))
    done = set()
    parts = re.split(r"(<[^>]+>)", html)
    skip = 0
    skip_tags = {"pre", "code", "a", "h1", "h2", "h3", "summary", "button", "label", "script", "style", "span", "math", "svg"}
    for i, part in enumerate(parts):
        if part.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", part)
            if m and not part.endswith("/>") and m[2].lower() not in {"br", "img", "input", "hr", "meta", "link"}:
                tag = m[2].lower()
                if m[1]:
                    if tag in skip_tags and skip:
                        skip -= 1
                else:
                    if tag in skip_tags:
                        skip += 1
            continue
        if skip or not part.strip():
            continue
        for t in learned:
            if t["term"] in done:
                continue
            idx = part.find(t["term"])
            if idx >= 0:
                done.add(t["term"])
                tip = escape(clean_plain_text(t["def"]), quote=True)
                part = (part[:idx] + f'<a class="term" href="f-glossary.html#{term_id(t)}" data-tip="{tip}">{t["term"]}</a>'
                        + part[idx + len(t["term"]):])
                break  # one link per text node keeps the HTML simple
        parts[i] = part
    return "".join(parts)


# ---------------------------------------------------------------- page shell
def nav_html(active):
    out = ['<nav class="chapters" aria-label="全章の目次">']
    for part in CUR["parts"]:
        is_open = active in part["chapters"] or active == "index"
        out.append(f'<details class="nav-part" {"open" if is_open else ""}><summary>{escape(part["title"])}</summary><ol>')
        for slug in part["chapters"]:
            meta = META[slug]
            cur = ' aria-current="page"' if slug == active else ""
            out.append(f'<li><a href="{slug}.html"{cur} data-slug="{slug}"><span class="num">{meta["num"]}</span>{escape(meta["short"])}</a></li>')
        out.append("</ol></details>")
    out.append('<details class="nav-part" open><summary>付録</summary><ol>')
    for slug in CUR["appendix"]:
        cur = ' aria-current="page"' if slug == active else ""
        out.append(f'<li><a href="{slug}.html"{cur}><span class="num">{slug[0].upper()}</span>{escape(META[slug]["short"])}</a></li>')
    out.append("</ol></details></nav>")
    return "".join(out)


def page(title, body, active="index", toc="", description=None):
    desc = description or f"{SITE_TITLE}：{CUR['subtitle']}。初日からLLMを動かし、理論は必要になった瞬間に学ぶ、無料で始められる日本語の教科書。"
    full_title = SITE_TITLE if title == SITE_TITLE else f"{title} | {SITE_TITLE}"
    widgets = '<script src="widgets.js" defer></script>' if active in widget_pages or active == "index" else ""
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(full_title)}</title><meta name="description" content="{escape(desc)}">
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#23443b">
<script>try{{const t=localStorage.getItem("tsukuru-llm-theme");if(t)document.documentElement.dataset.theme=t;const c=localStorage.getItem("tsukuru-llm-course")||"thorough";document.documentElement.dataset.course=c;}}catch(e){{}}</script>
<link rel="icon" href="img/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="katex/katex.min.css"><link rel="stylesheet" href="style.css">
<script src="app.js" defer></script><script src="study.js" defer></script>{widgets}</head>
<body data-page="{escape(active)}"><a class="skip" href="#main">本文へ移動</a>
<header class="topbar"><button type="button" class="menu-btn" id="menu" aria-expanded="false" aria-controls="sidebar" aria-label="目次を開く"><span></span><span></span><span></span></button>
<a class="brand" href="index.html"><img src="img/logo.svg" alt="" width="36" height="36"><span><b>{escape(SITE_TITLE)}</b><small>ボンゴ先生のLLM教室</small></span></a>
<nav class="topnav" aria-label="主なページ"><a href="index.html#map">目次</a><a href="review.html" class="nav-review">学習・復習<span class="due-badge" data-due-badge hidden>0</span></a><a href="a-setup.html">環境構築</a><a href="e-errors.html">エラー辞典</a><a href="f-glossary.html">用語集</a></nav>
<button id="theme" class="icon-btn" type="button" aria-label="明るさを切り替える" title="明るさを切り替える">◐</button></header>
<div class="layout"><aside id="sidebar" class="sidebar" aria-label="目次"><div class="search"><label for="search">教科書の中を探す</label><input id="search" type="search" placeholder="例：softmax、LoRA、GPU" autocomplete="off"><div id="results" aria-live="polite"></div></div>
<div class="course-switch" role="group" aria-label="学習コースの切り替え"><span class="cs-label">学習コース</span><div class="cs-btns"><button type="button" data-set-course="thorough" aria-pressed="true">じっくり理解</button><button type="button" data-set-course="standard" aria-pressed="false">標準</button></div><a class="sidebar-review-link" href="review.html">📊 学習状況・今日の復習 <span class="due-badge" data-due-badge hidden>0</span></a></div>
<div class="progress-box" data-progress hidden><span class="bar"><span></span></span><small></small></div>{nav_html(active)}</aside>
<main id="main" tabindex="-1">{body}
<footer class="site-footer"><p><b>{escape(SITE_TITLE)}</b> ── “What I cannot create, I do not understand.”（作れないものは、理解していない）── R. P. Feynman</p>
<p>本文・コード・サイトは学習者のためにAI支援で作成・改修し、検証範囲を明示しています。<a href="about.html">この教室について</a> · <a href="review.html">学習状況・復習</a> · <a href="j-references.html">参考文献</a> · <a href="https://github.com/{REPO}">GitHub</a></p></footer></main>{toc}</div></body></html>'''


# ---------------------------------------------------------------- chapters
def stars(n):
    n = int(n)
    return "★" * n + "☆" * (5 - n)


ENV_LABEL = {
    "none": "ブラウザで読むだけ",
    "cpu": "Google Colab（CPUでOK）",
    "gpu": "Google Colab（GPU：T4）",
    "any": "Colab・ローカルどちらでも",
}


def _strip_html_for_text(html_frag):
    """Strip HTML tags/scripts/KaTeX MathML duplicates to clean searchable plain text."""
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_frag, flags=re.S)
    s = re.sub(r"<span class=\"katex-html\"[^>]*>.*?</span>", " ", s, flags=re.S)
    s = re.sub(r"<pre\b[^>]*>.*?</pre>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
    return re.sub(r"\s+", " ", s).strip()


def add_heading_ids(html):
    """Add id="s1".."sN" to <h2> and id="s1-1".. to <h3>; return (html, h2_toc, all_sections)."""
    toc = []
    h2_count = 0
    h3_count = 0
    headings = []

    def repl(m):
        nonlocal h2_count, h3_count
        lvl = int(m.group(1))
        inner = m.group(2)
        text = clean_plain_text(_strip_html_for_text(restore_math(inner)))
        if lvl == 2:
            h2_count += 1
            h3_count = 0
            hid = f"s{h2_count}"
            toc.append((h2_count, text))
        else:
            h3_count += 1
            hid = f"s{h2_count}-{h3_count}"
        headings.append((hid, text))
        return f'<h{lvl} id="{hid}">{inner}</h{lvl}>'

    html = re.sub(r"<h([23])>(.*?)</h\1>", repl, html, flags=re.S)
    return html, toc, headings


def extract_sections_from_html(article_body_html):
    """Split rendered article body HTML by h2/h3 IDs into [{id, head, text}]."""
    matches = list(re.finditer(r'<h[23] id="(s\d+(?:-\d+)?)">(.*?)</h[23]>', article_body_html, flags=re.S))
    sections = []
    for idx, m in enumerate(matches):
        sec_id = m.group(1)
        head = _strip_html_for_text(m.group(2))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(article_body_html)
        body_text = _strip_html_for_text(article_body_html[start:end])
        sections.append({"id": sec_id, "head": head, "text": body_text})
    return sections


def toc_html(toc):
    if not toc:
        return ""
    links = "".join(f'<a href="#s{n}">{escape(t)}</a>' for n, t in toc)
    return f'<aside class="toc" aria-label="このページの見出し"><p>このページ</p>{links}<a class="toc-top" href="#main">↑ 先頭へ</a></aside>'


META = {}
SOURCES = {}
PAGE_BODY_HTML = {}
for part in CUR["parts"]:
    for slug in part["chapters"]:
        meta, body = read_source(BOOK / "chapters" / f"{slug}.md")
        meta.update(slug=slug, part=part["title"], num=str(int(slug[:2])))
        meta.setdefault("short", meta["title"])
        META[slug], SOURCES[slug] = meta, body
for slug in CUR["appendix"] + CUR.get("extra", []):
    meta, body = read_source(BOOK / "appendix" / f"{slug}.md")
    meta.update(slug=slug)
    meta.setdefault("short", meta["title"])
    META[slug], SOURCES[slug] = meta, body


def colab_url(slug):
    return f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{slug}.ipynb"


def chapter_page(slug, prev_slug, next_slug):
    meta, body = META[slug], SOURCES[slug]
    ctx = {"slug": slug, "quiz": 0, "exercise": 0}
    html = render_markdown(body, ctx)
    html, toc, _ = add_heading_ids(html)
    PAGE_BODY_HTML[slug] = html
    has_code = bool(cells(body))
    actions = ""
    if has_code:
        actions = (f'<div class="chapter-actions"><a class="btn primary" href="{colab_url(slug)}" target="_blank" rel="noopener">Colabで開く（完成ノート）</a>'
                   f'<a class="btn" href="notebooks/{slug}.ipynb" download>ノートブックをダウンロード</a></div>'
                   '<p class="hint">おすすめは「ページを読みながら、コードを自分のノートブックに1セルずつ貼って実行」。完成ノートは困ったときの答え合わせ用です。</p>')
    learn = ""
    rows = []
    if meta.get("builds"):
        rows.append(f'<div><h2 class="learn-head">つくるもの</h2><p>{render_inline_deferred(meta["builds"])}</p></div>')
    if meta.get("theory"):
        rows.append('<div><h2 class="learn-head">身につく数学・理論</h2><ul>' + "".join(f"<li>{render_inline_deferred(t)}</li>" for t in meta["theory"]) + "</ul></div>")
    if meta.get("python"):
        rows.append('<div><h2 class="learn-head">新しく使うPython・PyTorch</h2><ul>' + "".join(f"<li>{render_inline_deferred(t)}</li>" for t in meta["python"]) + "</ul></div>")
    if rows:
        learn = f'<section class="learn-grid" aria-label="この章の目標">{"".join(rows)}</section>'
    ex_count = ctx["exercise"]
    mastery_strip = (
        f'<section class="mastery-strip" data-mastery-chapter="{slug}" data-exercise-count="{ex_count}" aria-label="この章の学習状況">'
        f'<div class="ms-row"><span class="ms-stage" data-ms-stage>未学習</span>'
        f'<span class="ms-detail" data-ms-detail>演習 {ex_count} 問 · 途中の確認問題と復習で定着を確かめられます</span>'
        f'<a class="ms-link" href="review.html">学習状況・復習へ →</a></div>'
        f'</section>'
    )
    kicker = f'{escape(meta["part"])} · 第{meta["num"]}章'
    hero = (f'<header class="chapter-hero"><p class="kicker">{kicker}</p><h1>{escape(meta["title"])}</h1>'
            f'<p class="sub">{escape(meta.get("subtitle", ""))}</p><dl class="meta">'
            f'<div><dt>目安</dt><dd>{escape(meta.get("time", ""))}</dd></div>'
            f'<div><dt>環境</dt><dd>{escape(ENV_LABEL.get(meta.get("env", "cpu"), meta.get("env", "")))}</dd></div>'
            f'<div><dt>難しさ</dt><dd aria-label="5段階中{meta.get("level", 1)}">{stars(meta.get("level", 1))}</dd></div>'
            f'<div><dt>確認問題</dt><dd>{ex_count}問</dd></div></dl>{actions}</header>')
    done = (f'<section class="chapter-done"><button type="button" class="btn primary" data-done="{slug}">この章の説明を読み終えた！</button>'
            '<p>説明の読了チェックです（ブラウザ内にのみ保存）。「理解・定着」は途中の確認問題・自力実装・間隔復習の結果と合わせて記録されます。</p></section>')
    pager = '<nav class="pager" aria-label="前後の章">'
    if prev_slug:
        pager += f'<a href="{prev_slug}.html"><small>← 前の章</small>{escape(META[prev_slug]["title"])}</a>'
    if next_slug:
        pager += f'<a class="next" href="{next_slug}.html"><small>次の章 →</small>{escape(META[next_slug]["title"])}</a>'
    pager += "</nav>"
    article = f'<article class="chapter">{hero}{learn}{mastery_strip}{link_terms(html, slug)}{done}{pager}</article>'
    return page(meta["title"], article, slug, toc_html(toc), meta.get("subtitle"))


def appendix_page(slug):
    meta, body = META[slug], SOURCES[slug]
    if slug == "f-glossary":
        body = body.replace("<!-- GLOSSARY -->", glossary_markdown())
    if slug == "i-simulation":
        body = body.replace("<!-- PERSONA_TABLE -->", persona_table()).replace("<!-- CODE_REPORT -->", code_report_table())
    ctx = {"slug": slug, "quiz": 0}
    html = render_markdown(body, ctx)
    html, toc, _ = add_heading_ids(html)
    PAGE_BODY_HTML[slug] = html
    label = f"付録{slug[0].upper()}" if slug in CUR["appendix"] else ""
    hero = (f'<header class="chapter-hero appendix"><p class="kicker">{label}</p><h1>{escape(meta["title"])}</h1>'
            f'<p class="sub">{escape(meta.get("subtitle", ""))}</p></header>')
    return page(meta["title"], f'<article class="chapter">{hero}{html}</article>', slug, toc_html(toc), meta.get("subtitle"))


KANA_ROWS = ["あいうえおぁぃぅぇぉ", "かきくけこがぎぐげご", "さしすせそざじずぜぞ", "たちつてとだぢづでどっ",
             "なにぬねの", "はひふへほばびぶべぼぱぴぷぺぽ", "まみむめも", "やゆよゃゅょ", "らりるれろ", "わをん"]


def kana_row(reading):
    ch = reading[:1]
    if "ァ" <= ch <= "ヶ":
        ch = chr(ord(ch) - 0x60)              # カタカナをひらがなに
    for row in KANA_ROWS:
        if ch in row:
            return row[0] + "行"
    return "その他"


def glossary_markdown():
    groups = {}
    for t in sorted(GLOSSARY, key=lambda t: t.get("reading", t["term"])):
        groups.setdefault(kana_row(t.get("reading", t["term"])), []).append(t)
    order = [r[0] + "行" for r in KANA_ROWS] + ["その他"]
    out = []
    for head in [h for h in order if h in groups]:
        out.append(f"\n## {head}\n")
        out.append('<dl class="glossary">')
        for t in groups[head]:
            where = f' <a class="where" href="{t["chapter"]}.html">第{int(t["chapter"][:2])}章で登場</a>' if t.get("chapter") in META else ""
            en = f' <span class="en">{escape(t["en"])}</span>' if t.get("en") else ""
            out.append(f'<dt id="{term_id(t)}">{escape(t["term"])}{en}{where}</dt><dd>{render_inline_deferred(t["def"])}</dd>')
        out.append("</dl>\n")
    return "\n".join(out)


# ---------------------------------------------------------------- simulation report tables
def persona_table():
    path = ROOT / "verification" / "persona-metrics.json"
    if not path.exists():
        return "（`python tools/persona.py` を実行すると、ここに表が入ります）"
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = ["| 章 | 難しさ | 新しい用語 | 新しいPython | コードのセル | 会話 | クイズ | 実出力・図 | 最長の地の文（字） | 読むだけの時間（分） | 未習の先取り |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in data["chapters"]:
        early = len(r["early_terms"]) + len(r["early_python"])
        rows.append(f"| {int(r['slug'][:2])} | {'★' * (r['level'] or 1)} | {r['new_terms']} | {len(r['new_python'])} | {r['cells']} | {r['talks']} | {r['quizzes']} | "
                    f"{r['outputs'] + r['figures']} | {r['longest_prose_chars']} | {r['est_minutes']} | {early} |")
    rows.append("")
    rows.append("「読むだけの時間」は、文字数とセルの数から機械的に見積もった、読んでセルを実行するだけの時間です。"
                "考えたり、学習を待ったり、つまずいたりする時間は入っていないので、実際には各章の冒頭にある「所要時間」くらいかかります。")
    rows.append("")
    rows.append(f"機械チェックで残っている問題：**{len(data['issues'])}件**" + ("" if not data["issues"] else "（" + "、".join(data["issues"]) + "）"))
    return "\n".join(rows)


def code_report_table():
    path = ROOT / "verification" / "code-report.json"
    if not path.exists():
        return "（`python tools/verify.py` を実行すると、ここに表が入ります）"
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [f"検証日：{data['date']}　Python {data['python']}　PyTorch {data.get('torch', '?')}　transformers {data.get('transformers', '?')}", "",
            "| 章 | セル | 実行した | GPU・オンライン専用で飛ばした | 結果 |", "|---|---|---|---|---|"]
    for c in data["chapters"]:
        ok = "合格" if not c["failures"] else f"要確認（{len(c['failures'])}）"
        rows.append(f"| {int(c['slug'][:2])} | {c['cells']} | {c['cells'] - c.get('skipped', 0)} | {c.get('skipped', 0)} | {ok} |")
    rows.append("")
    rows.append(f"HTMLページ {data.get('html_pages', '?')} 枚のリンク切れ：{len(data.get('link_failures', []))}件")
    return "\n".join(rows)


# ---------------------------------------------------------------- home
def home_page():
    parts_html = []
    for i, part in enumerate(CUR["parts"]):
        items = []
        for slug in part["chapters"]:
            m = META[slug]
            items.append(f'<li><a href="{slug}.html" data-slug="{slug}"><span class="num">{m["num"]}</span><span class="t">{escape(m["title"])}</span>'
                         f'<small>{escape(m.get("subtitle", ""))}</small><span class="tags"><em>{escape(m.get("time", ""))}</em>'
                         f'<em>{escape(ENV_LABEL.get(m.get("env", "cpu"), ""))}</em></span></a></li>')
        lead = f'<p>{escape(part.get("lead", ""))}</p>' if part.get("lead") else ""
        parts_html.append(f'<section class="map-part"><h3>{escape(part["title"])}</h3>{lead}<ol>{"".join(items)}</ol></section>')
    appendix = "".join(f'<li><a href="{s}.html"><span class="num">{s[0].upper()}</span>{escape(META[s]["title"])}</a></li>' for s in CUR["appendix"])
    body = (BOOK / "home.html").read_text(encoding="utf-8")
    body = body.replace("<!-- MAP -->", "".join(parts_html)).replace("<!-- APPENDIX -->", appendix)
    body = body.replace("<!-- COUNT -->", str(len(CHAPTER_ORDER)))
    return page(SITE_TITLE, body, "index")


# ---------------------------------------------------------------- notebooks
NB_BLOCK_TITLES = {
    "goal": "🎯 この章でつくるもの",
    "review-bridge": "🔗 これまでの復習とつながり",
    "math": "📐 数学のポイント",
    "theory": "💡 理論のポイント",
    "python": "🐍 Python・PyTorchのポイント",
    "warn": "⚠️ つまずき注意",
    "tip": "✨ コツ",
    "try": "🔬 やってみよう",
    "fe": "📘 基本情報とのつながり",
    "free": "¥0 無料枠のコツ",
    "recap": "📝 まとめ",
}


def _rewrite_nb_links(text):
    """Rewrite relative chapter/appendix HTML links to absolute site URLs inside Colab notebooks."""
    site = CUR["site"]
    text = re.sub(r"\]\(([0-9a-z-]+\.html(?:#[^)]+)?)\)", rf"]({site}\1)", text)
    text = re.sub(r"\]\((img/[^)]+)\)", rf"]({site}\1)", text)
    return text


def _block_to_nb_markdown(name, arg, inner, slug):
    """Convert a custom :::block into clean, standalone Colab Markdown with zero ::: directives."""
    inner = _rewrite_nb_links(inner.strip())
    if name in AVATARS:
        who, _ = AVATARS[name]
        body = _strip_nested_blocks_to_nb(inner, slug)
        return f"**{who}**：{body}"
    if name == "widget":
        return f"*(対話デモはWeb教科書ページで確認できます：{CUR['site']}{slug}.html)*"
    if name == "quiz":
        q, _, a = inner.partition("\n:::answer\n")
        q_md = _strip_nested_blocks_to_nb(q.strip(), slug)
        a_md = _strip_nested_blocks_to_nb(a.strip(), slug)
        title = f"：{arg}" if arg else ""
        return f"**❓ クイズ{title}**\n\n{q_md}\n\n<details><summary>答えを見る（まず自分で考えてから！）</summary>\n\n{a_md}\n\n</details>"
    if name == "exercise":
        ids = [tok.strip() for tok in (arg + " " + inner).replace(",", " ").split() if tok.strip()]
        return _exercises_to_nb_markdown(ids, slug)
    if name in {"scaffold", "deep"}:
        label = "基礎の補足" if name == "scaffold" else "もっと深く"
        title = f"：{arg}" if arg else ""
        body = _strip_nested_blocks_to_nb(inner, slug)
        return f"<details><summary><b>{label}{title}</b>（クリックで開く）</summary>\n\n{body}\n\n</details>"
    if name == "checklist":
        items = [l[2:].strip() for l in inner.split("\n") if l.startswith("- ")]
        lines = ["**✅ できたらチェック**", ""] + [f"- [ ] {it}" for it in items]
        return "\n".join(lines)
    if name in NB_BLOCK_TITLES:
        label = NB_BLOCK_TITLES[name]
        title = f"：{arg}" if arg else ""
        body = _strip_nested_blocks_to_nb(inner, slug)
        # Keep math/scaffold-rich blocks readable without overly nested blockquotes
        if "```" in body or "\n|" in body or len(body) > 900:
            return f"#### {label}{title}\n\n{body}"
        quoted = "\n".join(("> " + l if l.strip() else ">") for l in body.split("\n"))
        return f"> **{label}{title}**\n>\n{quoted}"
    return _strip_nested_blocks_to_nb(inner, slug)


def _strip_nested_blocks_to_nb(text, slug):
    """Recursively render any nested :::blocks inside a block into clean Markdown."""
    parts = []
    for piece in split_blocks(text):
        if isinstance(piece, str):
            if piece.strip():
                parts.append(_rewrite_nb_links(piece.strip()))
        else:
            rendered = _block_to_nb_markdown(*piece, slug)
            if rendered:
                parts.append(rendered)
    return "\n\n".join(parts)


def _exercises_to_nb_markdown(ex_ids, slug):
    """Render selected chapter exercises as collapsible Colab self-check cards."""
    site = CUR["site"]
    cards = []
    # Include up to 2 exercises per inline :::exercise group to keep notebooks concise & readable
    shown = ex_ids[:2]
    for eid in shown:
        item = EXERCISES_BY_ID.get(eid)
        if not item or not item.get("variants"):
            continue
        v = item["variants"][0]
        t = item.get("type", "choice")
        lvl = item.get("level", 1)
        lines = [f"#### 📝 確認問題（`{eid}` · Lv.{lvl} · {item.get('conceptLabel', '')}）", ""]
        lines.append(v.get("prompt", ""))
        if v.get("code"):
            lines.extend(["", "```python", v["code"].rstrip(), "```"])
        if v.get("starterCode"):
            lines.extend(["", "**ひな形コード：**", "```python", v["starterCode"].rstrip(), "```"])
        if v.get("options"):
            lines.append("")
            for o in v["options"]:
                lines.append(f"- **{o['id']}.** {o['text']}")
        # Collapsible hints + answer + explanation
        ans_lines = []
        raw_hints = v.get("hints") if isinstance(v.get("hints"), list) and v.get("hints") else ([v["hint"]] if v.get("hint") else [])
        for hi, htxt in enumerate(raw_hints, 1):
            ans_lines.append(f"- **ヒント {hi}**：{htxt}")
        if t == "choice":
            ans_lines.append(f"- **正解**：`{v.get('answer')}`")
        elif t == "numeric":
            ans_val = v.get("answer", {}).get("value", "")
            unit = v.get("unit", "")
            ans_lines.append(f"- **正解**：`{ans_val}` {unit}".strip())
        elif t == "predict":
            acc = v.get("accept", [])
            ans_lines.append(f"- **期待される出力**：`{acc[0] if acc else ''}`")
        elif t == "code" and v.get("solutionCode"):
            ans_lines.extend(["", "**解答例：**", "```python", v["solutionCode"].rstrip(), "```"])
            if v.get("colabCheck"):
                ans_lines.extend(["", "**検算テスト（Colabで実行して確認）：**", "```python", v["colabCheck"].rstrip(), "```"])
        elif t == "explain" and v.get("modelAnswer"):
            ans_lines.append(f"- **解答の目安**：{v['modelAnswer']}")
        if v.get("reasoning"):
            ans_lines.extend(["", f"**考え方**：{v['reasoning']}"])
        if v.get("steps"):
            ans_lines.append("")
            for st in v["steps"]:
                ans_lines.append(f"1. {st}")
        ans_lines.append("")
        ans_lines.append(f"👉 自動採点・類題・間隔復習はWebページへ：{site}{slug}.html#ex-{eid}")
        lines.extend(["", "<details><summary>ヒント / 解答と解説を見る</summary>", "", "\n".join(ans_lines), "", "</details>"])
        cards.append("\n".join(lines))
    if len(ex_ids) > len(shown):
        more = ", ".join(f"`{e}`" for e in ex_ids[len(shown):])
        cards.append(f"*(この節の追加問題 {more} はWeb教科書 {site}{slug}.html で自動採点・復習できます)*")
    return "\n\n".join(cards)


def _to_source_lines(text):
    """Split text into standard nbformat source line list (preserving newlines cleanly)."""
    text = text.rstrip("\n")
    if not text:
        return []
    parts = text.split("\n")
    return [l + "\n" for l in parts[:-1]] + [parts[-1]]


def _pre_run_prompt(code, flags):
    """Generate a concise pre-run prediction & flag guidance note before a code cell."""
    notes = []
    if "gpu-only" in flags:
        notes.append("⚠️ **GPU専用セル（T4等）**：ランタイムがGPUであることを確認してから実行してください。")
    if "online" in flags:
        notes.append("🌐 **オンライン接続セル**：Hugging Faceへの接続（必要に応じてトークン設定）が必要です。")
    if "colab-only" in flags:
        notes.append("☁️ **Google Colab専用セル**：ローカルPC・Kaggleでは不要または代替手順を使います。")
    if "BitsAndBytesConfig" in code or "load_in_4bit" in code:
        notes.append("🔄 **実行前注意**：前のセルで読み込んだモデルがGPUメモリに残っていると不足することがあります。必要に応じて「ランタイム」→「セッションを再起動する」を行ってから実行してください。")
    if "print(" in code or ".shape" in code or "plt." in code:
        notes.append("🔎 **実行前に予想しよう**：このセルを実行すると、どんな数値・文字列・テンソルの形（shape）やグラフが出るか予想してから ▶ を押してください。")
    elif "!pip install" in code or "!wget" in code:
        notes.append("📦 **準備セル**：ライブラリや教材ファイルを取得します。エラーが出た場合は `-q` を外して詳細を確認してください。")
    else:
        notes.append("🔎 **実行前に確認**：コードの各行が何を受け取り、何を作るか確認してから ▶ を押してください。")
    return "\n\n".join(notes)


def make_notebook(slug, next_slug=None):
    """Build a standalone, pedagogically complete nbformat 4.5 Colab notebook for a chapter."""
    meta, body = META[slug], SOURCES[slug]
    site = CUR["site"]
    env = meta.get("env", "cpu")
    env_label = ENV_LABEL.get(env, env)

    # Cell 0: Rich Chapter Header + Environment & Resource Card
    header_lines = [
        f"# 第{meta['num']}章 {meta['title']}",
        "",
        meta.get("subtitle", ""),
        "",
        "## このノートブックの使い方・学習目標",
        "",
        f"- **教科書のWebページ**：{site}{slug}.html",
        f"- **エラーが出たとき**：[エラー辞典（付録E）]({site}e-errors.html)",
        f"- **復習・理解度管理**：[学習状況・間隔復習ダッシュボード]({site}review.html)",
    ]
    if meta.get("builds"):
        header_lines.append(f"- **この章でつくるもの**：{meta['builds']}")
    if meta.get("theory"):
        header_lines.append("- **身につく数学・理論**：" + " ／ ".join(meta["theory"]))
    if meta.get("python"):
        header_lines.append("- **新しく使うPython・PyTorch**：" + " ／ ".join(meta["python"]))
    header_lines.extend([
        "",
        "## 実行環境・リソースの目安",
        "",
        "| 項目 | 目安 |",
        "|---|---|",
        f"| 推奨ランタイム | {env_label} |",
        f"| 所要時間目安 | {meta.get('time', '—')} |",
        f"| 難易度 | {stars(meta.get('level', 1))} |",
    ])
    if env == "gpu":
        header_lines.extend([
            "",
            "> **⚠️ GPUランタイム設定**：メニューの「ランタイム」→「ランタイムのタイプを変更」→「**T4 GPU**」を選んでから上から順に実行してください。",
            "> 無料枠の混雑・上限でGPUに接続できない場合は、時間をおくか [Kaggle Notebooks]({0}a-setup.html) を使うか、各章のCPU短縮手順で進められます。接続切断に備え、学習済みモデルはこまめにGoogleドライブへ保存しましょう。".format(site),
        ])
    else:
        header_lines.extend([
            "",
            "> **✅ CPUでそのまま実行できます**：上のセルから順に再生ボタン（▶）または `Shift + Enter` で実行してください。",
        ])

    raw_cells = [("markdown", "\n".join(header_lines))]

    # Walk top-level pieces (blocks & prose+fences) in document order
    md_buf = []

    def flush_md():
        text = "\n\n".join(p.strip() for p in md_buf if p and p.strip()).strip()
        md_buf.clear()
        if text:
            raw_cells.append(("markdown", text))

    def emit_prose_and_fences(chunk):
        lines = chunk.split("\n")
        i = 0
        text_acc = []

        def flush_text_acc():
            t = "\n".join(text_acc).strip()
            text_acc.clear()
            if t:
                md_buf.append(_rewrite_nb_links(t))

        while i < len(lines):
            s = lines[i].strip()
            mf = re.match(r"^(`{3,})(.*)$", s)
            if mf:
                ticks, info = mf.groups()
                j = i + 1
                while j < len(lines) and lines[j].strip() != ticks:
                    j += 1
                code = "\n".join(lines[i + 1:j])
                lang, flags, _ = parse_info(info)
                i = j + 1

                if lang == "python" and "no-run" not in flags:
                    flush_text_acc()
                    md_buf.append(_pre_run_prompt(code, flags))
                    flush_md()
                    raw_cells.append(("code", code))
                elif lang in {"output", "output-example"}:
                    flush_text_acc()
                    label = "期待される出力（実測）" if lang == "output" else "出力の例（数値や文章は実行ごとに変わってOK）"
                    snippet = code.strip()
                    if len(snippet.splitlines()) > 18:
                        snippet = "\n".join(snippet.splitlines()[:18]) + "\n...（省略）"
                    md_buf.append(
                        f"<details><summary><b>📊 {label}</b>（実行後に自分の出力と見比べよう）</summary>\n\n```text\n{snippet}\n```\n\n</details>"
                    )
                else:
                    # Keep illustrative no-run / bash / text / json fences inside markdown prose
                    show_lang = lang or "text"
                    text_acc.append(f"```{show_lang}\n{code}\n```")
                continue
            text_acc.append(lines[i])
            i += 1
        flush_text_acc()

    def walk_pieces(text):
        for piece in split_blocks(text):
            if isinstance(piece, str):
                emit_prose_and_fences(piece)
            else:
                name, arg, inner = piece
                if name != "exercise" and cells(inner):
                    # Preserve executable code cells inside :::try / :::tip / :::scaffold / etc. as real code cells
                    if name in AVATARS:
                        who, _ = AVATARS[name]
                        md_buf.append(f"**{who}**")
                    elif name in NB_BLOCK_TITLES:
                        label = NB_BLOCK_TITLES[name]
                        title = f"：{arg}" if arg else ""
                        md_buf.append(f"#### {label}{title}")
                    elif name in {"scaffold", "deep"}:
                        label = "基礎の補足" if name == "scaffold" else "もっと深く"
                        title = f"：{arg}" if arg else ""
                        md_buf.append(f"#### 📘 {label}{title}")
                    walk_pieces(inner)
                else:
                    rendered = _block_to_nb_markdown(name, arg, inner, slug)
                    if rendered:
                        md_buf.append(rendered)

    walk_pieces(body)

    flush_md()

    # Closing Cell: Troubleshooting, Review & Next Chapter
    close_lines = [
        "## 学習のふりかえり・次のステップ",
        "",
        f"- **困ったとき・エラーが出たとき**：[エラー辞典（付録E）]({site}e-errors.html)",
        f"- **忘れる前に定着を確認**：[学習状況・間隔復習ダッシュボード]({site}review.html) で確認問題・類題・7段階の進捗を記録できます",
        f"- **この章のWebページ**：{site}{slug}.html",
    ]
    if next_slug and next_slug in META:
        nm = META[next_slug]
        close_lines.append(f"- **次の章**：[第{nm['num']}章 {nm['title']}]({site}{next_slug}.html)")
    raw_cells.append(("markdown", "\n".join(close_lines)))

    # Build valid nbformat 4.5 cells with deterministic IDs
    nb_cells = []
    for idx, (ctype, content) in enumerate(raw_cells):
        cid = f"{slug}-c{idx:02d}"
        if ctype == "markdown":
            nb_cells.append({
                "id": cid,
                "cell_type": "markdown",
                "metadata": {},
                "source": _to_source_lines(content),
            })
        else:
            src = content.split("\n")
            nb_cells.append({
                "id": cid,
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": [l + "\n" for l in src[:-1]] + [src[-1]],
            })

    meta_nb = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    }
    if env == "gpu":
        meta_nb["accelerator"] = "GPU"
        meta_nb["colab"]["gpuType"] = "T4"
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": meta_nb, "cells": nb_cells}


def notebook(slug):
    idx = CHAPTER_ORDER.index(slug) if slug in CHAPTER_ORDER else -1
    next_slug = CHAPTER_ORDER[idx + 1] if 0 <= idx + 1 < len(CHAPTER_ORDER) else None
    return make_notebook(slug, next_slug=next_slug)


# ---------------------------------------------------------------- search
def search_records():
    records = []
    for slug, meta in META.items():
        body = SOURCES[slug]
        rendered_html = restore_math(PAGE_BODY_HTML.get(slug, ""))
        sections = extract_sections_from_html(rendered_html)
        heads = [s["head"] for s in sections]
        # Full untruncated searchable text (stripped of fenced code & markup)
        text = re.sub(r"```.*?```", " ", body, flags=re.S)
        text = clean_plain_text(text)
        text = re.sub(r":::[a-z][\w-]*|:::", " ", text)
        text = re.sub(r"[#*`>\[\]()|]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        # Collect readings / English names for glossary terms appearing on this page
        readings_list = []
        seen_r = set()
        for t in GLOSSARY:
            if t["term"] in body:
                for cand in (t.get("reading", ""), t.get("en", "")):
                    cand = cand.strip()
                    if cand and cand not in seen_r:
                        seen_r.add(cand)
                        readings_list.append(cand)
        label = f"第{meta['num']}章" if "num" in meta else ("付録" if slug in CUR["appendix"] else "")
        records.append({
            "slug": slug,
            "title": meta["title"],
            "label": label,
            "heads": heads,
            "sections": sections,
            "readings": " ".join(readings_list),
            "text": text,
        })
    for t in GLOSSARY:
        r_parts = [p for p in (t.get("reading", "").strip(), t.get("en", "").strip()) if p]
        records.append({
            "slug": f"f-glossary.html#{term_id(t)}",
            "title": t["term"],
            "label": "用語",
            "heads": [],
            "sections": [],
            "readings": " ".join(r_parts),
            "text": clean_plain_text(t["def"]),
        })
    return records


# ---------------------------------------------------------------- review dashboard & exercise index
def exercises_meta_payload():
    """Slim exercise metadata (~25KB) for non-review pages (sidebar dots, due badge filtering)."""
    ids = []
    by_slug = {}
    for slug in CHAPTER_ORDER:
        items = []
        for item in EXERCISES_BY_CHAPTER.get(slug, []):
            ids.append(item["id"])
            lvl = int(item.get("level", 1))
            items.append({
                "id": item["id"],
                "difficulty": lvl,
                "level": lvl,
                "type": item.get("type", "choice"),
                "concept": item.get("concept", ""),
            })
        by_slug[slug] = items
    return {
        "version": 2,
        "total": len(ids),
        "ids": ids,
        "bySlug": by_slug,
    }


def exercises_index_payload():
    chapters = []
    for slug in CHAPTER_ORDER:
        m = META[slug]
        ex_list = [render_exercise_payload(item) for item in EXERCISES_BY_CHAPTER.get(slug, [])]
        chapters.append({
            "slug": slug,
            "num": int(m["num"]),
            "title": m["title"],
            "short": m["short"],
            "part": m["part"],
            "exercises": ex_list,
        })
    return {
        "version": 2,
        "defaultIntervalsDays": [1, 3, 7, 14, 30],
        "reviewChains": [
            {"id": "prob-softmax-att", "title": "確率 → softmax → Self-Attention → Transformer", "chapters": ["03-next-token", "04-bigram", "11-attention", "12-transformer"]},
            {"id": "vec-mat-tensor", "title": "ベクトル・行列 → テンソル演算 → MLP・LoRA", "chapters": ["06-tensors", "09-mlp", "19-lora"]},
            {"id": "diff-gd-gpt", "title": "微分・連鎖律 → 勾配降下法 → GPTの学習", "chapters": ["07-gradient", "08-neural-bigram", "10-training-tips", "13-train-gpt"]},
            {"id": "loss-sft-dpo", "title": "損失関数（交差エントロピー）→ SFT → DPO・評価", "chapters": ["05-loss", "18-sft", "20-evaluation", "22-alignment"]},
        ],
        "chapters": chapters,
    }


def review_page():
    body = '''<article class="chapter review-page">
<header class="chapter-hero">
  <p class="kicker">学習状況・間隔復習センター</p>
  <h1>理解度ダッシュボードと復習</h1>
  <p class="sub">「読んだ」だけで終わらせず、確認問題・自力実装・時間を空けた類題復習で定着を確かめます</p>
</header>

<section class="review-panel" aria-label="学習コースの選択">
  <h2>1. 学習コースの切り替え</h2>
  <p>どちらのコースを選んでも、<strong>最終的な技術的到達目標は同じ</strong>です。今の自分の得意・不得意に合わせて選べ、いつでも切り替えられます。</p>
  <div class="course-cards" role="group" aria-label="コース選択">
    <button type="button" class="course-card" data-set-course="thorough" aria-pressed="true">
      <b>じっくり理解コース（おすすめ）</b>
      <span>数学記号の読み方・なぜその式になるか・Python/PyTorchの構文分解（「基礎の補足」箱）をすべて開いた状態で表示し、段階的な演習と復習を重視します。</span>
    </button>
    <button type="button" class="course-card" data-set-course="standard" aria-pressed="false">
      <b>標準コース</b>
      <span>既知の基礎補足は折りたたみ表示にし、必要なときだけ開いて進めます。確認問題・応用・自力実装・復習の到達水準は同じです。</span>
    </button>
  </div>
</section>

<section class="review-panel" aria-label="7段階の習得状況">
  <h2>2. 全体の学習状況（7段階）</h2>
  <p class="muted-note">1回正解しただけでは「完全理解」とは表示しません。説明の読了、基礎・応用問題、自力実装、そして時間を空けた復習での再確認を区別して記録します。</p>
  <div id="dash-summary" class="dash-summary" aria-live="polite"><p>読み込み中…</p></div>
</section>

<section class="review-panel" aria-label="今日の復習">
  <h2>3. 今日復習すべき問題（間隔を空けた復習）</h2>
  <p class="muted-note">初期設定では <strong>1日後 → 3日後 → 7日後 → 14日後 → 30日後</strong> の間隔で復習を提案します（これは一般的な初期目安であり、唯一最適な間隔ではありません。誤答すると間隔が1日に短くなり、類題で連続正解すると少しずつ長くなります）。</p>
  <div id="dash-due" class="dash-due" aria-live="polite"><p>読み込み中…</p></div>
</section>

<section class="review-panel" aria-label="苦手な概念">
  <h2>4. 苦手な概念・誤答が多かった項目</h2>
  <div id="dash-weak" class="dash-weak" aria-live="polite"><p>読み込み中…</p></div>
</section>

<section class="review-panel" aria-label="知識のつながりマップ">
  <h2>5. 章をまたぐ知識のつながり</h2>
  <p class="muted-note">前の章で学んだ概念が、後の章の実装でそのまま土台になります。</p>
  <div id="dash-chains" class="dash-chains"></div>
</section>

<section class="review-panel" aria-label="章別の詳細状況">
  <h2>6. 章ごとの習得状況一覧</h2>
  <div id="dash-chapters" class="dash-chapters"></div>
</section>

<section class="review-panel" aria-label="データの保存とバックアップ">
  <h2>7. 学習履歴の保存・制約・バックアップ</h2>
  <p>このサイトはGitHub Pages上の静的サイトで、サーバーに学習データを送信しません。すべての履歴はこの端末のブラウザ内（<code>localStorage</code>）に保存されます。</p>
  <ul>
    <li><strong>保存容量の目安</strong>：ブラウザごとに通常 5MB 程度が上限です（本教材の学習履歴は通常数十KB以内です）。</li>
    <li><strong>ブラウザ・端末変更時の制約</strong>：別のブラウザや別PCには自動同期されません。また、ブラウザの「サイトデータを消去」を行うと履歴も消えます。</li>
    <li><strong>バックアップ</strong>：下のボタンで学習履歴をJSONファイルとして保存・復元できます。</li>
  </ul>
  <div class="backup-actions">
    <button type="button" class="btn primary" id="export-history">学習履歴をJSONで保存</button>
    <label class="btn file-btn" for="import-history">JSONから復元<input type="file" id="import-history" accept="application/json" class="visually-hidden"></label>
    <button type="button" class="btn ghost-danger" id="reset-history">学習履歴をリセット</button>
  </div>
  <p id="backup-status" class="muted-note" aria-live="polite"></p>
</section>
</article>'''
    return page("学習状況・復習", body, "review", "", "確認問題・7段階の習得状況・間隔復習のダッシュボード")


# ---------------------------------------------------------------- main
def main():
    load_exercises()
    if OUT.exists():
        for p in OUT.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    NB_OUT.mkdir(parents=True, exist_ok=True)
    pages = {}
    order = CHAPTER_ORDER
    ex_index = None
    # First pass collects math (including math inside exercises); second pass substitutes cached KaTeX HTML.
    for _ in range(2):
        for i, slug in enumerate(order):
            pages[slug] = chapter_page(slug, order[i - 1] if i else None, order[i + 1] if i + 1 < len(order) else None)
        for slug in CUR["appendix"] + CUR.get("extra", []):
            pages[slug] = appendix_page(slug)
        pages["review"] = review_page()
        pages["index"] = home_page()
        ex_index = exercises_index_payload()
        flush_math()
    for slug, html in pages.items():
        (OUT / f"{slug}.html").write_text(restore_math(html), encoding="utf-8", newline="\n")
    shutil.copytree(ROOT / "site", OUT, dirs_exist_ok=True)
    (OUT / "notebooks").mkdir(exist_ok=True)
    for i, slug in enumerate(order):
        if cells(SOURCES[slug]):
            next_slug = order[i + 1] if i + 1 < len(order) else None
            nb = json.dumps(make_notebook(slug, next_slug=next_slug), ensure_ascii=False, indent=1) + "\n"
            (NB_OUT / f"{slug}.ipynb").write_text(nb, encoding="utf-8", newline="\n")
            (OUT / "notebooks" / f"{slug}.ipynb").write_text(nb, encoding="utf-8", newline="\n")
    if (ROOT / "code").exists():
        shutil.copytree(ROOT / "code", OUT / "code", dirs_exist_ok=True)
    (OUT / "search.json").write_text(json.dumps(search_records(), ensure_ascii=False), encoding="utf-8", newline="\n")
    (OUT / "exercises-index.json").write_text(json.dumps(ex_index, ensure_ascii=False), encoding="utf-8", newline="\n")
    (OUT / "exercises-meta.json").write_text(json.dumps(exercises_meta_payload(), ensure_ascii=False), encoding="utf-8", newline="\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8", newline="\n")
    if not opts.no_write_cache:
        clean_cache = {k: v for k, v in math_cache.items() if k in math_used and "math-raw" not in v and not v.startswith("ERROR:")}
        MATH_CACHE_PATH.write_text(json.dumps(clean_cache, ensure_ascii=False, sort_keys=True, indent=0) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pages": len(pages), "chapters": len(order), "notebooks": len(list(NB_OUT.glob("*.ipynb"))),
                      "exercises": len(EXERCISES_BY_ID), "math": len(math_used)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
