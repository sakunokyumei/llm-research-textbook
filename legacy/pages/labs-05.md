# 2．byte BPEを自作する

この実習の5/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

```sh
python labs/bpe.py
```

[bpe.py](downloads/bpe.py)は頻出する隣接pairを順に結合します。初期語彙が256個のbyteなので、学習で見なかった日本語やemojiも符号化できます。復号して元の文字列に戻ることをassertします。大規模tokenizerの高速化・正規化・特殊token処理までは実装していない、読み通せる最小版です。

変更課題：merge数を0・5・20に変え、未使用文のtoken数を比べます。訓練文は固定し、評価文からmerge規則を学習しないでください。[29章](29-tokenization.html)

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-04.html">前の作業</a><a href="labs-06.html">次の作業</a></nav>
