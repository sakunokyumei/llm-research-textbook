# 2．小さい確認を先に通す

この実習の3/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

[実装ラボの準備](labs.html)を終え、リポジトリのフォルダで実行します。

```sh
python -m unittest discover -s labs -v
```

新しい[test_distance_study.py](downloads/test_distance_study.py)は、分割間の文書重複、再現可能なデータ、コピー位置の対応、最大系列長、未来を変えても過去が変わらない性質を確認します。正しい答えをseparator位置だけへ置く模型でも採点を確認するので、学習の成否とは独立に採点位置を検査できます。

`No module named tiny_transformer` なら、distance_study.py、tiny_transformer.py、paired_bootstrap.pyを同じlabsフォルダに置きます。torchの導入は[第26章](26-pytorch.html)。`index out of range` は表の行番号が範囲外という意味で、語彙IDと位置IDを分けて調べます。[損失](reference.html#term-loss)の[shape](reference.html#term-tensor)は[第32章](32-transformer.html)へ戻れます。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-02.html">前の作業</a><a href="capstone-guide-04.html">次の作業</a></nav>
