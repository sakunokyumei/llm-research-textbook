# 4．残差とMLP

この実習の5/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

各blockは、LayerNorm→Attention→残差加算、LayerNorm→MLP→残差加算のpre-norm構成です。MLPは各位置を独立に32→128→32へ変換し、GELUで非線形性を加えます。Attentionを外した条件では、MLPが他の位置のtokenを見られません。

初期実装を読みやすくするため、[RoPE](reference.html#term-rope)、RMSNorm、SwiGLU、dropout、KV cacheは含みません。講義で学んだ手法を追加するなら、一つずつ実装し、基準と数値比較を行います。この省略を最新モデルと同じ構成だと説明しないでください。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="lab-guide-04.html">前の作業</a><a href="lab-guide-06.html">次の作業</a></nav>
