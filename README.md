# つくってわかるLLM

手を動かしながら学ぶ、日本語のLLM（大規模言語モデル）の教科書です。Pythonの初歩から始めて、自分でGPTを作り、学習させ、既製のモデルを鍛え（SFT・LoRA・DPO）、評価し、検索やツールとつなぎ、Webに公開するところまで進みます。理論は、実際に必要になった場所で、その場で学びます。

公開サイト：https://sakunokyumei.github.io/llm-research-textbook/

- 全27章と付録10本。各章に、Google Colabでそのまま開けるノートブックがあります
- 基本的に0円で始められます。Google Colabの無料GPU（T4）で動き、混雑や無料枠の変動で使えない日はKaggle（電話番号確認が必要）やCPU短縮手順で進められます（無料枠の上限・仕様はサービス側の変更で変動するため、最新条件は各公式案内を確認してください）
- 第1章の45〜60分で本物のLLMと会話し、第4章で自分の言語モデルが夏目漱石風の文章を書きます
- 第13章で学習させた漱石GPTは、サイトのトップページでブラウザだけで動きます

## 本文・コード・サイトの作成について

本文・コード・サイトはAI（Claude Code）を用いて作成しています。各章のコードは、下の検証手順ですべて実行して確かめています。表示されている出力は、実際に実行した出力です。例として示した出力には、そうと書いてあります。事前学習済みモデルを使うコードは、同じ構造の小さな模擬モデルで動作を確かめています。そのため、本物のモデルの答えの質までは保証できません。検証の範囲は、付録「この教室について」と「学習者シミュレーション報告」に書いてあります。

以前の版（全56章の講義形式）は `legacy/` に残してあります。

## フォルダの構成

| フォルダ | 中身 |
|---|---|
| `book/` | 原稿です。`chapters/`（本文）、`exercises/`（章別の確認問題・類題・自力実装JSON）、`appendix/`（付録）、`curriculum.json`（章の順番）、`glossary.json`（用語集）、`home.html`（トップページ）があります |
| `site/` | CSS、JavaScript（`app.js`、`study.js`：自動採点・間隔復習・7段階進捗・2コース切替、`widgets.js`、`minigpt.js`）、画像です |
| `code/` | 章で使うPythonのファイルとデータです（`minigpt.py`、SFT・DPO・RAG用のJSONL） |
| `tools/` | サイトの生成（`build.py`、`mdfallback.py`）、コードの検証（`verify.py`）、演習・自動採点の検証（`test_exercises.py`）、ブラウザE2E検証（`test_site_e2e.py`）、学習者シミュレーション（`persona.py`）の道具です |
| `docs/` | 生成されたサイトです（`review.html`・`exercises-index.json` を含む）。GitHub Pagesはmainブランチの `/docs` を公開します |
| `notebooks/` | 生成されたColab用のノートブックです |
| `verification/` | 検証の記録です（`code-report.json`、`persona-metrics.json`） |
| `legacy/` | 以前の版です |

## サイトの生成

PythonとNode.jsを使います（数式をKaTeXで生成するため）。ビルド・テスト用の依存は `requirements-dev.txt`、各章のPythonコードをローカルで実行するための推奨バージョン範囲は `requirements-book.txt` にまとめています。`markdown-it-py` が入っていないオフライン環境でも、`tools/mdfallback.py` により自動で生成できます。数式が変わっていなければ、Node.jsがなくても `book/.mathcache.json` を使って生成できます。

```sh
pip install -r requirements-dev.txt          # ビルド・検証用（markdown-it-py, nbformat, playwright）
python tools/build.py                        # docs/ と notebooks/ を生成
python -m http.server 8765 --directory docs  # http://localhost:8765 で確認
```

原稿は `book/` にあります。`docs/` と `notebooks/` は直接編集せず、`tools/build.py` で作り直してください。

## 検証とCI

GitHub Actions（`.github/workflows/ci.yml`）では、`main` へのpushおよびPull Request時に以下を自動実行します（GPU専用セルの実機実行はCPUランナーでは行わず、検証範囲を明示しています）。

```sh
node --check site/*.js                       # JavaScript構文チェック
python tools/build.py                        # docs/・notebooks/ 再生成（差分チェック）
python tools/test_exercises.py --self-test   # 検証スクリプト自体の異常系自己テスト
python tools/test_exercises.py               # 全章の演習JSON・自動採点・純Pythonコード・アンカー検証
python tools/test_notebooks_and_code.py      # 全章コード構文・純Python実行・ノートブック整合性・nbformat 4.5検証
python tools/verify.py --links-only --check  # リンク切れ・未展開数式/Markdown・minigpt整合性の読み取り専用検証
python tools/persona.py --check              # 学習者シミュレーション（読み取り専用チェック）
python tools/test_site_e2e.py                # Playwrightによる全40ページPC/スマホ・自動採点・検索・復習・互換性E2E検証
# （PyTorch/Transformers導入環境での全コード実行検証：pip install -r requirements-book.txt）
python tools/testkit/make_fakes.py           # 小さな模擬モデルを .cache/fakes/ に作成
python tools/verify.py                       # 全章のコードを実行し、リンクも確認
```

各章は、新しいColabのセッションと同じように、空のフォルダで上から順に実行します。GPUが必要なセル（4ビット量子化など）とオンライン専用のセル（ログイン、公開リンク）は飛ばし、そのことを記録します。

## 原稿の書き方（抜粋）

本文はMarkdownです。次の囲みが使えます。

```text
:::sensei / :::minato        ボンゴ先生とミナトの会話
:::scaffold 見出し           基礎の補足（じっくり理解コースでは展開、標準コースでは折りたたみ）
:::review-bridge 見出し      前章までの知識とのつながり・復習ブリッジ
:::theory 見出し             理論の小部屋
:::try / :::warn / :::tip    やってみよう・つまずき注意・ヒント
:::exercise ch01-q01 ...     インタラクティブ確認問題・類題・自力実装（book/exercises/*.jsonから読込）
:::deep 見出し               もっと深く（読み飛ばしてよい）
:::widget softmax            動くデモ
```

コードブロックの言語名の後ろに、`no-run`（表示だけ）、`gpu-only`、`online`、`colab-only`、`test:元の文字列=>検証用の文字列`（検証のときだけ学習回数を減らすなど）を付けられます。出力は ```` ```output ```` （実際の出力として検証）または ```` ```output-example ```` （例）で書きます。

## プライバシー

サイトに、アクセス解析・広告・入力の送信はありません。読了の印・チェックリスト・確認問題の解答履歴・復習予定・コース設定・表示の明るさ・最後に開いたページは、あなたのブラウザの中（`localStorage`）だけに保存されます。バックアップや端末移行には「学習・復習」ページのJSONエクスポート／インポートを使えます。

## ライセンスと権利表示

- **本教材の本文・独自コード・演習・独自データセット・図版**：ライセンスは著者による正式選定・明記を待っている状態です（現時点ではリポジトリ直下に `LICENSE` ファイルは置いていません。再利用・転載の可否は著者の正式な案内を確認してください）。
- **同梱・参照している第三者アセットのライセンス**：
  - **KaTeX**（`tools/katex/`・`site/katex/`・`docs/katex/`）：MIT License（各フォルダに `LICENSE` を同梱）
  - **青空文庫（夏目漱石作品）**：パブリックドメイン（著作権保護期間満了、`aozorahack/aozorabunko_text` 経由で取得）
  - **事前学習済みモデル**：Qwen2.5（Apache License 2.0）、GPT-2（MIT License）、`intfloat/multilingual-e5-small`（MIT License）
  - **チャットテンプレート検証用ファイル**（`tools/testkit/qwen_chat_template.jinja`）：Qwen2.5由来（Apache License 2.0）
  - **参考実装の着想**：Andrej Karpathy 氏 `nanoGPT`（MIT License）ほか（詳細は `book/appendix/j-references.md`）
