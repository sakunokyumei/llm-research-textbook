{"title": "少ないメモリで鍛える：LoRAと量子化", "short": "LoRAと量子化", "subtitle": "本体には指一本触れず、小さな「付せん」だけを学習する", "time": "2時間", "env": "gpu", "level": 4, "builds": "LoRA層をゼロから実装してQwenに取り付け、学習するパラメータを1%以下にしてボンゴ先生化する。さらにPEFTとQLoRA（4ビット量子化＋LoRA）で、無料GPUに大きめのモデルを載せる", "theory": ["行列のランクと低ランク近似", "LoRA：重みの変化を小さな2つの行列の積で表す", "学習するパラメータ数とメモリの節約", "量子化（absmax・int8・4ビット）と誤差", "QLoRA：4ビットの本体＋LoRA", "アダプタの保存・合体（マージ）"], "python": ["`requires_grad_(False)` で凍結する", "モジュールの差し替え（`attn.q_proj = …`）", "`peft` の `LoraConfig` と `PeftModel`", "`BitsAndBytesConfig`（4ビット読み込み）"]}

:::goal
第18章では、0.5Bのモデルの全パラメータを学習させるのに約10GBのメモリを使いました。この方法では、7Bのモデルは無料のGPUに乗りません。この章では、モデル本体の重みを**凍結**（変えない）したまま、ほんの少しの追加パラメータだけを学習する **LoRA** を、まず自分の手で実装します。さらに、モデル本体を4ビットに縮める **量子化** と組み合わせた **QLoRA** で、無料のT4でも大きめのモデルを鍛えられるようにします。
:::

:::review-bridge 第1章・第6章・第18章とのつながり
- **第1章・第15章（VRAMの見積もり）**：学習時のメモリは「重み＋勾配＋Adamの記録 ≒ 16バイト × パラメータ数」で決まり、T4 GPUの16GB上限が大きな壁になることを学びました。
- **第6章（行列のかけ算の形）**：形 `(m, k)` の行列と `(k, n)` の行列を掛けると `(m, n)` になるルールを使います。LoRAの $BA$ と `x @ A.T @ B.T` はまさにこの形の組み合わせです。
- **第18章（全パラメータSFT）**：損失マスク `-100` とパディングで作ったボンゴ先生データを、そのままこの章のLoRA学習に再利用します！

この章では、**「なぜ低ランク行列 $BA$ でパラメータが1%以下に縮むのか」「なぜ $B=0$・$A$ はランダムに初期化するのか」「量子化の丸め誤差はどう計算されるのか」** を手計算と実装の両面からマスターします。
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

:::exercise ch19-q01
:::

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

:::math ランクとLoRA（$W' = W + \frac{\alpha}{r}BA$）：7ステップで理解する
**① 解決したい問題**：巨大な重み行列 $W$（たとえば 7B モデルにある $4096 \times 4096 = 1{,}677\text{万}$ 個の重み）を直接更新すると、勾配とAdamの記録だけでVRAMがパンクしてしまう。元の重み $W$ を凍結したまま、ほんのわずかなパラメータ数で表現力豊かな調整 $\Delta W$ を加えたい。

**② 素朴な方法では困る理由**：全要素を直接学習すると 16バイト × パラメータ数でメモリ不足になる。かといって最後の1層だけを学習するだけでは、モデル全体の口調や推論パターンを十分に変えられない。

**③ 発想（低ランク近似）**：6×6の行列 `W` には36個の数が並んでいますが、6×2と2×6の行列の積で作ったので、本当は**2次元ぶんの情報（ランク2）**しか持っていません。2021年にMicrosoftの研究者が提案した **LoRA**（Low-Rank Adaptation）は、「ファインチューニングでの重みの**変化 $\Delta W$** は低いランク $r$ で十分に表せる」という発見に基づき、変化ぶんだけを2つの細い行列 $B$ と $A$ の積に分解します。

**④ 記号表と数式**：

$$W' = W + \Delta W = W + \frac{\alpha}{r} B A$$

| 記号 | 形（shape） | 凍結／学習 | 意味 |
|---|---|---|---|
| $W$ | $(d_{\text{out}},\; d_{\text{in}})$ | **凍結**（更新しない） | 事前学習済みの元の重み行列 |
| $A$ | $(r,\; d_{\text{in}})$ | **学習する** | 入力を細い $r$ 次元へ圧縮（ランダム正規分布で初期化） |
| $B$ | $(d_{\text{out}},\; r)$ | **学習する** | $r$ 次元を元の出力次元へ展開（**すべて `0` で初期化**） |
| $r$ | スカラー整数（例：4, 8, 16） | ハイパーパラメータ | ランク（通り道の細さ・ボトルネックの幅） |
| $\alpha$ | スカラー（例：16, 32） | ハイパーパラメータ | 変化の効き具合を調整する倍率（$\frac{\alpha}{r}$ を掛ける） |

**⑤ 具体的な手計算でパラメータ削減量を確かめよう**：
一般の $d_{\text{out}} \times d_{\text{in}}$ の層で、元のパラメータ数は $d_{\text{out}} d_{\text{in}}$ 個、LoRAは $r(d_{\text{in}} + d_{\text{out}})$ 個です。
- **7Bクラスの層（$4096 \times 4096$、$r = 8$）**：
  - 元の重み $W$：$4096 \times 4096 = \mathbf{16{,}777{,}216}$ 個（約 16.78M）
  - LoRA（$A$ と $B$）：$8 \times (4096 + 4096) = \mathbf{65{,}536}$ 個（約 65.5K）
  - 割合：$65{,}536 \div 16{,}777{,}216 \approx \mathbf{0.39\%}$！（99.6%削減！）
- **この章のQwen2.5-0.5B（$896 \times 896$、$r = 8$）**：
  - 元の重み $W$：$896 \times 896 = 802{,}816$ 個 → LoRA：$8 \times (896 + 896) = \mathbf{14{,}336}$ 個（約 **1.79%**）

**⑥ なぜ「$B = 0$、$A =$ ランダム正規分布」で初期化するのか？**
1. **ステップ0で元のモデルを完全に守る**：$B = 0$ なら $\Delta W = \frac{\alpha}{r}BA = 0$ となり、学習開始瞬間の出力は事前学習済みモデルと**100%一致**します（最初から元の能力を壊さない！）。
2. **なぜ $A$ まで `0` にしてはいけないのか？**：連鎖律より、$B$ の勾配は $A$ に比例し、$A$ の勾配は $B$ に比例します。もし**両方とも `0`** にすると、$A$・$B$ 両方の勾配がずっと `0` のままになって学習が一歩も進みません！ $A$ をランダム（非ゼロ）にしておくことで、ステップ1から $B$ に非ゼロの勾配が流れて動き出し、ステップ2以降は $A$ も一緒に学習されます。

**⑦ 理解のための最小Pythonコード**：

```python no-run
d_in, d_out, r = 4096, 4096, 8
orig = d_in * d_out                 # 16,777,216
lora = r * (d_in + d_out)           # 65,536
print(f"{lora / orig:.2%}")         # 0.39%
```
:::

:::exercise ch19-q02 ch19-q03 ch19-q04
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

:::scaffold `x @ self.A.T @ self.B.T` のテンソル形状トレース（なぜ `.T` が要るのか？）
PyTorchの `nn.Linear(in_features, out_features)` は重みを `(out_features, in_features)` で持ち、入力 `x`（形 `(batch, in_features)`）に右から転置を掛けます。LoRAの2つの行列も同じ流儀で `A: (r, d_in)`、`B: (d_out, r)` と定義しているため、左から順に次のように形が変化します（例：`batch=2, d_in=896, r=8, d_out=896`）。

| ステップ | 式 | テンソルの形 | 役割 |
|---|---|---|---|
| 入力 | `x` | `(2, 896)` | バッチ2件 × 896次元 |
| 圧縮 | `x @ self.A.T` | `(2, 896) @ (896, 8) → (2, 8)` | 細いボトルネック（ランク8）へギュッと圧縮 |
| 展開 | `(x @ self.A.T) @ self.B.T` | `(2, 8) @ (8, 896) → (2, 896)` | 出力896次元へ戻して `self.base(x)` に足す |

`B @ A` を先に計算して `(896, 896)` の巨大行列を作らず、左から `(x @ A.T) @ B.T` と細い `(2, 8)` を経由するのが省メモリ＆高速のコツです！
:::

:::exercise ch19-q05 ch19-q06 ch19-q07
:::

## Qwenに付せんを貼る

:::tip 実行環境とリソースの目安（後半のQLoRAはGPU必須）
- **環境**：自作LoRAとPEFT節（0.5B）は無料GPU（T4）推奨（VRAM約3〜4GB、学習約1分）。後半の **QLoRA節（1.5B・4ビット量子化）は `bitsandbytes` がCUDAを必要とするためGPU必須**（T4でVRAM約4GB、約1〜2分）です。
- **ダウンロードと保存**：0.5B（約1GB）＋QLoRA節で1.5B（約3.1GB）。保存するLoRAアダプタは約35MBで済みます。
- **GPUが使えない日の代替**：行列のランク・自作 `LoRALinear`・absmax量子化の手計算セルは**CPUで数秒**で動きます。0.5Bの自作LoRA学習もCPUで `train_rows[:16]`・`epochs=1` に絞れば動作確認できます。QLoRA節だけはGPU確保後（またはKaggle T4）に実行してください。
- **ライブラリ互換性**：`dtype=` は `transformers >= 4.56`、`device_map="auto"` には `accelerate` が必要です（推奨環境は `requirements-book.txt`）。
:::

自作のLoRA層を、Qwen2.5-0.5B-Instructの全Attentionの `q_proj` と `v_proj`（QueryとValueを作る全結合層）に取り付けます。

```python
!wget -nv https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_sft.jsonl
!wget -nv https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_test.jsonl
import json, os
for fname in ("bongo_sft.jsonl", "bongo_test.jsonl"):
    if not os.path.exists(fname):
        raise RuntimeError(f"{fname} のダウンロードに失敗しました。ネットワーク接続を確認して再実行するか、付録E（エラー辞典）を参照してください。")
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
    n_steps = 0
    for i in range(0, len(examples), 4):
        with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "cuda")):
            loss = model(**collate(examples[i:i + 4])).loss
        opt.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        total += loss.item()
        n_steps += 1
    print(f"エポック {epoch + 1}：平均損失 {total / n_steps:.3f}")
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

:::exercise ch19-q08
:::

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

:::exercise ch19-q09
:::

## 量子化：数を粗くして小さくする

LoRAで、学習の**勾配とAdamの記録**は小さくなりました。残る大物は、モデル本体の重みそのものです。そこで、重みを少ないビット数で表す **量子化**（quantization）を使います。

一番シンプルな「対称absmax量子化」を、数式と手計算から確認してからコードで動かしましょう。

:::math 対称absmax量子化と逆量子化誤差：7ステップで理解する
**① 解決したい問題**：float32（4バイト）の重み $w$ を、int8（1バイト）や4ビット（0.5バイト）の小さな整数 $q$ に縮めてVRAMを4分の1〜8分の1にしたい。

**② 素朴な方法の失敗**：そのまま小数点以下を切り捨てて整数にすると、LLMの重みのほとんどは `[-0.5, +0.5]` の小さな小数なので、全部 `0` になって情報が消えてしまう。

**③ 発想**：まず重みの中の最大絶対値 $\max_i |w_i|$ を整数上限 $Q_{\max}$（8ビット符号付きなら `127`、4ビット符号付きなら `7`）にぴったり合わせる**縮尺（scale）** $s$ を作り、割って四捨五入する。使うときは $s$ を掛け戻す（逆量子化）。

**④ 記号表と数式**：

$$s = \frac{\max_i |w_i|}{Q_{\max}}, \qquad q_i = \operatorname{round}\!\left(\frac{w_i}{s}\right), \qquad \hat{w}_i = q_i \cdot s, \qquad \text{誤差}_i = |w_i - \hat{w}_i|$$

| 記号 | 意味 | Pythonでの対応 |
|---|---|---|
| $w_i$ | 元のfloat32の重み | `w` |
| $Q_{\max}$ | 整数表現の最大値（8bitなら `127`、4bitなら `7`） | `(1 << (bits - 1)) - 1` |
| $s$ | 縮尺（scale：1目盛りあたりの幅） | `max(abs(x) for x in w) / qmax` |
| $q_i$ | 量子化された整数（保存する値） | `round(x / scale)` |
| $\hat{w}_i$ | 逆量子化で元に戻した重み | `q * scale` |

**⑤ 小さな数字で手計算（4ビット：$Q_{\max}=7$）**：
重みが $w = [0.35,\; -0.70,\; 0.14]$ のとき：
1. 最大絶対値は $0.70$ ⇒ 縮尺 $s = 0.70 / 7 = 0.10$。
2. 割って四捨五入：$[3.5,\; -7.0,\; 1.4] \xrightarrow{\text{round}} q = [4,\; -7,\; 1]$。
3. 逆量子化：$\hat{w} = [0.40,\; -0.70,\; 0.10]$。
4. 誤差 $|w - \hat{w}| = [0.05,\; 0.00,\; 0.04]$（常に半目盛り $s/2 = 0.05$ 以下！）。

**⑥ 外れ値の罠**：もしここに1個だけ `10.0` が混ざって $w = [0.5,\; -0.5,\; 10.0]$ になると、$s = 10.0 / 7 \approx 1.43$ に跳ね上がり、$0.5 / 1.43 \approx 0.35 \to 0$、$-0.5 / 1.43 \approx -0.35 \to 0$ と**普通の重みが全部0に潰れて**しまいます！

**⑦ 理解のための最小Pythonコード**：

```python no-run
ws = [0.35, -0.70, 0.14]
scale = max(abs(x) for x in ws) / 7          # 0.10
q = [round(x / scale) for x in ws]           # [4, -7, 1]
w_hat = [qi * scale for qi in q]             # [0.40, -0.70, 0.10]
errs = [abs(a - b) for a, b in zip(ws, w_hat)]
```
:::

では、PyTorchで8ビットのabsmax量子化を動かして誤差を確かめてみましょう。

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

:::exercise ch19-q10 ch19-q11 ch19-q12 ch19-q13
:::

## QLoRA：4ビットの本体 ＋ LoRA

**QLoRA** は、モデル本体を4ビット（NF4）に量子化して凍結し、その上にLoRAの付せんを貼って学習する方法です。本体のメモリはfloat16の約4分の1（float32比で約8分の1）、学習するのは付せんだけ。この組み合わせで、無料のT4でも数Bのモデルを鍛えられます。

次のコードは、Qwen2.5-1.5B-Instructを4ビットで読み込んでLoRA学習する例です。4ビットの読み込みには `bitsandbytes` というライブラリを使い、**GPUが必要**です。

このセルは、メニューの「ランタイム」→「セッションを再起動する」で**GPUのメモリを空にしてから**実行します。上の節のモデルがGPUに残っていると、メモリの使用量を正しく測れないうえ、メモリが足りなくなることもあるからです。セッション切断でファイルが消えていても動くように、データが無ければ自動で再取得してから読み込み直します。

```python gpu-only
!pip install -q bitsandbytes peft trl
import json, os, urllib.request, torch
if not os.path.exists("bongo_sft.jsonl"):
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_sft.jsonl",
        "bongo_sft.jsonl",
    )
if not os.path.exists("bongo_sft.jsonl"):
    raise RuntimeError("bongo_sft.jsonl のダウンロードに失敗しました。ネットワーク接続を確認して再実行するか、付録E（エラー辞典）を参照してください。")
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
big = AutoModelForCausalLM.from_pretrained(big_name, quantization_config=bnb, device_map="auto")
big = prepare_model_for_kbit_training(big)
print(f"GPUメモリ使用量：{torch.cuda.memory_allocated() / 1e9:.2f} GB")

trainer = SFTTrainer(model=big, train_dataset=ds, processing_class=big_tok,
                     peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                            target_modules="all-linear", task_type="CAUSAL_LM"),
                     args=SFTConfig(output_dir="qlora-bongo", num_train_epochs=3, per_device_train_batch_size=4,
                                    learning_rate=2e-4, logging_steps=5, report_to="none", save_strategy="no",
                                    bf16=False, fp16=True, gradient_checkpointing=True))
trainer.train()
print(f"学習中の最大GPUメモリ：{torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
```

```output-example
GPUメモリ使用量：1.20 GB
...
学習中の最大GPUメモリ：3.85 GB
```

1.5Bのモデルを、4GB以下のメモリで学習できました。同じ方法で、7Bのモデル（4ビットで約4〜5GB）もT4で鍛えられます（時間はかかりますが）。

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

:::exercise ch19-q14 ch19-q15
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
