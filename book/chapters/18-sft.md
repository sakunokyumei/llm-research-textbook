{"title": "指示に従わせる：SFT（教師ありファインチューニング）", "short": "SFT", "subtitle": "ベースモデルを「ボンゴ先生」に変身させる", "time": "2時間", "env": "gpu", "level": 4, "builds": "60問のQ&Aデータで、ベースモデル（Qwen2.5-0.5B）を「質問に答えて止まる、ダジャレ好きのボンゴ先生」にファインチューニングする。学習ループは自分で書き、最後にTRLで同じことを10行で", "theory": ["SFTのデータ形式（指示と回答の組）", "損失マスク：答えの部分だけで学ぶ", "パディングとアテンションマスク", "ファインチューニングの学習率とエポック", "壊滅的忘却と、データの質の大切さ"], "python": ["JSONL（1行1件のJSON）を読む", "`-100`（損失を無視する印）", "自作の `collate` 関数でバッチを作る", "`trl` の `SFTTrainer`"]}

:::goal
第17章で、ベースモデルは「質問をくり返す」「答えた後も止まらない」ことを見ました。この章では、たった60問のお手本で、そのベースモデルを**質問に答えて、きちんと止まり、しかもボンゴ先生の口調でダジャレを言う**モデルに変身させます。チャットモデルを作る第2段階「SFT」を、自分の手でやってみるのです。
:::

:::review-bridge 第5章・第7章・第17章とのつながり
- **第5章（交差エントロピー損失と検証データ）**：正解トークンの予測確率が高いほど損失が小さくなり、学習に使っていないデータで本当の実力（汎化）を確かめることを学びました。
- **第7章・第13章（学習ループ）**：「順伝播 → 損失計算 → `zero_grad()` → `backward()` → `step()`」の基本ループと混合精度学習を実装しました。
- **第17章（チャットテンプレート）**：`<|im_start|>user ... <|im_end|>` の台本形式と、ベースモデルが答え終わっても止まらない挙動を観察しました。

この章では、その知識をすべて合流させ、**「答えの部分だけを採点する（損失マスク `-100`）」＋「長さの違う文章をそろえる（パディングと `attention_mask`）」** を加えて、本物のLLMのSFTを自作します！
:::

:::minato
60問って、少なくないですか？ ChatGPTは何百万問も学習したって聞きました。
:::

:::sensei
「何でも答えられる賢さ」を育てるなら、何百万問も必要だ。でも「話し方」や「答え方の作法」を教えるだけなら、驚くほど少なくていい。知識は事前学習でもう身についているからね。2023年の研究（LIMA）では、質の高い1000件のお手本だけで、かなり立派なチャットモデルができた。今日は60問で、どこまで変身するか見てみよう。
:::

## 準備：GPUとデータ

GPUのランタイム（T4）で実行してください。0.5Bのモデルの**全パラメータ**を学習させるので、メモリを10GBほど使います（第15章の「16バイト × パラメータ数」の計算を思い出してください）。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_sft.jsonl
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_test.jsonl
import json
train_rows = [json.loads(line) for line in open("bongo_sft.jsonl", encoding="utf-8")]
test_rows = [json.loads(line) for line in open("bongo_test.jsonl", encoding="utf-8")]
print("学習用：", len(train_rows), "問 / 評価用：", len(test_rows), "問")
print(train_rows[0])
```

```output
学習用： 60 問 / 評価用： 12 問
{'question': '空はなぜ青いの？', 'answer': 'いい質問だ！太陽の光が空気の分子にぶつかると、波長の短い青い光ほど四方八方に散らばるんだ。これをレイリー散乱という。空いっぱいに散った青が、キミの目に届いているわけさ。散乱だけに、さんざん考えた答えだよ！'}
```

:::python JSONL
**JSONL**（JSON Lines）は、「1行に1件のJSON」を並べたファイル形式です。1件ずつ読み書きできるので、大きなデータセットでよく使われます。`json.loads(line)` で、1行の文字列をPythonの辞書に変換しています。JSONはJavaScriptの書き方から来た形式なので、Webをやったことがあるキミにはおなじみかもしれません。
:::

データは、質問（`question`）とボンゴ先生の答え（`answer`）の組です。教科書のリポジトリの `code/bongo_sft.jsonl` に置いてあるので、ブラウザで開いて全部読んでみてください。**データを自分の目で読む**のは、機械学習でいちばん大事で、いちばんサボられがちな作業です。

評価用の12問は、学習用とは**別の**質問です。「見たことのない質問にも、ボンゴ先生らしく答えられるか」を確かめるためです（第5章の検証データと同じ考え方）。

:::exercise ch18-q01
:::

## 学習前のベースモデル

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

name = "Qwen/Qwen2.5-0.5B"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).to("cuda" if torch.cuda.is_available() else "cpu")
device = model.device

def chat(question, n=150):
    msgs = [{"role": "user", "content": question}]
    inputs = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True).to(device)
    out = model.generate(**inputs, max_new_tokens=n, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)

print(chat(test_rows[0]["question"]))
```

```output-example
海の水がしょっぱいのは、海水に塩分が含まれているからです。<|im_end|>
<|im_start|>user
なぜ空は青いの？<|im_end|>
<|im_start|>assistant
空が青いのは
```

ベースモデルでも、チャットの台本形式（第1章）を渡すと、それなりに答えます。ネットにはこの形式の文章も少し混ざっているからでしょう。でも、`<|im_end|>` の後も止まらずに、勝手に次の会話を作り続けています（`skip_special_tokens=False` にして、特別なトークンも表示しています）。そして、もちろんダジャレは言いません。

:::tip モデルをfloat32で読み込む理由
今回は、モデルの全パラメータを学習させるので、`dtype=torch.float32` で読み込みます。float16のまま学習させると、小さな更新が丸められて消えてしまう（第13章のアンダーフロー）ことがあるからです。計算は後で `autocast` を使ってfloat16で速くします（混合精度）。
:::

:::exercise ch18-q02
:::

## 学習データを作る：損失マスク

SFTのデータの作り方には、大事なコツがあります。

:::theory 答えの部分だけで学ぶ（損失マスク）
SFTの目的は、「質問に対する**良い答え**」を書けるようにすることです。質問の文章そのものを予測できるようになる必要はありません。

もし質問文まで損失に含めてしまうと、モデルは「ユーザーがどんな質問をしてくるか」という質問文の言い回しの丸暗記にせっかくの学習能力を使ってしまいます。LLMに身につけてほしいのは「どんな質問が来ても、それに続く素晴らしい回答を生成すること」です。そこで、台本の中の **アシスタントの答えの部分だけ** で損失を計算し、システムの指示やユーザーの質問の部分は損失に含めません。これを **損失マスク**（loss masking）と言います。

PyTorchの `cross_entropy` は、正解のラベルが **-100** の位置を自動的に無視してくれる約束になっています。だから、質問の部分の正解ラベルを全部 -100 にしておけばよいのです。

また、答えの最後には必ず `<|im_end|>` を付けて、それも予測させます。こうすることで、モデルは「答え終わったら `<|im_end|>` を出して止まる」ことを学びます。
:::

:::scaffold 損失マスク（`ignore_index=-100`）を小さなID列で見てみよう
たとえば、質問（システム＋ユーザー）のトークンIDが `prompt_ids = [10, 20, 30]`、答え＋`<|im_end|>` のトークンIDが `answer_ids = [40, 50, 99]` だとします。

| 位置 | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `input_ids`（モデルに読ませる入力） | `10` | `20` | `30` | `40` | `50` | `99` (`<|im_end|>`) |
| `labels`（採点に使う正解ラベル） | **`-100`** | **`-100`** | **`-100`** | `40` | `50` | `99` (`<|im_end|>`) |
| 損失を計算する？ | 無視 | 無視 | 無視 | **学習する** | **学習する** | **学習する** |

- **ポイント1**：`input_ids` には質問もそのまま入るので、モデルは質問を**しっかり読んだうえで**答えを予測します。マスクするのは「採点（損失）」だけです。
- **ポイント2**：Hugging Faceの `CausalLM` は内部で自動的に1トークンずらして「位置2の次 → ラベル3（`40`）」「位置4の次 → ラベル5（`<|im_end|>`）」を採点してくれます。

```python no-run
# 理解のための最小コード（純Python版）
prompt_ids = [10, 20, 30]
answer_ids = [40, 50, 99]                      # 99 が <|im_end|>
input_ids  = prompt_ids + answer_ids           # [10, 20, 30, 40, 50, 99]
labels     = [-100] * len(prompt_ids) + answer_ids  # [-100, -100, -100, 40, 50, 99]
```
:::

```python
def build_example(question, answer):
    prompt = tok.apply_chat_template([{"role": "user", "content": question}],
                                     add_generation_prompt=True, tokenize=False)
    prompt_ids = tok(prompt, add_special_tokens=False)["input_ids"]
    answer_ids = tok(answer + "<|im_end|>\n", add_special_tokens=False)["input_ids"]
    input_ids = prompt_ids + answer_ids
    labels = [-100] * len(prompt_ids) + answer_ids          # 質問の部分は -100（無視）
    return {"input_ids": input_ids, "labels": labels}

ex = build_example(train_rows[0]["question"], train_rows[0]["answer"])
print("トークン数：", len(ex["input_ids"]), " うち学習する部分：", sum(l != -100 for l in ex["labels"]))
print("学習しない部分：", repr(tok.decode([t for t, l in zip(ex["input_ids"], ex["labels"]) if l == -100])))
print("学習する部分　：", repr(tok.decode([l for l in ex["labels"] if l != -100])))
```

```output
トークン数： 114  うち学習する部分： 78
学習しない部分： '<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user\n空はなぜ青いの？<|im_end|>\n<|im_start|>assistant\n'
学習する部分　： 'いい質問だ！太陽の光が空気の分子にぶつかると、波長の短い青い光ほど四方八方に散らばるんだ。これをレイリー散乱という。空いっぱいに散った青が、キミの目に届いているわけさ。散乱だけに、さんざん考えた答えだよ！<|im_end|>\n'
```

質問の部分（システムの指示も含む）は学習せず、答えと `<|im_end|>` だけを学習することが確かめられました。

:::exercise ch18-q03 ch18-q04 ch18-q05 ch18-q06
:::

## バッチにまとめる：パディング

例によって長さがバラバラなので、1つのバッチにまとめるには、短いものの後ろを **パディング**（詰め物）で埋めて長さをそろえます。

```python
examples = [build_example(r["question"], r["answer"]) for r in train_rows]

def collate(batch):
    L = max(len(b["input_ids"]) for b in batch)
    ids, labels, mask = [], [], []
    for b in batch:
        pad = L - len(b["input_ids"])
        ids.append(b["input_ids"] + [tok.pad_token_id] * pad)
        labels.append(b["labels"] + [-100] * pad)           # 詰め物も学習しない
        mask.append([1] * len(b["input_ids"]) + [0] * pad)  # 詰め物は見ない
    return {k: torch.tensor(v).to(device) for k, v in
            {"input_ids": ids, "labels": labels, "attention_mask": mask}.items()}

batch = collate(examples[:4])
print({k: tuple(v.shape) for k, v in batch.items()})
```

```output
{'input_ids': (4, 114), 'labels': (4, 114), 'attention_mask': (4, 114)}
```

:::theory アテンションマスク
`attention_mask` は「どこが本物のトークンで、どこが詰め物か」を表す0と1の列です。モデルは、マスクが0の位置（詰め物）にAttentionで注目しないようにします（第11章の因果マスクに、もう1つマスクを重ねるイメージ）。詰め物の正解ラベルも -100 にしたので、損失にも入りません。
:::

:::scaffold パディングと `attention_mask`：なぜ「Attention」と「損失」の両方で消すのか？
長さ2のサンプル `[10, 20]` と長さ4のサンプル `[30, 40, 50, 60]` を1つのバッチ（形 `(2, 4)`）にまとめるとき、短い1件目の末尾に2個ぶんの詰め物（例：`pad_id = 0`）を足します。

| 配列 | サンプル0（元は長さ2） | サンプル1（元は長さ4） | 詰め物の位置に入れる値と理由 |
|---|---|---|---|
| `input_ids` | `[10, 20, 0, 0]` | `[30, 40, 50, 60]` | `pad_token_id`（形を長方形にするダミーID） |
| `attention_mask` | `[1, 1, 0, 0]` | `[1, 1, 1, 1]` | **`0`**（Attentionが詰め物を参照しないように隠す） |
| `labels` | `[-100, 20, -100, -100]` | `[-100, -100, 50, 60]` | **`-100`**（詰め物の予測誤差を損失に入れない） |

もし `labels` の詰め物を `-100` にし忘れると、モデルは「答えのあとに延々とパディング記号を出し続けろ」と誤学習してしまいます。**`attention_mask=0`（見るな）と `labels=-100`（採点するな）の2重ガード**が鉄則です。

```python no-run
# 理解のための最小コード（純Python版パディング）
seqs = [[10, 20], [30, 40, 50, 60]]
L = max(len(s) for s in seqs)                              # 4
masks = [[1] * len(s) + [0] * (L - len(s)) for s in seqs]  # [[1, 1, 0, 0], [1, 1, 1, 1]]
```
:::

:::exercise ch18-q07 ch18-q08 ch18-q09
:::

## 学習ループを自分で書く

ここまで来れば、学習ループは第13章とほとんど同じです。Hugging Faceのモデルは、`labels` を渡すと、1つずらした交差エントロピー損失を自動で計算してくれます。

```python
import random

def train_sft(model, examples, epochs=3, lr=1e-5, batch_size=4, seed=0):
    random.seed(seed)
    torch.manual_seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    model.train()
    for epoch in range(epochs):
        order = list(range(len(examples)))
        random.shuffle(order)                        # 毎エポック、順番を混ぜる
        total = 0.0
        for i in range(0, len(order), batch_size):
            batch = collate([examples[j] for j in order[i:i + batch_size]])
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                loss = model(**batch).loss
            opt.zero_grad()
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            total += loss.item()
        print(f"エポック {epoch + 1}：平均損失 {total / (len(order) / batch_size):.3f}")
    model.zero_grad(set_to_none=True)   # 最後の勾配を捨てて、GPUのメモリを空ける
    model.eval()

train_sft(model, examples)
```

```output-example
エポック 1：平均損失 2.412
エポック 2：平均損失 1.538
エポック 3：平均損失 1.071
```

T4なら1分もかかりません。60問を3周（3エポック）しただけです。

:::theory ファインチューニングの学習率
事前学習では学習率 $10^{-3}$〜$10^{-4}$ くらいを使いましたが、ファインチューニングでは $10^{-5}$ 前後と**ずっと小さく**します。事前学習で苦労して身につけた知識を、壊さないように少しずつ調整したいからです。彫刻で言えば、事前学習はノミで大きく削る作業、ファインチューニングは紙やすりで仕上げる作業です。
:::

:::exercise ch18-q10 ch18-q11
:::

## 変身した！？

試す前に、1つだけ設定を足します。モデルは「答え終わったら `<|im_end|>` を出す」ことを学びましたが、`generate` に「`<|im_end|>` が出たら止まって」と教えるのは、モデルとは別の**設定**の仕事です（第17章の `generation_config`）。ベースモデルの設定では、止まる合図は `<|endoftext|>` だけなので、`<|im_end|>` も合図に加えます。

```python
im_end = tok.convert_tokens_to_ids("<|im_end|>")
model.generation_config.eos_token_id = [im_end, tok.eos_token_id]   # どちらが出ても止まる
print("止まる合図：", model.generation_config.eos_token_id)
```

```output
止まる合図： [151645, 151643]
```

この設定は、後でモデルを保存するときに、いっしょに保存されます。では、学習用には入っていない、評価用の質問で試してみましょう。

```python
for r in test_rows[:4]:
    print("Q:", r["question"])
    print("A:", chat(r["question"]))
    print()
```

```output-example
Q: なぜ海の水はしょっぱいの？
A: いい質問だ！川の水が岩の塩分を少しずつ溶かして海に運び、海で水だけが蒸発して塩が残るからなんだ。何億年もかけてたまった塩の味さ。しょっぱいけど、しょうがないね！<|im_end|>

Q: 機械学習とディープラーニングの違いは？
A: 機械学習は、データからルールを学ぶ方法全体のことだ。ディープラーニングはその中の一つで、たくさんの層を重ねたニューラルネットワークを使う。深い（ディープ）だけに、ふかーい関係だね！<|im_end|>

Q: 変数ってなに？
A: 値を入れておく名前つきの箱だよ。x = 3 と書けば、xという箱に3が入る。箱の中身はあとで入れ替えられるんだ。へんすうだけに、変数の多い人生も楽しもう！<|im_end|>

Q: 地震はなぜ起きるの？
A: 地球の表面は何枚ものプレートでできていて、それがゆっくり動いている。プレートどうしがぶつかってひずみがたまり、一気にずれると地震が起きるんだ。ずれるだけに、ずれずれな答えになっていないといいけど！<|im_end|>
```

:::sensei
ドコドコドン！ 見たかい？ 学習していない質問なのに、ボンゴ先生の口調で「！」を交えて説明して、ダジャレで締めて、`<|im_end|>` できちんと止まっている。たった60問で、口調も、答え方の型も、止まり方も覚えた。ダジャレの質は……まあ、私と同じくらいだ。
:::

（ここに載せた出力は一例です。あなたの画面ではもっと面白いダジャレ、またはもっと寒いダジャレが出るでしょう。説明の中身が間違っていることもあります。0.5Bのモデルの知識には限りがあるからです。）

:::exercise ch18-q12
:::

## 鍛えたモデルを保存する

```python
from google.colab import drive
drive.mount("/content/drive")
save_dir = "/content/drive/MyDrive/tsukuru-llm/bongo-sft"
model.save_pretrained(save_dir)
tok.save_pretrained(save_dir)
print("保存しました")
```

```output
Mounted at /content/drive
保存しました
```

0.5Bのモデルを丸ごと保存するので、ドライブを約2GB使います（float32のため）。次の章のLoRAなら、保存するのは数十MBの「差分」だけで済みます。

:::deep Hugging Faceに公開するには
`model.push_to_hub("あなたのユーザー名/bongo-sensei-0.5b")` と `tok.push_to_hub("あなたのユーザー名/bongo-sensei-0.5b")` のように、**モデルとトークナイザーの両方**を書くと、Hugging Faceにアップロードできます（Writeの権限があるトークンが必要。第17章）。トークナイザーを忘れると、ほかの人が読み込むときにエラーになります。公開するときは、モデルカードに「どのモデルを元に、どんなデータで、どう学習したか」と、元のモデルのライセンス（Qwen2.5-0.5BはApache 2.0）を書いておきましょう。
:::

## 道具を使う：TRLのSFTTrainer

鍛えたモデルを保存できたら、もう一歩。ここまで自分で書いた「損失マスク」「パディング」「学習ループ」は、Hugging Faceの **TRL**（Transformer Reinforcement Learning）というライブラリを使うと、10行ほどで書けます。中でやっていることは、あなたが書いたものとほぼ同じです。

```python
!pip install -q trl
```

```python
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

ds = Dataset.from_list([
    {"prompt": [{"role": "user", "content": r["question"]}],
     "completion": [{"role": "assistant", "content": r["answer"]}]}
    for r in train_rows
])

model2 = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32)
config = SFTConfig(output_dir="sft-bongo", num_train_epochs=3, per_device_train_batch_size=4,
                   learning_rate=1e-5, logging_steps=5, report_to="none", save_strategy="no",
                   bf16=False, fp16=torch.cuda.is_available())
trainer = SFTTrainer(model=model2, args=config, train_dataset=ds, processing_class=tok)
trainer.train()
print("学習した部分のトークン数（1件目）：", sum(l != -100 for l in trainer.train_dataset[0]["labels"]))
```

```output-example
{'loss': 2.39, 'grad_norm': 18.2, 'learning_rate': 8.9e-06, 'epoch': 0.33}
...
{'train_runtime': 41.2, 'train_loss': 1.62, 'epoch': 3.0}
学習した部分のトークン数（1件目）： 78
```

（上のログは、辞書の形で表示される環境の例です。Colabでは、学習中のログが「Step」と「Training Loss」の表で表示されます。見た目は違っても、中身は同じです。）

`prompt`（質問）と `completion`（答え）に分けたデータを渡すと、TRLが自動で答えの部分だけを学習するように損失マスクを作ってくれます。最後の行で、自分で作ったとき（78トークン）と同じ部分だけを学習していることが確かめられます。

:::python SFTConfig の設定
`SFTConfig(…)` は、学習の設定をまとめたものです。第19〜22章でも、ほぼ同じ形で使います。

- `output_dir="sft-bongo"`：途中経過などを置くフォルダの名前
- `num_train_epochs=3`：データを何周するか（エポック数）
- `per_device_train_batch_size=4`：1回に何問まとめて学習するか（バッチの大きさ）
- `learning_rate=1e-5`：学習率
- `logging_steps=5`：何ステップごとにログ（損失）を記録するか
- `report_to="none"`：学習の記録を外部のサービスに送らない
- `save_strategy="no"`：学習の途中でモデルを保存しない（ドライブの容量の節約。保存は自分でやる）
- `bf16=False, fp16=…`：混合精度の設定（下の注意を参照）

自分のデータで学習するときに変えるのは、主に `num_train_epochs`、`per_device_train_batch_size`、`learning_rate` の3つです。
:::

:::warn T4では bf16=False に
TRLは、GPUが対応していれば自動で `bf16`（第13章のbfloat16）を使おうとします。T4はbfloat16に対応していないので、`bf16=False, fp16=True` を明示しないと、エラーになったり遅くなったりします。上のコードでは、GPUがあるときだけ `fp16=True` にしています。
:::

:::exercise ch18-q13
:::

## 気をつけたいこと：忘れることもある

:::theory 壊滅的忘却とデータの質
特定のデータだけでファインチューニングしすぎると、もともと持っていた能力を忘れてしまうことがあります。これを **壊滅的忘却**（catastrophic forgetting）と言います。たとえば、今回のモデルに「英語で答えて」と頼んでも、ボンゴ先生の日本語で答えてしまうかもしれません。60問すべてが日本語だったからです。

対策は、

- 学習率を小さく、エポックを少なくする（今回は3エポック）
- いろいろな種類のデータを混ぜる（英語の質問、計算問題、断るべき質問……）
- 次の章の **LoRA** のように、元の重みは変えずに「差分」だけを学習する

そして何より、**データの質** が大事です。お手本の答えが間違っていたら、モデルは自信満々に間違いを覚えます。お手本のダジャレが寒ければ、モデルのダジャレも寒くなります。60問のデータを作るのに一番時間がかかったのは、ここだけの話です。
:::

:::scaffold 壊滅的忘却が起きる仕組みと、設定のチェック表
LLMのすべての知識（英語・数学・歴史・コード・会話）は、別々のフォルダではなく**同じ5億個の重み行列に重ねて**保存されています。そのため、狭い1種類のデータだけで強い勾配更新を繰り返すと、古い知識を支えていた重みが上書きされてしまいます。

| 症状 | 考えられる原因 | 具体的な対策 |
|---|---|---|
| 英語や計算など元の能力が急落した | 学習率が大きすぎる／エポックが多すぎる／データが単一ジャンル | 学習率を $10^{-5}$ 前後に下げ、エポックを減らし、多様な汎用データを混ぜる（または第19章のLoRAで本体を凍結） |
| 何を聞いても似たような定型句ばかり返す | 同じ60問を回しすぎて丸暗記（過学習）した | エポック数を減らす・データ件数やバリエーションを増やす |
| もっともらしい嘘や変な口調が定着した | お手本データ自体に誤りや偏りがある | 学習前にJSONLの中身を自分の目で読み、質の低い例を修正・除外する |
:::

:::try 自分のキャラクターを作ろう
`bongo_sft.jsonl` を真似して、自分だけのキャラクターのデータを作ってみましょう。たとえば「関西弁で答える先輩」「必ず最後に俳句を詠む猫」など。20〜30問あれば、口調はかなり変わります。Colabの左のファイル一覧から `bongo_sft.jsonl` をダウンロードして編集し、アップロードし直せばOKです。作ったデータは、第20章の評価でも使えます（第22章の好みの学習に使うには、質問ごとに「悪い答え」も1つずつ書き足します）。
:::

:::warn よくあるつまずき
- **`CUDA out of memory`**：全パラメータの学習はメモリを食います。`batch_size=2` にする、`model.gradient_checkpointing_enable()` を実行する（第16章）、または次の章のLoRAを使いましょう。
- **答えの後も止まらない**：「変身した！？」の節の、止まる合図（`eos_token_id`）を設定するセルを実行したか確認しましょう。それでも止まらないなら、答えの最後に `<|im_end|>` を付け忘れていないか、`build_example` を確認しましょう。止まり方も「学習」で覚えるものです。
- **TRLの節で `CUDA out of memory`**：自分で鍛えたモデルがGPUに残っています。保存が済んでいることを確かめてから、`model.to("cpu"); torch.cuda.empty_cache()` を実行して、GPUから降ろしてからTRLのセルを実行しましょう。
- **損失が下がらない・nanになる**：学習率が大きすぎます。ファインチューニングは $10^{-5}$ 前後から試しましょう。
- **何を聞いても同じ答え**：学習しすぎ（エポックが多すぎ）で丸暗記した可能性があります。エポックを減らしましょう。
:::

:::exercise ch18-q14
:::

:::checklist
- 学習用と評価用のデータを分ける理由を説明できる
- 損失マスク（-100）で、答えの部分だけを学習させるデータを作れた
- パディングとアテンションマスクでバッチを作れた
- 自分で書いた学習ループで、ベースモデルをボンゴ先生にした
- TRLのSFTTrainerで同じことをした
- 壊滅的忘却とデータの質について説明できる
:::

:::recap
- **SFT**：「指示 → 良い答え」のお手本で、ベースモデルに答え方の作法を教える
- **損失マスク**：答えと `<|im_end|>` の部分だけで学習（ほかは -100）
- 長さをそろえる**パディング**と、詰め物を見ない**アテンションマスク**
- ファインチューニングは**小さな学習率**・**少ないエポック**で。データは**質**が命
- TRLの `SFTTrainer` は、これらを自動でやってくれる
:::

:::sensei
全パラメータを鍛えるのは、0.5Bでもメモリをけっこう使った。じゃあ7Bのモデルを無料のGPUで鍛えたかったら？ 答えは次の章の **LoRA**。モデル本体には指一本触れずに、小さな「付せん」だけを学習させる、魔法のような技だ。
:::
