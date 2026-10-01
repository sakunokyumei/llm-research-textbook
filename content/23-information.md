{"title": "23 情報量・損失・Perplexity", "part": "モデルを支える数学", "goal": "確率分布の評価を、対数と期待値から導く", "prereq": "07・20〜22", "subpages": ["23u-002", "23u-003", "23u-004", "23u-005", "23u-006", "23u-007", "23u-008", "23u-009", "23u-010", "23u-011", "23u-012"], "next": "23u-002", "previous": "22u-017", "microtitle": "23-1 自己情報量・math.log・math.exp", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "予測の確率を自己情報量へ直す"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/12ページ。

今回の用語：[自己情報量](beginner-glossary.html#self-information)・[math.log](beginner-glossary.html#math-log)・[math.exp](beginner-glossary.html#math-exp)。

## なぜ使うか

確率分布の評価を、対数と期待値から導くための一歩です。このページでは、予測の確率を自己情報量へ直すことを練習します。

## 確率の低い出来事が起きると、驚きが大きい

必ず起きる出来事より、起こりにくい出来事が起きたときの方が意外です。この「予測から見た意外さ」を数にする一つの方法が自己情報量です。日常の大切さや役立ち度を測っているわけではありません。

出来事の確率をpと書きます。0<p≤1で、自己情報量は **I(p)=−ln(p)** です。lnは[自然対数](07u-005.html)、負号は符号を反転する記号です。p=1なら0、p=1/2なら約0.693、p=1/4なら約1.386と、起こりにくいほど大きくなります。自然対数を使う単位をnatと呼びます。p=0は有限の対数を持たず、pが0へ近づくと情報量は限りなく大きくなります。

Pythonのmath.log(p)は、底を省くとln(p)を返します。math.exp(x)は**eˣを返す指数関数**です。eは約2.718の定数。x=2ならe×eですが、xは整数だけではありません。x=1/2なら√e、x=−1なら1/eです。「乗算回数」とだけ説明すると、これらの指数を扱えません。

expとlnは逆の対応なので、exp(ln(2))は丸め誤差の範囲で2になります。情報量Iから確率へ戻すならp=exp(−I)と負号を付けます。

[Python公式：expとlogの定義](https://docs.python.org/3/library/math.html#math.exp)

:::check 予測の確率を自己情報量へ直す
ln(1/4)≈−1.386です。確率1/4の出来事の自己情報量と、exp(−1.386)の近似値を答えてください。
:::answer
自己情報量は−ln(1/4)≈1.386nat。exp(−1.386)≈0.25で元の確率へ戻ります。expへ入れるのは情報量の負号付きの値です。
:::



## 今日の区切りと戻る場所

確認問題で「予測の確率を自己情報量へ直す」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](22u-017.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](23-reader.html)

<section class="resume-note" data-lesson="23-information"><h2>次回の再開メモ</h2><label for="resume-23-information">できたこと・止まった一文・次にすること</label><textarea id="resume-23-information" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="22u-017.html">前の小ページ</a><a href="23u-002.html">次の小ページ</a></nav>
