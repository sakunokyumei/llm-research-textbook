{"title": "Hugging Faceと事前学習済みモデル", "short": "事前学習済みモデル", "subtitle": "世界中のモデルを借りる前に知っておくこと：ベースとチャット、ライセンス、プロンプト", "time": "90分", "env": "gpu", "level": 3, "builds": "ベースモデルとチャットモデルの比較実験、複数ターンの会話、few-shotプロンプトの効果測定。Hugging Faceのアカウントとトークンも安全に準備する", "theory": ["事前学習→SFT→好みの学習（ベースとチャットの違い）", "モデルカードとライセンス", "チャットテンプレートと複数ターンの会話", "プロンプト技法（zero-shot・few-shot・段階的に考える）とその限界", "モデルの大きさとGPUメモリの見積もり", "safetensors（安全な重みのファイル形式）"], "python": ["`AutoModelForCausalLM` / `AutoTokenizer`", "`apply_chat_template`", "`generation_config`", "Colabのシークレット（`userdata`）"]}

:::goal
第4部まで、あなたは「LLMを作る側」でした。ここからは、世界中の研究機関や企業が公開している**事前学習済みモデル**を借りて、自分の目的に合わせて鍛える側に回ります。この章ではその準備として、Hugging Faceでのモデルの選び方、ベースモデルとチャットモデルの違い、プロンプトの工夫とその限界を、実験しながら学びます。
:::

:::minato
第1章でQwenを使ったときは、名前をコピペしただけでした。
:::

:::sensei
それで正解だった。でも、これからモデルを鍛えるなら、借りるモデルの「素性」を知っておく必要がある。どんなデータで育ったのか、何をしていいライセンスなのか、どれくらいの大きさなのか。中古車を買うときに、車検証を見るのと同じだ。
:::

## Hugging Face Hub を歩く

**Hugging Face Hub**（<https://huggingface.co/>）は、LLMを含むAIモデルとデータセットの、世界最大の置き場です。GitHubのAI版と考えてください。ブラウザで開いて、検索窓に `Qwen2.5-0.5B-Instruct` と入れてみましょう。モデルのページ（**モデルカード**）には、次のような情報が書いてあります。

| 項目 | 何が分かる？ |
|---|---|
| 説明（Model card） | どんな目的で作られたか、どんなデータで学習したか、性能、使い方 |
| ライセンス（License） | 商用利用してよいか、改変して公開してよいか |
| Files and versions | 重みのファイル（`model.safetensors`）、設定（`config.json`）、トークナイザー |
| パラメータ数・テンソル型 | 大きさ（0.5Bなど）と、保存されている数の形式（bfloat16など） |

:::theory ライセンスは必ず読む
モデルにも、ソフトウェアと同じようにライセンス（利用条件）があります。

- **Apache 2.0 / MIT**：商用利用も改変も自由（Qwen2.5の多くのサイズ、など）
- **独自ライセンス**：Llama（Meta）やGemma（Google）は、独自の利用規約に同意する必要がある。条件付きで商用利用可
- **CC BY-NC（非営利）**：研究や個人の学習はOKだが、商用は不可

学校の課題や個人の勉強ならほとんど問題ありませんが、**作ったものを公開したり、アルバイト先や就職先で使ったりする**ときには、必ず確認しましょう。学習に使ったデータセットのライセンスも同様です。
:::

## ベースモデルとチャットモデル

Qwen2.5-0.5Bには、2つの版があります。`Qwen2.5-0.5B`（**ベースモデル**）と、`Qwen2.5-0.5B-Instruct`（**チャットモデル**、指示に従うモデル）です。同じ質問をして、違いを見てみましょう。GPUのランタイムで実行してください。

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

gpu = torch.cuda.is_available()
dtype = torch.float16 if gpu else torch.float32

def load(name):
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype, device_map="auto")
    return tok, model

base_tok, base = load("Qwen/Qwen2.5-0.5B")
chat_tok, chat = load("Qwen/Qwen2.5-0.5B-Instruct")
print("読み込み完了")
```

```output
読み込み完了
```

ベースモデルに、質問の文章をそのまま渡してみます。

```python
def complete(tok, model, text, n=60):
    inputs = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=n, do_sample=False)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

print(complete(base_tok, base, "日本で一番高い山は何ですか？"))
```

```output-example
日本で一番高い山は何ですか？
日本で一番高い山は何ですか？
日本で一番高い山は何ですか？
日本で一番高い山は何ですか？
```

:::sensei
同じ質問をくり返している！ ベースモデルは「質問に答える」ことを教わっていない。ネットで「質問文」の次によく来るのは……別の質問文（よくある質問の一覧ページなど）だからね。ベースモデルは、ひたすら**ネットの文章の続き**を書く。それだけだ。
:::

答えさせたいなら、「答えが続きそうな文章」にしてあげればいいのです。

```python
print(complete(base_tok, base, "問：日本で一番高い山は何ですか？\n答：", n=30))
```

```output-example
富士山です。富士山は標高3776メートルで、静岡県と山梨県にまたがっています。
問：日本で一番長い川は何ですか？
答：
```

答えた後、また次の「問」を勝手に作り始めました。止まるタイミングを知らないのです。一方、チャットモデルは……

```python
def ask(tok, model, messages, n=100):
    inputs = tok.apply_chat_template(messages, add_generation_prompt=True,
                                     return_tensors="pt", return_dict=True).to(model.device)
    out = model.generate(**inputs, max_new_tokens=n, do_sample=False)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

print(ask(chat_tok, chat, [{"role": "user", "content": "日本で一番高い山は何ですか？"}]))
```

```output-example
日本で一番高い山は富士山です。標高は3,776メートルで、静岡県と山梨県の境にあります。
```

きちんと答えて、きちんと止まりました。

:::theory LLMができるまでの3段階
チャットモデルは、ふつう次の3段階で作られます。

1. **事前学習**（pre-training）：大量の文章で「次のトークン予測」を学ぶ（第13〜15章でやったこと）。ここでできるのが**ベースモデル**。知識と文章力は身につくが、会話の作法は知らない
2. **SFT**（教師ありファインチューニング）：「質問 → 良い答え」の例を数万〜数百万件、チャットテンプレート（第1章の台本形式）で学ばせる。会話の作法と、`<|im_end|>` で止まることを覚える（**第18章**）
3. **好みの学習**（RLHF・DPOなど）：同じ質問への2つの答えのどちらが良いかを人間が選び、良い方を出しやすくする。安全性や丁寧さもここで整える（**第22章**）

ベースモデルは「知識豊富だけど空気が読めない人」、チャットモデルは「それに接客研修を受けさせた人」、というイメージです。
:::

## チャットテンプレートと複数ターンの会話

第1章で見た台本形式を、もう少し詳しく見ておきます。会話を続けるには、**これまでの会話を全部** `messages` に入れて渡します。LLMは、前回の会話を覚えていません。毎回、台本の最初から読み直しているのです。

```python
messages = [
    {"role": "system", "content": "あなたは親切なアシスタントです。"},
    {"role": "user", "content": "私の名前はミナトです。"},
    {"role": "assistant", "content": "こんにちは、ミナトさん！"},
    {"role": "user", "content": "私の名前は何でしたっけ？"},
]
print(chat_tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
```

```output
<|im_start|>system
あなたは親切なアシスタントです。<|im_end|>
<|im_start|>user
私の名前はミナトです。<|im_end|>
<|im_start|>assistant
こんにちは、ミナトさん！<|im_end|>
<|im_start|>user
私の名前は何でしたっけ？<|im_end|>
<|im_start|>assistant

```

```python
print(ask(chat_tok, chat, messages))
```

```output-example
あなたの名前はミナトさんです。
```

:::theory 「記憶」の正体
ChatGPTなどのアプリが会話を覚えているように見えるのは、アプリが**過去の会話を毎回まとめてLLMに送っている**からです。会話が長くなると、その分トークンが増え、計算が重くなり（第16章のKVキャッシュ）、やがてコンテキスト長（第2章）の上限に達します。長い会話で、最初のほうの話を忘れてしまうのはこのためです。
:::

## プロンプトの工夫と、その限界

モデルの重みを変えずに、**入力の書き方（プロンプト）だけで**性能を上げる工夫を、プロンプトエンジニアリングと呼びます。小さな実験で効果を確かめてみましょう。お題は「レビューが肯定的か否定的かを判定する」です。

```python
reviews = [
    ("このラーメン、スープが最高においしかった！", "肯定"),
    ("店員さんの態度が悪くて二度と行かない。", "否定"),
    ("値段のわりに量が少なくてがっかり。", "否定"),
    ("駅から近くて便利、また来たいです。", "肯定"),
    ("注文してから40分も待たされた。", "否定"),
    ("期待していなかったけど、意外とよかった。", "肯定"),
]

def classify(review, few_shot=False):
    msgs = [{"role": "system", "content": "レビューが肯定的なら「肯定」、否定的なら「否定」とだけ答えてください。"}]
    if few_shot:   # 例を2つ見せる
        msgs += [{"role": "user", "content": "最高の一日でした。"}, {"role": "assistant", "content": "肯定"},
                 {"role": "user", "content": "最悪の対応でした。"}, {"role": "assistant", "content": "否定"}]
    msgs.append({"role": "user", "content": review})
    return ask(chat_tok, chat, msgs, n=5).strip()

for few in [False, True]:
    correct = sum(classify(r, few) == label for r, label in reviews)
    print(("few-shot " if few else "zero-shot"), f"正解 {correct}/{len(reviews)}")
```

```output-example
zero-shot 正解 4/6
few-shot  正解 6/6
```

:::theory プロンプト技法
- **zero-shot**：お手本なしで、指示だけを与える
- **few-shot**：答え方のお手本（例）を数個見せてから聞く。小さなモデルほど、出力の形式がそろって効果が大きい
- **段階的に考えさせる**（Chain-of-Thought）：「ステップごとに考えてから答えてください」と頼むと、計算や推論の問題で正答率が上がることがある。答えの前に考える過程を書かせることで、その過程が次のトークンの手がかりになるため（第1章：LLMは自分の出力を読みながら次を予測する）
- **役割（system）**：第1章のボンゴ先生のように、立場や口調を指定する

ただし、プロンプトには限界があります。上の6問では正解数が変わりましたが、**6問は少なすぎて、偶然の差かもしれません**。本当に効果があるかを確かめるには、もっと多くの問題と、統計の考え方が必要です（第20章）。また、小さなモデルに知らない知識はプロンプトでは教えられませんし、毎回お手本を入れるとトークン（お金と時間）を食います。そこで、モデル自体を鍛える **ファインチューニング**（第18〜19章）や、資料を検索して渡す **RAG**（第21章）の出番になります。
:::

:::try 段階的に考えさせる
`ask(chat_tok, chat, [{"role": "user", "content": "りんごが3個入った箱が4箱あり、2個食べました。残りは何個？"}])` と、同じ質問の最後に「ステップごとに考えてから答えてください。」を付けたものを比べてみましょう。小さなモデルなので、どちらも間違えるかもしれません。それも大事な観察結果です。
:::

## 生成の設定を確かめる

モデルには、作った人がおすすめする生成の設定が付いてきます。

```python
print(chat.generation_config)
```

```output-example
GenerationConfig {
  "bos_token_id": 151643,
  "do_sample": true,
  "eos_token_id": [
    151645,
    151643
  ],
  "pad_token_id": 151643,
  "repetition_penalty": 1.1,
  "temperature": 0.7,
  "top_k": 20,
  "top_p": 0.8
}
```

温度0.7、top-p 0.8、top-k 20、くり返しペナルティ1.1。第3章と第16章で学んだつまみが、全部出てきました。`eos_token_id` の151645は `<|im_end|>`（第2章）。これが出たら生成を止める、という設定です。

## モデルの大きさとGPUメモリ

借りるモデルを選ぶとき、一番の制約はGPUのメモリです。**推論（使うだけ）** に必要なメモリは、だいたい「パラメータ数 × 1個のバイト数」です。

```python
def infer_gb(n_params_billion, bytes_per_param):
    return n_params_billion * bytes_per_param

print("        float16   8ビット   4ビット")
for size in [0.5, 1.5, 3, 7, 14]:
    print(f"{size:4}B  {infer_gb(size, 2):6.1f}GB {infer_gb(size, 1):6.1f}GB {infer_gb(size, 0.5):6.1f}GB")
```

```output
        float16   8ビット   4ビット
 0.5B     1.0GB    0.5GB    0.2GB
 1.5B     3.0GB    1.5GB    0.8GB
   3B     6.0GB    3.0GB    1.5GB
   7B    14.0GB    7.0GB    3.5GB
  14B    28.0GB   14.0GB    7.0GB
```

T4（約15GB）なら、float16で3B程度まで余裕を持って動かせます。7Bはfloat16だとギリギリ（実際には計算用のメモリも必要なので厳しい）ですが、**4ビットに量子化**すれば3.5GBで動きます。量子化は第19章で学びます。

:::theory safetensors
モデルの重みのファイルには `model.safetensors` という形式がよく使われます。昔よく使われていた `pytorch_model.bin`（Pythonの `pickle` 形式）は、読み込むときに**任意のプログラムが実行される**危険がありました。知らない人が公開したファイルを開いたら、ウイルスが動く、ということが理論上ありえたのです。`safetensors` は数の並びだけを保存する形式なので、そうした危険がありません。知らない人のモデルを使うときは、safetensors形式を選びましょう。
:::

## Hugging Faceのアカウントとトークン

第18章以降で、自分で鍛えたモデルをHugging Faceに保存したり、利用規約への同意が必要なモデルを使ったりするには、**アカウント**と**アクセストークン**が必要です。

1. <https://huggingface.co/join> で無料アカウントを作る（メールアドレスの確認まで）
2. 右上のアイコン →「Settings」→「Access Tokens」→「Create new token」
3. 種類（Token type）は、最初は **Read**（読み取り専用）を選ぶ。モデルをアップロードするときだけ **Write** の権限があるものを作る
4. 表示されたトークン（`hf_` で始まる文字列）をコピー

:::warn トークンは「家の鍵」
アクセストークンは、あなたのアカウントの鍵です。**ノートブックのコードに直接書いてはいけません**。ノートブックを人に見せたり、GitHubに上げたりしたときに、鍵ごと渡してしまうからです。Colabでは、左側の **鍵のアイコン（シークレット）** に `HF_TOKEN` という名前で保存し、「ノートブックからのアクセス」をオンにします。すると、コードに書かなくても、自動で使われるようになります（第1章で出た黄色い警告が消えます）。もし漏らしてしまったら、すぐにHugging Faceの設定画面でそのトークンを削除（Invalidate）しましょう。
:::

コードからトークンを使う必要があるときは、次のように取り出します（シークレットが設定されていないとエラーになります）。

```python online
from google.colab import userdata
from huggingface_hub import login
login(token=userdata.get("HF_TOKEN"))
```

:::free 無料でできること
Hugging Faceの無料アカウントで、公開モデル・データセットのダウンロード、自分のモデル・データセットの公開（公開リポジトリ）ができます。アプリを公開する「Spaces」は、無料アカウントだと使える種類が限られます（2026年10月時点の公式ドキュメントでは、CPUで動くGradioアプリの新規作成には有料プランが必要で、無料では「ZeroGPU」のSpaceが2つまで、または静的ページのSpaceが使えます）。第24章では、0円で確実に公開できる方法を紹介します。
:::

:::warn よくあるつまずき
- **`OSError: … is not a local folder and is not a valid model identifier`**：モデル名のつづりが違うか、利用規約への同意が必要なモデル（gated model）です。Hugging Faceのモデルページで「Agree and access」を押し、`HF_TOKEN` を設定しましょう。
- **`CUDA out of memory`**：モデルを2つ同時に読み込んでいるとメモリを食います。使わなくなったモデルは `del base` で消し、`torch.cuda.empty_cache()` を実行しましょう。
- **ベースモデルが同じ文をくり返す**：正常です（この章の実験のとおり）。会話させたいならチャットモデル（Instruct）を使いましょう。
:::

:::quiz ベースとチャット
ベースモデルに「日本の首都は？」と聞くと、同じ質問をくり返すことがあるのはなぜ？
:::answer
ベースモデルは「ネットの文章の続きを書く」ことしか学んでいないからです。ネットには、質問文の後に別の質問文が続く文章（よくある質問の一覧など）がたくさんあるので、それを真似します。質問に答えて止まる作法は、SFT（第18章）で身につけます。
:::

:::quiz メモリ
7Bのモデルを4ビットに量子化すると、重みはだいたい何GB？ T4で動く？
:::answer
$7 \times 0.5 = 3.5$GB。計算用のメモリを足しても、T4（約15GB）で動かせます。
:::

:::quiz トークン
Hugging Faceのアクセストークンを、ノートブックのコードに直接書いてはいけないのはなぜ？
:::answer
ノートブックを共有したりGitHubに上げたりしたときに、トークン（アカウントの鍵）が他人に見えてしまうからです。Colabのシークレット機能に保存して使いましょう。
:::

:::checklist
- モデルカードで、説明・ライセンス・大きさを確認した
- ベースモデルとチャットモデルの違いを実験で確かめた
- 複数ターンの会話を `messages` で渡せた
- zero-shotとfew-shotを比べ、「6問では少なすぎる」理由を説明できる
- モデルの大きさから、必要なGPUメモリを見積もれた
- Hugging Faceのアカウントを作り、トークンをColabのシークレットに保存した
:::

:::recap
- チャットモデルは、**事前学習 → SFT → 好みの学習** の3段階で作られる。ベースモデルは「続きを書く」だけ
- 会話の「記憶」は、毎回これまでの会話全体を台本にして渡しているだけ
- プロンプトの工夫（few-shotなど）は手軽だが、効果は**十分な数の問題で測る**必要があり、知識の追加には限界がある
- 推論メモリ ≈ パラメータ数 × バイト数。T4ならfloat16で3B程度、4ビットなら7Bも動く
- モデルの**ライセンス**を確認し、トークンは**シークレット**で管理する
:::

:::sensei
次の章では、いよいよ「接客研修」を自分でやる。ベースモデルに、質問に答えて止まる作法を教える **SFT** だ。まずは自作の漱石GPTで仕組みを確かめてから、Qwenを「ボンゴ先生」に変身させよう。ダジャレの質は保証しない。
:::
