# つくってわかるLLM

手を動かしながら学ぶ、日本語のLLM（大規模言語モデル）の教科書です。Pythonの初歩から始めて、自分でGPTを作り、学習させ、既製のモデルを鍛え（SFT・LoRA・DPO）、評価し、検索やツールとつなぎ、Webに公開するところまで進みます。理論は、実際に必要になった場所で、その場で学びます。

公開サイト：https://sakunokyumei.github.io/llm-research-textbook/

- 全27章と付録10本。各章に、Google Colabでそのまま開けるノートブックがあります
- 費用は0円です。Google Colabの無料GPU（T4）で動き、Colabが使えない日はKaggleやCPUで進められます
- 第1章の30〜60分で本物のLLMと会話し、第4章で自分の言語モデルが夏目漱石風の文章を書きます
- 第13章で学習させた漱石GPTは、サイトのトップページでブラウザだけで動きます

## 本文・コード・サイトの作成について

本文・コード・サイトはAI（Claude Code）を用いて作成しています。各章のコードは、下の検証手順ですべて実行して確かめています。表示されている出力は、実際に実行した出力です。例として示した出力には、そうと書いてあります。事前学習済みモデルを使うコードは、同じ構造の小さな模擬モデルで動作を確かめています。そのため、本物のモデルの答えの質までは保証できません。検証の範囲は、付録「この教室について」と「学習者シミュレーション報告」に書いてあります。

以前の版（全56章の講義形式）は `legacy/` に残してあります。

## フォルダの構成

| フォルダ | 中身 |
|---|---|
| `book/` | 原稿です。`chapters/`（本文）、`appendix/`（付録）、`curriculum.json`（章の順番）、`glossary.json`（用語集）、`home.html`（トップページ）があります |
| `site/` | CSS、JavaScript（デモ、ブラウザで動くGPT）、画像です |
| `code/` | 章で使うPythonのファイルとデータです（`minigpt.py`、SFT・DPO・RAG用のJSONL） |
| `tools/` | サイトの生成（`build.py`）、コードの検証（`verify.py`）、学習者シミュレーション（`persona.py`）の道具です |
| `docs/` | 生成されたサイトです。GitHub Pagesはmainブランチの `/docs` を公開します |
| `notebooks/` | 生成されたColab用のノートブックです |
| `verification/` | 検証の記録です（`code-report.json`、`persona-metrics.json`） |
| `legacy/` | 以前の版です |

## サイトの生成

PythonとNode.jsを使います（数式をKaTeXで生成するため）。数式が変わっていなければ、Node.jsがなくても `book/.mathcache.json` を使って生成できます。

```sh
python -m pip install markdown-it-py
python tools/build.py                       # docs/ と notebooks/ を生成
python -m http.server 8765 --directory docs # http://localhost:8765 で確認
```

原稿は `book/` にあります。`docs/` と `notebooks/` は直接編集せず、`tools/build.py` で作り直してください。

## コードの検証

```sh
python -m pip install torch transformers trl peft datasets accelerate gradio matplotlib numpy
python tools/testkit/make_fakes.py          # 小さな模擬モデルを .cache/fakes/ に作成
python tools/verify.py                      # 全章のコードを実行し、リンクも確認
python tools/verify.py --only 04-bigram     # 1章だけ
python tools/verify.py --update             # 実際の出力を原稿の output ブロックに書き戻す
python tools/verify.py --links-only         # リンクだけ確認
python tools/persona.py                     # 学習者シミュレーション（機械チェック）
```

各章は、新しいColabのセッションと同じように、空のフォルダで上から順に実行します。GPUが必要なセル（4ビット量子化など）とオンライン専用のセル（ログイン、公開リンク）は飛ばし、そのことを記録します。

## 原稿の書き方（抜粋）

本文はMarkdownです。次の囲みが使えます。

```text
:::sensei / :::minato        ボンゴ先生とミナトの会話
:::theory 見出し             理論の小部屋
:::try / :::warn / :::tip    やってみよう・つまずき注意・ヒント
:::quiz 問題 … :::answer …   クイズ
:::deep 見出し               もっと深く（読み飛ばしてよい）
:::widget softmax            動くデモ
```

コードブロックの言語名の後ろに、`no-run`（表示だけ）、`gpu-only`、`online`、`colab-only`、`test:元の文字列=>検証用の文字列`（検証のときだけ学習回数を減らすなど）を付けられます。出力は ```` ```output ```` （実際の出力として検証）または ```` ```output-example ```` （例）で書きます。

## プライバシー

サイトに、アクセス解析・広告・入力の送信はありません。読了の印・チェックリスト・表示の明るさ・最後に開いたページは、あなたのブラウザの中だけに保存されます。
