{"title": "09 条件・繰り返し・関数", "part": "Pythonと研究の道具", "goal": "小さな処理を分け、繰り返しに適用する", "prereq": "08", "subpages": ["09u-002", "09u-003", "09u-004", "09u-005", "09u-006", "09u-007", "09u-008", "09u-009", "09u-010"], "next": "09u-002", "previous": "08u-016", "microtitle": "09-1 if・else", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "条件の境界を判定する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/10ページ。

今回の用語をまとめて復習：[if・else](beginner-glossary.html#concept-09-control)。

## なぜ使うか

小さな処理を分け、繰り返しに適用するための一歩です。このページでは、条件の境界を判定することを練習します。

## 意味と小さな例

条件を満たす側と、それ以外の側を選びます。price=100でprice>80ならif側です。elseはそれ以外。境界の80では>80は成り立ちません。

:::check 条件の境界を判定する
条件がprice>=100のとき、price=100はif側とelse側のどちらへ進みますか。price>100ならどう変わりますか。
:::answer
>=100なら等しい場合も含むのでif側、>100なら100は含まずelse側です。境界の値を一つ試すと条件の差が分かります。
:::



## 今日の区切りと戻る場所

確認問題で「条件の境界を判定する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](08u-016.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](09-reader.html)

<section class="resume-note" data-lesson="09-control"><h2>次回の再開メモ</h2><label for="resume-09-control">できたこと・止まった一文・次にすること</label><textarea id="resume-09-control" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="08u-016.html">前の小ページ</a><a href="09u-002.html">次の小ページ</a></nav>
