# CPUで、モデルの更新を一周する：まとめて参照

[小ページで読む](cpu-practice.html)


第26・27章の補習です。GPUや外部データは不要です。[準備](labs.html)で使ったPythonで、下のコードを `xor_practice.py` として保存して実行します。`No module named torch` なら[第26章](26-pytorch.html)へ、保存場所なら[第8章](08-python.html)へ戻れます。

## 四点を紙に描く

XORは `(0,0)→0、(0,1)→1、(1,0)→1、(1,1)→0` です。横を第一入力、縦を第二入力として四点を描き、対角の二点だけが正解1になる図を作ります。この四点を覚える実習であり、新しいデータでの性能を測る実験ではありません。

## 一周の流れ

`入力4行 → 点数4行 → 正解と比べた損失 → 勾配 → 重み更新` の順です。入力xは(4,2)、正解yは(4,1)。最終層が一個の点数を返すので、logitsも(4,1)になります。FはPyTorchの関数の集まりです。`binary_cross_entropy_with_logits` は、点数を二択確率へ変換したときの交差[エントロピー](reference.html#term-entropy)を安定な形で計算します。先にsigmoidした値をこの関数へ渡しません。

```python
import torch
from torch import nn
from torch.nn import functional as F

torch.set_num_threads(1)
torch.manual_seed(42)
x = torch.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
y = torch.tensor([[0.], [1.], [1.], [0.]])
net = nn.Sequential(nn.Linear(2, 8), nn.ReLU(), nn.Linear(8, 1))
optimizer = torch.optim.AdamW(net.parameters(), lr=0.03)
for step in range(1000):
    logits = net(x)
    loss = F.binary_cross_entropy_with_logits(logits, y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
with torch.no_grad():
    probabilities = net(x).sigmoid()
    predictions = (probabilities >= 0.5).float()
print(probabilities)
print(predictions)
print((predictions == y).float().mean().item())
```

`set_num_threads(1)` はCPUの計算に使うスレッド数を1へ絞る指定です。`sigmoid()` は第25章のσを適用します。比較 `>=0.5` がTrue/Falseの表を作り、`float()` が1/0へ変換します。正解と等しいかを比較し、1/0の平均を取れば正解率です。`item()` は一個の値を取り出します。`no_grad`、[optimizer](reference.html#term-optimizer)、[クラス](reference.html#term-class)は[第26章](26-pytorch.html)・[第11章](11-debug.html)へ戻れます。

:::exercise 1・形から読む
Linear(2,8)とLinear(8,1)のパラメータ数を求めてください。
:::answer
最初は2×8+8=24、次は8×1+1=9、合計33です。バッチの4はパラメータ数へ掛けません。
:::

:::exercise 2・正解率の手計算
予測が0,1,0,0なら正解率はいくつですか。
:::answer
正解0,1,1,0と比べて3/4=0.75です。
:::

:::exercise 3・活性化を外す
nn.ReLU()を外すと、一つの直線で四点を完全に分類できるようになりますか。
:::answer
[線形層](reference.html#term-linear-layer)の合成は一つのアフィン変換（[行列](reference.html#term-matrix)を掛けてずれを足す変換）なので、XORを一つの直線で分けられるようにはなりません。複数seedで全結果を残します。
:::

## 次へ進む目印

出力の見た目だけでなく、各行が四点のどれかを示し、[損失](reference.html#term-loss)→[勾配](reference.html#term-gradient)→更新の順を説明します。高い正解率を一回得ても一般的な分類能力を主張しません。失敗したseedと[学習率](reference.html#term-learning-rate)も記録して[第28章](28-numerics.html)へ進みます。

仕様の参照：[PyTorchの二値損失](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.binary_cross_entropy_with_logits.html)。
