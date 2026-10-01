# Tiny Transformerのコードを読む

この実習の1/9ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

[実装ラボへ戻る](labs.html)。このページでは、完成したコードの各段階がなぜ必要かを追います。先に32・33章を読み、[ソース](downloads/tiny_transformer.py)を並べてください。[クラス](reference.html#term-class)の継承、dataclass、chunk、辞書を引数へ展開する記法は[研究コードのPythonの橋](python-reading.html)で具体例へ戻せます。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](lab-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="beginner-route.html">前の作業</a><a href="lab-guide-02.html">次の作業</a></nav>

## 作業の地図

- [1．データを一行で追う](lab-guide-02.html)
- [2．embeddingは行を選ぶ](lab-guide-03.html)
- [3．QKVをheadへ分ける](lab-guide-04.html)
- [4．残差とMLP](lab-guide-05.html)
- [5．損失と更新](lab-guide-06.html)
- [6．評価を学習から分ける](lab-guide-07.html)
- [7．保存されるものを確認](lab-guide-08.html)
- [自分で確かめる課題](lab-guide-09.html)
