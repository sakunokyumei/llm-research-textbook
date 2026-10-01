# 3．実験票を書いてから九実行を残す

この実習の5/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

新しいコマンド引数は[Pythonの橋](python-reading.html)、データの再抽出は[第22章](22-statistics.html)、学習ループは[第33章](33-training.html)へ戻れます。コード中の `rng.randrange(2,6)` は2〜5の整数を選びます。`*noise` はnoiseの並びを文書の中へ展開する記法。`extend(rows)` は複数の行をリスト末尾へ追加します。setで重複を除き、sortedで順を固定してからshuffleするので、同じseedの文書が再現できます。

:::exercise 2・何が公平か
Attentionなしを含む三条件で同じトークン数を使いました。実時間の差を測らなくても同じ速度だと言えますか。
:::answer
言えません。Attentionなしでは位置間の計算を省いています。同じデータ量は同じ演算量や速度ではありません。
:::

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-04.html">前の作業</a><a href="capstone-guide-06.html">次の作業</a></nav>
