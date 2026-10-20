{"title": "環境構築大全：0円で本格開発", "short": "環境構築大全", "subtitle": "Colab・Kaggle・自分のパソコン。どれを、いつ、どう使うか"}

この付録は、環境構築で困ったときの「辞書」です。最初から全部読む必要はありません。困ったところだけ開いてください。

:::sensei
環境構築で挫折する人は多い。でも安心してほしい。この教科書は、**ブラウザとGoogleアカウントだけ**で最後まで進めるように作ってある。自分のパソコンに何かを入れるのは、やりたくなってからで十分だ。
:::

## 0円の原則

この教科書で使うサービスは、すべて**無料のプラン**で足ります。

1. **クレジットカードを登録しない**。「無料トライアル」でも、カードを登録すると、期限が過ぎたあとに自動で課金されることがあります
2. **有料プランへの誘導は、閉じてよい**。Colabの「Colab Pro」、Hugging Faceの「PRO」などの案内が出ても、この教科書の範囲では不要です
3. **困ったら小さくする**。GPUが足りない、時間が足りない、というときは、お金で解決する前に、モデルやデータを小さくする（第19章の量子化・LoRAなど）

:::free 無料の枠は変わる
無料で使える範囲（GPUの種類や時間）は、サービスの都合でよく変わります。この付録の内容は2026年10月時点のものです。数字は目安として読み、最新の情報は各サービスの公式ページで確かめてください。
:::

## 3つの環境の比べ方

| | Google Colab | Kaggle Notebooks | 自分のパソコン |
|---|---|---|---|
| 必要なもの | Googleアカウント | Kaggleアカウント（GPUには電話番号の確認が必要） | Pythonのインストール |
| GPU | 無料で使えることがある（T4など）。混雑時や使いすぎると使えない | 無料（T4×2またはP100）。週あたりの利用時間の上限あり（目安30時間前後、変動する） | NVIDIAのGPUがあれば使える。なければCPU（MacはApple SiliconのGPUも可） |
| 1回の長さ | 最長12時間ほど。操作しないと早めに切断 | 1回最長12時間 | 無制限 |
| ファイルの保存 | 切断で消える。Googleドライブに保存する | 「Save Version」で出力を保存 | ずっと残る |
| おすすめの場面 | この教科書の基本。すぐ始められる | ColabのGPUが使えないとき。長めの学習 | 第2部の小さな実験、第24章の公開ページの確認 |

**迷ったらColab。** ColabでGPUがつながらないときはKaggle、と覚えておけば十分です。

## Google Colab の使い方

### 始め方

1. <https://colab.research.google.com/> を開いて、Googleアカウントでログイン
2. 「ノートブックを新規作成」
3. セルにコードを書いて、<kbd>Shift</kbd> + <kbd>Enter</kbd> で実行

学校のGoogleアカウントでは、管理者の設定でColabが使えないことがあります。その場合は、個人のGoogleアカウントを作って使いましょう。

### よく使う操作

| やりたいこと | 操作 |
|---|---|
| セルを実行して次へ | <kbd>Shift</kbd> + <kbd>Enter</kbd> |
| コードのセルを追加 | 画面上の「+ コード」 |
| GPUにする | 「ランタイム」→「ランタイムのタイプを変更」→「T4 GPU」→「保存」 |
| 全部やり直す | 「ランタイム」→「セッションを再起動して、すべてのセルを実行する」 |
| メモリを空にする | 「ランタイム」→「セッションを再起動する」 |
| Linuxのコマンド | 行の先頭に `!` を付ける（例：`!ls`、`!nvidia-smi`） |
| ファイルを見る | 左のフォルダのアイコン |
| ファイルを手元に保存 | ファイル一覧で右クリック→「ダウンロード」、または `files.download("名前")` |
| 秘密の情報（トークン） | 左の鍵のアイコン（シークレット）。第17章 |

### この教科書の「Colabで開く」ボタン

各章の先頭の「Colabで開く（完成ノート）」を押すと、その章のコードが全部入ったノートブックがColabで開きます。

- 開くと「警告：このノートブックはGoogleが作成したものではありません」と出ます。この教科書のノートブックであることを確かめて、「このまま実行」を押してください
- そのままでは、変更しても保存されません。「ファイル」→「ドライブにコピーを保存」で、自分のドライブにコピーしてから使いましょう

:::tip おすすめの使い方
完成ノートを最初から実行するだけだと、「動いた」で終わってしまいがちです。おすすめは、**自分の新しいノートブックに、教科書のコードを1セルずつ貼って（または打って）実行する**こと。完成ノートは、うまくいかないときの答え合わせに使いましょう。
:::

### Googleドライブにつなぐ

Colabのファイルは、接続が切れると消えます。大事なもの（学習したモデルなど）は、Googleドライブに保存します。

```python no-run
from google.colab import drive
drive.mount("/content/drive")
# これで /content/drive/MyDrive/ が、自分のドライブの中身になる
```

初回は、Googleアカウントへのアクセスを許可する画面が出ます。この教科書では、`MyDrive/tsukuru-llm/` というフォルダにまとめて保存しています。

### GPUが使えないとき

「使用量の上限に達したため、現在GPUに接続できません」のような表示が出たら、

1. まずは**CPUのまま**進める（第0〜12章、第14〜16章、第25章はCPUで大丈夫）
2. 時間をおいて（数時間〜1日）、もう一度試す
3. **Kaggle** を使う（次の節）

GPUを使わないときは、ランタイムを「CPU」に戻しておくと、GPUの利用枠を節約できます。

## Kaggle Notebooks の使い方

**Kaggle** は、データ分析のコンペティションで有名なサイトで、無料でGPUを使えるノートブックがあります。

1. <https://www.kaggle.com/> でアカウントを作る
2. 設定（Settings）で**電話番号の確認**をする（GPUとインターネット接続を使うのに必要）
3. 「Create」→「New Notebook」
4. 右側の「Session options」（または「Settings」）で、
   - 「Accelerator」を「GPU T4 x2」または「GPU P100」にする
   - 「Internet」をオンにする（モデルやデータのダウンロードに必要）

Colabとの違いは次のとおりです。

| | Colab | Kaggle |
|---|---|---|
| ドライブへの保存 | `drive.mount` | 使えない。`/kaggle/working/` に保存して「Save Version」 |
| `from google.colab import …` | 使える | 使えない（その行は飛ばす） |
| GPUの残り時間 | 表示されない | アカウントの設定画面などで確認できる |

この教科書のコードは、`google.colab` を使う行（ドライブ、`files.download`、`userdata`）以外は、Kaggleでもそのまま動きます。

## 自分のパソコンで動かす

第2部（第4〜10章）や第25章の小さな実験は、自分のパソコンのCPUでも動きます。自分のパソコンに環境を作っておくと、ネットがなくても練習でき、第24章の公開ページの確認もできます。

### 手順1：Pythonを入れる

**Windows**

1. <https://www.python.org/downloads/> から、最新の安定版（3.12や3.13など）のインストーラーをダウンロード
2. インストール画面の最初で、**「Add python.exe to PATH」に必ずチェック**を入れてから「Install Now」
3. 「スタート」→「ターミナル」（またはPowerShell）を開き、次を入力して版が表示されれば成功

```powershell
python --version
```

**Mac**

1. <https://www.python.org/downloads/> から、macOS用のインストーラーをダウンロードして実行
2. 「ターミナル」を開いて確認（Macでは `python3` と打つことが多い）

```bash
python3 --version
```

### 手順2：作業用のフォルダと「仮想環境」を作る

**仮想環境**は、プロジェクトごとに道具（ライブラリ）を分けて入れておく仕組みです。別のプロジェクトの道具の版とぶつからないようにする、引き出しの仕切りのようなものです。

```bash
mkdir tsukuru-llm
cd tsukuru-llm
python -m venv .venv
```

仮想環境を **有効にする**（使い始める）コマンドは、OSによって違います。

```powershell
# Windows（PowerShell）
.venv\Scripts\Activate.ps1
```

```bash
# Mac / Linux
source .venv/bin/activate
```

行の先頭に `(.venv)` と表示されたら成功です。

:::warn Windowsで「スクリプトの実行が無効」と出たら
PowerShellで `Activate.ps1` を実行したときに「このシステムではスクリプトの実行が無効になっている」と出たら、次の1行を一度だけ実行してから、もう一度試してください（自分のユーザーだけ、署名されたスクリプトの実行を許可する設定です）。

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
:::

### 手順3：道具を入れる

```bash
pip install torch transformers datasets tokenizers peft trl sentence-transformers matplotlib matplotlib-fontja jupyter
```

数分かかります。NVIDIAのGPUを持っている人は、<https://pytorch.org/get-started/locally/> で自分の環境を選ぶと、GPU版のPyTorchを入れるコマンドが表示されます。

:::tip uv を使うともっと速い
**uv** という道具を使うと、仮想環境の作成と道具のインストールがとても速くなります。<https://docs.astral.sh/uv/> の手順でuvを入れたら、`uv venv` で仮想環境を作り、`uv pip install …` で道具を入れられます。慣れてきたら試してみてください。
:::

### 手順4：エディタ（VS Code）とノートブック

**VS Code**（Visual Studio Code）は、無料で人気のプログラム用エディタです。<https://code.visualstudio.com/> から入れて、拡張機能の「Python」と「Jupyter」を追加すると、VS Codeの中でColabのようなノートブック（`.ipynb`）を使えます。この教科書の「ノートブックをダウンロード」で取ってきたファイルも、そのまま開けます。

右上の「カーネルの選択」で、手順2で作った `.venv` を選ぶのを忘れないでください。

### GPUを自動で選ぶコード

自分のパソコンで動かすときは、教科書のコードの `device` の行を、次のようにすると、NVIDIAのGPU（cuda）、MacのGPU（mps）、CPUの順に自動で選べます。

```python no-run
import torch
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"        # Apple Silicon の Mac
else:
    device = "cpu"
print(device)
```

:::warn パソコンでのColab専用のコード
`from google.colab import drive` などの行は、Colab専用です。自分のパソコンではエラーになるので、その行は飛ばし、保存先を `"./saved"` のような自分のフォルダに変えてください。`!pip install …` の行も、ターミナルで `pip install …` として実行します。
:::

## 章ごとのおすすめ環境

| 章 | おすすめ | CPUでも？ | メモ |
|---|---|---|---|
| 1〜3 | Colab（GPU） | ○（少し遅い） | 0.5Bのモデルを動かす |
| 4〜12 | Colab（CPU）・自分のPC | ◎ | 小さな実験。第10章は数分かかる |
| 13 | Colab・Kaggle（GPU） | △（1時間以上） | 漱石GPTの学習 |
| 14〜16 | Colab（CPU）・自分のPC | ◎ | 第15章はGPT-2（500MB）のダウンロードあり |
| 17〜23 | Colab・Kaggle（GPU） | △ | Qwenの学習。QLoRAはGPU必須 |
| 24 | Colab ＋ 自分のPC ＋ GitHub | ◎ | Webページを作って公開 |
| 25 | Colab（CPU）・自分のPC | ◎ | 比較実験 |
| 26 | どれでも | — | 卒業制作 |

## そのほかのアカウント

| サービス | 何に使う？ | 章 | 料金 |
|---|---|---|---|
| Hugging Face | モデル・データのダウンロードと共有、トークン | 17〜 | 無料アカウントで十分 |
| GitHub | コードの保存、GitHub Pagesでの公開 | 24, 26 | 無料 |
| Ollama | 自分のパソコンでLLMを動かす | 24 | 無料 |

## それでも困ったら

1. [付録E エラー辞典](e-errors.html)で、エラーメッセージを探す
2. [付録H 挫折しない作戦帳](h-plan.html)の「AIに質問するテンプレート」で、ChatGPTやClaudeなどに聞く
3. 公式ドキュメントを見る（Colab：<https://research.google.com/colaboratory/faq.html>、Kaggle：<https://www.kaggle.com/docs/notebooks>）
