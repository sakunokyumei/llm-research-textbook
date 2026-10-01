# 7．保存されるものを確認

この実習の8/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

モデルだけではAdamWの履歴や次のbatchは再現できません。[optimizer](reference.html#term-optimizer)状態、step、batch抽出用generator、PyTorchの乱数状態、データhash、configを保存します。データhashが違えば再開を拒否します。別のコード版でも状態の読み込みに成功する場合があるため、研究ではGit commitも実験票に記録します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="lab-guide-07.html">前の作業</a><a href="lab-guide-09.html">次の作業</a></nav>
