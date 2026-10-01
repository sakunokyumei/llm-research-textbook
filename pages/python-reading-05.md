# 乱数・保存・実行を切り分ける

この実習の5/7ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`{name: value for name,value in items}` は辞書の内包表記です。通常のforなら空の辞書を作り、各回に `result[name] = value` と書きます。`record.update(status="ok")` は辞書のstatusというキーの値を更新する操作。`*items` はリストやタプルの中では要素をその場へ展開します。関数の引数に使う `**record` とは展開する対象が違います。

`Path(...).mkdir(parents=True,exist_ok=True)` は途中のフォルダも含めて作り、既にある場合はその理由だけでは失敗させない指定です。`with path.open("w",...) as stream:` は書くファイルを開き、その字下げした範囲を終えると閉じます。csvのDictWriterは辞書の各キーを列名として表へ書く道具で、writeheaderは列名、writerowsは複数行を書きます。形式の意味は[第10章](10-data.html)へ戻れます。

`random.Random(31415).shuffle(docs)` は固定した開始設定で文書順を並べ替えます。`torch.Generator()` はPyTorchの乱数生成器、`randint` は整数を抽出する操作、`multinomial` は渡した非負の重みに[比例](reference.html#term-proportion)して候補番号を選ぶ操作です。抽出の考えは[第22章](22-statistics.html)、生成確率は[第34章](34-generation.html)で確認します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](python-reading-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="python-reading-04.html">前の作業</a><a href="python-reading-06.html">次の作業</a></nav>
