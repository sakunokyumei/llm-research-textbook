# 3．Tiny Transformerを学習する

この実習の6/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

```sh
python labs/tiny_transformer.py --steps 300 --seed 0 --out labs/runs/attention-0
```

[tiny_transformer.py](downloads/tiny_transformer.py)はtoken embedding、位置embedding、multi-head causal attention、MLP、残差、LayerNorm、AdamW、学習・評価・生成・checkpointを含みます。[コードを一行ずつ読む](lab-guide.html)と並べて学びます。

文書は`[BOS, A, noise, noise, noise, noise, separator, A, EOS]`。2〜5の四種類の記号から全1,024文書を作り、固定seedで文書単位に768/128/128へ分割します。separatorの後で最初のAをコピーするには、離れた情報が必要です。これは自然言語の巨大な[事前学習](reference.html#term-pretrain)モデルではなく、その計算と実験管理を学ぶモデルです。

保存先にはmetrics.jsonとcheckpoint.ptができます。前者は設定・版・データhash・指標、後者はモデル・[optimizer](reference.html#term-optimizer)・乱数・stepを含みます。自分で作成したcheckpointを読みます。

### 保存と再開

```sh
python labs/tiny_transformer.py --steps 100 --out labs/runs/resume-demo
python labs/tiny_transformer.py --steps 300 --resume labs/runs/resume-demo/checkpoint.pt --out labs/runs/resumed
```

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-05.html">前の作業</a><a href="labs-07.html">次の作業</a></nav>
