# SVDを、数・形・実行の三回に分ける

[SVD](reference.html#term-svd)は行列の変換を三つへ分ける方法です。この補習では分解の一般的な証明を暗記する前に、与えられた三つの表で元へ戻せるかを確かめます。各節を別の日にできます。読む10〜15分、手計算10〜20分、実行15〜30分は別々の目安です。

## 1．まず向きと倍率だけを見る

横4倍、縦2倍なら、点(3,5)は(12,10)へ動きます。向きを変えない単位行列Iは `[[1,0],[0,1]]`。倍率を並べた対角行列Σは `[[4,0],[0,2]]`。対角線の外の0は、横と縦をこの段で混ぜないという意味です。

<svg viewBox="0 0 620 110" role="img" aria-labelledby="svd-steps-title"><title id="svd-steps-title">入力3,5から、向きをそろえ、横4倍縦2倍、向きを戻して12,10になる三段階</title><rect x="5" y="20" width="100" height="65" rx="8" fill="#f3efe6"/><text x="20" y="48">入力 (3,5)</text><text x="118" y="56">→</text><rect x="145" y="20" width="125" height="65" rx="8" fill="#f3efe6"/><text x="153" y="48">向きをそろえる</text><text x="153" y="72">この例は同じ</text><text x="283" y="56">→</text><rect x="310" y="20" width="120" height="65" rx="8" fill="#e4eee6"/><text x="320" y="48">4倍・2倍</text><text x="320" y="72">(12,10)</text><text x="443" y="56">→</text><rect x="470" y="20" width="145" height="65" rx="8" fill="#f3efe6"/><text x="480" y="48">向きを戻す</text><text x="480" y="72">この例は同じ</text></svg>

<div class="step-flow"><div>入力 (3,5)<br>向きをそろえる<br>この例は変わらない</div><div>横4倍・縦2倍<br>(12,10)へ</div><div>向きを戻す<br>この例は変わらない<br>結果 (12,10)</div></div>

式ではA=UΣVᵀで、この例はU=I、Vᵀ=Iです。右側のVᵀから入力へ作用し、その後Σ、最後にUを使います。ここでΣは行列の名前で、数を全部足す記号Σとは違います。

**確認：** 小さい倍率2を0にすると(3,5)の出力は(12,0)。元の縦成分10が失われます。低ランク近似は、残す方向を減らす操作です。

## 2．表の大きさを先に埋める

形は表の行数と列数です。3行2列のAなら、必要な本数kは小さい方の2。NumPyで `full_matrices=False` を使うと次の形になります。

|表|行|列|次の掛け算|
|---|---:|---:|---|
|U|3|2|U @ Σは3行2列|
|Σ|2|2|その結果 @ Vhも3行2列|
|Vh|2|2|最後は元のAと同じ形|

`@`は行列積。前の表の列数と次の表の行数が一致することを[第15章](15b-product.html)で確かめます。`s`は倍率だけの一覧で形(2,)。`np.diag(s)`が一覧からΣを作ります。実数を使うここではVhがVᵀに対応します。

**確認：** 2行3列のAなら、Uは(2,2)、Σは(2,2)、Vhは(2,3)です。`full_matrices=False`は必要な本数の形にする指定で、小さい倍率を捨てる指定ではありません。

## 3．一つの出力ずつ照合する

[NumPyの準備](pc-practice.html#numpy)を終えてから、次を保存・実行します。まず三つの形だけを予想し、次の回で再構成を確認してもかまいません。

```python
import numpy as np
A = np.array([[4., 0.], [0., 2.], [0., 0.]])
U, s, Vh = np.linalg.svd(A, full_matrices=False)
print("shapes", U.shape, s.shape, Vh.shape)
Sigma = np.diag(s)
rebuilt = U @ Sigma @ Vh
print("rebuilt", rebuilt)
print("matches", np.allclose(A, rebuilt))
```

`np.array`は数の表を配列へ、`np.linalg.svd`は分解、`shape`は形、`allclose`は小さい丸め差を許す一致判定です。最初の出力は(3,2)、(2,)、(2,2)、最後はTrue。UやVhは符号の違う組が返ってもよいので、その値の暗記ではなく積がAへ戻るかを照合します。

**止まったら：** `No module named numpy`は導入したPythonと実行したPythonを照合します。行列積の形のエラーなら各shapeを上の表へ書きます。NaNやInfなど数として有限でない値が入っていないかも確認します。エラーを消す前に最後の行を残してください。

**自分で変える：** 対角4,2を6,1へ変え、sが[6,1]になると予想して実行します。次に小さい倍率を0へ変える近似は[元の低ランクの講義](16u-020.html)で確かめます。

[自力の形の問題](16-workshop.html) · [SVDの元の例](16u-016.html) · [NumPy公式SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)
