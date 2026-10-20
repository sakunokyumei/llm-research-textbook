# 見つからない記法に出会ったら

この実習の7/7ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`try`の後の`finally`は、その処理が成功した場合も途中で失敗した場合も実行する片付けの場所です。観測の[hook](reference.html#term-hook)を解除する例で使います。`enumerate(values)` は位置番号と値を組で返す操作で、文書別の失敗を記録するときに使います。`torch.isfinite(x)` はNaNや無限大ではない位置をTrueにする検査で、第28章の非有限値を探す操作へ対応します。

名前・入力・出力・[shape](reference.html#term-tensor)をメモし、一行だけの例へ縮めます。「コードが動いた」と「各行を説明できる」は別に確認します。部品から学習へつなぐ順番は[lab-guide](lab-guide.html)へ戻ってください。

仕様の参照：[Python dataclasses](https://docs.python.org/3/library/dataclasses.html)・[argparse](https://docs.python.org/3/library/argparse.html)・[PyTorch Module](https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html)。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](python-reading-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="python-reading-06.html">前の作業</a><a href="beginner-route.html">次の作業</a></nav>
