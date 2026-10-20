# 4．ablationと複数seed

この実習の9/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

[paired_bootstrap.py](downloads/paired_bootstrap.py)は対応する文書を5,000回再抽出して、正解率差のpercentile区間を求めます。学習seedの揺れまで含む区間ではありません。設定を固定し終えたら`--evaluate-test`を付けた最終runでtestを評価し、それ以上の条件選びには使いません。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-08.html">前の作業</a><a href="labs-10.html">次の作業</a></nav>
