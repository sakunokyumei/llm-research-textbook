{"title": "速く・大きく：推論と学習の工学", "short": "推論と学習の工学", "subtitle": "KVキャッシュ、賢いサイコロ、メモリの節約術、そして何百枚ものGPU", "time": "2時間", "env": "cpu", "level": 4, "builds": "KVキャッシュ付きの生成（出力が変わらず速くなることを確認）、top-k / top-p サンプリング、勾配累積、FlashAttention の検証", "theory": ["KVキャッシュ：計算の使い回し", "KVキャッシュのメモリとGQA（グループ化クエリAttention）", "top-k・top-p（nucleus）・くり返しペナルティ", "勾配累積：小さなGPUで大きなバッチ", "活性化の再計算（勾配チェックポイント）", "FlashAttention（メモリに優しいAttention）", "分散学習：データ並列・テンソル並列・パイプライン並列・ZeRO"], "python": ["辞書やリストに途中結果をためる", "`time.perf_counter` で速さを測る", "`F.scaled_dot_product_attention`", "`torch.utils.checkpoint`"]}

:::goal
GPTの「仕組み」は前の章で完成しました。この章は「**工学**」の章です。同じGPTを、何倍も速く動かし、少ないメモリで学習させるための技を、実際にコードで確かめていきます。どれも、実際のLLMの開発現場で毎日使われている技です。
:::

:::minato
仕組みが分かったのに、まだ学ぶことがあるんですか？
:::

:::sensei
車の仕組みが分かっても、F1で勝てるとは限らない。ChatGPTが何億人もの質問に答えられるのは、モデルが賢いからだけじゃない。同じ計算を、いかに速く・安く・たくさんこなすか。その工夫の積み重ねなんだ。今日はピットクルーの修行だよ。
:::

## 準備：キャッシュ対応のGPT

第15章のGPT-2形式のAttentionに、**KVキャッシュ**という仕組みを追加したものを用意します。重みはでたらめでかまいません（速さと正しさを確かめるだけなので）。

:::tip この章のコードは「動かして、結果を見る」でOK
この章のコードは、これまでより密度が高めです。全部の行を理解できなくても大丈夫。まずは貼り付けて実行し、「結果が同じで、速くなった」「勾配が同じ」といった**結果**を確かめましょう。仕組みは「理論の小部屋」で説明します。気になった行があれば、`print(…shape)` を入れて中身をのぞけばOKです。
:::

```python
import math, time
import torch
import torch.nn as nn
import torch.nn.functional as F

class CachedAttention(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        self.n_head = n_head
        self.c_attn = nn.Linear(n_embd, 3 * n_embd)
        self.c_proj = nn.Linear(n_embd, n_embd)

    def forward(self, x, cache=None):
        B, T, C = x.shape
        hs = C // self.n_head
        q, k, v = self.c_attn(x).split(C, dim=2)
        q, k, v = [t.view(B, T, self.n_head, hs).transpose(1, 2) for t in (q, k, v)]
        if cache is not None:                      # 過去のKとVを使い回す
            if "k" in cache:
                k = torch.cat([cache["k"], k], dim=2)
                v = torch.cat([cache["v"], v], dim=2)
            cache["k"], cache["v"] = k, v
        L = k.shape[2]                             # 過去も含めた長さ
        att = q @ k.transpose(-2, -1) / math.sqrt(hs)
        mask = torch.tril(torch.ones(L, L))[L - T:]    # 新しいT個の行だけのマスク
        att = att.masked_fill(mask == 0, float("-inf"))
        y = F.softmax(att, dim=-1) @ v
        return self.c_proj(y.transpose(1, 2).contiguous().view(B, T, C))

class TinyGPT(nn.Module):
    def __init__(self, V=1000, n_embd=256, n_head=4, n_layer=6, block_size=512):
        super().__init__()
        self.wte, self.wpe = nn.Embedding(V, n_embd), nn.Embedding(block_size, n_embd)
        self.ln1 = nn.ModuleList([nn.LayerNorm(n_embd) for _ in range(n_layer)])
        self.attn = nn.ModuleList([CachedAttention(n_embd, n_head) for _ in range(n_layer)])
        self.ln2 = nn.ModuleList([nn.LayerNorm(n_embd) for _ in range(n_layer)])
        self.mlp = nn.ModuleList([nn.Sequential(nn.Linear(n_embd, 4 * n_embd), nn.GELU(), nn.Linear(4 * n_embd, n_embd)) for _ in range(n_layer)])
        self.ln_f, self.head = nn.LayerNorm(n_embd), nn.Linear(n_embd, V)

    def forward(self, idx, caches=None, start_pos=0):
        T = idx.shape[1]
        x = self.wte(idx) + self.wpe(torch.arange(start_pos, start_pos + T))
        for i in range(len(self.attn)):
            x = x + self.attn[i](self.ln1[i](x), None if caches is None else caches[i])
            x = x + self.mlp[i](self.ln2[i](x))
        return self.head(self.ln_f(x))

torch.manual_seed(0)
model = TinyGPT().eval()
print(f"パラメータ：{sum(p.numel() for p in model.parameters()):,}")
```

```output
パラメータ：5,383,144
```

## ムダに気づく：生成のたびに全部計算し直している

第3章からずっと使ってきた生成ループを思い出してください。

> 文章全体をモデルに通す → 最後の位置の確率で1トークン選ぶ → 付け足す → **また文章全体をモデルに通す** …

100トークン目を生成するとき、1〜99トークン目の計算を、またゼロからやり直しています。でも、因果マスクのおかげで、**過去の位置の計算結果は、未来のトークンが増えても変わりません**（第11章のカンニング検査で確かめましたね）。だったら、前回の計算結果を取っておいて使い回せばいいはずです。

:::theory KVキャッシュ
Attentionで、過去の位置から受け取るのは **Key** と **Value** でした。過去の位置のKeyとValueは、一度計算したら変わりません。そこで、

- 過去のトークンのK・Vを、層ごとに **キャッシュ**（取っておく場所）に保存しておく
- 新しいトークンが来たら、**その1トークンぶんだけ**Q・K・Vを計算し、Kと Vをキャッシュの後ろに付け足す
- 新しいトークンのQで、キャッシュの全K・Vに対してAttentionを計算する

こうすると、1トークンを生成するための計算が「文章全体」から「1トークンぶん」に減ります。上のコードの `cache` がそれです。これを **KVキャッシュ** と言い、ほぼすべてのLLMの推論で使われています。
:::

キャッシュなし・ありの2通りで生成して、**結果が同じで、速さが違う**ことを確かめましょう。

```python
@torch.no_grad()
def generate_naive(model, idx, n):
    for _ in range(n):
        logits = model(idx)                              # 毎回、全体を計算
        idx = torch.cat([idx, logits[:, -1:].argmax(-1)], dim=1)
    return idx

@torch.no_grad()
def generate_cached(model, idx, n):
    caches = [{} for _ in model.attn]
    logits = model(idx, caches)                          # 最初だけ全体を計算
    pos = idx.shape[1]
    for _ in range(n):
        next_id = logits[:, -1:].argmax(-1)
        idx = torch.cat([idx, next_id], dim=1)
        logits = model(next_id, caches, start_pos=pos)   # 新しい1トークンだけ
        pos += 1
    return idx

prompt = torch.randint(0, 1000, (1, 20))
t0 = time.perf_counter(); a = generate_naive(model, prompt, 200); t1 = time.perf_counter()
b = generate_cached(model, prompt, 200); t2 = time.perf_counter()
print("結果は同じ？", torch.equal(a, b))
print(f"キャッシュなし {t1 - t0:.2f}秒 / キャッシュあり {t2 - t1:.2f}秒 → {(t1 - t0) / (t2 - t1):.1f}倍速い")
```

```output-example
結果は同じ？ True
キャッシュなし 1.93秒 / キャッシュあり 0.31秒 → 6.2倍速い
```

（時間は実行する環境によって変わります。「結果は同じ？ True」が大事です。）文章が長くなるほど、差は大きくなります。

## KVキャッシュのメモリと、GQA

キャッシュは速さと引き換えに **メモリ** を使います。どれくらい使うのか、計算してみましょう。

```python
def kv_cache_bytes(n_layer, n_kv_head, head_dim, n_tokens, bytes_per_num=2):
    return 2 * n_layer * n_kv_head * head_dim * n_tokens * bytes_per_num   # 2 = KとV

# Qwen2.5-0.5B：24層、Queryのヘッド14、K・Vのヘッド2、ヘッドの大きさ64
per_token = kv_cache_bytes(24, 2, 64, 1)
print(f"1トークンあたり {per_token / 1024:.0f} KB → 32,768トークンで {kv_cache_bytes(24, 2, 64, 32768) / 1e9:.2f} GB")
print(f"もしK・Vのヘッドも14個なら → 32,768トークンで {kv_cache_bytes(24, 14, 64, 32768) / 1e9:.2f} GB")
```

```output
1トークンあたり 12 KB → 32,768トークンで 0.40 GB
もしK・Vのヘッドも14個なら → 32,768トークンで 2.82 GB
```

:::theory GQA：Key・Valueのヘッドを共有する
Qwen2.5-0.5Bは、Queryのヘッドが14個あるのに、KeyとValueのヘッドは**2個だけ**です。7個のQueryヘッドが、1組のKey・Valueを**共有**しているのです。これを **GQA**（Grouped-Query Attention、グループ化クエリAttention）と言います。

性能はほとんど落ちずに、KVキャッシュのメモリが7分の1になります（上の計算では2.82GB → 0.40GB）。長い文章を扱うLLMや、たくさんの人が同時に使うサービスでは、KVキャッシュのメモリが一番の悩みの種なので、最近のLLMのほとんどがGQAを採用しています。K・Vのヘッドを1組だけにした極端な版は **MQA**（Multi-Query Attention）と呼ばれます。
:::

## 賢いサイコロ：top-k と top-p

第3章では、温度でサイコロの尖り具合を調整しました。でも、温度を上げると「ありえない候補」まで選ばれてしまう問題がありました（温度1.5の支離滅裂な文章を思い出してください）。そこで、**候補をあらかじめ絞ってから**サイコロを振る方法が使われます。

```python
words = ["猫", "犬", "人間", "名前", "机", "宇宙", "の"]
logits = torch.tensor([3.0, 1.6, 1.2, 0.4, -1.0, -1.5, -2.0])
probs = F.softmax(logits, dim=0)

def top_k_filter(probs, k):
    keep = torch.zeros_like(probs)
    idx = torch.topk(probs, k).indices
    keep[idx] = probs[idx]
    return keep / keep.sum()

def top_p_filter(probs, p):
    sorted_p, order = torch.sort(probs, descending=True)
    cum = torch.cumsum(sorted_p, dim=0)
    n_keep = int((cum < p).sum()) + 1            # 累積がpを超えるまでの最小の候補数
    keep = torch.zeros_like(probs)
    keep[order[:n_keep]] = probs[order[:n_keep]]
    return keep / keep.sum()

show = lambda p: "  ".join(f"{w}{x:.2f}" for w, x in zip(words, p) if x > 0)
print("そのまま ：", show(probs))
print("top-k=3 ：", show(top_k_filter(probs, 3)))
print("top-p=0.9：", show(top_p_filter(probs, 0.9)))
```

```output
そのまま ： 猫0.66  犬0.16  人間0.11  名前0.05  机0.01  宇宙0.01  の0.00
top-k=3 ： 猫0.71  犬0.17  人間0.12
top-p=0.9： 猫0.71  犬0.17  人間0.12
```

:::theory top-k と top-p（nucleus sampling）
- **top-k**：確率の高い上位 **k個** だけを候補に残す。シンプルだが、確率の分布の形を気にしない。候補がほぼ1つに決まっている場面でも、無理にk個残してしまう
- **top-p**（nucleus sampling、核サンプリング）：確率の高い順に足していき、合計が **p**（例えば0.9）を超えるまでの候補だけを残す。自信があるときは候補が少なく、迷っているときは多くなる。賢い

どちらも、残した候補の確率を足して1になるように割り直してから、サイコロを振ります。実際のチャットでは、「温度0.7、top-p 0.8」のような組み合わせがよく使われます。

もう1つ、同じ言葉をくり返しすぎるのを防ぐ **くり返しペナルティ**（repetition penalty）もよく使われます。すでに出てきたトークンの点数を少し下げる、という単純な方法です。第3章で小さなモデルが同じフレーズをくり返したのを、これで和らげられます。
:::

:::widget softmax full
:::

上のデモは、第3章のサイコロに top-k と top-p のつまみを付けたものです。温度を上げて候補を平らにしてから、top-p を0.8くらいに下げてみましょう。「机」のようなありえない候補が、サイコロから消えるのが分かります。`transformers` では、次のように指定するだけで使えます（Qwenなどで試すときに）。

```python no-run
out = model.generate(**inputs, max_new_tokens=100, do_sample=True,
                     temperature=0.7, top_p=0.8, top_k=50, repetition_penalty=1.1)
```

## 学習の工学1：勾配累積

T4のメモリに、バッチ64が入らない。でもバッチ64で学習したい。そんなときの技が **勾配累積**（gradient accumulation）です。小さなバッチで何回か `backward()` して勾配を**ためて**から、まとめて1回更新します。第7章で「`.grad` は足し算されていく」と注意しましたが、それを逆に利用するのです。

```python
torch.manual_seed(0)
net = nn.Linear(16, 4)
x, y = torch.randn(32, 16), torch.randint(0, 4, (32,))

net.zero_grad()
F.cross_entropy(net(x), y).backward()            # バッチ32で1回
g_big = net.weight.grad.clone()

net.zero_grad()
for i in range(4):                               # バッチ8を4回に分ける
    xb, yb = x[i * 8:(i + 1) * 8], y[i * 8:(i + 1) * 8]
    (F.cross_entropy(net(xb), yb) / 4).backward()    # 4で割ってから足し込む
g_acc = net.weight.grad

print("勾配は同じ？", torch.allclose(g_big, g_acc, atol=1e-6))
```

```output
勾配は同じ？ True
```

メモリに乗るのは「バッチ8」ぶんだけなのに、バッチ32で計算したのと同じ勾配が手に入りました。計算の量はバッチ32を1回やるのと同じなので、時間は大きくは変わりません（小分けにするぶん、少し遅くなる程度）。減るのは**途中の計算結果（活性化）のメモリ**で、だいたい4分の1になります。モデルの重み・勾配・AdamWの記録（第15章の「1パラメータあたり16バイト」）は、バッチの大きさに関係なく必要なので減りません。損失を累積回数（4）で割るのを忘れないのがコツです。

## 学習の工学2：活性化の再計算

学習中のメモリを一番食うのは、パラメータではなく、**逆伝播のために取っておく途中の計算結果**（活性化）であることがよくあります。第7章の計算グラフを思い出してください。`backward()` のために、順方向の途中の値を全部覚えておく必要がありました。

:::theory 勾配チェックポイント
**勾配チェックポイント**（activation checkpointing）は、途中の値を**覚えておかずに捨ててしまい**、逆伝播で必要になったときに**もう一度計算し直す**方法です。計算時間が約3割増える代わりに、メモリを大幅に節約できます。「メモを取らずに、必要なときに考え直す」作戦です。PyTorchでは `torch.utils.checkpoint.checkpoint(block, x)` のように、ブロックを包むだけで使えます。
:::

```python
from torch.utils.checkpoint import checkpoint

block = nn.Sequential(nn.Linear(64, 256), nn.GELU(), nn.Linear(256, 64))
x = torch.randn(8, 64, requires_grad=True)
out1 = block(x).sum(); out1.backward(); g1 = x.grad.clone()
x.grad = None
out2 = checkpoint(block, x, use_reentrant=False).sum(); out2.backward(); g2 = x.grad
print("同じ勾配？", torch.allclose(g1, g2))
```

```output
同じ勾配？ True
```

## 学習の工学3：FlashAttention

Attentionは、文章の長さ $T$ に対して $T \times T$ の点数表を作ります。長さ8000なら6400万マス。これをGPUのメモリに書いて、また読んで……をくり返すのが遅さの原因でした。

**FlashAttention** は、点数表を**小さなタイルに分けて**、GPUの中の超高速な小さいメモリの中だけで計算を済ませてしまう方法です。結果は同じなのに、速く、メモリも少なく済みます。PyTorchでは `F.scaled_dot_product_attention` を使うと、使える環境なら自動でFlashAttention（などの高速な方法）が選ばれます。

```python
torch.manual_seed(0)
q, k, v = (torch.randn(2, 4, 128, 32) for _ in range(3))     # [B, ヘッド, T, hs]

att = q @ k.transpose(-2, -1) / math.sqrt(32)
att = att.masked_fill(torch.tril(torch.ones(128, 128)) == 0, float("-inf"))
manual = F.softmax(att, dim=-1) @ v

fast = F.scaled_dot_product_attention(q, k, v, is_causal=True)
print("手作りと同じ？", torch.allclose(manual, fast, atol=1e-5))
```

```output
手作りと同じ？ True
```

第15章の `CausalSelfAttention` の中の4行（点数→マスク→softmax→Vを掛ける）を、この1行に置き換えるだけで、GPUでは何倍も速くなります。自分のGPTを速くしたくなったら、最初に試すべき改造です。

:::deep torch.compile
`model = torch.compile(model)` の1行で、PyTorchがモデルの計算をまとめて最適化してくれます（初回の実行は準備に時間がかかります）。GPU上では、学習が数割速くなることがよくあります。
:::

## 何百枚ものGPUで学習する：分散学習

1枚のGPUに乗らない、あるいは1枚では何年もかかる学習は、たくさんのGPUで分担します。この教科書の範囲（無料の環境）ではめったに使いませんが、論文やニュースを読むために、考え方だけは押さえておきましょう。

:::theory 分散学習の4つの作戦
- **データ並列**（DDP）：GPUごとにモデルを**丸ごとコピー**し、違うデータで学習。勾配だけを全GPUで平均する。一番シンプルで、よく使われる。でも、モデルが1枚に乗らないと使えない
- **ZeRO / FSDP**：データ並列の発展版。パラメータ・勾配・Adamの記録（第15章の16バイトの内訳）を、GPUたちで**分割して持ち合う**。必要なときだけ集めてくる。1枚に乗らない大きさのモデルも学習できる
- **テンソル並列**：1つの行列の掛け算を、**行列を分割して**複数のGPUで計算する。1つの層が大きすぎるときに使う。GPU間の通信が多いので、同じマシン内のGPUどうしで使う
- **パイプライン並列**：層ごとに担当のGPUを決める（1〜10層はGPU1、11〜20層はGPU2…）。工場の流れ作業。待ち時間（バブル）を減らす工夫が必要

最先端のLLMは、これらを全部組み合わせて（「3D並列」などと呼ばれます）、数千〜数万枚のGPUで学習されています。
:::

:::free 0円で分散学習を体験するなら
Kaggleのノートブックでは、無料で「T4×2」（GPU2枚）を選べることがあります。PyTorchの `torchrun` と DDP を使えば、2枚でのデータ並列を体験できます。興味がある人は、PyTorch公式の「DDPチュートリアル」を、Kaggleで試してみてください（[付録A](a-setup.html)にKaggleの使い方があります）。
:::

:::warn よくあるつまずき
- **KVキャッシュ付きの生成で結果が変わる**：位置の埋め込みの番号（`start_pos`）がずれていないか確認しましょう。キャッシュを使うときは、新しいトークンの位置は「これまでの長さ」から始まります。
- **勾配累積で学習がおかしい**：損失を累積回数で割っていないと、学習率が実質何倍にもなってしまいます。また、`zero_grad()` は「更新した後」に1回だけ呼びます。
- **`scaled_dot_product_attention` が遅い・使えない**：古いGPUや古いPyTorchでは、FlashAttentionが選ばれないことがあります。それでも結果は正しいので、心配はいりません。
:::

:::quiz KVキャッシュ
KVキャッシュで、過去のQueryは保存しなくていいのはなぜ？
:::answer
新しいトークンを生成するとき、Attentionの計算に使うのは「新しいトークンのQuery」と「過去を含む全部のKey・Value」だからです。過去の位置のQueryは、過去の位置の出力を計算するためにしか使わず、その出力はもう計算済みです。
:::

:::quiz top-p
確率が `[0.5, 0.3, 0.1, 0.05, 0.05]` のとき、top-p=0.85 で残る候補はいくつ？
:::answer
上位から足すと 0.5 → 0.8 → 0.9。0.85を超えるのは3つ目を足したときなので、**3つ**残ります。
:::

:::quiz 勾配累積
バッチ8で勾配累積を4回するのは、バッチ何で学習するのと同じ？ 何に気をつける？
:::answer
バッチ32と同じです。損失を4で割ってから `backward()` すること、4回ためた後に1回だけ更新して、それから勾配を0に戻すことに気をつけます。
:::

:::checklist
- KVキャッシュあり・なしで、同じ結果がより速く出ることを確かめた
- KVキャッシュのメモリを計算し、GQAで減る理由を説明できる
- top-k と top-p の違いを説明できる
- 勾配累積で、大きなバッチと同じ勾配になることを確かめた
- `scaled_dot_product_attention` が手作りのAttentionと一致することを確かめた
- 分散学習の4つの作戦を、ひとことずつ説明できる
:::

:::recap
- **KVキャッシュ**：過去のKey・Valueを取っておき、新しいトークンだけ計算する。生成が大幅に速くなる
- KVキャッシュのメモリ ＝ 2 × 層数 × K/Vのヘッド数 × ヘッドの大きさ × トークン数 × バイト数。**GQA**で減らせる
- **top-k / top-p** で候補を絞ってからサンプリングする。くり返しペナルティも
- **勾配累積**・**勾配チェックポイント**・**FlashAttention**・混合精度で、少ないメモリで速く学習する
- 大きなLLMは、データ並列・ZeRO・テンソル並列・パイプライン並列を組み合わせて学習する
:::

:::sensei
第4部、お疲れさま！ ここまでで、キミは「LLMを中身から作れる人」になった。次の第5部からは、視点を変える。世界中の企業が何億円もかけて事前学習したモデルを**借りてきて**、キミの目的に合わせて鍛え直す。現代のLLM開発の、いちばん実践的な部分だ。
:::
