# 46 RoPEと長い文脈：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](46-context.html)を使い、ここへ戻って式やコードを引けます。


## 位置を回転で表す

円の上の点を、角度θで表すことを考えます。半径1の円では横座標がcosθ、縦座標がsinθです。角度はラジアンで測り、一周は2π。cos²θ+sin²θ=1が成り立ちます。

二次元[ベクトル](reference.html#term-vector)(x,y)をθだけ回すと、`(x cosθ−y sinθ, x sinθ+y cosθ)`。[行列](reference.html#term-matrix)ならR(θ)=[[cosθ,−sinθ],[sinθ,cosθ]]です。回転しても長さや、両方を同じ角度だけ回したときの[内積](reference.html#term-dot)は変わりません。

[RoPE](reference.html#term-rope)はQとKの成分を二つずつ組にし、位置mに応じた角度mθで回します。Q側が位置m、K側が位置nなら、回転後の内積は`(R(mθ)q)ᵀR(nθ)k = qᵀR((n−m)θ)k`となり、位置の差に依存する構造が入ります。組ごとに異なる周波数を使います。

## 入れられる長さと使える長さ

最大入力長が10万tokenでも、すべての位置の情報を同じように利用できるとは限りません。学習範囲を超える位置では分布外になります。周波数や位置の尺度を調整する拡張、長い系列での追加学習、sparse attentionなど、複数の対策があります。それぞれ何を近似・変更しているかを確認します。

一つの秘密文字列を探すneedle-in-a-haystack試験は、特定の検索能力を測る有用な診断ですが、複数根拠の統合、長文の要約、一貫した計画、位置による偏りの全てを測るわけではありません。

## 長文評価の設計

同じ根拠を先頭・中央・末尾へ移動し、長さを変えます。根拠が複数ある問題、紛らわしい文書、答えがない場合も含めます。短い文脈での性能が悪化していないか、KV容量・遅延・コストがどう変わるかを併記します。

## 回転の二つの性質をコードで比較する

```python
import numpy as np
def R(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])
q = np.array([2., 3.])
k = np.array([1., -1.])
theta = 0.2
m, n = 5, 8
left = (R(m * theta) @ q) @ (R(n * theta) @ k)
right = q @ (R((n - m) * theta) @ k)
print(np.linalg.norm(q), np.linalg.norm(R(theta) @ q))
print(left, right)
assert np.allclose(left, right)
assert np.allclose(np.linalg.norm(q), np.linalg.norm(R(theta) @ q))
```

`np.cos`と`np.sin`はラジアンの角度から三角関数を計算します。ベクトル同士の `@` は内積。Rは上で定義した回転行列、allcloseは丸めの差を許した一致確認です。長さと回転内積の二つを別々に確認します。三角関数は本章冒頭の円の例へ、行列は[第15章](15-matrices.html)へ戻れます。sparse attentionは全位置を比較せず一部の組だけを参照する方式。needle-in-a-haystackは大量の文中に一つの探す対象を埋める試験です。

## 演習

:::exercise 1・四分の一回転
θ=π/2ではcosθ=0、sinθ=1です。(2,3)を回してください。
:::answer
(−3,2)です。長さはどちらも√13で変わりません。
:::

:::exercise 2・相対位置
m=5、n=8なら、上の回転内積に現れる角度の差はいくつですか。
:::answer
(8−5)θ=3θです。この表記ではK側からQ側の位置を引いています。
:::

:::exercise 3・cache
同じ構造で系列長を4倍にすると、通常のKV cacheの要素数はどうなりますか。
:::answer
おおむね4倍です。通常の全[Attention](reference.html#term-attention)点数表の16倍とは違います。
:::

:::exercise 4・評価の範囲
長文中の一つの鍵を見つける試験が100%なら、長文要約も解決したと言えますか。
:::answer
言えません。課題が測る技能が異なります。根拠統合、圧縮、一貫性などを別の評価で確認します。
:::

## 到達課題と出典

二次元の回転をNumPyで実装し、長さ保存と相対位置の内積式を数値で確認してください。[RoFormer](https://arxiv.org/abs/2104.09864)、[Lost in the Middle](https://arxiv.org/abs/2307.03172) を参照。
