# 16-6 小さい方向を捨てた誤差を測る

読む・手計算の目安：20〜30分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

## 残すものと失うものを分ける

diag(3,1)の二つ目の特異値を0にするとdiag(3,0)。独立な方向が一つだけ残るので、[第15章のランク](15-matrices.html)は1です。これが低[ランク](reference.html#term-rank)近似の例です。

元との差はdiag(0,1)。[行列](reference.html#term-matrix)の全要素を二乗して足し、その平方根を取る大きさをFrobenius（フロベニウス）[ノルム](reference.html#term-norm)と呼びます。この例の誤差は√(0²+0²+0²+1²)=1です。[平方根の復習](04d-roots.html)へ戻れます。

```python
import numpy as np
A = np.array([[0., 1., 0.], [3., 0., 0.]])
U, s, Vh = np.linalg.svd(A, full_matrices=False)
kept = s.copy()
kept[1] = 0
approx = U @ np.diag(kept) @ Vh
error = np.linalg.norm(A - approx, ord="fro")
print(approx)
print(error)
assert np.allclose(error, 1.0)
```

`copy`で元の一覧を保ち、位置1にある二つ目の特異値だけを0にします。`ord="fro"`は先ほどの全要素の二乗和の平方根を使う指定です。近似は[[0,0,0],[3,0,0]]、誤差は1になります。

一般にも、大きい方からr個の特異値を残す方法は、この誤差についてランクr以下の最良の近似の一つになります。ただし行列の差が小さいことと、文章の予測結果がよいことは別です。近似した後の課題の成績も測る必要があります。

:::exercise 8・低ランク近似
diag(4,2,1)を上位一つの特異値だけで近似したとき、Frobeniusノルムでの誤差は何ですか。
:::answer
残る近似はdiag(4,0,0)、差はdiag(0,2,1)。全要素の二乗和の平方根なので√5です。
:::

## 章の到達課題と戻り先

1. diag(4,2,1)を九つの要素の表へ戻します。
2. 上の二つのコードを別々のファイルに保存して実行します。
3. Aを[[4,0],[0,2]]へ変えます。再構成は元に戻り、小さい特異値を0にすると誤差2になるか、先に予想して確かめます。
4. 「何を捨てたか」「何の誤差を測ったか」を各一行で説明します。

NumPyが見つからないなら[第12章の導入](12-environment.html)、行列積が合わないなら[第15章](15-matrices.html)、戻り値の[代入](reference.html#term-substitution)が読めないなら[第14章](14-vectors.html)へ戻れます。形のエラーではU、s、Vhの[shape](reference.html#term-tensor)を表示し、上の表と照合します。

仕様の出典：[NumPy arange](https://numpy.org/doc/stable/reference/generated/numpy.arange.html)、[diag](https://numpy.org/doc/stable/reference/generated/numpy.diag.html)、[broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)、[SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)。数学的背景：[MIT 18.06の特異値分解](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/lecture-29-singular-value-decomposition/)。

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](16e-rebuild.html) · [次の学習ページ](17-calculus.html) · [章の地図](16-tensors.html)
