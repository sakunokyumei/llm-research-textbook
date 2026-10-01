{"title": "30 数えるモデルから、学ぶモデルへ", "part": "言語モデルを作る", "goal": "次トークン予測と教師信号のずらし方を理解する", "prereq": "23・29", "subpages": ["30u-002", "30u-003", "30u-004", "30u-005", "30u-006", "30u-007", "30u-008"], "next": "30u-002", "previous": "29u-012", "microtitle": "30-1 bigram・n-gram", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/8ページ。今日の目標：bigram・n-gramの小例を一つ追う。

今日の言葉：[bigram](beginner-glossary.html#concept-30-language-model)・[n-gram](beginner-glossary.html#concept-30-language-model)。

## なぜ使うか

次トークン予測と教師信号のずらし方を理解するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

直前一単位から次を数えるのがbigram。連続するn単位の組がn-gramです。a b a cならaの次はbとcが一回ずつ。長い前の情報を同じようには使えません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
直前一単位から次を数えるのがbigram。連続するn単位の組がn-gramです。a b a cならaの次はbとcが一回ずつ。長い前の情報を同じようには使えません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](29-tokenization.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](30-reader.html)

<section class="resume-note" data-lesson="30-language-model"><h2>次回の再開メモ</h2><label for="resume-30-language-model">できたこと・止まった一文・次にすること</label><textarea id="resume-30-language-model" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="29-tokenization.html">前の小ページ</a><a href="30u-002.html">次の小ページ</a></nav>
