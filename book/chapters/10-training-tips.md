{"title": "学習のお医者さん：うまく学習させる技", "short": "学習のお医者さん", "subtitle": "初期化・正規化・Adam・ドロップアウト・学習率スケジュールを救急箱に", "time": "2〜3時間（2回に分けてOK）", "env": "cpu", "level": 3, "builds": "過学習を抑え、安定して学習する改良版MLPと、学習の「診察表」。モデルをGoogleドライブに保存する方法も", "theory": ["平均・分散・標準偏差と正規分布", "初期化：最初の損失は $\\log V$ 付近が健康", "活性化の大きさが層を通るたびに暴れる問題（勾配消失・爆発）", "LayerNorm（層正規化）", "Adam / AdamW（慣性と、パラメータごとの歩幅）", "過学習とドロップアウト・重み減衰", "学習率のウォームアップとコサイン減衰", "勾配クリッピング"], "python": ["`torch.randn` と `.mean()` `.std()`", "`model.train()` と `model.eval()`", "`torch.save` / `torch.load`", "`google.colab.drive` でドライブに保存"]}

:::goal
第9章のMLPは、bigramの記録を破りましたが、途中から**丸暗記（過学習）**を始めていました。この章では、学習がうまくいかないときの「症状」と「治療法」をまとめて学びます。治療をすべて施した改良版MLPで、記録を **3.395 → 3.18 前後** まで伸ばします。ここで学ぶ技は、第13章のGPTでもそのまま使います。
:::

:::minato
「学習のお医者さん」って、なんだか大げさですね。
:::

:::sensei
いや、大げさじゃない。ニューラルネットワークの学習は、とても繊細な生き物だ。熱が出たり（損失が爆発）、寝込んだり（損失が下がらない）、物覚えが良すぎて応用がきかなくなったり（過学習）する。プロの研究者も、時間の大半を「診察」に使っている。今日はキミに聴診器を渡そう。
:::

## 準備

準備セルは第9章とほぼ同じです。モデルには、この章で学ぶ部品（`LayerNorm` と `Dropout`）をあらかじめ入れてあります。説明は後で出てくるので、今は貼り付けて実行してください。

:::tip 2回に分けるときは
この章は長いので、「診察3：過学習」の手前で一度休むのがおすすめです。Colabは、しばらく放っておくとセッションが切れて、変数（`train` や `hist_a` など）が全部消えます。2回目は、メニューの「ランタイム」→「前のセルを実行」などで、**この準備セルから順に全部実行し直して**から続きを読みましょう（CPUで10分ほどかかります）。
:::

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
T = 8

class MLP(nn.Module):
    def __init__(self, V, T, d=32, H=256, dropout=0.0):
        super().__init__()
        self.emb = nn.Embedding(V, d)
        self.fc1 = nn.Linear(T * d, H)
        self.ln = nn.LayerNorm(H)           # この章で学ぶ「層正規化」
        self.drop = nn.Dropout(dropout)     # この章で学ぶ「ドロップアウト」
        self.fc2 = nn.Linear(H, V)

    def forward(self, x):
        e = self.emb(x)
        h = torch.tanh(self.ln(self.fc1(e.view(len(x), -1))))
        return self.fc2(self.drop(h))

val_X = torch.stack([val_data[i:i + T] for i in range(len(val_data) - T)])
val_Y = val_data[T:]

@torch.no_grad()
def val_loss(model):
    model.eval()
    loss = F.cross_entropy(model(val_X), val_Y).item()
    model.train()
    return loss
```

## 診察1：最初の損失を見る

学習を始める前に、まず **最初の損失** を見ます。何も学んでいないモデルは、全部の文字を同じくらいの確率で選ぶはずなので、損失は $\log V$ くらいになるはずでした（第8章）。

```python
torch.manual_seed(0)
model = MLP(V, T)
x, y = val_X[:512], val_Y[:512]
print("理想の最初の損失 log V：", round(math.log(V), 3))
print("このモデルの最初の損失：", round(F.cross_entropy(model(x), y).item(), 3))

with torch.no_grad():
    model.fc2.weight *= 30          # わざと出力層の重みを30倍にしてみる
print("重みを30倍にしたら：", round(F.cross_entropy(model(x), y).item(), 3))
```

```output
理想の最初の損失 log V： 7.631
このモデルの最初の損失： 7.7
重みを30倍にしたら： 37.845
```

重みを大きくしたら、最初の損失が30以上に跳ね上がりました。何も知らないくせに、点数（ロジット）に大きな差をつけて「この文字に違いない！」と**自信満々に間違えている**状態です。こうなると、学習の最初の時間を「自信過剰を直す」ことだけに使ってしまいます。

:::tip 処方箋：最初の損失は log V の近くに
学習を始める前に、必ず最初の損失を `print` しましょう。$\log V$ から大きく外れていたら、初期化（パラメータの最初の値）がおかしいサインです。出力層の重みを小さめにしておくのが定石です。
:::

## 統計の道具：平均・分散・標準偏差

初期化の話をもう少し深めるために、統計の道具を3つだけ用意します。

```python
z = torch.randn(10000)       # 「標準正規分布」から10000個の数を引く
print("平均：", round(z.mean().item(), 3))
print("分散：", round(z.var().item(), 3))
print("標準偏差：", round(z.std().item(), 3))
```

```output
平均： -0.03
分散： 1.001
標準偏差： 1.001
```

:::math 平均・分散・標準偏差
- **平均**（mean）：全部足して個数で割る。データの「真ん中」
- **分散**（variance）：「平均からのずれ」を2乗して平均したもの。データの「ばらつき」
- **標準偏差**（standard deviation）：分散の平方根。ばらつきを元の単位に戻したもの。$\sigma$（シグマ）と書く

$$\sigma = \sqrt{\frac{1}{N}\sum_{i=1}^{N} (x_i - \bar{x})^2}$$

$\bar{x}$ は平均です。またΣ（for文）が出てきましたね。

`torch.randn` は **正規分布**（ガウス分布）という、平均0・標準偏差1の釣り鐘型のばらつきから数を引きます。身長やテストの点数など、自然界のいろいろなばらつきがこの形になります。ヒストグラムで見てみましょう。
:::

```python
!pip install -q matplotlib-fontja
```

```python
import matplotlib.pyplot as plt
import matplotlib_fontja

plt.figure(figsize=(6, 3))
plt.hist(z.numpy(), bins=60)
plt.title("torch.randn の数のばらつき（正規分布）")
plt.xlabel("値"); plt.ylabel("個数")
plt.show()
```

![正規分布のヒストグラム。0を中心にした釣り鐘型](img/figs/10-training-tips/cell4_0.png)

## 診察2：層を通るたびに暴れる数

ニューラルネットワークを深く（層をたくさん）すると、層を通るたびに数の大きさが変わっていきます。10層の全結合層＋tanhに、標準偏差1の数を流して、各層の出力の標準偏差を測ってみましょう。

```python
def stack_stats(weight_scale, layers=10, width=256):
    torch.manual_seed(0)
    h = torch.randn(1000, width)
    stds = []
    for _ in range(layers):
        W = torch.randn(width, width) * weight_scale
        h = torch.tanh(h @ W)
        stds.append(round(h.std().item(), 3))
    return stds

print("重みの大きさ 1.0  ：", stack_stats(1.0))
print("重みの大きさ 0.01 ：", stack_stats(0.01))
print("重みの大きさ 1/√256：", stack_stats(1 / math.sqrt(256)))
```

```output
重みの大きさ 1.0  ： [0.975, 0.974, 0.974, 0.974, 0.974, 0.974, 0.974, 0.974, 0.974, 0.974]
重みの大きさ 0.01 ： [0.156, 0.025, 0.004, 0.001, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
重みの大きさ 1/√256： [0.628, 0.486, 0.408, 0.359, 0.322, 0.293, 0.271, 0.253, 0.238, 0.226]
```

:::theory 勾配消失と飽和
- **重みが大きすぎる（1.0）**：数がどんどん大きくなり、tanhの出力がほとんど ±1 に張り付きます（標準偏差0.97≒ほぼ全部が±1）。tanhは±1の近くで**傾きがほぼ0**なので、誤差逆伝播で勾配がほとんど伝わりません（**飽和**）
- **重みが小さすぎる（0.01）**：数がどんどん小さくなり、4層目ではほぼ0。信号が消えてしまいます。勾配も同じように消えていきます（**勾配消失**）
- **ちょうどいい（$1/\sqrt{\text{入力の数}}$）**：大きさがゆっくり減る程度で、深い層まで信号が届きます

入力が256個あると、256個の数を足し合わせるので、ばらつきが $\sqrt{256} = 16$ 倍に膨らみます。だから重みを $1/\sqrt{256}$ にしておくと、ちょうど打ち消し合うのです。PyTorchの `nn.Linear` は、最初からこの考え方に基づいた大きさで初期化されています（**Xavier初期化**、**Kaiming初期化**などと呼ばれる方法の仲間）。

逆向きの勾配が層を通るたびに大きくなりすぎる場合は **勾配爆発** と言います。損失が突然 `nan`（計算不能）になるのは、たいていこれです。
:::

## 治療1：LayerNorm（層正規化）

初期化に気をつけても、学習中にパラメータが変わると、また数の大きさは暴れ出します。そこで、**毎回、強制的に大きさをそろえる**部品を挟みます。それが **LayerNorm**（レイヤーノーム、層正規化）です。

```python
h = torch.randn(2, 6) * 5 + 3      # 平均3、標準偏差5くらいの、暴れた数
mean = h.mean(dim=1, keepdim=True)
std = h.std(dim=1, keepdim=True, unbiased=False)   # unbiased=False：数式どおり N で割る
h_hand = (h - mean) / (std + 1e-5)  # 平均を引いて、標準偏差で割る

ln = nn.LayerNorm(6, elementwise_affine=False)
print(h_hand)
print(ln(h))
```

```output
tensor([[-0.2989,  0.0184, -1.2615,  1.8086,  0.5781, -0.8448],
        [-0.0293,  0.7320,  1.0004, -0.1376, -2.0512,  0.4857]])
tensor([[-0.2989,  0.0184, -1.2615,  1.8086,  0.5781, -0.8448],
        [-0.0293,  0.7320,  1.0004, -0.1376, -2.0512,  0.4857]])
```

:::theory LayerNormは「偏差値」
LayerNormは、1つのデータ（1行）の中の数について、**平均を引いて標準偏差で割る**だけです。すると、元の数がどんなに大きくても小さくても、平均0・標準偏差1にそろいます。

これは、テストの点数を **偏差値** にするのと同じ発想です。難しいテストでも簡単なテストでも、偏差値にすれば同じものさしで比べられますよね。

実際の `nn.LayerNorm` は、そろえた後に「学習可能な倍率と足し算」で少しだけ形を調整できるようになっています（上では `elementwise_affine=False` でそれを切っています）。LayerNormはGPTの部品として、第12章で何度も登場します。
:::

## 治療2：Adam（賢い坂の下り方）

第7章からずっと、坂の下り方は「傾きに学習率を掛けて進む」SGDでした。現代のLLMの学習では、ほぼ必ず **Adam**（アダム）またはその改良版 **AdamW** を使います。

:::theory Adamは「慣性」と「自分専用の歩幅」
SGDの弱点は2つあります。

1. **ミニバッチのぶれに振り回される**：毎回の勾配がガタガタなので、ジグザグに進んでしまう
2. **全パラメータが同じ歩幅**：めったに出てこない文字の埋め込みは、勾配がたまにしか来ないので、なかなか学習が進まない

Adamは次の2つの工夫でこれを解決します。

- **慣性（モーメンタム）**：これまでの勾配の平均的な向きを覚えておき、それに沿って進む。ボールが坂を転がるとき、小さなでこぼこでは向きを変えないのと同じ
- **パラメータごとの歩幅**：勾配がいつも小さいパラメータは歩幅を大きく、いつも大きいパラメータは歩幅を小さくする。2乗の平均（分散のようなもの）で割ることで実現する

AdamWの「W」は **重み減衰**（weight decay）を正しく組み込んだ版、という意味です（重み減衰は後で出てきます）。
:::

では、AdamWで学習させてみましょう。学習の様子を記録しながら、6000ステップ進めます。

```python
def train(model, steps=6000, lr=1e-3, weight_decay=0.0, schedule=False, seed=0):
    g = torch.Generator().manual_seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    history = []
    for step in range(steps + 1):
        if schedule:                                   # 学習率スケジュール（後で説明）
            for group in opt.param_groups:
                group["lr"] = lr_at(step, lr, steps)
        ix = torch.randint(0, len(train_data) - T, (256,), generator=g)
        x = torch.stack([train_data[i:i + T] for i in ix])
        y = train_data[ix + T]
        loss = F.cross_entropy(model(x), y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # 勾配クリッピング（後で説明）
        opt.step()
        if step % 1000 == 0:
            history.append((step, loss.item(), val_loss(model)))
            print(f"ステップ {step:4d}：訓練 {history[-1][1]:.3f}  検証 {history[-1][2]:.3f}")
    return history

torch.manual_seed(0)
model_a = MLP(V, T)
hist_a = train(model_a, lr=1e-3)
```

```output
ステップ    0：訓練 7.678  検証 7.660
ステップ 1000：訓練 3.540  検証 3.581
ステップ 2000：訓練 2.765  検証 3.419
ステップ 3000：訓練 2.775  検証 3.386
ステップ 4000：訓練 2.434  検証 3.392
ステップ 5000：訓練 2.393  検証 3.428
ステップ 6000：訓練 1.937  検証 3.465
```

速い！ SGDでは1万ステップかかった3.4台に、2000ステップで到達しました。でも、よく見てください。3000ステップを過ぎると、**訓練損失は下がり続けているのに、検証損失は上がり始めて**います。

## 診察3：過学習

```python
def plot_history(hists, labels, title):
    plt.figure(figsize=(6, 3.5))
    for h, label in zip(hists, labels):
        s = [r[0] for r in h]
        plt.plot(s, [r[1] for r in h], linestyle="--", label=label + "（訓練）")
        plt.plot(s, [r[2] for r in h], label=label + "（検証）")
    plt.ylim(1.5, 4.5)
    plt.xlabel("ステップ"); plt.ylabel("損失")
    plt.legend(); plt.title(title)
    plt.show()

plot_history([hist_a], ["AdamW"], "訓練は下がり続け、検証は途中から悪化")
```

![AdamWで学習したMLPの学習曲線。訓練損失は下がり続けるが、検証損失は3000ステップ付近を底に上がっていく](img/figs/10-training-tips/cell8_0.png)

:::theory 過学習（オーバーフィッティング）
訓練データに合わせすぎて、検証データでの成績が悪くなる現象を **過学習**（overfitting）と言います。過去問の答えを丸暗記して、本番で応用がきかない状態です。

過学習が起きやすいのは、

- データが少ない（『こころ』の16万字は、LLMの世界では米粒ほど）
- モデルが大きい（パラメータが多いほど、丸暗記の容量がある）
- 長く学習しすぎる

ときです。治療法は「データを増やす」が一番ですが（第13章でやります）、ここでは**モデルの側で丸暗記しにくくする**方法を2つ使います。
:::

## 治療3：ドロップアウトと重み減衰

:::theory ドロップアウト：わざと一部を休ませる
**ドロップアウト**（dropout）は、学習中に、ニューロンの一部（例えば30%）を**ランダムに0にする**方法です。毎回違うニューロンが休むので、モデルは「特定のニューロンに頼った丸暗記」ができなくなり、どのニューロンが休んでもなんとかなるような、頑丈な特徴を学ぶようになります。

チームで練習するとき、毎回ランダムに3割が欠席するとしたら、「エースに全部任せる」作戦は使えませんよね。全員がそこそこできるようになるしかない。それがドロップアウトです。

評価（検証や生成）のときは、全員出席（ドロップアウトなし）にします。そのために `model.eval()`（評価モード）と `model.train()`（学習モード）を切り替えます。準備セルの `val_loss` 関数の中で、これをやっていました。
:::

:::theory 重み減衰：大きな重みに罰金
**重み減衰**（weight decay）は、毎ステップ、重みを少しだけ0に向かって縮める方法です。極端に大きな重みを持つ（＝特定のパターンに極端に反応する）ことを防ぎます。第8章で話した **正則化** の代表選手で、第5章のスムージングの親戚です。AdamWでは `weight_decay=0.1` のように指定します。
:::

## 治療4：学習率スケジュール

最後に、学習率を学習の途中で変える技です。

```python
def lr_at(step, max_lr, total, warmup=200):
    if step < warmup:
        return max_lr * step / warmup                       # ウォームアップ：0から徐々に上げる
    progress = (step - warmup) / (total - warmup)
    return max_lr * 0.5 * (1 + math.cos(math.pi * progress))  # コサイン減衰：なめらかに0へ

steps = list(range(6001))
plt.figure(figsize=(6, 2.8))
plt.plot(steps, [lr_at(s, 2e-3, 6000) for s in steps])
plt.xlabel("ステップ"); plt.ylabel("学習率")
plt.title("ウォームアップ＋コサイン減衰")
plt.show()
```

![学習率スケジュールのグラフ。最初の200ステップで0から最大値まで上がり、その後コサインカーブでなめらかに0まで下がる](img/figs/10-training-tips/cell9_0.png)

:::theory なぜ学習率を変えるのか
- **最初（ウォームアップ）**：学習の最初は、パラメータがでたらめで勾配も荒れています。いきなり大股で進むと転ぶので、小股から始めて徐々に歩幅を広げます
- **最後（減衰）**：谷底に近づいたら、大股だと谷底を行ったり来たりしてしまいます（第7章の学習率が大きすぎる例）。歩幅を小さくして、そっと谷底に着地します

**コサイン減衰**は、三角関数のコサインのカーブを使って、なめらかに学習率を下げる方法です。GPTを含む多くのLLMで使われています。
:::

:::python opt.param_groups
`train` 関数の中の `for group in opt.param_groups: group["lr"] = …` が、学習率を変えている部分です。`opt.param_groups` は、オプティマイザーが持っている設定（学習率など）の入れ物のリストで、`group["lr"]` を書き換えると、次の `opt.step()` からその学習率で進みます。`schedule=True` のときは、これを毎ステップ `lr_at` の値に書き換えています。
:::

:::theory 勾配クリッピング
`train` 関数の中の `clip_grad_norm_(model.parameters(), 1.0)` は、**勾配の大きさが1.0を超えたら、1.0に縮める**処理です。たまに来る異常に大きな勾配（勾配爆発）で、一気に遠くへ吹き飛ばされるのを防ぐ安全ベルトです。向きはそのままで、長さだけを制限します。
:::

## 全部の治療を施す

ドロップアウト30%、重み減衰0.1、学習率スケジュール、勾配クリッピング。全部入りで学習させてみましょう。

```python
torch.manual_seed(0)
model_b = MLP(V, T, dropout=0.3)
hist_b = train(model_b, lr=2e-3, weight_decay=0.1, schedule=True)
```

```output
ステップ    0：訓練 7.706  検証 7.703
ステップ 1000：訓練 3.533  検証 3.530
ステップ 2000：訓練 2.856  検証 3.347
ステップ 3000：訓練 2.917  検証 3.272
ステップ 4000：訓練 2.656  検証 3.213
ステップ 5000：訓練 2.831  検証 3.183
ステップ 6000：訓練 2.469  検証 3.177
```

```python
plot_history([hist_a, hist_b], ["治療前", "治療後"], "治療前と治療後")
```

![治療前と治療後の学習曲線の比較。治療後は検証損失が最後まで下がり続け、3.18付近に到達する](img/figs/10-training-tips/cell11_0.png)

検証損失が最後まで下がり続け、**3.177** に到達しました。訓練損失と検証損失の差も小さくなっています。治療成功です。

| モデル | 章 | 検証データの損失 |
|---|---|---|
| でたらめ | 5 | 7.631 |
| bigram（数える） | 5 | 3.581 |
| ニューラルbigram | 8 | 3.685 |
| MLP（SGD） | 9 | 3.395 |
| **MLP（LayerNorm＋AdamW＋ドロップアウト＋スケジュール）** | **10** | **3.177** |

## 学習したモデルを保存する

2分かけて学習したモデルも、Colabの接続が切れたら消えてしまいます。**Googleドライブ**に保存しておきましょう。

```python
from google.colab import drive
drive.mount("/content/drive")
```

実行すると、Googleアカウントへのアクセスを許可するか聞かれます。自分のアカウントを選んで許可してください。すると `/content/drive/MyDrive` が、あなたのGoogleドライブの中身になります。

```python
import os
save_dir = "/content/drive/MyDrive/tsukuru-llm"
os.makedirs(save_dir, exist_ok=True)
torch.save(model_b.state_dict(), f"{save_dir}/mlp_kokoro.pt")
print("保存しました：", os.listdir(save_dir))
```

```output
保存しました： ['mlp_kokoro.pt']
```

読み込むときは、同じ設計図でモデルを作ってから、保存した中身を流し込みます。

```python
loaded = MLP(V, T, dropout=0.3)
loaded.load_state_dict(torch.load(f"{save_dir}/mlp_kokoro.pt"))
print("読み込んだモデルの検証損失：", round(val_loss(loaded), 3))
```

```output
読み込んだモデルの検証損失： 3.177
```

:::python state_dict
`model.state_dict()` は、モデルの全パラメータを「名前 → テンソル」の辞書にしたものです。保存されるのは**中身の数だけ**で、設計図（クラスの定義）は保存されません。だから読み込むときは、先に同じクラスでモデルを作る必要があります。ゲームのセーブデータを読み込むには、ゲーム本体が必要なのと同じです。
:::

:::free ドライブの容量
無料のGoogleアカウントのドライブ容量は15GB（Gmailや写真と共有）です。このMLPの保存ファイルは約2.6MBなので心配いりませんが、第17章以降の大きなモデル（数百MB〜数GB）を保存するときは、容量に気をつけましょう。いらなくなったファイルは消すのが0円のコツです。
:::

## 学習の診察表

この章のまとめとして、症状と治療法の表を作っておきます。学習がうまくいかないときは、上から順に確認しましょう。

| 症状 | 考えられる原因 | 治療法 |
|---|---|---|
| 最初の損失が $\log V$ よりずっと大きい | 初期化が大きすぎる | 出力層の重みを小さく。デフォルトの初期化を使う |
| 損失がまったく下がらない | 学習率が小さすぎる／バグ（`zero_grad` 忘れ、`requires_grad` 忘れ） | 学習率を10倍に。コードを見直す |
| 損失が `nan` になる、急に跳ね上がる | 学習率が大きすぎる／勾配爆発 | 学習率を下げる。勾配クリッピング。ウォームアップ |
| 損失がガタガタで下がりにくい | バッチが小さい／学習率が大きい | バッチを大きく。学習率スケジュール |
| 訓練だけ下がって、検証が上がる | 過学習 | データを増やす。ドロップアウト。重み減衰。早めに止める |
| 訓練も検証も高いまま横ばい | モデルが小さすぎる（表現力不足） | 層や幅を増やす。窓（文脈）を広げる |

:::tip 研究者の口ぐせ：「まず小さなデータで過学習させてみよ」
新しいモデルを作ったら、最初に**ごく少ないデータ（例えば1バッチだけ）で学習**させて、訓練損失がほぼ0まで下がるか確かめます。下がらなければ、モデルか学習ループにバグがあります。丸暗記すらできないモデルが、汎化できるはずがないからです。
:::

:::warn よくあるつまずき
- **`drive.mount` で止まる・失敗する**：ポップアップがブロックされていないか確認しましょう。アカウント選択の画面で、すべての項目にチェックを入れて「続行」を押します。
- **`RuntimeError: Error(s) in loading state_dict`**：保存したときと違う設計図（`dropout` 以外の `d` や `H`、`T` など）でモデルを作っています。保存時と同じ設定で作りましょう。
- **検証損失が、同じモデルなのに実行するたびにぶれる**：`model.eval()` と `model.train()` の切り替えを忘れていないか確認しましょう。評価時にドロップアウトが効いていると、結果がぶれます。
- **`.std()` で計算した標準偏差が、手計算と合わない**：PyTorchの `.std()` と `.var()` は、標準では N ではなく N−1 で割ります（統計で「標本から全体を推定する」ときの割り方）。数式どおり N で割るには `unbiased=False` を付けます。LayerNormは N で割るほうです。
:::

:::quiz 過学習の見分け方
学習中、訓練損失は2.0まで下がりましたが、検証損失は3.5から3.7に上がってきました。何が起きている？ 何をする？
:::answer
過学習です。訓練データを丸暗記し始めています。対策は、データを増やす、ドロップアウトや重み減衰を強める、モデルを小さくする、検証損失が最も低かった時点で学習を止める（そのときのモデルを使う）、などです。
:::

:::quiz LayerNorm
LayerNormに `[2, 4, 6]` を入れると（倍率などの調整なし）、どんな数になる？
:::answer
平均は4、標準偏差は $\sqrt{((2-4)^2 + 0 + (6-4)^2)/3} = \sqrt{8/3} \approx 1.633$。平均を引いて割ると、約 `[-1.22, 0, 1.22]` になります。
:::

:::quiz Adamの慣性
Adamの「慣性（モーメンタム）」は、どんな問題を和らげる？
:::answer
ミニバッチごとに勾配の向きがぶれて、ジグザグに進んでしまう問題です。過去の勾配の平均的な向きに沿って進むので、小さなぶれに振り回されにくくなります。
:::

:::checklist
- 最初の損失を $\log V$ と比べる習慣がついた
- 平均・分散・標準偏差をテンソルで計算できた
- 重みの大きさで、層を通る数が消えたり飽和したりするのを見た
- LayerNormを手計算と `nn.LayerNorm` で確かめた
- AdamWで学習し、過学習の学習曲線を見た
- ドロップアウト・重み減衰・スケジュールで検証損失を3.18前後まで下げた
- モデルをGoogleドライブに保存し、読み込めた
:::

:::recap
- まず **最初の損失** を見る。$\log V$ から外れていたら初期化を疑う
- 重みの大きさが不適切だと、深い層で信号が **消える・飽和する**。$1/\sqrt{\text{入力数}}$ が目安
- **LayerNorm** は各データの数を平均0・標準偏差1にそろえる（偏差値）
- **AdamW** は慣性とパラメータごとの歩幅で、SGDより速く賢く下る
- **過学習** には、ドロップアウト・重み減衰・データを増やす
- **ウォームアップ＋コサイン減衰**、**勾配クリッピング** で学習を安定させる
:::

:::sensei
第2部、完走おめでとう！ ここまでで、ニューラル言語モデルを作って鍛えるための道具は、ほとんどそろった。足りないのは、あと1つだけ。「直前8文字」の窓を、もっと賢く、もっと長く使う方法だ。それが **Attention**。GPTの心臓部だ。第3部で、いよいよGPTを組み立てるぞ。
:::
