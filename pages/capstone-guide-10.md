# 制作時の実測例：負の結果も読む

この実習の10/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

Python 3.14、PyTorch 2.13.0+cpu、NumPy 2.5.2で上の二設定を各300更新、各3seedで実行しました。下はvalidationのcopy正解率で、括弧内はseed0／1／2です。

|条件|未学習noise8（context12）|未学習noise10（context14）|
|---|---|---|
|Attentionあり|1.000／0.750／0.625|0.000／0.438／0.500|
|位置Embeddingなし|1.000／1.000／1.000|1.000／1.000／1.000|
|Attentionなし|0.250／0.250／0.250|0.000／0.250／0.250|

![未学習のコピー距離ごとのvalidation正解率。棒は3seedの平均、点は各seedの値。noise8と10はcontextが異なる二実験。](distance-study.svg)

この合成課題では位置Embeddingなしがよい値でした。一方、Attentionありは未学習距離でseedによる違いが大きく、失敗もあります。これを「位置表現は一般に不要」とは解釈しません。noise10はcontextも増えているため、二実験の差を距離だけへ帰せない点も報告します。各32文書の小さいvalidation集合です。

[全18実行の設定・文書別結果・対応差](downloads/distance_results.json)を配布します。noise8の実行だけは固定条件で最終testも測り、noise10は探索としてvalidationだけを測りました。良いseedだけを採用せず、全結果と評価を使った範囲を確認する例です。第三者による再現は未実施です。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-09.html">前の作業</a><a href="capstone-guide-11.html">次の作業</a></nav>
