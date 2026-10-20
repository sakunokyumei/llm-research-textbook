{"title": "ターミナル・Linux・Git", "short": "ターミナル・Linux・Git", "subtitle": "黒い画面と、コードの保存・共有の早見表"}

## ターミナルとは

**ターミナル**（黒い画面、コマンドライン）は、文字でコンピュータに命令する画面です。Colabでは、セルの先頭に `!` を付けると、その行がLinuxのコマンドとして実行されます。自分のパソコンでは、Windowsなら「ターミナル」やPowerShell、Macなら「ターミナル」アプリを使います。

:::tip Colabで練習できる
Linuxのコマンドは、Colabのセルで `!ls` のように試せます。壊しても、セッションを再起動すれば元に戻るので、安心して練習しましょう。
:::

## よく使うコマンド

| コマンド | 意味 | 例 |
|---|---|---|
| `pwd` | 今いる場所（フォルダ）を表示 | `pwd` |
| `ls` | ファイルの一覧 | `ls -la`（隠しファイルも詳しく） |
| `cd` | フォルダを移動 | `cd tsukuru-llm` / `cd ..`（1つ上へ） |
| `mkdir` | フォルダを作る | `mkdir data` |
| `cp` | コピー | `cp a.txt b.txt` |
| `mv` | 移動・名前の変更 | `mv old.txt new.txt` |
| `rm` | 削除（元に戻せない！） | `rm temp.txt` |
| `cat` | ファイルの中身を表示 | `cat kokoro.txt` |
| `head` / `tail` | 最初・最後の数行を表示 | `head -n 5 kokoro.txt` |
| `wc` | 行数・文字数を数える | `wc -l data.jsonl` |
| `grep` | 文字を探す | `grep 先生 kokoro.txt` |
| `wget` / `curl` | インターネットからダウンロード | `wget https://…/minigpt.py` |
| `nvidia-smi` | GPUの状態を表示 | `nvidia-smi` |
| `du -sh` | フォルダの大きさ | `du -sh *` |

Windowsのコマンドプロンプトでは、`ls` の代わりに `dir`、`cat` の代わりに `type` を使います（PowerShellなら `ls` や `cat` も使えます）。

:::warn rm は慎重に
`rm` で消したファイルは、ごみ箱に入らず、元に戻せません。特に `rm -rf`（フォルダを中身ごと強制的に消す）は、場所を間違えると大惨事です。実行する前に `pwd` で今いる場所を確かめましょう。
:::

## パス（ファイルの住所）

- **絶対パス**：一番上から書く住所。`/content/drive/MyDrive/tsukuru-llm/soseki_gpt.pt`
- **相対パス**：今いる場所から見た住所。`./data/kokoro.txt`（`.` は今いる場所、`..` は1つ上）

HTMLで `<img src="img/logo.png">` と書くときの考え方と同じです。

## Git と GitHub

**Git** は、ファイルの変更の歴史を記録する道具です。「いつ、何を、なぜ変えたか」をセーブポイントとして残せるので、壊しても前の状態に戻せます。**GitHub** は、Gitで管理したファイルをインターネット上に置いて、共有・公開するサービスです（第24章でGitHub Pagesを使いました）。

:::tip まずはブラウザだけでOK
第24章のように、GitHubのWebページからファイルをアップロードするだけでも、十分に使えます。Gitのコマンドは、慣れてきたら少しずつ覚えれば大丈夫です。
:::

### Gitの基本の流れ

```bash
git init                      # このフォルダをGitで管理し始める
git add index.html            # 記録するファイルを選ぶ（ステージング）
git commit -m "漱石GPTのページを追加"   # セーブポイントを作る（コミット）
git log --oneline             # これまでのセーブポイントを見る
```

GitHubのリポジトリとつなげて、アップロードする（**プッシュ**）には次のようにします（`あなたの名前` は自分のユーザー名に）。

```bash
git remote add origin https://github.com/あなたの名前/soseki-gpt.git
git branch -M main
git push -u origin main
```

最初のプッシュでは、GitHubへのログインを求められます。パスワードの代わりに「個人用アクセストークン」が必要になることがあるので、GitHubの公式ドキュメント（「Managing your personal access tokens」）を参照してください。トークンは、Hugging Faceのトークン（第17章）と同じく、家の鍵として大切に扱います。

| 用語 | 意味 |
|---|---|
| リポジトリ | ファイルと、その変更の歴史をまとめた置き場所 |
| コミット | セーブポイント。変更内容と、短いメッセージを記録する |
| プッシュ | 手元のコミットを、GitHubにアップロードする |
| プル | GitHubの変更を、手元にダウンロードする |
| ブランチ | 歴史の枝分かれ。試したいことを、本流を壊さずに試せる |
| `.gitignore` | Gitで管理しないファイル（大きなモデル、秘密の情報など）を書いておくファイル |

:::warn GitHubに上げてはいけないもの
- トークン、パスワード、APIキー
- 個人情報
- 大きすぎるファイル（1ファイル100MB以上はそもそも置けない。モデルの重みはHugging Faceへ）

うっかり上げてしまったトークンは、ファイルを消すだけでは不十分です（歴史に残るため）。すぐにそのトークンを無効にしましょう。
:::

:::quiz パス
今 `/content/tsukuru-llm` にいるとき、`../data/a.txt` はどこを指す？
:::answer
`/content/data/a.txt` です。`..` で1つ上の `/content` に上がってから、`data/a.txt` に進みます。
:::
