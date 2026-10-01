# ゼロから、LLMを研究する。

sakunokyumei の日本語LLM教科書。算数から実装・再現実験・研究へ進むための講義と演習。

本文・コード・サイトはAI（OpenAI Codex）を用いて作成しています。出典照合・実行検証の範囲はサイトの編集方針に記載します。原資料のPDF、個人向けの記載、連絡先、元の文書メタデータは公開しません。

公開サイト：https://sakunokyumei.github.io/llm-research-textbook/

56章の講義、少数の新語と小例から講義へ進む学習ページ、解答付き演習、CPUで動くTransformer・BPE・検索・方策勾配・統計比較のラボを収録。第6〜56章はページ単位で中断・再開でき、長い参照ページも別に引けます。
研究ガイドは2026年9月30日を確認日とし、一次資料の確認範囲と未検証の範囲を区別しています。

## 開発

Pythonで以下を実行します。制作時の検証はPython 3.14です。

```sh
python -m pip install -r requirements-site.txt
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

`python verify.py`は内部リンク・exercise構造・本文のPythonコードを検証します。本文のコード実行にはNumPyとPyTorchも必要です。
`python build.py --output docs`でGitHub Pages用の静的サイトを生成します。Pagesの公開元はmainブランチの`/docs`です。
サイトに外部JavaScript、アクセス解析、広告、入力送信はありません。再開メモは端末内のブラウザに保存し、ページごとに削除できます。ブラウザ間の同期は行いません。

研究実験は `labs/README.md` を参照してください。

原資料とのテーマ対応は`pages/coverage.md`、出典と検証方針は`pages/references.md`、検証記録は`verification/`にあります。
公開対象は教材・コード・検証済み静的出力に限定し、原本PDF・私的メモ・認証情報・個人プロフィールは含めません。
