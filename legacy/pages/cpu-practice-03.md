# 一周の流れ

この実習の3/5ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

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

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](cpu-practice-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="cpu-practice-02.html">前の作業</a><a href="cpu-practice-04.html">次の作業</a></nav>
