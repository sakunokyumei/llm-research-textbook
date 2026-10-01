# 設定と関数の呼び方

この実習の4/7ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`@dataclass` は[クラス](reference.html#term-class)の設定値をまとめやすくするPythonの指定です。`seed: int = 0` はseedの型の目印と初期値。型の注釈だけでは不正な値を自動で拒否しません。`Config(seed=1)` で指定しなかった幅などは初期値になります。`asdict(cfg)` は設定を辞書に変換します。

`Config(**record)` の `**` はここではべき乗ではなく、辞書のキーを引数名に展開する記法です。`record={"seed":1}` なら `Config(seed=1)` と同じ指定です。`model,opt,rng = setup(cfg)` は第14章の三つの戻り値のアンパックです。

`[f(z) for z in (q,k,v)]` はq,k,vそれぞれへ同じ処理を適用した並びです。複数forの内包表記は組合せを列挙します。読みづらければ通常のforを重ねて書きます。`_` はこの処理で使わない値に付ける慣習的な名前で、特別な演算ではありません。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](python-reading-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="python-reading-03.html">前の作業</a><a href="python-reading-05.html">次の作業</a></nav>
