"""Build the textbook. No private input documents are required or copied."""
from pathlib import Path
from html import escape
import argparse, json, re, shutil
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', choices=['dist', 'docs'], default='dist')
OUT = ROOT / parser.parse_args().output
OUT.mkdir(exist_ok=True)
md = MarkdownIt('commonmark', {'html': True}).enable('table')
chapters = []
for path in sorted((ROOT / 'content').glob('*.md')):
    meta, body = path.read_text(encoding='utf-8').split('\n', 1)
    record = json.loads(meta)
    record.update(slug=path.stem, body=body)
    chapters.append(record)
groups = list(dict.fromkeys(c['part'] for c in chapters))

def render(body):
    def exercise(match):
        title, question, answer = match.groups()
        return '<section class="exercise"><h3>'+escape(title)+'</h3>'+md.render(question)+'<details><summary>解答と考え方を読む</summary>'+md.render(answer)+'</details></section>\n\n'
    body = re.sub(r':::exercise (.*?)\n(.*?)\n:::answer\n(.*?)\n:::', exercise, body, flags=re.S)
    return md.render(body)

def nav(active):
    result = '<a class="side-title" href="index.html">学習の地図</a>'
    for idx, group in enumerate(groups):
        result += f'<details class="nav-group" {"open" if active=="index" or any(c["slug"]==active and c["part"]==group for c in chapters) else ""}><summary><span>{idx+1:02}</span> {escape(group)}</summary>'
        for c in chapters:
            if c['part'] == group:
                result += f'<a {"aria-current=page" if c["slug"]==active else ""} href="{c["slug"]}.html">{escape(c["title"])}</a>'
        result += '</details>'
    result += '<div class="resource-nav"><a href="labs.html">実装ラボ</a><a href="research.html">研究を読む</a><a href="reference.html">用語・記号の早見表</a><a href="coverage.html">原資料との対応</a><a href="about.html">編集方針</a></div>'
    return result

def page(title, body, active='index', toc=''):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | sakunokyumei</title><meta name="description" content="算数からLLMの実装・再現実験・独自研究へ。動機から学ぶ日本語の講義、解答付き演習、実装ラボ。AI支援で作成した公開教科書。">
<meta name="color-scheme" content="light"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head>
<body><a class="skip" href="#main">本文へ</a><header><a class="brand" href="index.html"><span class="brand-mark">∑</span><span>sakunokyumei<small>LLM RESEARCH TEXTBOOK</small></span></a><nav aria-label="メイン"><a href="index.html#curriculum">講義</a><a href="labs.html">実装ラボ</a><a href="research.html">研究を読む</a><a href="about.html">編集方針</a></nav><button id="menu" aria-expanded="false" aria-controls="sidebar">目次</button></header>
<div class="layout"><aside id="sidebar"><label for="search">教材を探す</label><input id="search" type="search" placeholder="例：微分、Attention" autocomplete="off"><div id="results" aria-live="polite"></div><nav aria-label="全章目次">{nav(active)}</nav><div class="side-note">AI支援で作成<br>出典・検証範囲を各章に掲載<br><a href="about.html">この教材について</a></div></aside><main id="main" tabindex="-1">{body}<footer><strong>sakunokyumei</strong><p>AI（OpenAI Codex）を用いて作成した教材です。理解は、小さな実験で確かめよう。</p><a href="about.html">編集・検証・プライバシー</a> · <a href="references.html">出典一覧</a> · <a href="coverage.html">原資料との対応</a></footer></main>{toc}</div></body></html>'''

exercise_count = sum(c['body'].count(':::exercise ') for c in chapters)
cards=''
for idx, group in enumerate(groups):
    items=''.join(f'<li><a href="{c["slug"]}.html"><span>{escape(c["title"])}</span><small>{escape(c.get("goal",""))}</small></a></li>' for c in chapters if c['part']==group)
    cards+=f'<section class="part"><div class="part-heading"><span>{idx+1:02}</span><h3>{escape(group)}</h3></div><ol>{items}</ol></section>'
first=chapters[0]['slug'] if chapters else 'index'
home=f'''<div class="home-intro"><p class="eyebrow">A QUESTION IS WHERE RESEARCH BEGINS.</p><h1>ゼロから、<br>LLMを研究する。</h1><p class="lead">「なぜ？」を、ひとつずつ。<br>算数の最初の一歩から、数式を読み、モデルを作り、<br class="desktop">自分の問いを実験で確かめるところまで。</p><div class="start-row"><a class="primary" href="{first}.html">最初の講義を読む</a><a href="#curriculum">学習の地図を見る</a></div><div class="counts"><span><b>{len(chapters)}</b> 講義</span><span><b>{exercise_count}</b> 解答付き演習</span><span>紙とCPUから始められる</span></div></div>
<section class="learning-strip" aria-label="学びの流れ"><span><b>01</b>疑問を持つ</span><span><b>02</b>小さく計算する</span><span><b>03</b>コードで確かめる</span><span><b>04</b>自分の言葉にする</span></section>
<section class="intro-note"><h2>難しさの上限を下げずに、<br>一段を小さくする。</h2><p>初めての概念は、身近な問題から。数式の意味をつかんだら、例題を追い、答えを隠して演習に取り組みます。行き詰まったら、前提の章に戻って大丈夫。研究も、同じ積み重ねです。</p></section>
<section id="curriculum"><p class="eyebrow">THE LEARNING MAP</p><h2>学習の地図</h2><p>上から順に進めます。既に知っている章も、解答を見ずに演習と到達課題を解いて確認してください。</p>{cards}</section>'''
(OUT/'index.html').write_text(page('ゼロから、LLMを研究する。',home),encoding='utf-8')
for i,c in enumerate(chapters):
    html=render(c['body'])
    headings=[]
    def heading(m):
        number=len(headings)+1; headings.append((number,re.sub('<[^>]*>','',m[1])))
        return f'<h2 id="section-{number}">{m[1]}</h2>'
    html=re.sub(r'<h2>(.*?)</h2>',heading,html)
    toc='<aside class="toc"><strong>この講義で学ぶこと</strong>'+''.join(f'<a href="#section-{n}">{escape(t)}</a>' for n,t in headings)+'</aside>'
    pager='<nav class="pager" aria-label="前後の講義">'
    if i: pager+=f'<a href="{chapters[i-1]["slug"]}.html"><small>前の講義</small>{escape(chapters[i-1]["title"])}</a>'
    if i+1<len(chapters): pager+=f'<a href="{chapters[i+1]["slug"]}.html"><small>次の講義</small>{escape(chapters[i+1]["title"])}</a>'
    pager+='</nav>'
    body=f'<article><p class="eyebrow">{escape(c["part"])}</p><h1>{escape(c["title"])}</h1><p class="lesson-goal">到達目標：{escape(c.get("goal",""))}</p><div class="lesson-meta">前提：{escape(c.get("prereq","なし"))} <span>演習 {c["body"].count(":::exercise ")} 問</span></div>{html}{pager}</article>'
    (OUT/(c['slug']+'.html')).write_text(page(c['title'],body,c['slug'],toc),encoding='utf-8')
for path in (ROOT/'pages').glob('*.md'):
    title,body=path.read_text(encoding='utf-8').split('\n',1)
    (OUT/(path.stem+'.html')).write_text(page(title.lstrip('# '),'<article><h1>'+escape(title.lstrip('# '))+'</h1>'+render(body)+'</article>',path.stem),encoding='utf-8')
for path in (ROOT/'assets').glob('*'):
    shutil.copy2(path,OUT/path.name)
(OUT/'search.json').write_text(json.dumps([{k:c[k] for k in ['slug','title','part','goal']} for c in chapters],ensure_ascii=False),encoding='utf-8')
(OUT/'.nojekyll').write_text('',encoding='utf-8')
if (ROOT/'labs').exists():
    for p in (ROOT/'labs').glob('*'):
        if p.is_file() and p.suffix in ['.py','.md','.txt','.json','.csv']:
            (OUT/'downloads').mkdir(exist_ok=True); shutil.copy2(p,OUT/'downloads'/p.name)
print(json.dumps({'chapters':len(chapters),'exercises':exercise_count,'pages':len(list(OUT.glob('*.html')))},ensure_ascii=False))
