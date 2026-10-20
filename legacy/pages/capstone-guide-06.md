# 4．一つの変更を自分の問いにする

この実習の6/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

保存した自作checkpointは、次のコマンドで文書別の誤答と最初の層の観測を調べられます。

```sh
python labs/inspect_distance.py labs/runs/distance-study/attention-0.pt
```

[inspect_distance.py](downloads/inspect_distance.py)は、保存設定から未学習の長さを求め、同じデータhashかを確認して読みます。誤答は文書・正解ID・予測IDを並べます。観測ではコピー対象とコピー先だけを変えた二文書を同じ層で比べ、[hook](reference.html#term-hook)を解除します。平均絶対差があることは因果的な役割の証明ではありません。[第51章](51-interpretability.html)へ戻り、観察と次の介入案を別々に書きます。

fで始まる文字列の `{variant}` は、その変数の値を名前へ埋め込むPythonの書き方です。`attention-0.pt` は条件attention、seed0の保存物。新しい研究コードの保存・読み込みは[Pythonの橋](python-reading.html)へ戻れます。

結果を見て仮説を変えた場合は、次を探索実験として記録します。たとえば未学習のnoiseを8から10へ変え、他の条件を固定します。

```sh
python labs/distance_study.py --steps 300 --held-out-noise 10 --out labs/runs/distance-10
```

入力長は14となり、位置Embeddingの行数も自動で14へ変わります。全条件で同じ行数ですが、noise8実験に比べて保存するパラメータ数も増えます。したがって主張は「この実装で長さを延ばした結果」であり、長さだけの純粋な効果だと断定しません。全長さで同じ最大contextを使う対照を次の実験にするなど、[交絡](reference.html#term-confounding)を考えます。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-05.html">前の作業</a><a href="capstone-guide-07.html">次の作業</a></nav>
