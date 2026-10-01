# 5．最終testの前に固定する

この実習の8/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

validationで確認した後、設定と解釈のルールを固定し、最終評価用の新しいフォルダを使います。

```sh
python labs/distance_study.py --steps 300 --evaluate-test --out labs/runs/distance-final
```

testを見て設定を選び直したら、そのtestを最終的な未知の評価と呼び続けません。全seedの値、平均、[標準偏差](reference.html#term-variance)、同じ文書の対応差を区別します。高い点数が出ない場合も、仮説を支持しなかった結果を記録します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-07.html">前の作業</a><a href="capstone-guide-09.html">次の作業</a></nav>
