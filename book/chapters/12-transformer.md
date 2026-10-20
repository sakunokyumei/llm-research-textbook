{"title": "部品を組み立てる：Transformer", "short": "Transformer", "subtitle": "話し合い（Attention）と、ひとりで考える時間（MLP）を、何層も積み重ねる", "time": "2時間", "env": "cpu", "level": 4, "builds": "GPTそのもの。マルチヘッドAttention・フィードフォワード・残差接続・LayerNormを組み合わせたミニGPTのクラス（第13章以降で使う `minigpt.py` と同じコード）", "theory": ["マルチヘッドAttention（分業）", "フィードフォワード層（各位置で考える）", "残差接続（情報と勾配の高速道路）", "Pre-LN（正規化してから処理する）", "GPTの全体構造とパラメータの内訳", "まず1バッチで過学習させるテスト"], "python": ["`nn.ModuleList` と `nn.Sequential`", "`torch.cat` でつなげる", "`self.apply` で全部品を初期化", "`named_parameters` で中身を調べる"]}

:::goal
第11章のAttentionヘッドを部品にして、**GPT**を組み立てます。この章で書くクラスは、第13章で漱石の小説を学習させ、第15章では本物のGPT-2の重みを読み込むことになる、あなたのGPTの本体です。部品の1つ1つに「なぜそれが必要か」を確かめながら進みます。
:::

:::minato
Transformerって、「変形ロボット」みたいな名前ですよね。
:::

:::sensei
英語の transform は「変換する」だ。入力の文字列を、少しずつ「次の文字を当てやすい表現」に変換していく装置、という意味だよ。……まあ、合体ロボットっぽさはある。小さな部品を組み合わせて、巨大なものを作るからね。今日はキミが組み立て係だ。
:::

## 準備

```python
import re, math, urllib.request
import torch
import torch.nn as nn
import torch.nn.functional as F

def load_soseki(file_id="773_ruby_5968"):
    url = ("https://raw.githubusercontent.com/aozorahack/aozorabunko_text/master/"
           f"cards/000148/files/{file_id}/{file_id}.txt")
    text = urllib.request.urlopen(url).read().decode("cp932")
    text = text.split("-------------------------------------------------------")[2]
    text = text.split("底本：")[0]
    text = re.sub(r"《.*?》", "", text)
    text = re.sub(r"※?［＃.*?］", "", text)
    text = text.replace("｜", "").replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

text = load_soseki()
chars = sorted(set(text))
V = len(chars)
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}
data = torch.tensor([stoi[c] for c in text])
n = int(len(data) * 0.9)
train_data, val_data = data[:n], data[n:]

def get_batch(data, batch_size, T, g):
    ix = torch.randint(0, len(data) - T, (batch_size,), generator=g)
    x = torch.stack([data[i:i + T] for i in ix])
    y = torch.stack([data[i + 1:i + T + 1] for i in ix])
    return x, y
```

## 全体図

先に完成図を見ておきましょう。下から上に、データが流れていきます。

![ミニGPTの全体図。文字のIDが埋め込みになり、LayerNorm→マルチヘッドAttention→足し算、LayerNorm→フィードフォワード→足し算のブロックをN回通り、最後に出力層で次の文字の点数になる](img/transformer.svg)

部品は5種類だけです。

1. **Head**（第11章で作ったAttentionヘッド）
2. **MultiHeadAttention**：ヘッドを何個も並べたもの
3. **FeedForward**：各位置で「考える」小さなMLP（第9章の親戚）
4. **Block**：2と3を、LayerNormと残差接続でつないだもの
5. **GPT**：埋め込み＋Blockを何層も＋出力層

順番に作っていきましょう。

## 部品1：Head（おさらい）

第11章のHeadに、ドロップアウト（第10章）を1行足しただけです。

```python
class Head(nn.Module):
    """Attentionヘッド1つ（第11章）"""

    def __init__(self, n_embd, head_size, block_size, dropout):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k, q, v = self.key(x), self.query(x), self.value(x)
        scores = q @ k.transpose(-2, -1) / math.sqrt(k.shape[-1])
        scores = scores.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        self.wei = F.softmax(scores, dim=-1)
        return self.dropout(self.wei) @ v
```

## 部品2：マルチヘッドAttention

```python
class MultiHeadAttention(nn.Module):
    """ヘッドを何個も並べて、結果をつなげる"""

    def __init__(self, n_embd, n_head, block_size, dropout):
        super().__init__()
        head_size = n_embd // n_head
        self.heads = nn.ModuleList([Head(n_embd, head_size, block_size, dropout) for _ in range(n_head)])
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))

mha = MultiHeadAttention(n_embd=64, n_head=4, block_size=8, dropout=0.0)
x = torch.randn(2, 8, 64)
print(mha(x).shape)
```

```output
torch.Size([2, 8, 64])
```

:::theory ヘッドを増やして分業する
1つのヘッドは、1種類の「注目の仕方」しかできません。でも文章を理解するには、「直前の文字」「文の主語」「かぎかっこの始まり」など、いろいろな観点で過去を見る必要があります。そこで、**小さなヘッドを何個も並べて**、それぞれに違う見方を学ばせます。

64個の数を4つのヘッドで分けると、各ヘッドは16個ずつ担当します（`head_size = n_embd // n_head`）。4つのヘッドの結果を `torch.cat` で横につなげると、また64個に戻ります。最後の `proj`（全結合層）で、4つの見方を混ぜ合わせます。

会議で、全員が同じ資料の同じ行を見ていたら意味がありませんよね。分担して違うところを読み、最後に持ち寄る。それがマルチヘッドです。第13章で、学習したヘッドたちが実際に役割分担している様子を見ます。
:::

:::python ModuleList
`nn.ModuleList([...])` は、部品のリストをPyTorchに「これも全部モデルの部品だよ」と教えるための入れ物です。普通のPythonのリスト `[...]` に入れただけだと、PyTorchがパラメータを見つけられず、学習されません（`model.parameters()` に入らない）。気づきにくい落とし穴です。
:::

## 部品3：フィードフォワード（考える時間）

```python
class FeedForward(nn.Module):
    """各位置で、ひとりで「考える」MLP"""

    def __init__(self, n_embd, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.GELU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)
```

:::theory 話し合いと、ひとりで考える時間
Attentionは「文字どうしが情報をやりとりする」部品でした。いわば**話し合い**です。でも、話し合いで集めた情報を**消化する時間**も必要です。それがフィードフォワード層です。各位置で独立に（ほかの位置とは関係なく）、第9章と同じ「全結合層 → 活性化関数 → 全結合層」の小さなMLPを通します。

真ん中で一度 **4倍** の幅に広げるのが定番です（GPTの論文の設計）。広い作業机でいったん情報を広げて考え、また元の幅にまとめる、というイメージです。活性化関数には、GPTと同じ **GELU** を使います。

実は、モデルの「知識」の多く（「漱石」の次は「夏目」が来やすい、など）は、このフィードフォワード層に蓄えられていると考えられています（第25章の解釈可能性の話題）。
:::

:::python Sequential
`nn.Sequential(A, B, C)` は、部品を**順番に通す**入れ物です。`self.net(x)` と書くと、`C(B(A(x)))` と同じ計算になります。流れ作業のベルトコンベアです。
:::

## 部品4：Block（残差接続とLayerNorm）

```python
class Block(nn.Module):
    """Transformerブロック：話し合い（Attention）→ 考える（FeedForward）"""

    def __init__(self, n_embd, n_head, block_size, dropout):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.attn = MultiHeadAttention(n_embd, n_head, block_size, dropout)
        self.ln2 = nn.LayerNorm(n_embd)
        self.ffwd = FeedForward(n_embd, dropout)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x
```

たった2行の `forward` ですが、ここにTransformerの設計の知恵が詰まっています。

:::theory 残差接続：情報の高速道路
`x = x + self.attn(…)` の **`x +`** の部分が **残差接続**（residual connection）です。第11章でも1回出てきましたね。

部品の出力で `x` を**置き換える**のではなく、`x` に**足し込む**。こうすると、

- **情報の高速道路**：元の情報（自分が何の文字か、など）が、何層通っても消えずに残る。各層は「少しだけ書き足す」係になる
- **勾配の高速道路**：誤差逆伝播で、勾配が足し算の道を通って、入口までまっすぐ届く（足し算の微分は1なので、勾配が弱まらない）。第10章の「深い層で勾配が消える」問題を、根本から解決する

LLMの層を何十、何百と深くできるのは、この残差接続のおかげです。2015年の画像認識モデル **ResNet** で有名になった方法で、Transformerはこれを借りてきました。

研究者はよく、この `x` の流れを **残差ストリーム**（residual stream）と呼びます。各層のAttentionとMLPは、川の流れに情報を書き足していく、川沿いの作業員のようなものです。
:::

:::theory Pre-LN：まず整えてから処理する
各部品に入る**前に** LayerNorm をかけています（`self.attn(self.ln1(x))`）。これを **Pre-LN**（前置き正規化）と言います。2017年の元祖Transformerは「処理した後に」正規化していましたが、GPT-2以降は、学習が安定するPre-LNが主流です。残差ストリーム `x` 自体は正規化せず、各作業員が仕事をする前に、手元のコピーだけを整えるイメージです。
:::

## 部品5：GPT（全体）

最後に、全部をつなげます。

```python
class GPT(nn.Module):
    def __init__(self, vocab_size, block_size=128, n_embd=128, n_head=4, n_layer=4, dropout=0.1):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, n_embd)
        self.pos_emb = nn.Embedding(block_size, n_embd)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head, block_size, dropout) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        if isinstance(module, nn.Linear) and module.bias is not None:
            nn.init.zeros_(module.bias)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(pos))
        x = self.blocks(x)
        logits = self.lm_head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(B * T, -1), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]          # 窓に入る分だけ
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature      # 最後の位置の点数
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("inf")
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, next_id], dim=1)
        return idx
```

:::python 新しく出てきた書き方
- `nn.Sequential(*[Block(…) for _ in range(n_layer)])`：Blockを `n_layer` 個作ってリストにし、`*` でばらして `Sequential` に渡しています。Blockを何層も積み重ねる、の1行版です。
- `self.apply(self._init_weights)`：モデルの中の**すべての部品**に対して `_init_weights` を実行します。GPT-2と同じく、重みを標準偏差0.02の正規分布で初期化します（第10章の初期化の話）。
- `isinstance(module, nn.Linear)`：「`module` は `nn.Linear` の仲間（インスタンス）か？」を `True` / `False` で答える関数です。`(nn.Linear, nn.Embedding)` のように並べると「どちらかの仲間か？」になります。部品の種類ごとに、初期化の仕方を変えるために使っています。
- `generate` は、第3章で自作した生成ループと同じです。違いは、入力を最後の `block_size` 文字に切り詰めること（位置の埋め込みは `block_size` 個しかないので）と、上位 `top_k` 個以外を候補から外せること（第16章で詳しく）。
:::

## 動かしてみる

CPUでも動く小さめの設定で、GPTを作ってみましょう。

```python
torch.manual_seed(0)
model = GPT(V, block_size=64, n_embd=64, n_head=4, n_layer=2, dropout=0.0)
total = sum(p.numel() for p in model.parameters())
print(f"パラメータの数：{total:,}")
groups = {"埋め込み（文字・位置）": 0, "Transformerブロック": 0, "最後のLayerNorm＋出力層": 0}
for name, p in model.named_parameters():
    if name.startswith(("tok_emb", "pos_emb")):
        groups["埋め込み（文字・位置）"] += p.numel()
    elif name.startswith("blocks"):
        groups["Transformerブロック"] += p.numel()
    else:
        groups["最後のLayerNorm＋出力層"] += p.numel()
for k, v in groups.items():
    print(f"  {k}：{v:,}（{v / total:.0%}）")
```

```output
パラメータの数：369,677
  埋め込み（文字・位置）：136,000（37%）
  Transformerブロック：99,584（27%）
  最後のLayerNorm＋出力層：134,093（36%）
```

まだ小さなモデルなので、語彙（2061文字）に関わる埋め込みと出力層がパラメータの大半を占めています。Blockを増やしたり、`n_embd` を大きくしたりすると、Transformerブロックの割合が増えていきます。

第10章の診察その1、「最初の損失を見る」もやっておきましょう。

```python
g = torch.Generator().manual_seed(0)
x, y = get_batch(train_data, 8, 64, g)
_, loss = model(x, y)
print("最初の損失：", round(loss.item(), 3), " log V：", round(math.log(V), 3))
```

```output
最初の損失： 7.656  log V： 7.631
```

$\log V$ とほぼ一致。初期化は健康です。

## 1バッチで丸暗記させるテスト

第10章で紹介した研究者の口ぐせ「まず小さなデータで過学習させてみよ」を実行します。同じ1バッチだけを300回学習させて、丸暗記できるか試します。

```python
torch.manual_seed(0)
model = GPT(V, block_size=64, n_embd=64, n_head=4, n_layer=2, dropout=0.0)
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
x, y = get_batch(train_data, 8, 64, torch.Generator().manual_seed(0))   # この1バッチだけ
for step in range(301):
    _, loss = model(x, y)
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 100 == 0:
        print(f"ステップ {step}：損失 {loss.item():.3f}")
```

```output
ステップ 0：損失 7.656
ステップ 100：損失 0.025
ステップ 200：損失 0.012
ステップ 300：損失 0.009
```

損失がほぼ0になりました。モデルは、このバッチの文章を完全に丸暗記しました。**丸暗記ができる＝モデルと学習ループにバグがない**、ことの確認です。もし下がらなかったら、どこかの部品のつなぎ方を間違えています（`ModuleList` を普通のリストにしてしまった、など）。

## 『こころ』で少しだけ学習させる

本格的な学習は第13章でGPUを使ってやります。ここでは、CPUで1500ステップだけ学習させて、ちゃんと学べることを確かめます。

```python
@torch.no_grad()
def val_loss(model, T):
    model.eval()
    starts = range(0, len(val_data) - T - 1, T)
    xs = torch.stack([val_data[i:i + T] for i in starts])
    ys = torch.stack([val_data[i + 1:i + T + 1] for i in starts])
    loss = model(xs, ys)[1].item()
    model.train()
    return loss

torch.manual_seed(0)
g = torch.Generator().manual_seed(0)
model = GPT(V, block_size=64, n_embd=64, n_head=4, n_layer=2, dropout=0.1)
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
for step in range(1501):
    x, y = get_batch(train_data, 32, 64, g)
    _, loss = model(x, y)
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 500 == 0:
        print(f"ステップ {step:4d}：訓練 {loss.item():.3f}  検証 {val_loss(model, 64):.3f}")
```

```output
ステップ    0：訓練 7.646  検証 7.495
ステップ  500：訓練 3.092  検証 3.316
ステップ 1000：訓練 3.041  検証 3.148
ステップ 1500：訓練 2.741  検証 3.097
```

1500ステップ、たった37万個のパラメータで、第11章の1ヘッドモデル（28万個、2000ステップで3.31）より良い検証損失になりました。まだ下がり続けています。続きは、第13章でGPUを使って思う存分やりましょう。

```python
model.eval()
torch.manual_seed(0)
start = torch.tensor([[stoi[c] for c in "私はその人を"]])
out = model.generate(start, max_new_tokens=80, temperature=0.8)
print("".join(itos[i] for i in out[0].tolist()))
```

```output
私はその人を選んな一人の間に見て、今、念とうとうところでした。私は一種を語る時々らなくなった。父はまた私を欺くより返して来た。私に告げた一人にする親類を利き事があった。この
```

## このコードの行き先

この章で書いた5つのクラス（`Head`、`MultiHeadAttention`、`FeedForward`、`Block`、`GPT`）は、教科書のリポジトリに **`code/minigpt.py`** として、まったく同じ内容で置いてあります。第13章からは、毎回このファイルをダウンロードして使います。あなたが書いたものと同じものです。自信を持って `import` してください。

:::deep 本物のGPT-2との違い
この章のGPTと、OpenAIが2019年に公開したGPT-2の構造は、ほとんど同じです。違いは主に次の3つで、第15章で本物のGPT-2の重みを読み込むときに、ここを合わせます。

- GPT-2は、Q・K・Vを作る3つの全結合層を1つにまとめている（計算が速い）。数学的には同じ
- GPT-2は、Q・K・Vの全結合層にもバイアスがある
- GPT-2は、出力層の重みを文字の埋め込みの表と**共有**している（weight tying。パラメータの節約）

大きさは、GPT-2の一番小さい版で12層・12ヘッド・768次元、約1億2400万パラメータです。
:::

:::warn よくあるつまずき
- **`RuntimeError: shape '[…]' is invalid for input of size …`**：`n_embd` が `n_head` で割り切れないと、ヘッドの大きさがずれます。64と4、128と4、384と6のように、割り切れる組み合わせにしましょう。
- **損失がまったく下がらない**：`self.heads` を `nn.ModuleList` ではなく普通のリストにしていませんか？ `print(model)` で部品の一覧を表示して、ヘッドが入っているか確認しましょう。
- **`IndexError: index out of range in self`**：`block_size` より長い文字列を `model(…)` に入れています。`generate` は自動で切り詰めますが、自分で `model(x)` を呼ぶときは注意。
:::

:::quiz 残差接続
`x = x + self.attn(self.ln1(x))` を `x = self.attn(self.ln1(x))` に変えると、何が困る？
:::answer
元の情報が層を通るたびに置き換えられて失われやすくなり、また誤差逆伝播で勾配が層を通るたびに弱まって、深いモデルが学習しにくくなります。足し算でつなぐと、情報も勾配も「近道」を通れます。
:::

:::quiz マルチヘッド
`n_embd=384`、`n_head=6` のとき、1つのヘッドの大きさ（head_size）は？
:::answer
384 ÷ 6 ＝ 64 です。6つのヘッドの出力（64ずつ）をつなげると、384に戻ります。
:::

:::quiz 1バッチテスト
新しいモデルを作ったら、なぜ最初に「1バッチで丸暗記できるか」を試すの？
:::answer
丸暗記すらできないなら、モデルの部品のつなぎ方や学習ループにバグがあると分かるからです。逆に、丸暗記できれば、少なくとも学習の仕組みは正しく動いています。大きなデータで何時間も学習させてから失敗に気づくより、ずっと早くバグを見つけられます。
:::

:::checklist
- マルチヘッドAttentionで、ヘッドの出力をつなげて元の幅に戻せた
- フィードフォワード層の役割（各位置で考える）を説明できる
- 残差接続が「情報と勾配の高速道路」である理由を説明できる
- GPTクラスを組み立て、パラメータの内訳を調べた
- 1バッチの丸暗記テストで、損失がほぼ0になるのを確かめた
- 『こころ』で少し学習させ、文章を生成した
:::

:::recap
- **マルチヘッドAttention**：小さなヘッドを並べて、違う観点で過去を見る（話し合い）
- **フィードフォワード**：各位置で独立に考える小さなMLP（4倍に広げてGELU）
- **残差接続** `x = x + f(x)`：情報と勾配の高速道路。深い層を可能にする
- **Pre-LN**：各部品の前でLayerNorm
- GPT ＝ 埋め込み ＋ Block×N ＋ LayerNorm ＋ 出力層。これが `code/minigpt.py`
:::

:::sensei
組み立て完了！ キミのGPTは、まだCPUで少し走っただけの子馬だ。次の章では、GPUという牧場で、漱石の小説を100万字読ませて、思い切り走らせる。どこまで速くなるか、楽しみだね。
:::
