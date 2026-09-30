"""Validate textbook structure, internal targets and executable lesson snippets."""
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
failures = []


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for name in ["href", "src"]:
            if name in attrs:
                self.links.append(attrs[name])


pages = {}
for file in (ROOT / "dist").glob("*.html"):
    parser = Links()
    parser.feed(file.read_text(encoding="utf-8"))
    pages[file.resolve()] = parser
    if ":::" in file.read_text(encoding="utf-8"):
        failures.append(f"unrendered exercise: {file.name}")
for file, parser in pages.items():
    for link in parser.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (file.parent / unquote(url.path)).resolve() if url.path else file
        if not target.is_file():
            failures.append(f"missing target: {file.name} -> {link}")
        elif url.fragment and target in pages and url.fragment not in pages[target].ids:
            failures.append(f"missing anchor: {file.name} -> {link}")

snippets = 0
scratch = ROOT / ".sites-runtime" / "snippet-checks"
scratch.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONIOENCODING="utf-8")
for file in sorted(list((ROOT / "content").glob("*.md")) + list((ROOT / "pages").glob("*.md"))):
    source = file.read_text(encoding="utf-8")
    if file.parent.name == "content":
        json.loads(source.splitlines()[0])
    assert source.count(":::exercise ") == source.count(":::answer"), file.name
    for i, code in enumerate(re.findall(r"```python\n(.*?)\n```", source, re.S)):
        snippets += 1
        directory = scratch / f"{file.stem}-{i}"
        directory.mkdir(exist_ok=True)
        result = subprocess.run([sys.executable, "-c", code], cwd=directory,
                                capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        if result.returncode:
            failures.append(f"snippet {file.name}:{i}: {result.stderr[-1800:]}")
report = {"date": "2026-09-30", "html_pages": len(pages),
          "python_snippets_executed": snippets, "failures": failures}
(ROOT / "verification").mkdir(exist_ok=True)
# Failures may contain local paths. Only publish clean reports.
if not failures:
    (ROOT / "verification" / "site-checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=True, indent=2))
sys.exit(bool(failures))
