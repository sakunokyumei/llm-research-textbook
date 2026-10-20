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

from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).parent))
from bookparse import BOOK, ROOT, load_curriculum, read_source, parse_info, cells  # noqa: E402

args = argparse.ArgumentParser()
args.add_argument("--out", default="docs")
args.add_argument("--notebooks", default="notebooks")
opts = args.parse_args()
OUT = ROOT / opts.out
NB_OUT = ROOT / opts.notebooks
CUR = load_curriculum()
REPO = CUR["repo"]
SITE_TITLE = CUR["title"]

# ---------------------------------------------------------------- math
MATH_CACHE_PATH = BOOK / ".mathcache.json"
math_cache = json.loads(MATH_CACHE_PATH.read_text(encoding="utf-8")) if MATH_CACHE_PATH.exists() else {}
math_used = set()
math_pending = {}


def math_key(tex, display):
    return hashlib.sha1(((("D" if display else "I") + tex)).encode()).hexdigest()[:16]


def math_placeholder(tex, display):
    key = math_key(tex, display)
    math_used.add(key)
    if key not in math_cache:
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
        print("warning: KaTeX unavailable, math left as TeX:", e, file=sys.stderr)
        rendered = [None] * len(items)
    for (key, (tex, display)), html in zip(items, rendered):
        if html is None:
            html = f'<code class="math-raw">{escape(tex)}</code>'
        elif html.startswith("ERROR:"):
            raise SystemExit(f"KaTeX error in {tex!r}: {html}")
        math_cache[key] = html
    math_pending.clear()


def protect_math(text):
    """Replace $$..$$ and $..$ outside inline code with placeholders."""
    pieces = re.split(r"(`+[^`\n]*?`+)", text)
    out = []
    for piece in pieces:
        if piece.startswith("`"):
            out.append(piece)
            continue
        piece = piece.replace(r"\$", "DOLLARPHX")
        piece = re.sub(r"\$\$(.+?)\$\$", lambda m: "\n\n<div class=\"math-display\">" + math_placeholder(m[1].strip(), True) + "</div>\n\n", piece, flags=re.S)
        piece = re.sub(r"(?<![\w$])\$([^$\n]+?)\$(?![\w$])", lambda m: math_placeholder(m[1], False), piece)
        out.append(piece)
    return "".join(out)


def restore_math(html):
    html = html.replace("DOLLARPHX", "$")
    return re.sub(r"MATHPH([0-9a-f]{16})X", lambda m: math_cache.get(m[1], m[0]), html)


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
}
widget_pages = set()


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


def render_markdown(text, ctx):
    html_parts = {}
    pieces = []
    for piece in split_blocks(text):
        if isinstance(piece, str):
            pieces.append(protect_math(piece))
        else:
            key = f"BLOCKPH{len(html_parts)}X"
            html_parts[key] = render_block(*piece, ctx)
            pieces.append(f"\n\n<div>{key}</div>\n\n")
    html = md.render("\n".join(pieces))
    for key, value in html_parts.items():
        html = html.replace(f"<div>{key}</div>", value)
    return html


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
        return (f'<section class="quiz"><p class="quiz-label">クイズ {ctx["quiz"]}{"：" + escape(arg) if arg else ""}</p>'
                f'{render_markdown(question, ctx)}<details><summary>答えを見る（まず自分で考えてから！）</summary>'
                f'{render_markdown(answer, ctx)}</details></section>\n')
    if name == "deep":
        return (f'<details class="deep"><summary><span>もっと深く</span>{escape(arg)}</summary>'
                f'{render_markdown(inner, ctx)}</details>\n')
    if name == "checklist":
        items = [l[2:].strip() for l in inner.strip().split("\n") if l.startswith("- ")]
        lis = "".join(f'<li><label><input type="checkbox" data-check="{ctx["slug"]}:{n}"> <span>{md.renderInline(protect_math(t))}</span></label></li>'
                      for n, t in enumerate(items))
        return f'<section class="checklist"><p class="box-title">できたらチェック</p><ul>{restore_math(lis)}</ul></section>\n'
    if name == "widget":
        widget_pages.add(ctx["slug"])
        wname, _, mode = arg.partition(" ")
        mode_attr = f' data-mode="{escape(mode)}"' if mode else ""
        return f'<div class="widget" data-widget="{escape(wname)}"{mode_attr}><noscript>このデモはJavaScriptを有効にすると動きます。</noscript></div>\n'
    if name in BOX:
        title, cls = BOX[name]
        heading = f'{title}{"：" + escape(arg) if arg else ""}'
        return f'<aside class="box box-{cls}"><p class="box-title">{heading}</p>{render_markdown(inner, ctx)}</aside>\n'
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
    stack = []
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
                tip = escape(t["def"], quote=True)
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
<script>try{{const t=localStorage.getItem("tsukuru-llm-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="icon" href="img/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="katex/katex.min.css"><link rel="stylesheet" href="style.css">
<script src="app.js" defer></script>{widgets}</head>
<body data-page="{escape(active)}"><a class="skip" href="#main">本文へ移動</a>
<header class="topbar"><button class="menu-btn" id="menu" aria-expanded="false" aria-controls="sidebar" aria-label="目次を開く"><span></span><span></span><span></span></button>
<a class="brand" href="index.html"><img src="img/logo.svg" alt="" width="36" height="36"><span><b>{escape(SITE_TITLE)}</b><small>ボンゴ先生のLLM教室</small></span></a>
<nav class="topnav" aria-label="主なページ"><a href="index.html#map">目次</a><a href="a-setup.html">環境構築</a><a href="e-errors.html">エラー辞典</a><a href="f-glossary.html">用語集</a></nav>
<button id="theme" class="icon-btn" type="button" aria-label="明るさを切り替える" title="明るさを切り替える">◐</button></header>
<div class="layout"><aside id="sidebar" class="sidebar"><div class="search"><label for="search">教科書の中を探す</label><input id="search" type="search" placeholder="例：softmax、LoRA、GPU" autocomplete="off"><div id="results" aria-live="polite"></div></div>
<div class="progress-box" data-progress hidden><span class="bar"><span></span></span><small></small></div>{nav_html(active)}</aside>
<main id="main" tabindex="-1">{body}
<footer class="site-footer"><p><b>{escape(SITE_TITLE)}</b> ── “What I cannot create, I do not understand.”（作れないものは、理解していない）── R. P. Feynman</p>
<p>本文・コード・サイトは学習者 sakunokyumei のためにAI（Claude Code）を用いて作成し、コードは自動検証しています。<a href="about.html">この教室について</a> · <a href="j-references.html">参考文献</a> · <a href="https://github.com/{REPO}">GitHub</a></p></footer></main>{toc}</div></body></html>'''


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


def add_heading_ids(html):
    toc = []

    def h2(m):
        n = len(toc) + 1
        text = re.sub("<[^>]+>", "", m[1])
        toc.append((n, text))
        return f'<h2 id="s{n}">{m[1]}</h2>'
    html = re.sub(r"<h2>(.*?)</h2>", h2, html)
    return html, toc


def toc_html(toc):
    if not toc:
        return ""
    links = "".join(f'<a href="#s{n}">{escape(t)}</a>' for n, t in toc)
    return f'<aside class="toc" aria-label="このページの見出し"><p>このページ</p>{links}<a class="toc-top" href="#main">↑ 先頭へ</a></aside>'


META = {}
SOURCES = {}
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
    ctx = {"slug": slug, "quiz": 0}
    html = render_markdown(body, ctx)
    html, toc = add_heading_ids(html)
    has_code = bool(cells(body))
    actions = ""
    if has_code:
        actions = (f'<div class="chapter-actions"><a class="btn primary" href="{colab_url(slug)}" target="_blank" rel="noopener">Colabで開く（完成ノート）</a>'
                   f'<a class="btn" href="notebooks/{slug}.ipynb" download>ノートブックをダウンロード</a></div>'
                   '<p class="hint">おすすめは「ページを読みながら、コードを自分のノートブックに1セルずつ貼って実行」。完成ノートは困ったときの答え合わせ用です。</p>')
    learn = ""
    rows = []
    if meta.get("builds"):
        rows.append(f'<div><h3>つくるもの</h3><p>{md.renderInline(meta["builds"])}</p></div>')
    if meta.get("theory"):
        rows.append('<div><h3>ついでに身につく理論</h3><ul>' + "".join(f"<li>{md.renderInline(protect_math(t))}</li>" for t in meta["theory"]) + "</ul></div>")
    if meta.get("python"):
        rows.append('<div><h3>新しく使うPython</h3><ul>' + "".join(f"<li>{md.renderInline(t)}</li>" for t in meta["python"]) + "</ul></div>")
    if rows:
        learn = f'<section class="learn-grid">{"".join(rows)}</section>'
    kicker = f'{escape(meta["part"])} · 第{meta["num"]}章'
    hero = (f'<header class="chapter-hero"><p class="kicker">{kicker}</p><h1>{escape(meta["title"])}</h1>'
            f'<p class="sub">{escape(meta.get("subtitle", ""))}</p><dl class="meta">'
            f'<div><dt>目安</dt><dd>{escape(meta.get("time", ""))}</dd></div>'
            f'<div><dt>環境</dt><dd>{escape(ENV_LABEL.get(meta.get("env", "cpu"), meta.get("env", "")))}</dd></div>'
            f'<div><dt>難しさ</dt><dd aria-label="5段階中{meta.get("level", 1)}">{stars(meta.get("level", 1))}</dd></div></dl>{actions}</header>')
    done = (f'<section class="chapter-done"><button type="button" class="btn primary" data-done="{slug}">この章をクリアした！</button>'
            '<p>押すと目次にチェックが付きます（この端末のブラウザにだけ保存）。</p></section>')
    pager = '<nav class="pager" aria-label="前後の章">'
    if prev_slug:
        pager += f'<a href="{prev_slug}.html"><small>← 前の章</small>{escape(META[prev_slug]["title"])}</a>'
    if next_slug:
        pager += f'<a class="next" href="{next_slug}.html"><small>次の章 →</small>{escape(META[next_slug]["title"])}</a>'
    pager += "</nav>"
    article = f'<article class="chapter">{hero}{learn}{link_terms(html, slug)}{done}{pager}</article>'
    return page(meta["title"], article, slug, toc_html(toc), meta.get("subtitle"))


def appendix_page(slug):
    meta, body = META[slug], SOURCES[slug]
    if slug == "f-glossary":
        body = body.replace("<!-- GLOSSARY -->", glossary_markdown())
    ctx = {"slug": slug, "quiz": 0}
    html = render_markdown(body, ctx)
    html, toc = add_heading_ids(html)
    label = f"付録{slug[0].upper()}" if slug in CUR["appendix"] else ""
    hero = (f'<header class="chapter-hero appendix"><p class="kicker">{label}</p><h1>{escape(meta["title"])}</h1>'
            f'<p class="sub">{escape(meta.get("subtitle", ""))}</p></header>')
    return page(meta["title"], f'<article class="chapter">{hero}{html}</article>', slug, toc_html(toc), meta.get("subtitle"))


def glossary_markdown():
    groups = {}
    for t in sorted(GLOSSARY, key=lambda t: t.get("reading", t["term"])):
        head = t.get("reading", t["term"])[:1].upper()
        groups.setdefault(head, []).append(t)
    out = []
    for head in sorted(groups):
        out.append(f"\n## {head}\n")
        out.append('<dl class="glossary">')
        for t in groups[head]:
            where = f' <a class="where" href="{t["chapter"]}.html">第{int(t["chapter"][:2])}章で登場</a>' if t.get("chapter") in META else ""
            en = f' <span class="en">{escape(t["en"])}</span>' if t.get("en") else ""
            out.append(f'<dt id="{term_id(t)}">{escape(t["term"])}{en}{where}</dt><dd>{md.renderInline(protect_math(t["def"]))}</dd>')
        out.append("</dl>\n")
    return "\n".join(out)


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
def notebook(slug):
    meta, body = META[slug], SOURCES[slug]
    nb_cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        f"# 第{meta['num']}章 {meta['title']}\n\n",
        f"{meta.get('subtitle', '')}\n\n",
        f"教科書のページ：{CUR['site']}{slug}.html\n\n",
        "上のセルから順に、再生ボタン（▶）か `Shift + Enter` で実行します。説明は教科書のページにあります。\n",
        "\n**このノートはGPUを使います。** メニューの「ランタイム」→「ランタイムのタイプを変更」→「T4 GPU」を選んでから実行してください。\n" if meta.get("env") == "gpu" else "",
    ]}]
    heading = None
    from bookparse import iter_fences
    lines = body.split("\n")
    fence_iter = iter(c for c in iter_fences(body))
    # Walk lines to keep headings next to their code.
    i = 0
    fence_re = re.compile(r"^(`{3,})(.*)$")
    while i < len(lines):
        s = lines[i].strip()
        m = fence_re.match(s)
        if m:
            lang, flags, subs, code = next(fence_iter)
            j = i + 1
            while j < len(lines) and lines[j].strip() != m[1]:
                j += 1
            i = j + 1
            if lang == "python" and "no-run" not in flags:
                if heading:
                    nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": [heading]})
                    heading = None
                src = code.split("\n")
                nb_cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                                 "source": [l + "\n" for l in src[:-1]] + [src[-1]]})
            continue
        if s.startswith("## ") or s.startswith("### "):
            heading = s + "\n"
        i += 1
    meta_nb = {"kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}, "colab": {"provenance": []}}
    if meta.get("env") == "gpu":
        meta_nb["accelerator"] = "GPU"
        meta_nb["colab"]["gpuType"] = "T4"
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": meta_nb, "cells": nb_cells}


# ---------------------------------------------------------------- search
def search_records():
    records = []
    for slug, meta in META.items():
        body = SOURCES[slug]
        heads = re.findall(r"^#{2,3} (.+)$", body, re.M)
        text = re.sub(r"```.*?```", " ", body, flags=re.S)
        text = re.sub(r"[#*`>\[\]()|:-]+", " ", text)
        text = re.sub(r"\s+", " ", text)[:4000]
        label = f"第{meta['num']}章" if "num" in meta else ("付録" if slug in CUR["appendix"] else "")
        records.append({"slug": slug, "title": meta["title"], "label": label, "heads": heads, "text": text})
    for t in GLOSSARY:
        records.append({"slug": f"f-glossary.html#{term_id(t)}", "title": t["term"], "label": "用語", "heads": [], "text": t["def"]})
    return records


# ---------------------------------------------------------------- main
def main():
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
    # First pass collects math; render twice so cached math is substituted.
    for _ in range(2):
        for i, slug in enumerate(order):
            pages[slug] = chapter_page(slug, order[i - 1] if i else None, order[i + 1] if i + 1 < len(order) else None)
        for slug in CUR["appendix"] + CUR.get("extra", []):
            pages[slug] = appendix_page(slug)
        pages["index"] = home_page()
        flush_math()
    for slug, html in pages.items():
        (OUT / f"{slug}.html").write_text(restore_math(html), encoding="utf-8")
    shutil.copytree(ROOT / "site", OUT, dirs_exist_ok=True)
    (OUT / "notebooks").mkdir(exist_ok=True)
    for slug in order:
        if cells(SOURCES[slug]):
            nb = json.dumps(notebook(slug), ensure_ascii=False, indent=1) + "\n"
            (NB_OUT / f"{slug}.ipynb").write_text(nb, encoding="utf-8")
            (OUT / "notebooks" / f"{slug}.ipynb").write_text(nb, encoding="utf-8")
    if (ROOT / "code").exists():
        shutil.copytree(ROOT / "code", OUT / "code", dirs_exist_ok=True)
    (OUT / "search.json").write_text(json.dumps(search_records(), ensure_ascii=False), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    unused = set(math_cache) - math_used
    for key in unused:
        del math_cache[key]
    MATH_CACHE_PATH.write_text(json.dumps(math_cache, ensure_ascii=False, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(pages), "chapters": len(order), "notebooks": len(list(NB_OUT.glob("*.ipynb"))),
                      "math": len(math_used)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
