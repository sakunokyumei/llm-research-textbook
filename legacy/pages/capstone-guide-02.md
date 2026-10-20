# 1．どの距離を測るか、図で決める

この実習の2/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

文書を `[BOS, A, noiseがn個, separator, A, EOS]` とします。BOSは開始、EOSは終端、separatorは区切り、noiseはコピーに不要なランダム記号です。位置番号は0からです。

|場所|位置番号|
|---|---|
|最初のコピー対象A|1|
|separator|n+2|
|コピー先A|n+3|
|EOS|n+4|

入力の長さはn+4、文書全体はn+5。separatorの位置のlogitから、次のコピー先Aを予測します。最初のAからseparatorまでの距離はn+1、二つのAの距離はn+2です。論文や図で「距離」とだけ書かず、どちらかを定義してください。

元のTiny Transformerはnoise4個に固定されていました。新しい[distance_study.py](downloads/distance_study.py)は長さからseparatorの位置を求め、最長入力に合わせて位置[Embedding](reference.html#term-embedding)の行数も用意します。長さを変えても固定の位置6を採点する誤りを防ぎます。

:::exercise 1・位置を先に予想する
n=8のとき、文書長・入力長・separator・コピー先の位置を答えてください。
:::answer
文書長13、入力長12、separatorは10、コピー先は11です。separatorの出力からコピー先を予測します。
:::

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide.html">前の作業</a><a href="capstone-guide-03.html">次の作業</a></nav>
