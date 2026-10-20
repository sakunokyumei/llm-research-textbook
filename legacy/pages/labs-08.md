# 4．ablationと複数seed

この実習の8/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

```sh
python labs/run_experiments.py
```

[run_experiments.py](downloads/run_experiments.py)は3条件×3seed、各300更新を実行します。数分程度を目安とし、出力先はlabs/runsです。制作時の[全9runのCSV](downloads/results.csv)を配布します。

|条件|copy正解率（seed 0 / 1 / 2）|validation NLL（同順）|
|---|---|---|
|Attentionあり|1.000 / 1.000 / 1.000|0.8751 / 0.8775 / 0.8850|
|位置embeddingなし|1.000 / 1.000 / 1.000|0.8815 / 0.8743 / 0.8819|
|Attentionなし|0.2266 / 0.2500 / 0.2500|1.0527 / 1.0457 / 1.0522|

**位置embeddingを外しても、この短い固定位置課題は解けました。** 予想と違う結果も隠さず、課題の容易さやcausal maskによる構造を考えます。これは位置表現が一般に不要だという証明ではありません。[Attention](reference.html#term-attention)なしではtoken間の情報交換がなく、copyが難しくなります。外した部品のパラメータは保持しているため、総パラメータ数は同じでも有効な[計算量](reference.html#term-complexity)は異なります。

NLLがゼロにならないのは、noise部分が予測不可能だからです。全token損失とcopy位置の正解率は、異なる側面を測っています。

```sh
python labs/paired_bootstrap.py labs/runs/attention-0/metrics.json labs/runs/no-attention-0/metrics.json
```

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-07.html">前の作業</a><a href="labs-09.html">次の作業</a></nav>
