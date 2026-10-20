# 2．embeddingは行を選ぶ

この実習の3/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

token embeddingは7×32の学習可能な表です。IDが2なら2行目を取り出します。batch32、長さ8なら出力[shape](reference.html#term-tensor)は32×8×32。最後の32は意味を表すために学ぶ幅で、語彙数ではありません。位置embeddingは8×32で、位置0〜7の[ベクトル](reference.html#term-vector)を足します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="lab-guide-02.html">前の作業</a><a href="lab-guide-04.html">次の作業</a></nav>
