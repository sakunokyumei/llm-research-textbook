# 乱数・保存・実行を切り分ける

この実習の6/7ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`state_dict()` はモデルの重みなどの状態を名前付きの辞書として取り出し、`load_state_dict(...)` は対応する状態を読み込みます。[optimizer](reference.html#term-optimizer)にも同様の状態があります。`torch.save` はファイルへ書き、`torch.load(...,weights_only=True)` は読み込みの対象を制限して読む指定です。この指定も未知のファイルを全面的に安全にする保証ではありません。実習では自分が作ったファイルを読みます。

`@torch.no_grad()` はその関数の計算中に通常の[勾配](reference.html#term-gradient)追跡をしない指定です。第26章のwithで囲む形式と目的は同じです。`torch.cat` は指定した軸へ並びを連結し、`break` は今のループを終えます。

argparseは実行コマンドの `--steps 300` などを読む道具です。`add_argument` が受け付ける名前と型を定め、`parse_args()` が実際の値を読みます。`if __name__ == "__main__":` は、そのファイルを直接実行したときだけmainを呼ぶ目印。importして再利用するときには、その内側の実験を自動では始めません。

:::exercise 1・辞書から設定へ
record={"seed":2,"width":16}をConfigへ渡す指定を通常の引数へ展開してください。
:::answer
`Config(seed=2,width=16)` です。辞書にそのクラスが受け付けない名前があればエラーになるので、設定の名前を確認します。
:::

:::exercise 2・二軸の交換
qが(2,4,8,16)でbatch、head、time、特徴の順なら `q.transpose(-1,-2)` の形は何ですか。
:::answer
(2,4,16,8)です。batchとheadは入れ替えません。
:::

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](python-reading-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="python-reading-05.html">前の作業</a><a href="python-reading-07.html">次の作業</a></nav>
