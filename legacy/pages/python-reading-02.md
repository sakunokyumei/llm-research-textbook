# クラスを部品として使う

この実習の2/7ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`class Block(nn.Module):` は、PyTorchのModuleが持つ仕組みを引き継いだBlockを定義する書き方です。これを継承と呼びます。`super().__init__()` は引き継いだ側の初期化を呼び、PyTorchが重みなどを登録できるようにします。`self.norm1 = ...` のselfはこの部品そのものです。[第11章](11-debug.html)のCounterの状態と操作へ戻れます。

`forward(self,x)` は入力から出力を作る計算です。`model(x)` と呼ぶとPyTorchの仕組みを通してforwardが呼ばれます。`nn.ModuleList` は複数の部品を登録した並び。普通のリストへ入れるだけではモデルの重み登録と同じ扱いにならない場合があります。GELUはReLUとは違う滑らかな[活性化関数](reference.html#term-activation)で、数式は `xΦ(x)`、Φは標準正規分布の累積確率です。この実習では `nn.GELU()` がその計算を担い、手書きの近似へ勝手に置き換えません。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](python-reading-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="python-reading.html">前の作業</a><a href="python-reading-03.html">次の作業</a></nav>
