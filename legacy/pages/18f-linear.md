# 18-6 一出力の重みとbiasを微分する

読む・手計算の目安：15〜25分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

## 同じ連鎖律を三つの入力へ使う

入力がx=2、重みがw=3、ずれがb=1の一出力を考えます。y=xw+b=7、[損失](reference.html#term-loss)をL=y²とするとL=49です。[線形層](reference.html#term-linear-layer)という名前は、ここでは[行列](reference.html#term-matrix)積と加算を行う部品を指します。行列を掛け、一定のずれを足すこの変換を、数学では[アフィン変換](reference.html#term-affine)と呼びます。b=0の場合の行列積だけの変換は線形変換です。

後の計算から届く出力の変化率はG=dL/dy=2y=14。これは**[上流の勾配](reference.html#term-upstream)**です。Lではなく、yに対するLの[微分](reference.html#term-derivative)の値を受け取ります。

|変えるもの|yの変化率|上流G|Lまでの変化率|
|---|---|---|---|
|w|x=2|14|2×14=28|
|b|1|14|1×14=14|
|x|w=3|14|3×14=42|

この表は、前の一経路の[連鎖律](reference.html#term-chain-rule)を三回使っただけです。**bias**は掛けた後に加えるずれ、**線形層**はこの計算を複数の入力・出力へまとめる部品です。[線形層とbias](reference.html#term-linear-layer)・[上流の勾配](reference.html#term-upstream)へ戻れます。

:::exercise 9・一出力の勾配を計算する
x=3,w=2,b=0,L=y²ならy、G、wとbへの[勾配](reference.html#term-gradient)はいくつですか。
:::answer
y=6、G=12、wの勾配3×12=36、bの勾配12です。
:::

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](18e-products.html) · [次の学習ページ](18g-batch.html) · [章の地図](18-chain.html)
