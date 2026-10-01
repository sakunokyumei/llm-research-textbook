{"title": "30 数えるモデルから、学ぶモデルへ", "part": "言語モデルを作る", "goal": "次トークン予測と教師信号のずらし方を理解する", "prereq": "23・29", "subpages": ["30u-002", "30u-003", "30u-004", "30u-005", "30u-006", "30u-007", "30u-008"], "next": "30u-002", "previous": "29u-012", "microtitle": "30-1 bigram・n-gram", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "直前の記号別に次を数える"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/8ページ。

今回の用語をまとめて復習：[bigram・n-gram](beginner-glossary.html#concept-30-language-model)。

## なぜ使うか

次トークン予測と教師信号のずらし方を理解するための一歩です。このページでは、直前の記号別に次を数えることを練習します。

## 意味と小さな例

直前一単位から次を数えるのがbigram。連続するn単位の組がn-gramです。a b a cならaの次はbとcが一回ずつ。長い前の情報を同じようには使えません。

:::check 直前の記号別に次を数える
列a b a b a cで、aの次のbとcの回数と確率を求めてください。
:::answer
bは2回、cは1回で、確率は2/3と1/3です。最後までの隣接組を数え、a自体の頻度と混同しません。
:::



## 今日の区切りと戻る場所

確認問題で「直前の記号別に次を数える」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](29u-012.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](30-reader.html)

<section class="resume-note" data-lesson="30-language-model"><h2>次回の再開メモ</h2><label for="resume-30-language-model">できたこと・止まった一文・次にすること</label><textarea id="resume-30-language-model" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="29u-012.html">前の小ページ</a><a href="30u-002.html">次の小ページ</a></nav>
