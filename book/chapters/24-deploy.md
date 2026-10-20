{"title": "世界に公開する：ブラウザで動くあなたのLLM", "short": "世界に公開する", "subtitle": "HTMLとCSSとJavaScriptで、漱石GPTを誰でも使えるWebページにする", "time": "2〜3時間", "env": "cpu", "level": 3, "builds": "第13章の漱石GPTを8ビットに量子化してJSONに書き出し、JavaScriptで推論するWebページを作って、GitHub Pagesで世界に公開する（このサイトのトップページと同じもの）", "theory": ["推論だけなら、どこでも同じ計算ができる（言語を変えても同じ数式）", "量子化した重みの書き出し（第19章の実践）", "ブラウザの中で動かす利点（サーバー代0円・入力が外に出ない）", "公開のいろいろな方法：GitHub Pages・Gradio・Ollama・Hugging Face", "GGUFと量子化の名前の読み方", "公開前のチェックリスト（ライセンス・安全・プライバシー）"], "python": ["`files.download` でColabからファイルを取り出す", "JavaScriptの読み方（Pythonとの対応表）", "`python -m http.server` でローカル確認"]}

:::goal
ついに、あなたのLLMを**世界に公開**します。第13章で育てた漱石GPTを、あなたが専門学校で学んだ **HTMLとCSS** と、少しの **JavaScript** でWebページにして、**GitHub Pages**（無料）で公開します。完成すると、スマートフォンからでも、友だちのパソコンからでも、URLを開くだけであなたのGPTが動きます。このサイトのトップページで動いている漱石GPTは、まさにこの章の方法で作ったものです。
:::

:::minato
やっとHTMLとCSSの出番だ！ でも、JavaScriptでGPTって動くんですか？ Pythonじゃないとダメなんじゃ……。
:::

:::sensei
GPTの正体は、掛け算と足し算と、expと平方根の組み合わせだっただろう？ そんなもの、どんな言語でも書ける。電卓でだって（何年かかるかは別として）計算できる。言語が変わっても、数式は変わらない。第15章でGPT-2の重みを自作コードに入れたのと同じで、今度は**別の言語**に重みを入れるんだ。
:::

## 全体の流れ

1. **Colab**：第13章で保存したモデルを、Webで読める形（JSON）に書き出す
2. **パソコン**：HTML・CSS・JavaScriptのページを作り、手元で動作確認する
3. **GitHub**：ファイルをアップロードして、GitHub Pagesで公開する

## 手順1：モデルをJSONに書き出す（Colab）

Colabで新しいノートブックを作り、第13章でGoogleドライブに保存した `soseki_gpt.pt` を読み込みます。CPUのままで大丈夫です。

```python
from google.colab import drive
drive.mount("/content/drive")
```

```python
import os
ckpt = "/content/drive/MyDrive/tsukuru-llm/soseki_gpt.pt"
print("チェックポイントはある？", os.path.exists(ckpt))
```

```output-example
チェックポイントはある？ True
```

:::warn Falseだった人へ
第13章を飛ばした人や、保存に失敗した人は、第13章に戻って学習と保存をしてから進むのがおすすめです。どうしても今すぐ試したい人は、この教科書のサイトに置いてある完成品のJSON（<https://sakunokyumei.github.io/llm-research-textbook/model/soseki-gpt.json>）をダウンロードして、手順2に進んでもかまいません。
:::

書き出しの関数です。第19章のabsmax量子化を、重みの**行ごと**に行って、8ビットの整数にします。そして、JSONに入れられるように **base64**（バイト列を文字だけで表す方法）に変換します。

```python
import base64, json
import torch

def quantize_rows(w):
    w = w.float()
    if w.dim() == 1:                                   # バイアスやLayerNormはそのまま（float32）
        return {"shape": list(w.shape), "f32": base64.b64encode(w.numpy().tobytes()).decode()}
    scale = w.abs().amax(dim=1).clamp(min=1e-8) / 127  # 行ごとの縮尺
    q = torch.round(w / scale[:, None]).clamp(-127, 127).to(torch.int8)
    return {"shape": list(w.shape),
            "i8": base64.b64encode(q.numpy().tobytes()).decode(),
            "scale": base64.b64encode(scale.numpy().astype("float32").tobytes()).decode()}

ck = torch.load(ckpt, map_location="cpu")
weights = {name: quantize_rows(t) for name, t in ck["model"].items() if not name.endswith("tril")}
with open("soseki-gpt.json", "w", encoding="utf-8") as f:
    json.dump({"config": ck["config"], "chars": ck["chars"], "weights": weights}, f, ensure_ascii=False)
print("書き出したサイズ：", round(os.path.getsize("soseki-gpt.json") / 1e6, 1), "MB")
```

```output-example
書き出したサイズ： 2.5 MB
```

:::fe base64
**base64** は、どんなバイト列も、英数字と `+` `/` の64種類の文字だけで表す方法です。3バイト（24ビット）を6ビットずつ4文字に分けて表すので、サイズは約1.33倍になります。メールに画像を添付するときにも使われています。基本情報の「ビットの切り分け」の練習問題そのものですね。
:::

書き出したファイルを、自分のパソコンにダウンロードします。

```python colab-only
from google.colab import files
files.download("soseki-gpt.json")
```

## 手順2：Webページを作る（パソコン）

パソコンに `soseki-gpt` という名前のフォルダを作り、次の3つのファイルを入れます。

```text
soseki-gpt/
├── index.html          ← これから作るページ
├── minigpt.js          ← GPTの計算をするJavaScript（教科書のものを使う）
└── soseki-gpt.json     ← 手順1でダウンロードしたモデル
```

`minigpt.js` は、このサイトのリポジトリの `site/minigpt.js` です。ブラウザで <https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/site/minigpt.js> を開き、右クリック→「名前を付けて保存」で保存してください。

### index.html

ここは、あなたの得意分野です。まずは次の内容で作り、後で好きなデザインに変えてください。

```html
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>わたしの漱石GPT</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px;
           background: #faf7f0; color: #222; line-height: 1.8; }
    h1 { color: #b9501a; }
    input, button { font-size: 16px; padding: 8px 12px; border-radius: 8px; border: 1px solid #ccc; }
    button { background: #b9501a; color: white; border: none; cursor: pointer; }
    #out { white-space: pre-wrap; background: white; border-radius: 12px; padding: 16px; min-height: 8em; margin-top: 16px; }
  </style>
</head>
<body>
  <h1>わたしの漱石GPT</h1>
  <p>夏目漱石の7作品だけで学習した、約175万パラメータの小さなGPTです。ブラウザの中だけで動きます。</p>
  <input id="start" value="吾輩は">
  <button id="go" disabled>読み込み中…</button>
  <div id="out"></div>

  <script type="module">
    import { load } from "./minigpt.js";
    const model = await load("./soseki-gpt.json");
    const go = document.getElementById("go");
    const out = document.getElementById("out");
    go.textContent = "続きを書かせる";
    go.disabled = false;
    go.addEventListener("click", async () => {
      const start = document.getElementById("start").value;
      out.textContent = start;
      go.disabled = true;
      await model.generate(start, 150, 0.8, (ch) => { out.textContent += ch; });
      go.disabled = false;
    });
  </script>
</body>
</html>
```

HTMLとCSSは見慣れた姿だと思います。新しいのは最後の `<script type="module">` の部分だけです。

### minigpt.js の中身を読む

`minigpt.js` は約150行です。中で何をしているか、Pythonの対応する部分と比べてみましょう。第12章のコードと、ほぼ1対1で対応しています。

| JavaScript（minigpt.js） | Python（minigpt.py・第12章） | やっていること |
|---|---|---|
| `dequantize(w)` | — | 8ビットの整数 × 縮尺で、重みを小数に戻す（第19章） |
| `linear(W, b, x)` | `nn.Linear` | $y = Wx + b$。二重のforループで掛けて足す |
| `layerNorm(x, w, b)` | `nn.LayerNorm` | 平均を引いて標準偏差で割る（第10章） |
| `gelu(x)` | `nn.GELU` | 活性化関数（第9章） |
| `step(id, pos, cache)` の中のheadのループ | `Head.forward` | Q・K・V、内積、softmax、重みつき平均（第11章） |
| `cache[l][j].k.push(k)` | — | 過去のKeyとValueを取っておく **KVキャッシュ**（第16章） |
| `x[i] += a[i]` | `x = x + self.attn(...)` | 残差接続（第12章） |
| `sample(logits, temperature)` | `torch.multinomial` | 温度つきのサイコロ（第3章） |

:::python JavaScriptをPythonの目で読む
- `const` / `let`：変数を作る（`const` は後で入れ替えない変数）
- `function f(x) { … return y; }`：`def f(x): … return y`
- `for (let i = 0; i < n; i++) { … }`：`for i in range(n):`
- `arr.map((v) => v * 2)`：`[v * 2 for v in arr]`
- `Float32Array`：float32の数だけが並んだ配列（PyTorchのテンソルの、とても素朴な版）
- `async` / `await`：「時間のかかる処理（ファイルの読み込みなど）を待つ」書き方

インデント（字下げ）の代わりに `{ }` で範囲を表す、行の最後に `;` を付ける、くらいの違いで、考え方はPythonと同じです。
:::

:::theory 推論だけなら、どこでも動く
学習には、自動微分（第7章）やAdam（第10章）、GPUが必要でした。でも、**学習済みの重みで推論するだけ**なら、必要なのは掛け算と足し算と、exp・平方根などの簡単な関数だけです。だから、JavaScriptでも、スマートフォンでも、マイコンでも、原理的にはどこでも動かせます。

ブラウザの中で動かすことには、大きな利点があります。

- **サーバー代が0円**：計算は見る人のパソコンやスマホがやってくれる
- **入力が外に出ない**：入力した文章はどこにも送信されない（プライバシーに優しい）
- **オフラインでも動く**：一度読み込めば、ネットが切れても使える

ただし、大きなモデル（数百MB〜数GB）は、ダウンロードも計算も重くなります。175万パラメータ（2.5MB）くらいが、気軽に試せる大きさです。もっと大きなモデルをブラウザで動かすには、GPUを使うWebGPUや、専用のライブラリ（transformers.jsなど）を使います。
:::

## 手順3：手元で動作確認する

作った `index.html` をダブルクリックで開いても、**モデルが読み込めません**（ブラウザの安全のための制限で、`file://` から別のファイルを `fetch` で読めないため）。簡単なWebサーバーを立てて確認します。ターミナル（Windowsならコマンドプロンプトや PowerShell）で、`soseki-gpt` フォルダに移動して、次を実行します。

```bash
cd soseki-gpt
python -m http.server 8000
```

:::tip Windowsで、フォルダの場所でターミナルを開く
エクスプローラーで `soseki-gpt` フォルダを開き、上のアドレス欄（パスが表示されているところ）をクリックして `cmd` と入力し、<kbd>Enter</kbd> を押すと、そのフォルダでコマンドプロンプトが開きます。この場合、上の `cd soseki-gpt` は不要です。Macでは、Finderでフォルダを右クリック→「フォルダに新規ターミナル」（設定で有効にする必要がある場合あり）が便利です。
:::

ブラウザで <http://localhost:8000/> を開き、「続きを書かせる」を押して、文章が出てくれば成功です。終わったら、ターミナルで <kbd>Ctrl</kbd> + <kbd>C</kbd> を押してサーバーを止めます。

:::tip Pythonが入っていなかったら
自分のパソコンにPythonが入っていない人は、[付録A](a-setup.html)の手順で入れるか、この手順を飛ばして手順4（GitHub Pages）で直接確かめてもかまいません。
:::

## 手順4：GitHub Pagesで世界に公開する

**GitHub** は、プログラムを保存・公開するための、世界最大のサービスです。**GitHub Pages** を使うと、置いたHTMLファイルを無料でWebサイトとして公開できます（このサイトも、GitHub Pagesで公開されています）。

1. <https://github.com/> でアカウントを作る（無料）。ユーザー名はURLの一部になるので、よく考えて
2. 右上の「＋」→「New repository」で、新しい置き場所（**リポジトリ**）を作る。名前は `soseki-gpt`、**Public**（公開）を選んで「Create repository」
3. 「uploading an existing file」のリンクを押し、`index.html`、`minigpt.js`、`soseki-gpt.json` の3つをドラッグ＆ドロップして、「Commit changes」
4. リポジトリの「Settings」→ 左の「Pages」→「Build and deployment」の「Branch」で `main` と `/ (root)` を選んで「Save」
5. 1〜2分待つと、`https://あなたのユーザー名.github.io/soseki-gpt/` で公開されます

:::sensei
URLをスマートフォンで開いてごらん。キミが作ったGPTが、キミのポケットの中で動いている。サーバーもいらない、お金もかからない。友だちに送ったら、きっと驚くぞ。「これ、自分で作ったの？」って。ドコドコドン！
:::

:::free GitHub Pages の注意
- 無料で使えるのは、**Public（公開）リポジトリ**です。中身は世界中から見えるので、パスワードやトークン（第17章）、個人情報は絶対に入れないでください
- 1つのファイルは100MBまで、サイト全体は1GBまでが目安です。数百MB以上のモデルを置くのには向きません
- 学習に使った青空文庫の作品は著作権が切れていますが、自分で集めたデータで学習したモデルを公開するときは、データの権利も確認しましょう
:::

## そのほかの公開・共有の方法

GitHub Pagesは小さなモデル向けです。Qwenのような大きめのモデルを人に使ってもらうには、ほかの方法もあります。

### Colabで一時的に公開する：Gradio

**Gradio** は、Pythonだけでチャット画面などのWebアプリを作れるライブラリです。Colabで `share=True` にすると、72時間有効な公開URLが発行されます。第18〜19章のボンゴ先生モデルを、友だちに試してもらうのにぴったりです。

```python
!pip install -q gradio
import gradio as gr
from transformers import pipeline

bot = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct", device_map="auto")

def text_of(content):
    if isinstance(content, list):          # 新しいGradioでは、文字以外の部品のリストのこともある
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content

def reply(message, history):
    messages = [{"role": h["role"], "content": text_of(h["content"])} for h in history]
    messages.append({"role": "user", "content": text_of(message)})
    out = bot(messages, max_new_tokens=200)
    return out[0]["generated_text"][-1]["content"]

demo = gr.ChatInterface(reply, title="ボンゴ先生に質問しよう")
print(reply("こんにちは！", []))
```

```output-example
こんにちは！何かお手伝いできることはありますか？
```

```python colab-only
demo.launch(share=True)
```

```output-example
* Running on public URL: https://xxxxxxxxxxxxxxxx.gradio.live
```

:::warn Gradioの版の違い
Gradioは版によって書き方が少しずつ変わります。古い解説記事に `gr.ChatInterface(…, type="messages")` と書いてあっても、新しい版（6系）ではこの引数がなくなっていて、エラーになります。エラーが出たら、まずGradioの版（`print(gr.__version__)`）と、公式ドキュメントを確認しましょう。
:::

`model=` の部分を、第18章で保存したフォルダ（`/content/drive/MyDrive/tsukuru-llm/bongo-sft`）に変えれば、あなたのボンゴ先生が公開されます。Colabのセッションが切れると、URLも使えなくなります。

### 自分のパソコンで動かす：Ollama

**Ollama**（オラマ）は、LLMを自分のパソコンで簡単に動かせる無料のアプリです。<https://ollama.com/> からインストールして、ターミナルで次を実行するだけで、Qwen2.5-0.5Bと会話できます（初回はダウンロードに時間がかかります）。

```bash
ollama run qwen2.5:0.5b
```

インターネットにつながっていなくても動き、入力した内容が外に送られることもありません。少し性能の良いパソコンなら、`qwen2.5:7b` なども動きます。

:::theory GGUFと、量子化の名前
OllamaやLM Studioなどのアプリは、**GGUF** という形式のモデルファイルを使います。llama.cpp というC++で書かれた高速な推論プログラムのための形式で、量子化した重みをまとめて1つのファイルにしたものです。

ファイル名についている `Q4_K_M` や `Q8_0` は、量子化の方法の名前です。`Q4` は約4ビット、`Q8` は約8ビット。数字が小さいほどファイルは小さく、性能は少し下がります。迷ったら `Q4_K_M` がよく使われる、バランスの良い選択です。第19章で手計算した量子化が、ここで使われているわけです。
:::

### Hugging Faceで共有する

学習したモデルやLoRAのアダプタは、Hugging Faceにアップロードして共有できます（第18章の「もっと深く」）。アプリを公開する **Spaces** は、2026年10月時点で、無料アカウントでは種類が限られています（CPUで動くGradioアプリの新規作成には有料プランが必要で、無料では「ZeroGPU」を使うSpaceが2つまで、または**静的なHTMLのSpace**が使えます）。静的なSpaceなら、この章で作ったページ（3つのファイル）をそのまま置いて公開することもできます。サービスの条件はよく変わるので、使う前に公式ドキュメントで確認しましょう。

## 公開前のチェックリスト

:::warn 公開する前に確かめること
1. **ライセンス**：元のモデル（Qwen2.5はApache 2.0）と、学習データのライセンスを守っているか。モデルカードやページに書いたか
2. **秘密の情報**：トークン、パスワード、個人情報が、コードやデータに入っていないか
3. **出力の注意書き**：「AIが生成した文章で、内容が正しいとは限りません」と書いたか
4. **悪用の可能性**：誰かを傷つける文章を簡単に作れてしまわないか
5. **お金**：クレジットカードの登録が必要なサービスを、知らないうちに使っていないか（0円の原則）
:::

:::try 自分のページをデザインしよう
`index.html` のCSSを書き換えて、自分だけのデザインにしましょう。和紙風の背景、縦書き（`writing-mode: vertical-rl`）、温度のスライダー（`<input type="range">`）、生成した文章をX（旧Twitter）で共有するボタン……。HTMLとCSSの腕の見せどころです。完成したら、URLを第26章の卒業制作のポートフォリオに載せましょう。
:::

:::quiz ブラウザで動かす利点
LLMをサーバーではなく、見る人のブラウザの中で動かすと、どんな利点がある？ 欠点は？
:::answer
利点：サーバー代がかからない、入力した内容が外部に送信されない、一度読み込めばオフラインでも動く。欠点：モデルのダウンロードと計算が見る人の端末の負担になるので、大きなモデルには向かない。
:::

:::quiz file:// で動かない理由
`index.html` をダブルクリックで開くと、モデルが読み込めないのはなぜ？
:::answer
ブラウザの安全のための制限で、`file://` で開いたページからは、`fetch` で別のファイルを読み込めないからです。`python -m http.server` などで簡単なWebサーバーを立てて、`http://localhost` で開く必要があります。
:::

:::checklist
- 第13章のモデルを、8ビットに量子化してJSONに書き出した
- `minigpt.js` の主な関数が、Pythonのどの部品に対応するか説明できる
- 手元のWebサーバーで、自分の漱石GPTを動かした
- GitHub Pagesで公開し、スマートフォンからも開けた
- Gradio・Ollama・Hugging Faceの使い分けを説明できる
- 公開前のチェックリストを確認した
:::

:::recap
- 推論は掛け算と足し算の組み合わせなので、**どの言語でも**書ける。JavaScriptならブラウザで動く
- ブラウザで動かすと、**サーバー代0円**・**入力が外に出ない**
- 重みは**量子化**して**base64**でJSONに入れ、`minigpt.js` で読み込む
- **GitHub Pages**で無料公開。大きめのモデルは **Gradio**（一時公開）や **Ollama**（ローカル）で
- 公開前に、ライセンス・秘密情報・注意書き・悪用・お金をチェック
:::

:::sensei
第6部、完走だ！ キミのLLMは、もう世界のどこからでも動かせる。残るは第7部、研究の入口だ。最新のLLMが使っている部品（RoPE、RMSNorm、SwiGLU、MoE）を、キミのGPTに移植して、本当に良くなるのかを**実験で確かめる**。そして最後に、卒業制作と、2030年までの地図を描こう。
:::
