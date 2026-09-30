# 15-5 連立方程式を解き、コードで確認する

読む・手計算の目安：15〜25分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

## 同じ条件を表と式で書く

`x+y=5`、`x−y=1`を足すと2x=6なのでx=3、y=2です。これもAx=bという[行列](reference.html#term-matrix)の形にできます。逆行列は変換を元に戻す行列ですが、すべての行列に存在するわけではありません。二行が同じなら、二つの独立な条件がありません。数値計算では逆行列を明示的に作るより、連立[方程式](reference.html#term-equation)を解く専用関数を使います。

NumPyは数の配列を扱う[ライブラリ](reference.html#term-library)です。準備がまだなら[第12章](12-environment.html)へ戻ってください。`import numpy as np`はNumPyをnpという短い名前で使う指定、`np.array`は数の並びから計算用の配列を作る操作です。

```python
import numpy as np
A = np.array([[1., 1.], [1., -1.]])
b = np.array([5., 1.])
x = np.linalg.solve(A, b)
print(x)
print(A @ x)
```

NumPyは数の配列を扱うライブラリです。未導入なら[第12章の仮想環境とインストール手順](12-environment.html)へ戻ります。`@`は行列積で、`*`は要素ごとの積です。出力は[3,2]と[5,1]になります。

:::exercise 6・方程式
2x+y=7、x−y=2を解いてください。
:::answer
二式を足して3x=9、x=3。x−y=2からy=1。元の両式へ[代入](reference.html#term-substitution)して確認できます。
:::

## 章の到達課題と出典

手計算した2行2列の行列積をNumPyの`@`で確認し、`*`との差を説明してください。[MIT 18.06](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)、[NumPy 初心者ガイド](https://numpy.org/doc/stable/user/absolute_beginners.html) を参照。

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](15d-basis.html) · [次の学習ページ](16-tensors.html) · [章の地図](15-matrices.html)
