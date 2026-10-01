# 3．QKVをheadへ分ける

この実習の4/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`qkv`は最後の幅32を96へ写し、32ずつQ,K,Vへ分けます。4headなら一head8次元です。reshapeで32×8×4×8、transposeでbatch×head×time×head_dimに変えます。

QKᵀは32×4×8×8。後ろの二軸は[query](reference.html#term-attention)位置とkey位置です。8次元の[内積](reference.html#term-dot)なので√8で割り、未来のkeyへ−∞を入れ、key軸に[softmax](reference.html#term-softmax)します。maskの対角は許可するため、現在位置自身は読めます。現在のtokenは入力として既知だからです。

重みとVを掛けると32×4×8×8。最後の8は今度はheadの特徴次元です。同じ数字でも軸の意味が違う点に注意してください。transpose後にcontiguousで連続した配置を用意し、headを結合して幅32へ戻します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="lab-guide-03.html">前の作業</a><a href="lab-guide-05.html">次の作業</a></nav>
