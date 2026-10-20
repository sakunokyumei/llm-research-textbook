# 18-5 入力の方向と、出力から戻る勾配を分ける

読む・手計算の目安：20〜30分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

同じJ=[[4,0],[3,2]]に対して、二つの違う問いを考えます。

## 入力を動かしたら出力はどう動くか

入力を方向v=(1,−1)へ小さく動かします。出力の一次近似はJv=(4,1)。一行目は4×1+0×(−1)=4、二行目は3×1+2×(−1)=1です。これを**[JVP](reference.html#term-jvp-vjp)**と呼びます。正確な変化は、移動量hで割ったとき(4+h,1−h)なので、hが小さいと(4,1)へ近づきます。

## 損失の変化率を入力へ戻す

[損失](reference.html#term-loss)をL=2f₁+f₂と定めます。出力をどちらか一つだけ1動かしたときのLの変化率はg=(2,1)。この出力側の変化率を「感度」とも呼びます。xへの影響はf₁経由の4×2とf₂経由の3×1を足して11。yへの影響は0×2+2×1=2です。

|戻す入力|f₁経由|f₂経由|合計|
|---|---|---|---|
|x|4×2=8|3×1=3|11|
|y|0×2=0|2×1=2|2|

[列ベクトル](reference.html#term-column-vector)として書けばJᵀg=(11,2)。行ベクトルとして書く場合はgᵀJ=(11,2)で、表す向きが違うだけです。これが**VJP**の計算です。JVPの入力方向vと、VJPの出力感度gを同じものとして扱わないでください。JVP/VJPへ戻れます。

## 手計算をコードで照合する

```python
import numpy as np
J = np.array([[4., 0.], [3., 2.]])
v = np.array([1., -1.])
g = np.array([2., 1.])
print(J @ v)
print(J.T @ g)
print(g @ J)
assert np.allclose(J @ v, [4., 1.])
assert np.allclose(J.T @ g, [11., 2.])
assert np.allclose(g @ J, [11., 2.])
```

NumPyの一次元配列は、行か列かを[shape](reference.html#term-tensor)で区別していません。ここでは式の意味を先に定め、@の結果を確認します。二次元で列を明示するならgを(2,1)に整え、Jᵀgも(2,1)になります。[自動微分](reference.html#term-autograd)のコードは[第26章](26-pytorch.html)で確認します。仕様の出典：[PyTorchのJVPとVJP](https://docs.pytorch.org/tutorials/intermediate/jacobians_hessians.html)。
:::exercise 8・JVPを計算する
上のJで入力方向v=(0,1)、出力感度g=(1,0)のJvとJᵀgを求めてください。
:::answer
Jv=(0,2)、Jᵀg=(4,0)。同じ[微分](reference.html#term-derivative)[行列](reference.html#term-matrix)を使いますが、掛ける方向と意味が異なります。
:::

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](18d-jacobian.html) · [次の学習ページ](18f-linear.html) · [章の地図](18-chain.html)
