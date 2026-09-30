# 16-5 SVDの戻り値から行列を作り直す

読む・手計算の目安：20〜30分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

## 形を表にしてから実行する

[行列](reference.html#term-matrix)Aがm行n列なら、kをmとnの小さい方とします。必要な方向の本数だけを返す指定が `full_matrices=False` です。これは小さい特異値を捨てる指定ではありません。

|戻る値|形|役割|
|---|---|---|
|U|(m,k)|出力側の方向を列に持つ|
|s|(k,)|大きい順に並んだ特異値の一覧|
|Vh|(k,n)|入力側の方向を行に持つ|

この章では[実数](reference.html#term-real)を使うため、Vhは式のVᵀに対応します。sは一覧で、Σはその値を対角線へ並べた行列です。`np.diag(s)`で一覧から[対角行列](reference.html#term-diagonal)を作れます。たとえば2行3列ならk=2で、Uは(2,2)、sは(2,)、Vhは(2,3)。積の形は(2,2)×(2,2)×(2,3)=(2,3)に戻ります。

```python
import numpy as np
A = np.array([[0., 1., 0.], [3., 0., 0.]])
U, s, Vh = np.linalg.svd(A, full_matrices=False)
Sigma = np.diag(s)
rebuilt = U @ Sigma @ Vh
print(U.shape, s.shape, Vh.shape)
print(s)
print(rebuilt)
print(np.allclose(A, rebuilt))
assert np.allclose(A, rebuilt)
```

三つの戻り値を三つの名前へ分ける[代入](reference.html#term-substitution)は[第14章のアンパック](14-vectors.html)と同じ考えです。`shape`で形を取り出し、`@`で行列積を計算します。`np.allclose`は丸めによる小さな差を許して、各要素がおよそ一致するかを調べます。

形の出力は `(2, 2) (2,) (2, 3)`、特異値は `[3. 1.]`、最後は `True`です。途中の方向の符号が違っても、積が同じになる分解があります。Uの数値そのものを暗記して照合せず、再構成と形を確かめましょう。

`(U * s) @ Vh`も同じ再構成です。sの各値がUの対応する列全体へ掛かるためです。まず `U @ np.diag(s) @ Vh`で意味を確認してから短い形へ進みます。

:::exercise 7・戻り値の形を決める
3行2列のAをfull_matrices=Falseで分解します。U、s、Vhの形は何ですか。
:::answer
k=2なので(3,2)、(2,)、(2,2)。U @ diag(s) @ Vhの形は(3,2)です。
:::

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](16d-svd.html) · [次の学習ページ](16f-lowrank.html) · [章の地図](16-tensors.html)
