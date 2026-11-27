"""Pure-Python CommonMark + GFM Table + Strikethrough fallback for tools/build.py.

Used only when `markdown-it-py` is not installed in the Python environment.
Implements the small subset of the MarkdownIt API used by tools/build.py:
  - MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
  - add_render_rule("fence", fn)
  - render(text)
  - renderInline(text)
"""
from html import escape
import re


class _FenceToken:
    def __init__(self, info, content):
        self.info = info
        self.content = content


_HTML_BLOCK_TAGS = (
    "div", "dl", "dt", "dd", "table", "thead", "tbody", "tr", "th", "td",
    "section", "aside", "article", "header", "footer", "nav", "details",
    "summary", "figure", "figcaption", "ul", "ol", "li", "p", "pre", "blockquote", "hr",
)
_HTML_BLOCK_RE = re.compile(r"^\s*</?(?:" + "|".join(_HTML_BLOCK_TAGS) + r")(?:\s|>|$|/)", re.I)
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_HR_RE = re.compile(r"^ {0,3}(?:(\*\s*){3,}|(-\s*){3,}|(_\s*){3,})$")
_UL_RE = re.compile(r"^( *)([-*+])\s+(.*)$")
_OL_RE = re.compile(r"^( *)(\d+)\.\s+(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")


def _split_table_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith(r"\|"):
        s = s[:-1]
    cells = []
    buf = []
    i = 0
    in_code = False
    while i < len(s):
        ch = s[i]
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
        elif ch == "\\" and i + 1 < len(s) and s[i + 1] == "|" and not in_code:
            buf.append("|")
            i += 1
        elif ch == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


class MarkdownIt:
    def __init__(self, preset="commonmark", options=None):
        self.preset = preset
        self.options = options or {}
        self._rules = {}

    def enable(self, _name):
        return self

    def add_render_rule(self, name, fn):
        self._rules[name] = fn

    # ---- inline rendering
    def renderInline(self, text):
        if not text:
            return ""
        stash = {}

        def keep(html):
            key = f"\x00INL{len(stash)}X\x00"
            stash[key] = html
            return key

        # 1. Code spans (backticks of any length)
        def repl_code(m):
            ticks = m.group(1)
            body = m.group(2)
            if len(body) >= 2 and body.startswith(" ") and body.endswith(" ") and body.strip():
                body = body[1:-1]
            return keep(f"<code>{escape(body)}</code>")

        text = re.sub(r"(`+)(.+?)\1", repl_code, text)

        # 2. Autolinks <https://...>
        text = re.sub(
            r"<(https?://[^<>\s]+)>",
            lambda m: keep(f'<a href="{escape(m.group(1), quote=True)}">{escape(m.group(1))}</a>'),
            text,
        )

        # 3. Inline HTML tags (e.g., <br>, <kbd>...</kbd>, <mark>...</mark>, <span ...>)
        text = re.sub(
            r"</?[a-zA-Z][a-zA-Z0-9-]*(?:\s+[^<>]*)?/?>",
            lambda m: keep(m.group(0)),
            text,
        )

        # 4. Images ![alt](src)
        def repl_img(m):
            alt = escape(m.group(1), quote=True)
            src = escape(m.group(2).strip(), quote=True)
            return keep(f'<img src="{src}" alt="{alt}">')

        text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+(?:\s+\"[^\"]*\")?)\)", repl_img, text)

        # 5. Links [label](href)
        def repl_link(m):
            label = self.renderInline(m.group(1))
            href = escape(m.group(2).strip(), quote=True)
            return keep(f'<a href="{href}">{label}</a>')

        text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", repl_link, text)

        # 6. Escape plain HTML entities (&, <, >) outside stashed placeholders
        parts = re.split(r"(\x00INL\d+X\x00)", text)
        for idx, p in enumerate(parts):
            if p.startswith("\x00INL"):
                continue
            # Backslash escapes for common markdown punctuation
            p = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", lambda m: keep(escape(m.group(1))), p)
            p = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts[idx] = p
        out = "".join(parts)
        # Strikethrough ~~...~~
        out = re.sub(r"~~(.+?)~~", r"<s>\1</s>", out)
        # Bold **...** and __...__ (may wrap stashed code/links/html)
        out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
        out = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"<strong>\1</strong>", out)
        # Italic *...* (avoid matching inside spaces or asterisks)
        out = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", out)

        # Restore stashed items (nested placeholders may require multiple passes)
        for _ in range(4):
            if "\x00INL" not in out:
                break
            out = re.sub(r"\x00INL\d+X\x00", lambda m: stash.get(m.group(0), m.group(0)), out)
        return out

    # ---- block rendering
    def render(self, text):
        lines = text.replace("\r\n", "\n").split("\n")
        return self._render_lines(lines)

    def _render_fence(self, info, content):
        tok = _FenceToken(info.strip(), content)
        if "fence" in self._rules:
            return self._rules["fence"](self, [tok], 0, self.options, {})
        return f"<pre><code>{escape(content)}</code></pre>\n"

    def _render_lines(self, lines):
        out = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            s = line.strip()

            # Blank line
            if not s:
                i += 1
                continue

            # Fenced code block
            mf = _FENCE_OPEN_RE.match(line)
            if mf:
                fence_chars, info = mf.group(1), mf.group(2)
                fence_ch = fence_chars[0]
                fence_len = len(fence_chars)
                j = i + 1
                code_lines = []
                close_re = re.compile(rf"^ {{0,3}}{re.escape(fence_ch)}{{{fence_len},}}\s*$")
                while j < n and not close_re.match(lines[j]):
                    code_lines.append(lines[j])
                    j += 1
                content = "\n".join(code_lines) + ("\n" if code_lines else "")
                out.append(self._render_fence(info, content))
                i = j + 1
                continue

            # Heading
            mh = _HEADING_RE.match(line)
            if mh:
                lvl = len(mh.group(1))
                out.append(f"<h{lvl}>{self.renderInline(mh.group(2))}</h{lvl}>\n")
                i += 1
                continue

            # Horizontal rule
            if _HR_RE.match(line):
                out.append("<hr />\n")
                i += 1
                continue

            # HTML block (single or multi-line until blank line)
            if _HTML_BLOCK_RE.match(line):
                html_lines = [line]
                j = i + 1
                while j < n and lines[j].strip() != "":
                    html_lines.append(lines[j])
                    j += 1
                out.append("\n".join(html_lines) + "\n")
                i = j
                continue

            # Blockquote
            if line.lstrip().startswith(">"):
                bq_lines = []
                j = i
                while j < n and (lines[j].lstrip().startswith(">") or (lines[j].strip() and bq_lines and not _HEADING_RE.match(lines[j]))):
                    if lines[j].lstrip().startswith(">"):
                        bq_lines.append(re.sub(r"^ {0,3}>\s?", "", lines[j]))
                    else:
                        bq_lines.append(lines[j])
                    j += 1
                out.append(f"<blockquote>\n{self._render_lines(bq_lines)}</blockquote>\n")
                i = j
                continue

            # GFM Table
            if "|" in line and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
                headers = _split_table_row(line)
                j = i + 2
                rows = []
                while j < n and lines[j].strip() and "|" in lines[j] and not _FENCE_OPEN_RE.match(lines[j]):
                    rows.append(_split_table_row(lines[j]))
                    j += 1
                th = "".join(f"<th>{self.renderInline(c)}</th>" for c in headers)
                tbody = ""
                for row in rows:
                    # Pad/trim to header length
                    cells = (row + [""] * len(headers))[:len(headers)]
                    tbody += "<tr>" + "".join(f"<td>{self.renderInline(c)}</td>" for c in cells) + "</tr>\n"
                out.append(f"<table>\n<thead>\n<tr>{th}</tr>\n</thead>\n<tbody>\n{tbody}</tbody>\n</table>\n")
                i = j
                continue

            # Lists (ul / ol, with optional 1-level nesting)
            mul = _UL_RE.match(line)
            mol = _OL_RE.match(line)
            if mul or mol:
                tag = "ul" if mul else "ol"
                base_indent = len((mul or mol).group(1))
                start_attr = ""
                if mol and mol.group(2) != "1":
                    start_attr = f' start="{mol.group(2)}"'
                items = []
                j = i
                while j < n:
                    cur = lines[j]
                    if not cur.strip():
                        # Check if next non-blank line continues this list
                        k = j + 1
                        while k < n and not lines[k].strip():
                            k += 1
                        if k < n:
                            m_next = _UL_RE.match(lines[k]) if tag == "ul" else _OL_RE.match(lines[k])
                            if m_next and len(m_next.group(1)) == base_indent:
                                j = k
                                continue
                        break
                    m_same = _UL_RE.match(cur) if tag == "ul" else _OL_RE.match(cur)
                    if m_same and len(m_same.group(1)) == base_indent:
                        items.append([m_same.group(3)])
                        j += 1
                        continue
                    # Continuation or nested sub-list indented deeper than base_indent
                    lead = len(cur) - len(cur.lstrip(" "))
                    if items and lead > base_indent:
                        items[-1].append(cur[base_indent + 2:] if lead >= base_indent + 2 else cur.lstrip())
                        j += 1
                        continue
                    break
                lis = []
                for item_lines in items:
                    if len(item_lines) == 1:
                        lis.append(f"<li>{self.renderInline(item_lines[0])}</li>\n")
                    else:
                        first_line = item_lines[0]
                        rest = item_lines[1:]
                        # If rest starts with a sublist or fence, render recursively
                        if _UL_RE.match(rest[0]) or _OL_RE.match(rest[0]) or _FENCE_OPEN_RE.match(rest[0]):
                            lis.append(f"<li>{self.renderInline(first_line)}\n{self._render_lines(rest)}</li>\n")
                        else:
                            joined = "\n".join(item_lines)
                            lis.append(f"<li>{self.renderInline(joined)}</li>\n")
                out.append(f"<{tag}{start_attr}>\n{''.join(lis)}</{tag}>\n")
                i = j
                continue

            # Paragraph
            para = [line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if not nxt.strip():
                    break
                if (_FENCE_OPEN_RE.match(nxt) or _HEADING_RE.match(nxt) or _HR_RE.match(nxt)
                        or _HTML_BLOCK_RE.match(nxt) or nxt.lstrip().startswith(">")
                        or _UL_RE.match(nxt) or _OL_RE.match(nxt)):
                    break
                if "|" in nxt and j + 1 < n and _TABLE_SEP_RE.match(lines[j + 1]):
                    break
                para.append(nxt)
                j += 1
            out.append(f"<p>{self.renderInline(' '.join(p.strip() for p in para))}</p>\n")
            i = j

        return "".join(out)
