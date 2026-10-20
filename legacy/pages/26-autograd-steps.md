# 自動微分を、一値と一更新から確かめる

手計算10〜15分、PC実行15〜30分。初回の[PyTorch準備](pc-practice.html#torch)は別の回です。まず[第18章の一つの重み](18-gradient-steps.html)を確かめます。

## 1．実行する前に二つの数を予想する

w=2、L=(w−5)²なら、損失9、wへの微分2(w−5)=−6です。この二つを紙へ書いてから実行します。

```python
import torch
w = torch.tensor(2.0, requires_grad=True)
loss = (w - 5) ** 2
loss.backward()
print(loss.item())
print(w.grad.item())
```

`torch.tensor`は計算する数を作ります。`requires_grad=True`は微分を追う指定。`backward`は微分を計算し、`grad`に結果が入ります。`item`は一つの数を取り出します。出力9.0、−6.0を手計算と照合します。名前が多ければ今日は最初の三行までを追い、次回は微分と表示を確かめます。

## 2．一度だけ重みを直す

歩幅0.1なら2−0.1×(−6)=2.6。ここでは更新そのものの微分を追加しないため、`torch.no_grad()`の範囲で値を変更します。`with`と字下げは、その管理を適用する処理範囲を示します。

```python
import torch
w = torch.tensor(2.0, requires_grad=True)
loss = (w - 5) ** 2
loss.backward()
with torch.no_grad():
    w -= 0.1 * w.grad
print(round(w.item(), 3))
```

出力2.6。`-=`は元の値から引いて更新する書き方です。`round`は表示用に小数点以下3桁へ丸めます。

## 3．二回目に古い微分を混ぜない

PyTorchでは勾配が蓄積されるので、独立の更新ごとに消します。`None`は値がないことを表すPythonの値で、0の微分が計算された場合とは異なります。

```python
import torch
w = torch.tensor(2.0, requires_grad=True)
for step in range(2):
    w.grad = None
    loss = (w - 5) ** 2
    loss.backward()
    print(step, round(w.item(), 3), round(w.grad.item(), 3))
    with torch.no_grad():
        w -= 0.1 * w.grad
print(round(w.item(), 3))
```

|回|更新前のw|今回の微分|更新後のw|
|---|---:|---:|---:|
|0|2|−6|2.6|
|1|2.6|−4.8|3.08|

最後は3.08。消さない場合、前の−6も加わって別の更新になります。[本編](26-reader.html)のoptimizerでは `zero_grad` と `step`が消去と更新をまとめます。

**自分で変える：** 目標5を4にし、二回の表を実行前に作ります。wは2→2.4→2.72。これはこの二更新の検算で、大きなモデルが正しく学習することの証明ではありません。

**止まったら：** importで止まるなら[準備](pc-practice.html#torch)。gradがNoneなら追跡指定とbackwardを確認します。微分する重みは整数ではなく、この例の2.0のような浮動小数点にします。

[自力の照合問題](26-workshop.html) · [公式のautograd入門](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
