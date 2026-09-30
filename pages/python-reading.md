# 研究コードへ進むためのPythonの橋

完成したモデルは、式の計算以外に設定・保存・実行手順を持ちます。このページは[第32章](32-transformer.html)・[第33章](33-training.html)から使う補習です。[Tiny Transformerの解説](lab-guide.html)とソースを並べます。新しい記法は、次の短い形へ戻して読んでください。

## クラスを部品として使う

`class Block(nn.Module):` は、PyTorchのModuleが持つ仕組みを引き継いだBlockを定義する書き方です。これを継承と呼びます。`super().__init__()` は引き継いだ側の初期化を呼び、PyTorchが重みなどを登録できるようにします。`self.norm1 = ...` のselfはこの部品そのものです。[第11章](11-debug.html)のCounterの状態と操作へ戻れます。

`forward(self,x)` は入力から出力を作る計算です。`model(x)` と呼ぶとPyTorchの仕組みを通してforwardが呼ばれます。`nn.ModuleList` は複数の部品を登録した並び。普通のリストへ入れるだけではモデルの重み登録と同じ扱いにならない場合があります。GELUはReLUとは違う滑らかな[活性化関数](reference.html#term-activation)で、数式は `xΦ(x)`、Φは標準正規分布の累積確率です。この実習では `nn.GELU()` がその計算を担い、手書きの近似へ勝手に置き換えません。

## 表を分けて、また戻す

|コード|小さい例と意味|
|---|---|
|`chunk(3,dim=-1)`|最後の幅12を4ずつQ,K,Vへ分ける。このモデルでは3等分できる幅を用意する|
|`transpose(1,2)`|(B,T,H,d_h)のTとHを交換し(B,H,T,d_h)へ|
|`transpose(-1,-2)`|最後の二軸だけを交換する。四次元の.Tで代用しない|
|`contiguous()`|軸交換後の値を連続した配置にそろえる。値の意味やshapeは変えない|
|`reshape(-1,7)`|要素数が合うよう最初の長さを自動計算し、候補7個の行へまとめる|
|`argmax(-1)`|末尾の候補のうち最大の値がある位置番号を選ぶ|
|`eq(other)`|otherと等しい位置をTrueにする|
|`tolist()`|テンソルの値をPythonのリストへ移す|

たとえばlogitが(B=2,T=3,V=7)なら、[損失](reference.html#term-loss)に渡す形は(6,7)、正解IDは(6,)です。候補の軸を一緒に潰して(42,)へするのは違う計算です。復習は[第16章](16-tensors.html)・[第31章](31-attention.html)へ。

## 設定と関数の呼び方

`@dataclass` は[クラス](reference.html#term-class)の設定値をまとめやすくするPythonの指定です。`seed: int = 0` はseedの型の目印と初期値。型の注釈だけでは不正な値を自動で拒否しません。`Config(seed=1)` で指定しなかった幅などは初期値になります。`asdict(cfg)` は設定を辞書に変換します。

`Config(**record)` の `**` はここではべき乗ではなく、辞書のキーを引数名に展開する記法です。`record={"seed":1}` なら `Config(seed=1)` と同じ指定です。`model,opt,rng = setup(cfg)` は第14章の三つの戻り値のアンパックです。

`[f(z) for z in (q,k,v)]` はq,k,vそれぞれへ同じ処理を適用した並びです。複数forの内包表記は組合せを列挙します。読みづらければ通常のforを重ねて書きます。`_` はこの処理で使わない値に付ける慣習的な名前で、特別な演算ではありません。

## 乱数・保存・実行を切り分ける

`{name: value for name,value in items}` は辞書の内包表記です。通常のforなら空の辞書を作り、各回に `result[name] = value` と書きます。`record.update(status="ok")` は辞書のstatusというキーの値を更新する操作。`*items` はリストやタプルの中では要素をその場へ展開します。関数の引数に使う `**record` とは展開する対象が違います。

`Path(...).mkdir(parents=True,exist_ok=True)` は途中のフォルダも含めて作り、既にある場合はその理由だけでは失敗させない指定です。`with path.open("w",...) as stream:` は書くファイルを開き、その字下げした範囲を終えると閉じます。csvのDictWriterは辞書の各キーを列名として表へ書く道具で、writeheaderは列名、writerowsは複数行を書きます。形式の意味は[第10章](10-data.html)へ戻れます。

`random.Random(31415).shuffle(docs)` は固定した開始設定で文書順を並べ替えます。`torch.Generator()` はPyTorchの乱数生成器、`randint` は整数を抽出する操作、`multinomial` は渡した非負の重みに[比例](reference.html#term-proportion)して候補番号を選ぶ操作です。抽出の考えは[第22章](22-statistics.html)、生成確率は[第34章](34-generation.html)で確認します。

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

## 見つからない記法に出会ったら

`try`の後の`finally`は、その処理が成功した場合も途中で失敗した場合も実行する片付けの場所です。観測の[hook](reference.html#term-hook)を解除する例で使います。`enumerate(values)` は位置番号と値を組で返す操作で、文書別の失敗を記録するときに使います。`torch.isfinite(x)` はNaNや無限大ではない位置をTrueにする検査で、第28章の非有限値を探す操作へ対応します。

名前・入力・出力・[shape](reference.html#term-tensor)をメモし、一行だけの例へ縮めます。「コードが動いた」と「各行を説明できる」は別に確認します。部品から学習へつなぐ順番は[lab-guide](lab-guide.html)へ戻ってください。

仕様の参照：[Python dataclasses](https://docs.python.org/3/library/dataclasses.html)・[argparse](https://docs.python.org/3/library/argparse.html)・[PyTorch Module](https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html)。
