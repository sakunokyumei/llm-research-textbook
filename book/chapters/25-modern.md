{"title": "最新LLMの部品を移植する", "short": "最新の部品を移植", "subtitle": "RoPE・RMSNorm・SwiGLU・MoEを自分のGPTに入れて、公平に比べる", "time": "2〜3時間", "env": "cpu", "level": 5, "builds": "第12章のGPTを、LlamaやQwenと同じ部品（RMSNorm・SwiGLU・RoPE）に置き換えた「現代版ミニGPT」と、その効果を確かめる比較実験。MoE層の試作も", "theory": ["RMSNorm（LayerNormの簡略版）", "SwiGLU（門番つきのフィードフォワード）", "RoPE（回転位置埋め込み）と相対位置", "公平な比較実験の作り方（同じ条件・複数のシード）", "MoE（専門家の混合）とルーティング", "長いコンテキスト・推論モデル・状態空間モデル・マルチモーダル・解釈可能性の地図"], "python": ["`torch.rsqrt`", "`F.silu`", "三角関数 `torch.cos` / `torch.sin`", "`F.scaled_dot_product_attention`（第16章）"]}

:::goal
第12章のGPTは、2019年のGPT-2とほぼ同じ設計でした。その後のLLM（Llama、Qwen、Gemmaなど）は、いくつかの部品を改良しています。この章では、その代表的な部品を**自分のGPTに移植**し、本当に良くなるのかを**公平な実験**で確かめます。論文を読んで「良いらしい」で終わらせず、自分の手で確かめる。それが研究の第一歩です。
:::

:::minato
最新のモデルの部品って、難しそうです……。
:::

:::sensei
1つ1つは、驚くほど短いコードだよ。RMSNormは5行、SwiGLUは3行、RoPEも10行ほど。大事なのは部品の難しさじゃなくて、「本当に良くなったのか？」を確かめる**実験の作法**のほうだ。今日はキミが研究者だ。
:::

## 準備と、比べる相手（ベースライン）

第12章と同じ小さな設定（2層・幅64・窓64・1500ステップ）を使います。CPUでも1回数分で終わるので、何度も実験できます。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/minigpt.py
import re, math, urllib.request
import torch
import torch.nn as nn
import torch.nn.functional as F
from minigpt import GPT

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
data = torch.tensor([stoi[c] for c in text])
n = int(len(data) * 0.9)
train_data, val_data = data[:n], data[n:]
T = 64

def get_batch(data, g):
    ix = torch.randint(0, len(data) - T, (32,), generator=g)
    return torch.stack([data[i:i + T] for i in ix]), torch.stack([data[i + 1:i + T + 1] for i in ix])

@torch.no_grad()
def val_loss(model):
    model.eval()
    starts = range(0, len(val_data) - T - 1, T)
    xs = torch.stack([val_data[i:i + T] for i in starts])
    ys = torch.stack([val_data[i + 1:i + T + 1] for i in starts])
    loss = model(xs, ys)[1].item()
    model.train()
    return loss

def experiment(make_model, seed, steps=1500):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = make_model()
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
    for step in range(steps):
        x, y = get_batch(train_data, g)
        _, loss = model(x, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return val_loss(model), sum(p.numel() for p in model.parameters())

base = lambda: GPT(V, block_size=T, n_embd=64, n_head=4, n_layer=2, dropout=0.0)   # 現代版に合わせてドロップアウトなし
results = {"ベースライン（GPT-2型）": [experiment(base, seed) for seed in [0, 1]]}
for name, rs in results.items():
    print(name, "検証損失：", [round(r[0], 3) for r in rs], " パラメータ：", rs[0][1])
```

```output
ベースライン（GPT-2型） 検証損失： [3.21, 3.275]  パラメータ： 369677
```

:::theory 公平な比較の作法
「新しい部品で良くなった」と言うためには、**部品以外のすべてを同じにする**必要があります。

- 同じデータ、同じ分け方（訓練・検証）
- 同じステップ数、同じバッチの大きさ、同じ学習率、同じ正則化（ドロップアウトの有無など）
- **パラメータの数をなるべくそろえる**（大きくすれば良くなるのは当たり前なので）
- **シード（乱数の種）を変えて何回か**やる。1回だけだと、たまたまかもしれない（第20章）

ここでは、シード0と1の2回ずつ実験します。本当は5回以上やりたいところですが、時間との相談です。研究の世界では、この「何回やって、どれくらいばらついたか」を必ず書きます。
:::

## 部品1：RMSNorm

```python
class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight

x = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
print(RMSNorm(4)(x))
```

```output
tensor([[0.3651, 0.7303, 1.0954, 1.4606]], grad_fn=<MulBackward0>)
```

:::theory LayerNormから「平均を引く」を省いた版
第10章のLayerNormは「平均を引いて、標準偏差で割る」でした。**RMSNorm**（Root Mean Square Normalization）は、**平均を引かずに**、2乗の平均の平方根（RMS）で割るだけです。

$$\mathrm{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \epsilon}} \cdot w$$

`torch.rsqrt` は「平方根の逆数」です。平均を計算しない分、少し速く、性能はほとんど変わらないことが分かったので、LlamaやQwenはこちらを使っています。上の例では、$\sqrt{(1+4+9+16)/4} \approx 2.739$ で割っています。
:::

## 部品2：SwiGLU

```python
class SwiGLU(nn.Module):
    def __init__(self, dim, hidden):
        super().__init__()
        self.w1 = nn.Linear(dim, hidden, bias=False)   # 中身
        self.w3 = nn.Linear(dim, hidden, bias=False)   # 門番
        self.w2 = nn.Linear(hidden, dim, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))
```

:::theory 門番つきのフィードフォワード
第12章のフィードフォワード層は「広げる → GELU → 戻す」でした。**SwiGLU** は、広げる全結合層を**2つ**用意して、片方（`w3`）を「門番」として使います。もう片方（`w1`）の出力を活性化関数SiLU（GELUとよく似た形）に通し、門番の値を**掛け算**します。門番が0に近いところは情報が通らず、大きいところはよく通る。「どの情報を通すか」を、入力に応じて細かく調整できるのです。

重みが3つになる分、パラメータが増えるので、広げる幅を4倍ではなく約8/3倍（≒2.67倍）にして、パラメータ数をそろえるのが定番です。
:::

## 部品3：RoPE（回転位置埋め込み）

第11章で、Attentionは順番を知らないので、**位置の埋め込み**を足しました。でも、足す方式には弱点があります。「3番目と5番目」と「103番目と105番目」は、どちらも「2つ離れている」のに、モデルにとっては別の組み合わせに見えてしまうのです。言葉の関係で大事なのは、多くの場合「**何文字離れているか**（相対位置）」なのに。

**RoPE**（Rotary Position Embedding）は、位置を**足す**代わりに、QueryとKeyのベクトルを位置に応じた角度だけ**回転**させます。

```python
def rope_cache(T, hs, base=10000.0):
    freqs = 1.0 / (base ** (torch.arange(0, hs, 2).float() / hs))   # ペアごとの回転の速さ
    angles = torch.outer(torch.arange(T).float(), freqs)            # [T, hs/2]：位置 × 速さ
    return torch.cos(angles), torch.sin(angles)

def apply_rope(x, cos, sin):
    x1, x2 = x[..., 0::2], x[..., 1::2]            # 数を2つずつペアにする
    T = x.shape[-2]
    c, s = cos[:T], sin[:T]
    out = torch.stack([x1 * c - x2 * s, x1 * s + x2 * c], dim=-1)   # 各ペアを回転
    return out.flatten(-2)
```

:::python 1つ飛ばしのスライス、...、stack と flatten
小さな例で見ると分かりやすいです。`a = torch.arange(6)`（中身は `[0, 1, 2, 3, 4, 5]`）とすると、

- `a[0::2]` は「0番目から、2つ飛ばしで」→ `[0, 2, 4]`。`a[1::2]` は「1番目から、2つ飛ばしで」→ `[1, 3, 5]`。これで、隣どうしの数がペア（0と1、2と3、4と5）に分かれます
- `x[..., 0::2]` の `...` は「前の軸は全部そのまま」という意味です。`x` の形が `[T, hs]` でも `[B, T, hs]` でも、**最後の軸だけ**を1つ飛ばしで取り出せます
- `torch.stack([A, B], dim=-1)` は、AとBを最後の軸に並べて、ペアの形 `[…, 3, 2]` にします。`.flatten(-2)` は、最後の2つの軸をつないで1列に戻します。結果、`[A0, B0, A1, B1, A2, B2]` と、元の並び順に戻ります
- `torch.outer(a, b)` は、`a` と `b` の全部の組み合わせの掛け算の表（九九の表のようなもの）を作ります
- 下のセルの `q.expand(200, hs)` は、形 `[hs]` の `q` を、200行ぶん並べた `[200, hs]` に見せかけます（コピーはしません）。「200か所のどこにでも置ける」ようにするためです
:::

:::math 回転と、内積の不思議
平面上の点 $(x_1, x_2)$ を角度 $\theta$ だけ回転させると、

$$(x_1 \cos\theta - x_2 \sin\theta,\ \ x_1 \sin\theta + x_2 \cos\theta)$$

になります（`apply_rope` の中の式です）。$\cos$ と $\sin$ は、時計の針の先の、横と縦の位置を表す関数だと思ってください。

RoPEのすごいところは、位置 $m$ のQueryを $m\theta$ 回転、位置 $n$ のKeyを $n\theta$ 回転させると、2つの**内積**（Attentionの点数）が、**差 $m - n$ だけで決まる**ことです。2本の時計の針を同じだけ回しても、針と針の間の角度は変わらない。それと同じです。確かめてみましょう。
:::

```python
hs = 16
cos, sin = rope_cache(200, hs)
torch.manual_seed(0)
q, k = torch.randn(hs), torch.randn(hs)

def score_at(m, n):
    qm = apply_rope(q.expand(200, hs), cos, sin)[m]   # 位置mに置いたQuery
    kn = apply_rope(k.expand(200, hs), cos, sin)[n]   # 位置nに置いたKey
    return (qm @ kn).item()

print(f"位置(5, 3)の点数：{score_at(5, 3):.4f}")
print(f"位置(105, 103)の点数：{score_at(105, 103):.4f}")
print(f"位置(5, 1)の点数：{score_at(5, 1):.4f}")
```

```output
位置(5, 3)の点数：-1.8956
位置(105, 103)の点数：-1.8956
位置(5, 1)の点数：-3.3877
```

位置が(5, 3)でも(105, 103)でも、**離れ具合が同じなら同じ点数**です。一方、(5, 1)のように離れ具合が違えば点数も変わります。RoPEは、Attentionに「何文字離れているか」を自然に教えてくれるのです。足し算式の位置埋め込みのように「位置ごとの表」を持たないので、学習時より長い文章に伸ばす工夫（**RoPEの拡張**）もしやすく、長いコンテキストのLLMで重宝されています。

## 現代版ミニGPTを組み立てる

3つの部品を使って、GPTを組み立て直します。Attentionは、第15〜16章で学んだ「QKVをまとめて作り、`scaled_dot_product_attention` で計算する」書き方にします。位置の埋め込み（`pos_emb`）はなくなり、代わりにRoPEを使います。

```python
class ModernAttention(nn.Module):
    def __init__(self, dim, n_head, block_size):
        super().__init__()
        self.n_head = n_head
        self.qkv = nn.Linear(dim, 3 * dim, bias=False)
        self.proj = nn.Linear(dim, dim, bias=False)
        cos, sin = rope_cache(block_size, dim // n_head)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q, k, v = [t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v)]
        q, k = apply_rope(q, self.cos, self.sin), apply_rope(k, self.cos, self.sin)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.proj(y.transpose(1, 2).contiguous().view(B, T, C))

class ModernBlock(nn.Module):
    def __init__(self, dim, n_head, block_size):
        super().__init__()
        self.norm1, self.norm2 = RMSNorm(dim), RMSNorm(dim)
        self.attn = ModernAttention(dim, n_head, block_size)
        self.ffn = SwiGLU(dim, hidden=int(dim * 8 / 3))

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        return x + self.ffn(self.norm2(x))

class ModernGPT(nn.Module):
    def __init__(self, V, block_size, dim=64, n_head=4, n_layer=2):
        super().__init__()
        self.tok_emb = nn.Embedding(V, dim)
        self.blocks = nn.Sequential(*[ModernBlock(dim, n_head, block_size) for _ in range(n_layer)])
        self.norm = RMSNorm(dim)
        self.lm_head = nn.Linear(dim, V, bias=False)
        for p in self.parameters():
            if p.dim() == 2:
                nn.init.normal_(p, std=0.02)

    def forward(self, idx, targets=None):
        x = self.blocks(self.tok_emb(idx))
        logits = self.lm_head(self.norm(x))
        loss = None if targets is None else F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

modern = lambda: ModernGPT(V, block_size=T)
results["現代版（RMSNorm＋SwiGLU＋RoPE）"] = [experiment(modern, seed) for seed in [0, 1]]
for name, rs in results.items():
    losses = [r[0] for r in rs]
    print(f"{name}：検証損失 {[round(l, 3) for l in losses]}  平均 {sum(losses) / len(losses):.3f}  パラメータ {rs[0][1]:,}")
```

```output
ベースライン（GPT-2型）：検証損失 [3.21, 3.275]  平均 3.243  パラメータ 369,677
現代版（RMSNorm＋SwiGLU＋RoPE）：検証損失 [3.284, 3.229]  平均 3.256  パラメータ 362,176
```

:::sensei
さて、結果を読もう。大事なのは、良くなったか悪くなったかより、**その差が、シードによるばらつきより大きいか**だ。

- 2つのモデルの平均の差：3.256 − 3.243 ＝ **0.013**
- 同じモデルでもシードを変えただけで：ベースラインは3.21〜3.275（幅 **0.065**）、現代版は3.229〜3.284（幅 **0.055**）

差は、ばらつきよりずっと小さい。だから結論は「**この規模の実験では、現代版の部品の効果は確認できなかった**」。がっかりするかもしれないが、これが誠実な結論だ。そして、それも立派な研究成果なんだよ。
:::

:::minato
実は、教科書を作るときに最初にこの実験をしたら、ベースラインにだけドロップアウトが入っていて、ベースラインが3.10で圧勝していたそうですね。
:::

:::sensei
そうなんだ。まさに「公平な比較の作法」を破っていた。気づいて条件をそろえたら、差は消えた。逆に言うと、**この規模では、部品の違いよりもドロップアウト（第10章）のほうがずっと効く**、という発見でもある。データが少ないときは過学習対策が一番大事、という第13章の教訓と同じだね。研究では、こういう「失敗から見つかる発見」がよくある。だから、うまくいかなかった実験も記録に残しておくんだ。
:::

:::theory 小さな実験と大きな実験
最新の部品の多くは、**大きなモデル・大量のデータ**で効果が確かめられたものです。2層・幅64・1500ステップという小さな実験では、効果がはっきり出ないこともありますし、逆に小さい規模でしか効かない工夫もあります。

だから研究者は、小さな実験で素早くアイデアを試し、**有望なものだけを大きな実験で確かめる**、という順番で進めます。第15章のスケーリング則の話を思い出してください。小さな実験の結果を、どこまで大きな規模に当てはめてよいかを考えることも、研究の大事な仕事です。
:::

## MoE：専門家を使い分ける

最近の大きなLLMの多くが採用している **MoE**（Mixture of Experts、専門家の混合）も、小さく作ってみましょう。

```python
class TinyMoE(nn.Module):
    def __init__(self, dim, n_experts=4, hidden=128):
        super().__init__()
        self.router = nn.Linear(dim, n_experts, bias=False)       # どの専門家に任せるか決める係
        self.experts = nn.ModuleList([SwiGLU(dim, hidden) for _ in range(n_experts)])

    def forward(self, x):
        B, T, C = x.shape
        flat = x.view(-1, C)
        gate = F.softmax(self.router(flat), dim=-1)                # 各トークンの、専門家ごとの重み
        weight, choice = gate.max(dim=-1)                          # 一番の専門家を1人だけ選ぶ（top-1）
        out = torch.zeros_like(flat)
        for e, expert in enumerate(self.experts):
            mask = choice == e
            if mask.any():
                out[mask] = weight[mask, None] * expert(flat[mask])
        self.last_choice = choice
        return out.view(B, T, C)

torch.manual_seed(0)
moe = TinyMoE(64)
x = torch.randn(2, 16, 64)
y = moe(x)
print(y.shape)
print("各専門家が担当したトークン数：", torch.bincount(moe.last_choice, minlength=4).tolist())
```

```output
torch.Size([2, 16, 64])
各専門家が担当したトークン数： [6, 6, 14, 6]
```

:::theory MoE：大きいのに軽い
MoEでは、フィードフォワード層を何個も（数個〜数百個）用意して、**ルーター**が各トークンを、一部の専門家（1〜数個）だけに振り分けます。

- **パラメータ全体はとても多い**（専門家の数だけ増える）ので、たくさんの知識を蓄えられる
- でも、**1つのトークンの計算に使うのは一部の専門家だけ**なので、計算は軽い

「何でも知っている1人の先生」より「各教科の専門の先生がたくさんいて、質問ごとに担当が答える」ほうが、効率がいい、という発想です。ただし、ルーターが一部の専門家ばかりに仕事を振ってしまう（**負荷の偏り**）問題があり、偏りを罰する工夫（負荷分散の損失）が必要です。上の出力で、担当のトークン数がばらついているのが分かりますね。
:::

## 最新研究の地図

ここまでで、あなたは現代のLLMの主要な部品を、すべて自分の手で書いたことになります。最後に、この先の研究の世界を、地図として眺めておきましょう。どれも、この教科書で学んだことの延長線上にあります。

:::theory 長いコンテキスト
何十万〜何百万トークンを一度に読むLLMが登場しています。課題は、Attentionの計算とKVキャッシュのメモリが長さとともに増えること（第16章）。RoPEの拡張、GQA、FlashAttention、一部のトークンだけに注目する**疎なAttention**などを組み合わせて実現しています。
:::

:::theory 推論モデルと「考える時間」
答える前に長く考える**推論モデル**は、推論のとき（テスト時）に多くの計算（トークン）を使うほど賢くなる、という性質を利用しています（**テスト時の計算のスケーリング**）。第22章で触れた「答えが確かめられる問題での強化学習（RLVR）」で、考え方そのものを学ばせます。

GRPOの中心にあるのは、驚くほど単純な計算です。同じ問題に何通りも答えさせ、それぞれの報酬が**グループの平均よりどれだけ良いか**（アドバンテージ）で、その答えを強めたり弱めたりします。

```python
rewards = torch.tensor([1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0])   # 8通りの答えの正誤
advantage = (rewards - rewards.mean()) / (rewards.std() + 1e-6)
print("グループの平均：", rewards.mean().item())
print("アドバンテージ：", [round(a, 2) for a in advantage.tolist()])
```

```output
グループの平均： 0.375
アドバンテージ： [1.21, -0.72, -0.72, 1.21, 1.21, -0.72, -0.72, -0.72]
```

正解した答えはプラス（強める）、間違えた答えはマイナス（弱める）。平均と比べるので、「全員正解」の簡単な問題や「全員不正解」の難しすぎる問題からは、何も学びません（アドバンテージが0になる）。ちょうどいい難しさの問題から学ぶ、よくできた仕組みです。
:::

:::theory Transformer以外の選択肢
Attentionの計算量が長さの2乗で増えるのを避けるため、**状態空間モデル**（SSM、代表例はMamba）のように、RNN（第9章のMLPを時間方向にくり返し使うような仕組み）の考え方を現代的に作り直したモデルも研究されています。過去の情報を、決まった大きさの「状態」に圧縮して持ち歩くので、長さに比例した計算で済みます。Transformerと組み合わせた**ハイブリッド**のモデルも登場しています。
:::

:::theory マルチモーダル
画像を小さな正方形（パッチ）に切り分け、各パッチを1つの「トークン」としてベクトルにすれば、Transformerは文章と同じように画像も扱えます（Vision Transformer）。画像のトークンと文章のトークンを並べて入力すれば、画像について会話するLLMになります。音声や動画も同じ発想です。第2章の「何でもトークンにする」が、ここまで広がるのです。
:::

:::theory 解釈可能性
LLMの中で何が起きているのかを調べる研究を **解釈可能性**（interpretability）と言います。第13章でヘッドの注目の仕方を可視化したのは、その入口です。特定の概念に反応するニューロンや、ある処理を担う回路を見つけたり、中間の層のベクトルから「何を考えているか」を読み取ったり（プロービング）します。安全なAIを作るためにも、とても重要な分野です。
:::

:::theory 蒸留
大きなモデル（先生）の出力の確率を、小さなモデル（生徒）にまねさせて学習させる方法を **蒸留**（distillation）と言います。正解の1トークンだけでなく、先生の「2位、3位の候補への確率」からも学べるので、小さなモデルが効率よく賢くなります。第3章の「確率の分布」そのものが、教材になるわけです。
:::

:::try 自分で部品を1つずつ試す
3つの部品を一度に入れると、どれが効いたのか分かりません。研究では、1つずつ入れたり外したりして、効果を切り分けます（**アブレーション**）。`ModernBlock` の `RMSNorm` を `nn.LayerNorm` に戻す、`SwiGLU` を第12章の `FeedForward` に戻す、などして、どの部品がどれくらい効いているか調べてみましょう。結果を表にまとめれば、立派な研究ノートです。
:::

:::warn よくあるつまずき
- **RoPEで形のエラー**：`head_size`（`dim // n_head`）が**偶数**でないと、2つずつのペアが作れません。
- **現代版のほうが損失が悪い**：小さな規模や短い学習では、そういうこともあります。学習率など、ハイパーパラメータは部品ごとに最適な値が違うこともあるので、それぞれで少し調整するのが本当は公平です。
- **MoEで一部の専門家が全然使われない**：負荷の偏りです。ルーターの出力に、偏りを罰する損失を足すのが一般的な対策です。
:::

:::quiz RMSNorm
RMSNormは、LayerNormと比べて何を省いている？
:::answer
平均を引く操作（と、バイアス）を省いています。2乗の平均の平方根（RMS）で割って、学習可能な重みを掛けるだけです。
:::

:::quiz RoPE
RoPEを使うと、QueryとKeyの内積（Attentionの点数）は何によって決まる？
:::answer
QueryとKeyの中身と、2つの位置の**差**（相対位置）によって決まります。絶対的な位置（何番目か）にはよりません。
:::

:::quiz 公平な比較
新しい部品を入れたモデルの検証損失が、1回の実験で0.01良くなりました。「効果がある」と言える？
:::answer
まだ言えません。シードを変えて何回か実験し、その差がシードによるばらつきより十分大きいかを確かめる必要があります。また、パラメータ数や学習の条件をそろえたかも確認します。
:::

:::checklist
- RMSNorm・SwiGLU・RoPEをそれぞれ自分で実装した
- RoPEで、点数が相対位置だけで決まることを確かめた
- 現代版ミニGPTを組み立て、ベースラインと公平に比べた
- 差がシードのばらつきより大きいかを考えて、結論を書いた
- MoEのルーティングと負荷の偏りを観察した
- GRPOのアドバンテージを計算した
:::

:::recap
- 現代のLLMは、**RMSNorm**・**SwiGLU**・**RoPE**など、GPT-2から少しずつ改良された部品を使う
- **RoPE**は、QueryとKeyを位置に応じて回転させ、点数を**相対位置**で決まるようにする
- 比較実験は、**部品以外をそろえ**、**複数のシード**でばらつきと差を比べる
- **MoE**は、ルーターがトークンを一部の専門家に振り分ける。大きいのに計算は軽い
- 研究の地図：長いコンテキスト・推論モデル（RLVR・GRPO）・SSM・マルチモーダル・解釈可能性・蒸留
:::

:::sensei
キミはもう、論文を読んで「それ、自分のGPTに入れて試せるな」と思える人になった。次はいよいよ最終章。卒業制作のテーマを決めて、2030年までの地図を描こう。ここまで来たキミなら、どこへでも行ける。
:::
