{"title": "少ないメモリで鍛える：LoRAと量子化", "short": "LoRAと量子化", "subtitle": "本体には指一本触れず、小さな「付せん」だけを学習する", "time": "2時間", "env": "gpu", "level": 4, "builds": "LoRA層をゼロから実装してQwenに取り付け、学習するパラメータを1%以下にしてボンゴ先生化する。さらにPEFTとQLoRA（4ビット量子化＋LoRA）で、無料GPUに大きめのモデルを載せる", "theory": ["行列のランクと低ランク近似", "LoRA：重みの変化を小さな2つの行列の積で表す", "学習するパラメータ数とメモリの節約", "量子化（absmax・int8・4ビット）と誤差", "QLoRA：4ビットの本体＋LoRA", "アダプタの保存・合体（マージ）"], "python": ["`requires_grad_(False)` で凍結する", "モジュールの差し替え（`attn.q_proj = …`）", "`peft` の `LoraConfig` と `PeftModel`", "`BitsAndBytesConfig`（4ビット読み込み）"]}

:::goal
第18章では、0.5Bのモデルの全パラメータを学習させるのに約10GBのメモリを使いました。この方法では、7Bのモデルは無料のGPUに乗りません。この章では、モデル本体の重みを**凍結**（変えない）したまま、ほんの少しの追加パラメータだけを学習する **LoRA** を、まず自分の手で実装します。さらに、モデル本体を4ビットに縮める **量子化** と組み合わせた **QLoRA** で、無料のT4でも大きめのモデルを鍛えられるようにします。
:::

:::minato
本体を変えずに鍛えるって、どういうことですか？ 筋トレしないでマッチョになる、みたいな……？
:::

:::sensei
いい例えだ（いや、そうでもない）。教科書に書き込みをする代わりに、**付せん**を貼るイメージだ。教科書（元のモデル）はきれいなまま。付せん（LoRA）に「ここはこう読み替える」と書いておく。付せんは小さいから、何枚作っても軽い。しかも剥がせば元通り。用途ごとに付せんを取り替えることもできる。
:::

## なぜ全部を学習すると重いのか

第15章で計算したとおり、AdamWで学習するときのメモリは、だいたい「16バイト × パラメータ数」でした。

| モデル | 推論（float16） | 全パラメータの学習 |
|---|---|---|
| 0.5B | 約1GB | 約8GB |
| 1.5B | 約3GB | 約24GB（T4に乗らない） |
| 7B | 約14GB | 約112GB（T4が7枚以上） |

学習のメモリの大半は、**勾配**と**Adamの記録**（慣性と歩幅）です。どちらも「学習するパラメータの数」に比例します。だったら、**学習するパラメータを減らせば**いいのです。

## 行列のランク：情報は意外と少ない

LoRAのアイデアの元になる、**ランク**（階数）という考え方を見ておきましょう。

```python
import torch
torch.manual_seed(0)
A = torch.randn(6, 2)
B = torch.randn(2, 6)
W = A @ B                       # 6×2 と 2×6 の積 → 6×6の行列
print(W.shape, "のランク：", torch.linalg.matrix_rank(W).item())
print("Wの数の個数：", W.numel(), " AとBの数の個数：", A.numel() + B.numel())
```

```output
torch.Size([6, 6]) のランク： 2
Wの数の個数： 36  AとBの数の個数： 24
```

:::math ランク：本当は何次元ぶんの情報か
6×6の行列 `W` には36個の数が並んでいますが、6×2と2×6の行列の積で作ったので、本当は**2次元ぶんの情報**しか持っていません。これを「ランクが2」と言います。表の見た目は大きくても、中身の自由度は小さいのです。

一般に、$d \times d$ の行列を、$d \times r$ と $r \times d$ の積で表すと、数の個数は $d^2$ 個から $2dr$ 個に減ります。$d = 896$（Qwen2.5-0.5Bの幅）、$r = 8$ なら、80万個が1万4千個（約1.8%）になります。
:::

:::theory LoRA：重みの「変化」は低ランクでいい
2021年にMicrosoftの研究者が提案した **LoRA**（Low-Rank Adaptation）は、次の発想に基づいています。

> ファインチューニングで重み $W$ が $W + \Delta W$ に変わるとき、その**変化 $\Delta W$ は、低いランクで十分に表せる**

事前学習で、モデルはすでに大事な能力を身につけています。ボンゴ先生の口調を覚えるのに必要な「変化」は、全体から見ればごく小さな方向の調整にすぎない、というわけです。そこで、

$$W' = W + \frac{\alpha}{r} B A$$

として、元の $W$ は**凍結**し、小さな行列 $A$（$r \times$ 入力）と $B$（出力 $\times r$）だけを学習します。$\alpha$ は効き具合を調整するハイパーパラメータです。最初は $B = 0$ にしておくので、学習を始めた瞬間のモデルは、元のモデルと完全に同じです。
:::

## LoRA層を自分で作る

```python
import torch.nn as nn

class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r=8, alpha=16):
        super().__init__()
        self.base = base
        self.base.requires_grad_(False)                       # 本体は凍結
        self.A = nn.Parameter(torch.randn(r, base.in_features) * 0.01)
        self.B = nn.Parameter(torch.zeros(base.out_features, r))   # 最初は0
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + (x @ self.A.T @ self.B.T) * self.scale

base = nn.Linear(896, 896)
lora = LoRALinear(base)
x = torch.randn(2, 896)
print("最初は元の層と同じ？", torch.allclose(base(x), lora(x)))
trainable = sum(p.numel() for p in lora.parameters() if p.requires_grad)
print(f"学習するパラメータ：{trainable:,} / 元の層：{base.weight.numel() + base.bias.numel():,}")
```

```output
最初は元の層と同じ？ True
学習するパラメータ：14,336 / 元の層：803,712
```

:::python requires_grad_(False) と nn.Parameter
`requires_grad_(False)` は「このパラメータの勾配は計算しなくていい（学習しない）」という設定です。勾配もAdamの記録も作られないので、メモリを食いません。これを **凍結**（freeze）と言います。<br>
`nn.Parameter(テンソル)` は、そのテンソルを「このモデルの学習するパラメータ」として登録します。こうしておくと、`model.parameters()` に含まれ、オプティマイザが更新してくれます。<br>
`def __init__(self, base: nn.Linear, …)` の `: nn.Linear` は **型ヒント**（「ここには全結合層が入ります」というメモ）で、動きは変わりません。第23章でもう一度出てきます。
:::

## Qwenに付せんを貼る

自作のLoRA層を、Qwen2.5-0.5B-Instructの全Attentionの `q_proj` と `v_proj`（QueryとValueを作る全結合層）に取り付けます。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_sft.jsonl
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_test.jsonl
import json
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" if torch.cuda.is_available() else "cpu"
name = "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).to(device)
model.requires_grad_(False)                       # まず全部凍結

for layer in model.model.layers:                  # 全層のAttentionに付せんを貼る
    attn = layer.self_attn
    attn.q_proj = LoRALinear(attn.q_proj).to(device)
    attn.v_proj = LoRALinear(attn.v_proj).to(device)

total = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"全パラメータ {total:,} のうち、学習するのは {trainable:,}（{trainable / total:.2%}）")
```

```output-example
全パラメータ 494,573,440 のうち、学習するのは 540,672（0.11%）
```

学習するのは、全体の**0.1%ほど**だけになりました。

`attn.q_proj = LoRALinear(attn.q_proj)` の1行で、なぜモデルの計算が変わるのでしょう？ Qwenの中では、Attentionの計算のときに `self.q_proj(x)` と、**その名前の部品**を呼び出しています。だから、`q_proj` という名前の部品を、元の層を包んだLoRA層に差し替えれば、次からはLoRA層が呼ばれるのです。部品を差し替えるだけで、Qwenのコードは1行も書き換えていません。

学習は、第18章のデータ作りと学習ループをそのまま使います（自分で書いたものを再利用！）。

```python
import random
train_rows = [json.loads(l) for l in open("bongo_sft.jsonl", encoding="utf-8")]
test_rows = [json.loads(l) for l in open("bongo_test.jsonl", encoding="utf-8")]

def build_example(question, answer):
    prompt = tok.apply_chat_template([{"role": "user", "content": question}],
                                     add_generation_prompt=True, tokenize=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    a = tok(answer + "<|im_end|>\n", add_special_tokens=False)["input_ids"]
    return {"input_ids": p + a, "labels": [-100] * len(p) + a}

def collate(batch):
    L = max(len(b["input_ids"]) for b in batch)
    pad = lambda xs, v: [x + [v] * (L - len(x)) for x in xs]
    return {"input_ids": torch.tensor(pad([b["input_ids"] for b in batch], tok.pad_token_id)).to(device),
            "labels": torch.tensor(pad([b["labels"] for b in batch], -100)).to(device),
            "attention_mask": torch.tensor(pad([[1] * len(b["input_ids"]) for b in batch], 0)).to(device)}

examples = [build_example(r["question"], r["answer"]) for r in train_rows]
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))
random.seed(0); torch.manual_seed(0)
model.train()
for epoch in range(3):
    random.shuffle(examples)
    total = 0.0
    for i in range(0, len(examples), 4):
        with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "cuda")):
            loss = model(**collate(examples[i:i + 4])).loss
        opt.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        total += loss.item()
    print(f"エポック {epoch + 1}：平均損失 {total / 15:.3f}")
model.eval()
```

```output-example
エポック 1：平均損失 2.873
エポック 2：平均損失 1.792
エポック 3：平均損失 1.415
```

:::tip LoRAの学習率は大きめ
全パラメータの学習（第18章）では学習率 $10^{-5}$ でしたが、LoRAでは $10^{-4}$〜$10^{-3}$ と大きめにします。学習するのは小さな付せんだけで、しかも $B$ が0から始まるので、ある程度大きく動かさないと効果が出ないからです。
:::

```python
def chat(question, n=150):
    inputs = tok.apply_chat_template([{"role": "user", "content": question}], add_generation_prompt=True,
                                     return_tensors="pt", return_dict=True).to(device)
    out = model.generate(**inputs, max_new_tokens=n, do_sample=False)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

print(chat(test_rows[6]["question"]))
```

```output-example
いい質問だ！星は自分の中で核融合という反応を起こして、ものすごいエネルギーを光として出しているんだ。何光年も旅してきた光が、今キミの目に届いている。星だけに、ほしい答えだったかな！
```

付せんだけで、ボンゴ先生になりました。

## 道具を使う：PEFT

自作のLoRAで仕組みが分かったら、実務では Hugging Faceの **PEFT**（Parameter-Efficient Fine-Tuning）ライブラリを使います。どの層に付せんを貼るか、ランクをいくつにするかを指定するだけです。TRLの `SFTTrainer` と組み合わせると、第18章と同じ書き方でLoRA学習ができます。

```python
!pip install -q peft trl
```

```python
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

ds = Dataset.from_list([{"prompt": [{"role": "user", "content": r["question"]}],
                         "completion": [{"role": "assistant", "content": r["answer"]}]} for r in train_rows])
lora_config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules="all-linear", task_type="CAUSAL_LM")
base_model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32)
config = SFTConfig(output_dir="lora-bongo", num_train_epochs=3, per_device_train_batch_size=4,
                   learning_rate=2e-4, logging_steps=5, report_to="none", save_strategy="no",
                   bf16=False, fp16=torch.cuda.is_available())
trainer = SFTTrainer(model=base_model, args=config, train_dataset=ds,
                     processing_class=tok, peft_config=lora_config)
trainer.model.print_trainable_parameters()
trainer.train()
```

```output-example
trainable params: 8,798,208 || all params: 502,830,976 || trainable%: 1.7497
{'loss': 2.81, 'grad_norm': 1.9, 'learning_rate': 0.000178, 'epoch': 0.33}
...
{'train_runtime': 38.5, 'train_loss': 1.71, 'epoch': 3.0}
```

`target_modules="all-linear"` は「全部の全結合層に付せんを貼る」指定です。Attentionだけでなく、フィードフォワード層にも貼ると、効果が上がることが多いと言われています。

### 付せんだけを保存する

```python
trainer.model.save_pretrained("bongo-lora-adapter")
import os
size = sum(os.path.getsize(os.path.join("bongo-lora-adapter", f)) for f in os.listdir("bongo-lora-adapter"))
print(f"保存したアダプタの大きさ：{size / 1e6:.1f} MB")
```

```output-example
保存したアダプタの大きさ：35.2 MB
```

第18章で全体を保存したときは約2GBでした。LoRAでは、付せん（**アダプタ**）だけを保存すればよいので、ずっと小さくて済みます。使うときは、元のモデルを読み込んでから、アダプタを貼り付けます。

```python
from peft import PeftModel
reloaded = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(name), "bongo-lora-adapter")
merged = reloaded.merge_and_unload()      # 付せんを本体に書き込んで、ふつうのモデルに戻す
print(type(merged).__name__)
```

```output
Qwen2ForCausalLM
```

`merge_and_unload()` は、$W' = W + \frac{\alpha}{r}BA$ を実際に計算して本体に書き込み、付せんを外します。こうすると、推論のときに追加の計算が要らなくなります。

## 量子化：数を粗くして小さくする

LoRAで、学習の**勾配とAdamの記録**は小さくなりました。残る大物は、モデル本体の重みそのものです。そこで、重みを少ないビット数で表す **量子化**（quantization）を使います。

一番シンプルな「absmax量子化」を、自分でやってみましょう。重みを、最大値（の絶対値）で割って、-127〜127の整数（8ビット）に丸めます。

```python
torch.manual_seed(0)
w = torch.randn(8) * 0.1
scale = w.abs().max() / 127                     # 最大値を127に合わせる
q = torch.round(w / scale).to(torch.int8)       # 8ビットの整数に
w_back = q.float() * scale                      # 元に戻す（逆量子化）
print("元の重み  ：", w.numpy().round(4))
print("8ビット整数：", q.numpy())
print("戻した重み：", w_back.numpy().round(4))
print("最大の誤差：", (w - w_back).abs().max().item())
```

```output
元の重み  ： [ 0.1541 -0.0293 -0.2179  0.0568 -0.1085 -0.1399  0.0403  0.0838]
8ビット整数： [  90  -17 -127   33  -63  -82   24   49]
戻した重み： [ 0.1544 -0.0292 -0.2179  0.0566 -0.1081 -0.1407  0.0412  0.0841]
最大の誤差： 0.0008392892777919769
```

:::theory 量子化の考え方
- float32（4バイト）の重みを、int8（1バイト）の整数と、1つの「縮尺」（scale）で表す。メモリは約4分の1
- 戻すと少し誤差が出る（上の例では最大0.0008）。LLMの重みはたくさんあるので、1つ1つの小さな誤差は、全体ではあまり効かないことが多い
- 4ビット（-8〜7の16段階など）まで粗くすると、メモリは8分の1。誤差は大きくなるが、工夫（重みをグループに分けて別々の縮尺を使う、正規分布に合わせた段階を使う **NF4** など）で、性能の低下を小さく抑えられる

ただし、**外れ値**（とても大きな重み）が1つあると、縮尺が大きくなり、ほかの全部の重みが粗くなってしまいます。実際の量子化手法の工夫の多くは、この外れ値との戦いです。
:::

:::fe 固定小数点と浮動小数点
基本情報で、小数の表し方に「固定小数点」と「浮動小数点」があることを習いましたね。量子化は、ある意味で浮動小数点数を「縮尺つきの固定小数点（整数）」に変換する作業です。ビット数を減らせば、表せる段階の数（8ビットなら256段階、4ビットなら16段階）が減り、誤差が増える。試験で計算した「表現できる範囲と精度」の話が、そのままLLMのメモリ節約の話になっています。
:::

## QLoRA：4ビットの本体 ＋ LoRA

**QLoRA** は、モデル本体を4ビット（NF4）に量子化して凍結し、その上にLoRAの付せんを貼って学習する方法です。本体のメモリは約4分の1、学習するのは付せんだけ。この組み合わせで、無料のT4でも数Bのモデルを鍛えられます。

次のコードは、Qwen2.5-1.5B-Instructを4ビットで読み込んでLoRA学習する例です。4ビットの読み込みには `bitsandbytes` というライブラリを使い、**GPUが必要**です。

このセルは、メニューの「ランタイム」→「セッションを再起動する」で**GPUのメモリを空にしてから**実行します。上の節のモデルがGPUに残っていると、メモリの使用量を正しく測れないうえ、メモリが足りなくなることもあるからです。再起動すると変数は消えますが、ダウンロードしたファイルは残っているので、このセルだけで動くように、必要なものを全部読み込み直しています。

```python gpu-only
!pip install -q bitsandbytes peft trl
import json, torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

train_rows = [json.loads(l) for l in open("bongo_sft.jsonl", encoding="utf-8")]
ds = Dataset.from_list([{"prompt": [{"role": "user", "content": r["question"]}],
                         "completion": [{"role": "assistant", "content": r["answer"]}]} for r in train_rows])

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
big_name = "Qwen/Qwen2.5-1.5B-Instruct"
big_tok = AutoTokenizer.from_pretrained(big_name)
big = AutoModelForCausalLM.from_pretrained(big_name, quantization_config=bnb, device_map="auto",
                                           dtype=torch.float16)   # T4はbfloat16が苦手なので、float16を指定
big = prepare_model_for_kbit_training(big)        # 本体を凍結し、学習の準備をする（下で説明）
print(f"GPUメモリ使用量：{torch.cuda.memory_allocated() / 1e9:.2f} GB")

trainer = SFTTrainer(model=big, train_dataset=ds, processing_class=big_tok,
                     peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                            target_modules="all-linear", task_type="CAUSAL_LM"),
                     args=SFTConfig(output_dir="qlora-bongo", num_train_epochs=3, per_device_train_batch_size=4,
                                    learning_rate=2e-4, logging_steps=5, report_to="none", save_strategy="no",
                                    bf16=False, fp16=True, gradient_checkpointing=True))
for p in trainer.model.parameters():              # TRLがbf16にした付せんを、T4のfp16学習用にfloat32へ戻す
    if p.requires_grad:
        p.data = p.data.float()
trainer.train()
print(f"学習中の最大GPUメモリ：{torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
```

```output-example
GPUメモリ使用量：1.6 GB
...
学習中の最大GPUメモリ：2.5 GB
```

（数字は目安です。文章の長さやライブラリの版で、少し変わります。）

`prepare_model_for_kbit_training` は、4ビットのモデルを学習する前の準備をまとめてやってくれる関数です。本体を全部凍結し、埋め込みや正規化の層のように量子化されていない部分をfloat32に戻して計算を安定させ、メモリを節約する勾配チェックポイント（第16章）をオンにします。埋め込みの表（約15万語 × 1536）がfloat32になるぶん、使用量は4ビットの本体だけのときより少し増えます。

`trainer.train()` の前の3行が、T4で動かすためのコツです。TRLは、4ビットのモデルを渡されると、学習する付せん（LoRAの $A$ と $B$）を自動でbfloat16にします。ところがT4はbfloat16が苦手で、`fp16=True` の学習と組み合わせると、最初の1歩で `not implemented for 'BFloat16'` というエラーになります。そこで、付せんだけをfloat32に戻しています。付せんは小さいので、float32にしてもメモリはほとんど増えません。

1.5Bのモデルを、3GBにも満たないメモリで学習できました。同じ方法で、7Bのモデル（準備の後で約8GB）も、15GBのT4に乗せて鍛えられます（時間はかかりますが）。

| 方法 | 1.5Bの学習メモリの目安 | 7Bの学習メモリの目安 |
|---|---|---|
| 全パラメータ（float32 ＋ AdamW） | 約24GB | 約112GB |
| LoRA（本体はfloat16） | 約4〜5GB | 約16GB以上 |
| QLoRA（本体は4ビット） | 約3〜4GB | 約6〜10GB |

（使う文章の長さやバッチの大きさで変わります。）

:::free 無料GPUで大きなモデルを鍛える作戦
1. まず0.5Bで、データと学習の設定を固める（速いので、失敗してもすぐやり直せる）
2. うまくいったら、QLoRAで1.5B → 3B → 7Bと大きくする
3. 学習したアダプタだけをドライブやHugging Faceに保存する（数十MB）

いきなり7Bで試すと、1回の失敗で何十分も失います。研究でも「小さく試してから大きく」が鉄則です。
:::

:::warn よくあるつまずき
- **`bitsandbytes` のエラー（CUDAが見つからない等）**：4ビットの読み込みにはGPUが必要です。ランタイムが「T4 GPU」になっているか確認しましょう。インストールした直後に「入っていない」と言われるときは、「ランタイム」→「セッションを再起動する」をしてから、QLoRAのセルをもう一度実行しましょう。
- **LoRAで全然変化しない**：学習率が小さすぎる（$10^{-5}$ など）ことが多いです。$10^{-4}$〜$10^{-3}$ にしてみましょう。また、`print_trainable_parameters()` で学習するパラメータが0でないか確認しましょう。
- **`merge_and_unload` 後に結果が少し変わる**：4ビットのモデルにマージすると、丸めの誤差が出ます。マージは、float16などで読み込み直した本体に対して行いましょう。
:::

:::quiz ランク
$1024 \times 1024$ の全結合層に、ランク $r = 4$ のLoRAを付けると、学習するパラメータはいくつ？（バイアスは除く）
:::answer
$A$ が $4 \times 1024$、$B$ が $1024 \times 4$ なので、$4096 + 4096 = 8192$ 個です。元の層の約105万個の0.8%です。
:::

:::quiz Bを0で始める理由
LoRAで、行列 $B$ を最初に0にしておくのはなぜ？
:::answer
学習を始めた瞬間の $BA$ が0になり、モデルが元のモデルと完全に同じ状態から出発できるからです。最初から元の能力を壊さずに、少しずつ変化を加えていけます。
:::

:::quiz 量子化の誤差
absmax量子化で、重みの中に1つだけ極端に大きな値（外れ値）があると、何が困る？
:::answer
縮尺（scale）がその外れ値に合わせて大きくなるので、ほかの普通の大きさの重みが、少ない段階でしか表されなくなり（ほとんど0に丸められるなど）、誤差が大きくなります。
:::

:::checklist
- 行列のランクと、低ランクの積で数の個数が減ることを確かめた
- LoRA層を自作し、最初は元の層と同じ出力になることを確かめた
- 自作LoRAをQwenに取り付け、0.1%のパラメータだけでボンゴ先生化した
- PEFTとTRLでLoRA学習し、アダプタだけを保存・マージした
- absmax量子化を手で計算し、誤差を確かめた
- QLoRAの仕組みと、無料GPUで大きなモデルを鍛える作戦を説明できる
:::

:::recap
- **LoRA**：重みの変化 $\Delta W$ を低ランクの $BA$ で表し、本体は凍結して $A$・$B$ だけ学習する
- 学習するパラメータが1%以下になり、勾配とAdamのメモリが激減。保存も**アダプタ**だけでよい
- **量子化**：重みを少ないビット数（8ビット・4ビット）で表してメモリを節約。外れ値が敵
- **QLoRA** ＝ 4ビットの本体 ＋ LoRA。無料のT4でも数Bのモデルを鍛えられる
:::

:::sensei
これで、キミはモデルを好きなように鍛えられるようになった。でも、ちょっと待ってほしい。「鍛えたら良くなった」と、どうやって言い切る？ 何問か試して「なんとなく良くなった」では、研究にならない。次の章は、多くの人がさぼりがちで、でも一番大事な **評価** の話だ。
:::
