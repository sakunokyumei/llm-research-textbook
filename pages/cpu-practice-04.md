# 一周の流れ

この実習の4/5ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

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

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](cpu-practice-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="cpu-practice-03.html">前の作業</a><a href="cpu-practice-05.html">次の作業</a></nav>
