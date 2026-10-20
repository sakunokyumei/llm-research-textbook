# 5．損失と更新

この実習の6/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

最後の[線形層](reference.html#term-linear-layer)は32→7へ写し、32×8×7のlogitを作ります。cross entropyへは(32×8)×7に並べ直し、正解IDも256個にします。すでにsoftmaxした確率を渡す必要はありません。cross_entropyが安定な[対数](reference.html#term-log)確率の計算を含みます。

`zero_grad`→`backward`→[勾配](reference.html#term-gradient)normのclipping→`step`の順です。clippingは発散の万能な修理ではなく、大きすぎる更新を抑える手段です。ラベルやmaskの誤りは別に直します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="lab-guide-05.html">前の作業</a><a href="lab-guide-07.html">次の作業</a></nav>
