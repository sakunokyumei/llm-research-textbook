{"title": "数の表を一気に扱う：テンソル", "short": "テンソル", "subtitle": "for文を卒業して、420万マスの表を一瞬で計算する", "time": "60〜90分", "env": "cpu", "level": 2, "builds": "bigramモデルを「確率の表（行列）」として作り直し、損失計算を一瞬で終わらせる", "theory": ["ベクトル・行列・テンソルと「形（shape）」", "行ごとの合計とブロードキャスト", "one-hotベクトルと行列の掛け算（＝表の行を取り出す）", "行列の積の形のルール $(n \\times k)(k \\times m) = (n \\times m)$", "なぜGPUは速いのか（並列計算）"], "python": ["`torch.tensor` / `torch.zeros`", "`.shape` と `.dtype`", "インデックスとスライス（`N[i, j]`、`N[:, j]`）", "`sum(dim=…, keepdim=True)`", "`@`（行列の掛け算）", "`time` で計測"]}

:::goal
第5章では、Pythonのfor文で1文字ずつ確率を計算しました。それでも動きますが、これから作るモデルは**何百万回、何億回**も計算します。for文では日が暮れて、夜が明けて、また日が暮れます。この章では、たくさんの数をまとめて一気に計算する道具 **テンソル** を手に入れ、bigramモデルを「確率の表」として作り直します。
:::

:::minato
テンソルって、名前がもう強そうです。
:::

:::sensei
名前はね。でも中身は「数を並べた箱」だ。1列に並べたらベクトル、表にしたら行列、それを何枚も重ねたら3次元のテンソル。HTMLの `<table>` が書けるキミなら、もう半分わかっている。
:::

## 準備

いつもの準備セルです（第5章と同じ）。今回は `torch` も使います。

```python
import re, math, time, urllib.request
from collections import Counter
import torch

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
print("語彙の数：", V)
```

```output
語彙の数： 2061
```

:::python 辞書を1行で作る
`{ch: i for i, ch in enumerate(chars)}` は、第2章でfor文を使って作った `stoi` を1行で書いたものです（**辞書内包表記**）。やっていることは同じです。
:::

## テンソル入門：数を並べた箱

テンソルを作ってみましょう。

```python
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([10.0, 20.0, 30.0])
print(a + b)
print(a * b)
print(a * 2)
print(a.sum())
```

```output
tensor([11., 22., 33.])
tensor([10., 40., 90.])
tensor([2., 4., 6.])
tensor(6.)
```

ポイントは、**for文を書いていないのに、全部の要素がいっぺんに計算されている**ことです。`a + b` は「同じ位置どうしを足す」、`a * 2` は「全部を2倍」。リストでやろうとすると、for文が必要でしたね。

次は2次元、つまり表です。

```python
M = torch.tensor([[1, 2, 3],
                  [4, 5, 6]])
print(M.shape)
print(M[0])       # 0行目
print(M[:, 1])    # 1列目（全部の行の、1番目）
print(M[1, 2])    # 1行目の2列目
```

```output
torch.Size([2, 3])
tensor([1, 2, 3])
tensor([2, 5])
tensor(6)
```

:::theory ベクトル・行列・テンソルと「形」
- 数を1列に並べたもの：**ベクトル**（vector）。`a` は長さ3のベクトル
- 数を表（縦×横）に並べたもの：**行列**（matrix）。`M` は2行3列の行列
- さらに何枚も重ねたもの（3次元以上も含めた総称）：**テンソル**（tensor）

テンソルを扱うときに一番大事なのは **形**（shape）です。`M.shape` は `[2, 3]`、つまり「2行3列」。この先、エラーの半分以上は「形が合わない」ことが原因です。迷ったら、とにかく `.shape` を `print` しましょう。これはこの教科書で一番役に立つアドバイスかもしれません。
:::

:::fe 2次元配列
基本情報の擬似言語やアルゴリズムの問題で出てくる「2次元配列」が、まさに行列です。`M[1, 2]` は「1行目の2列目」。ただしPythonは0から数えるので、人間の感覚では「2行目の3列目」です。試験の問題が1から数えるか0から数えるかは、毎回確認しましょう。
:::

## bigramの表を作る

いよいよ本題です。第4章の「今の文字（行）×次の文字（列）」の表を、2061×2061の行列として作ります。

```python
n = int(len(text) * 0.9)
train_text, val_text = text[:n], text[n:]

pairs = Counter(zip(train_text, train_text[1:]))
N = torch.zeros((V, V))
for (a, b), count in pairs.items():
    N[stoi[a], stoi[b]] = count

print(N.shape)
print("「先」→「生」の回数：", N[stoi["先"], stoi["生"]].item())
print("表のマスの数：", N.numel(), " うち0でないマス：", (N > 0).sum().item())
```

```output
torch.Size([2061, 2061])
「先」→「生」の回数： 597.0
表のマスの数： 4247721  うち0でないマス： 20395
```

:::python .item() と比較
`N[i, j]` の結果は「数が1つだけ入ったテンソル」です。`.item()` を付けると、ふつうのPythonの数として取り出せます。<br>
`N > 0` は、全部のマスについて「0より大きい？」を調べた、True/Falseの表を作ります。それを `.sum()` すると、Trueの数（＝0でないマスの数）が数えられます。
:::

約420万マスのうち、0でないのは約2万マス（0.5%以下）。第4章で話した「スパース（まばら）」が、数字で見えました。

## 回数を確率に変える：行ごとの合計とブロードキャスト

回数を確率にするには、各行を「その行の合計」で割ればよいのでした。スムージングの `k` も足しておきます。

```python
k = 0.01
row_sums = (N + k).sum(dim=1, keepdim=True)
print(row_sums.shape)

P = (N + k) / row_sums
print(P.shape)
print("各行の合計（最初の5行）：", P.sum(dim=1)[:5])
```

```output
torch.Size([2061, 1])
torch.Size([2061, 2061])
各行の合計（最初の5行）： tensor([1.0000, 1.0000, 1.0000, 1.0000, 1.0000])
```

:::theory 合計の方向と、ブロードキャスト
`sum(dim=1)` は「1番目の軸（横方向）に沿って足す」、つまり**各行の合計**です。`dim=0` なら各列の合計になります。`keepdim=True` は「足した軸を消さずに長さ1で残す」指定で、結果の形は `[2061, 1]`（縦に2061個並んだ数）になります。

そして `(N + k) / row_sums` では、形が `[2061, 2061]` と `[2061, 1]` で違うのに、割り算ができています。これは **ブロードキャスト** という仕組みで、長さ1の軸が自動的に「横にコピーされた」ものとして扱われるからです。

<div class="math-display">[[a, b, c],      [[x],        [[a/x, b/x, c/x],
 [d, e, f]]  ÷   [y]]    →    [d/y, e/y, f/y]]</div>

各行が、その行の合計で割られます。for文なしで、420万マスの割り算が一瞬です。
:::

:::warn keepdim を忘れると
`keepdim=True` を付けないと、`row_sums` の形は `[2061]` になり、ブロードキャストの向きが変わって「各**列**を割る」ことになってしまいます。エラーにならずに**間違った答えが出る**ので、とても危険です。形を `print` して確かめるクセをつけましょう。
:::

## 損失を一瞬で計算する

第5章では、for文で1文字ずつ損失を計算しました。テンソルなら、こうなります。

```python
val_ids = torch.tensor([stoi[c] for c in val_text])
xs, ys = val_ids[:-1], val_ids[1:]

start = time.time()
probs = P[xs, ys]
loss = -probs.log().mean()
print(f"検証データの損失：{loss.item():.3f}（{time.time() - start:.4f}秒）")
```

```output-example
検証データの損失：3.581（0.0012秒）
```

第5章と同じ **3.581** です。`P[xs, ys]` は「`xs` の各文字の行の、`ys` の各文字の列」をいっぺんに取り出す書き方（**高度なインデックス**）で、16,246個の確率が一度に手に入ります。`.log()` で全部の対数をとり、`.mean()` で平均。3行で損失が出ました。

:::sensei
同じことをfor文でやると、パソコンにもよるが100倍くらい時間がかかる。テンソルの計算は、中身がC言語などで書かれた高速なプログラムで、しかもまとめて処理されるからだ。「Pythonでfor文を書いたら負け」という格言が、機械学習の世界にはある。……まあ、第4章で散々書いたけどね。
:::

## 表を眺める

表の一部を、色の濃さで描いてみましょう。

```python
!pip install -q matplotlib-fontja
```

```python
import matplotlib.pyplot as plt
import matplotlib_fontja

look = ["私", "先", "生", "は", "の", "に", "を", "た", "。", "、", "奥", "さ", "ん", "Ｋ"]
idx = [stoi[c] for c in look]
sub = P[idx][:, idx]

plt.figure(figsize=(6, 5))
plt.imshow(sub, cmap="Blues")
plt.xticks(range(len(look)), look)
plt.yticks(range(len(look)), look)
plt.xlabel("次の文字")
plt.ylabel("今の文字")
plt.colorbar(label="確率")
plt.title("bigramの確率表（一部）")
plt.show()
```

![bigramの確率表の一部。先→生、奥→さ、さ→ん、私→は、。→私などが濃い](img/figs/06-tensors/cell7_0.png)

「先→生」「奥→さ」「さ→ん」（奥さん！）が濃く光っています。この表こそが、bigramモデルの「頭の中」のすべてです。

## 表から文章を作る

テンソル版の生成も作っておきましょう。`torch.multinomial` は、第3章で自作したくじ引きのテンソル版です。

```python
g = torch.Generator().manual_seed(0)
ix = stoi["私"]
out = ["私"]
for _ in range(60):
    ix = torch.multinomial(P[ix], num_samples=1, generator=g).item()
    out.append(itos[ix])
print("".join(out))
```

```output
私は段加減です。そう渇様子先生といと私はた。しまで。私は一種を極ったがら見える資刹郵濯耐皇奪焼肩煎諺者櫓剛示樹息貪橋の男で
```

（出てくる文章は、乱数の種 `manual_seed(0)` の数字を変えると変わります。）

:::minato
途中で「資刹郵濯耐皇奪…」って、読めない漢字が延々と続いてますけど……。
:::

:::sensei
いいところに気づいた！ これは**スムージングの副作用**だ。珍しい文字の行は、数えた回数の合計がとても少ない。そこに全部の文字へ0.01ずつ、合計 $0.01 \times 2061 \approx 20.6$ 回分の「おまけ」を足すと、おまけのほうが本物の回数より多くなってしまう。するとその行は、ほとんど「でたらめ」になる。一度珍しい文字に迷い込むと、次も珍しい文字、その次も……と抜け出せなくなるんだ。数えるだけのモデルの、もう1つの限界だね。
:::

## one-hotと行列の掛け算

最後に、次の章から何度も出てくる大事な計算を1つ。**行列の掛け算**です。

文字「私」を、「私」の位置だけ1で、残りが全部0の長さ2061のベクトルで表すことにします。これを **one-hot**（ワンホット、1か所だけ熱い）ベクトルと言います。

```python
import torch.nn.functional as F

x = F.one_hot(torch.tensor(stoi["私"]), num_classes=V).float()
print(x.shape, x.sum())

row = x @ P            # one-hot × 確率表
print(row.shape)
print(torch.allclose(row, P[stoi["私"]]))
```

```output
torch.Size([2061]) tensor(1.)
torch.Size([2061])
True
```

`@` は行列の掛け算の記号です。one-hotベクトルに表を掛けると、**表の「私」の行がそのまま取り出される**ことが確かめられました（`allclose` は「ほぼ等しい？」を調べる関数）。

:::math 行列の掛け算
小さな例で手計算してみましょう。

$$\begin{pmatrix} 1 & 2 \end{pmatrix} \begin{pmatrix} 3 & 4 & 5 \\ 6 & 7 & 8 \end{pmatrix} = \begin{pmatrix} 1\cdot3+2\cdot6 & 1\cdot4+2\cdot7 & 1\cdot5+2\cdot8 \end{pmatrix} = \begin{pmatrix} 15 & 18 & 21 \end{pmatrix}$$

左の**行**と右の**列**の、同じ位置どうしを掛けて足す。これをすべての組み合わせでやります。

```python
A = torch.tensor([[1., 2.]])
B = torch.tensor([[3., 4., 5.],
                  [6., 7., 8.]])
print(A @ B)
print(A.shape, "@", B.shape, "→", (A @ B).shape)
```

```output
tensor([[15., 18., 21.]])
torch.Size([1, 2]) @ torch.Size([2, 3]) → torch.Size([1, 3])
```

**形のルール**：$(n \times k)$ の行列と $(k \times m)$ の行列を掛けると、$(n \times m)$ になります。真ん中の $k$ が一致していないと掛けられません。これが「形が合わない」エラーの正体です。

one-hotベクトルを掛けると、「1の位置の行 × 1」以外は全部「× 0」で消えるので、1の位置の行がそのまま出てくるのです。
:::

:::theory なぜこれが大事なのか
「one-hot × 表 ＝ 表の行を取り出す」。当たり前に見えますが、ここに大事な発想の転換があります。

- 今は、表の中身（確率）を**数えて**決めました
- でも、表の中身を**学習で少しずつ調整する数（パラメータ）**にしたら？

第8章では、まさにそれをやります。表の中身を最初はでたらめにして、損失が小さくなるように少しずつ調整していくのです。そのためには「調整の方向」を知る必要があります。それが次の章の **微分** です。
:::

## GPUは何が速いのか

:::theory 並列計算
行列の掛け算は、「掛けて足す」をたくさん、**お互いに関係なく**計算できます。2061×2061の行列どうしの掛け算なら、約87億回の掛け算です。

- **CPU**：とても賢い職人が数人〜数十人。複雑な仕事が得意
- **GPU**：そこそこの作業員が数千人。単純な計算を**同時に**こなすのが得意

行列の掛け算は「単純な計算を大量に」の典型なので、GPUの独壇場です。LLMの計算のほとんどは行列の掛け算なので、LLMにはGPUが欠かせないのです。Colabで確かめたい人は、次を実行してみてください（CPUのままなら `cuda` の行は飛ばされます）。

```python
X = torch.randn(2000, 2000)
start = time.time(); _ = X @ X; print(f"CPU：{time.time() - start:.3f}秒")
if torch.cuda.is_available():
    Xg = X.to("cuda"); _ = Xg @ Xg; torch.cuda.synchronize()
    start = time.time(); _ = Xg @ Xg; torch.cuda.synchronize()
    print(f"GPU：{time.time() - start:.4f}秒")
```

```output-example
CPU：0.152秒
GPU：0.0021秒
```
:::

:::deep NumPyとの関係
Pythonで数の表を扱う道具としては、**NumPy**（ナムパイ）も有名です。`numpy.array` はテンソルとほぼ同じ使い心地で、データ分析ではNumPyが主役です。PyTorchのテンソルはNumPyの配列に「GPUで動く」「微分を自動で計算できる（次の章）」機能を足したもの、と考えてOKです。`t.numpy()` と `torch.from_numpy(a)` で行き来できます。
:::

:::quiz 形の計算
形が `[32, 2061]` のテンソルと `[2061, 64]` のテンソルを `@` で掛けると、結果の形は？
:::answer
`[32, 64]` です。真ん中の2061が一致しているので掛けられ、外側の32と64が残ります。
:::

:::quiz keepdim
`N.sum(dim=1, keepdim=True)` の形は `[2061, 1]` でした。`N.sum(dim=0)` の形は？ 何を表す？
:::answer
`[2061]` です。各**列**の合計、つまり「その文字が『次の文字』として何回出てきたか」を表します。
:::

:::checklist
- テンソルの足し算・掛け算がfor文なしでできることを確かめた
- `.shape` で形を確認するクセがついた
- bigramの表を行列 `N` として作り、確率の表 `P` に変換した
- テンソルで損失を計算し、第5章と同じ3.581になった
- one-hot × 行列 ＝ 行の取り出し、を確かめた
:::

:::recap
- **テンソル**は数を並べた箱。1次元がベクトル、2次元が行列。一番大事なのは **形（shape）**
- テンソルの計算はfor文なしで全要素をまとめて処理するので、とても速い
- `sum(dim=1, keepdim=True)` と **ブロードキャスト** で、各行を合計で割れる
- 行列の掛け算の形のルール：$(n \times k) @ (k \times m) = (n \times m)$
- **one-hot × 表 ＝ 表の行の取り出し**。この表の中身を「学習で決める」のが次の目標
:::

:::sensei
表の中身を「数える」のではなく「学習で決める」。そのためには、中身を少し変えたら損失がどう変わるかを知る必要がある。それを教えてくれるのが**微分**だ。次の章は、坂道を転がるボールの話から始めよう。物理屋の血が騒ぐね。
:::
