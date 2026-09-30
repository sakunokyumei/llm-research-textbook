# 実装ラボ：動かし、壊し、確かめる

すべてのCPUラボは合成データを使い、APIキーや外部モデルのダウンロードを必要としません。ブラウザ上では下の確率の実験を動かせます。Pythonラボは自分のPCで実行します。

## まず確率を動かしてみよう

三つの候補のscore（logit）を確率へ変換します。温度を下げる前に、どの候補がどれくらい選ばれやすくなるか予想してください。すべてのscoreへ同じ数を足したら、確率はどうなるでしょう。

<div class="playground">
<label>候補1のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="2" aria-label="候補1のscore"></label><br>
<label>候補2のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="1" aria-label="候補2のscore"></label><br>
<label>候補3のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="0" aria-label="候補3のscore"></label><br>
<label for="temperature">温度：<output id="temperature-value">1.0</output></label>
<input id="temperature" type="range" min="0.1" max="3" step="0.1" value="1">
<div id="softmax-output" aria-live="polite"></div>
</div>

同じ数を足してもsoftmaxは変わりません。温度を下げると最大scoreの候補へ集中します。温度は正解率を直接表す値ではありません。[28章](28-numerics.html)・[34章](34-generation.html)

## 0．実行の準備

[GitHubリポジトリ](https://github.com/sakunokyumei/llm-research-textbook)を取得します。WindowsではPowerShell、macOS/Linuxではterminalを開きます。コマンドは一行ずつ入力します。`cd`は作業フォルダを移る命令です。

```sh
git clone https://github.com/sakunokyumei/llm-research-textbook.git
cd llm-research-textbook
python -m venv .venv
```

Windowsの有効化は `.venv\Scripts\Activate.ps1`、macOS/Linuxは `source .venv/bin/activate`。Windowsで有効化が制限される場合、設定を変えず `.venv\Scripts\python.exe` を以後の`python`の代わりに使えます。Pythonが見つからない場合は[08章](08-python.html)へ戻ります。

```sh
python -m pip install torch==2.13.0 numpy==2.5.2
python -m unittest discover -s labs -v
```

制作時の実行環境はPython 3.14、PyTorch 2.13.0+cpu、NumPy 2.5.2です。OSやPython版によってwheelの提供状況が違うため、導入に失敗したら[PyTorch公式インストール案内](https://pytorch.org/get-started/locally/)で対応する組合せを確認し、実際の版を記録してください。GPUは不要です。テストは数秒〜数分を見込み、速度はPCによります。

## 1．数式と自動微分

```sh
python labs/math_checks.py
```

[math_checks.py](downloads/math_checks.py)は、通常のsoftmaxとonline計算、有限差分と自動微分、LoRAの凍結と勾配を比較します。制作時には全assertが通り、重み付き和は約5.056113、微分は約5.337499でした。

変更課題：scoreをすべて1000増やしても結果が変わらないか。有限差分のhを極端に小さくすると、誤差は必ず減るか。LoRAのBをゼロ以外で初期化するとAの最初の勾配はどうなるか。

## 2．byte BPEを自作する

```sh
python labs/bpe.py
```

[bpe.py](downloads/bpe.py)は頻出する隣接pairを順に結合します。初期語彙が256個のbyteなので、学習で見なかった日本語やemojiも符号化できます。復号して元の文字列に戻ることをassertします。大規模tokenizerの高速化・正規化・特殊token処理までは実装していない、読み通せる最小版です。

変更課題：merge数を0・5・20に変え、未使用文のtoken数を比べます。訓練文は固定し、評価文からmerge規則を学習しないでください。[29章](29-tokenization.html)

## 3．Tiny Transformerを学習する

```sh
python labs/tiny_transformer.py --steps 300 --seed 0 --out labs/runs/attention-0
```

[tiny_transformer.py](downloads/tiny_transformer.py)はtoken embedding、位置embedding、multi-head causal attention、MLP、残差、LayerNorm、AdamW、学習・評価・生成・checkpointを含みます。[コードを一行ずつ読む](lab-guide.html)と並べて学びます。

文書は`[BOS, A, noise, noise, noise, noise, separator, A, EOS]`。2〜5の四種類の記号から全1,024文書を作り、固定seedで文書単位に768/128/128へ分割します。separatorの後で最初のAをコピーするには、離れた情報が必要です。これは自然言語の巨大な事前学習モデルではなく、その計算と実験管理を学ぶモデルです。

保存先にはmetrics.jsonとcheckpoint.ptができます。前者は設定・版・データhash・指標、後者はモデル・optimizer・乱数・stepを含みます。自分で作成したcheckpointを読みます。

### 保存と再開

```sh
python labs/tiny_transformer.py --steps 100 --out labs/runs/resume-demo
python labs/tiny_transformer.py --steps 300 --resume labs/runs/resume-demo/checkpoint.pt --out labs/runs/resumed
```

`--steps`は追加回数ではなく最終的な合計です。resume時はcheckpointの設定を引き継ぎます。因果性・分割・連続学習との一致・学習成立を[test_labs.py](downloads/test_labs.py)で確認しています。同一CPU環境内の一致を確認したテストであり、別の機種やライブラリ版までbit単位で同じという保証ではありません。

### 日本語の文章でも学習する

```sh
python labs/text_lm.py --steps 300 --evaluate-test
```

[text_lm.py](downloads/text_lm.py)は同じTransformerを使い、「ねこは公園で赤い箱を見つけた。」のような512種類の合成文をbyteの列として学習します。384/64/64文書へ分割し、paddingの位置を損失から除きます。ダウンロードだけで実行する場合はtiny_transformer.pyも同じフォルダへ置いてください。

制作時の固定したseed0・300更新では、validation NLLが5.6787から0.1491、最終test NLLは0.1512でした。生成例は「ねこは川で小さな花を見つけた。」です。[設定・学習曲線・実測値](downloads/text_results.json)を配布します。単位はbyteとEOSであり、別のtokenizerのPPLとは直接比較しません。非常に限定された合成文法を学ぶ実験で、一般的な会話能力の証拠ではありません。

変更課題：場所や対象を増やす、学習時に一部の組合せを除く、文を長くする、の一つを選び、検証条件を先に決めます。byteを自由に生成すると不正なUTF-8になる可能性もあるため、コードはvalid_utf8を記録します。

## 4．ablationと複数seed

```sh
python labs/run_experiments.py
```

[run_experiments.py](downloads/run_experiments.py)は3条件×3seed、各300更新を実行します。数分程度を目安とし、出力先はlabs/runsです。制作時の[全9runのCSV](downloads/results.csv)を配布します。

|条件|copy正解率（seed 0 / 1 / 2）|validation NLL（同順）|
|---|---|---|
|Attentionあり|1.000 / 1.000 / 1.000|0.8751 / 0.8775 / 0.8850|
|位置embeddingなし|1.000 / 1.000 / 1.000|0.8815 / 0.8743 / 0.8819|
|Attentionなし|0.2266 / 0.2500 / 0.2500|1.0527 / 1.0457 / 1.0522|

**位置embeddingを外しても、この短い固定位置課題は解けました。** 予想と違う結果も隠さず、課題の容易さやcausal maskによる構造を考えます。これは位置表現が一般に不要だという証明ではありません。Attentionなしではtoken間の情報交換がなく、copyが難しくなります。外した部品のパラメータは保持しているため、総パラメータ数は同じでも有効な計算量は異なります。

NLLがゼロにならないのは、noise部分が予測不可能だからです。全token損失とcopy位置の正解率は、異なる側面を測っています。

```sh
python labs/paired_bootstrap.py labs/runs/attention-0/metrics.json labs/runs/no-attention-0/metrics.json
```

[paired_bootstrap.py](downloads/paired_bootstrap.py)は対応する文書を5,000回再抽出して、正解率差のpercentile区間を求めます。学習seedの揺れまで含む区間ではありません。設定を固定し終えたら`--evaluate-test`を付けた最終runでtestを評価し、それ以上の条件選びには使いません。

## 5．検索と報酬を独立に検証する

```sh
python labs/rag_eval.py
python labs/bandit.py
```

[rag_eval.py](downloads/rag_eval.py)は4文書からの語の一致に基づく検索と、根拠文の抽出を行います。制作時は4問でRecall@1とMRRが1でした。小さな意図的に簡単な集合なので、一般的な検索性能を示すものではありません。生成モデルは含みません。最後の「電話番号」という答えのない質問でも文書は返ります。検索順位が高いことと、答えがあることの違いを調べます。

[bandit.py](downloads/bandit.py)は成功確率0.2と0.8の二択でREINFORCEを実行します。3seedでよい選択肢への最終確率は約0.985、0.979、0.976でした。報酬そのものではなく、選択肢の対数確率を微分します。これはLLMのRLHF全体の実装ではなく、方策勾配の最小実験です。

## 6．独自実験へ

[研究計画テンプレート](downloads/research_template.md)を先に埋め、[53章](53-research-design.html)から[56章](56-capstone.html)に沿って、距離・語彙・データ量など一つの条件を変えます。GPUのTritonや分散学習へ進む際は、[追加実習](systems-lab.html)で前提と未検証の範囲を確認してください。
