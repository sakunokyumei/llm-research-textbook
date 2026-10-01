{"title": "23 情報量・損失・Perplexity", "part": "モデルを支える数学", "goal": "確率分布の評価を、対数と期待値から導く", "prereq": "07・20〜22", "subpages": ["23u-002", "23u-003", "23u-004", "23u-005", "23u-006", "23u-007", "23u-008", "23u-009", "23u-010", "23u-011", "23u-012"], "next": "23u-002", "previous": "22u-017", "microtitle": "23-1 自己情報量・math.log・math.exp", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/12ページ。今日の目標：自己情報量・math.log・math.expの小例を一つ追う。

今日の言葉：[自己情報量](beginner-glossary.html#concept-23-information)・[math.log](beginner-glossary.html#concept-23-information)・[math.exp](beginner-glossary.html#concept-23-information)。

## なぜ使うか

確率分布の評価を、対数と期待値から導くための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

起こる確率pの負の対数が自己情報量です。p=1なら0、1/2なら約0.693。math.logはln、math.expはeの乗算回数を使う指数です。exp(ln(2))は丸めの範囲で2になります。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
起こる確率pの負の対数が自己情報量です。p=1なら0、1/2なら約0.693。math.logはln、math.expはeの乗算回数を使う指数です。exp(ln(2))は丸めの範囲で2になります。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](22-statistics.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](23-reader.html)

<section class="resume-note" data-lesson="23-information"><h2>次回の再開メモ</h2><label for="resume-23-information">できたこと・止まった一文・次にすること</label><textarea id="resume-23-information" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="22-statistics.html">前の小ページ</a><a href="23u-002.html">次の小ページ</a></nav>
