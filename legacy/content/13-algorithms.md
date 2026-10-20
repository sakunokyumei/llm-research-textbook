{"title": "13 計算量・検索・SQLの入口", "part": "Pythonと研究の道具", "goal": "データ量に応じて処理方法を選び、集計する", "prereq": "10〜12", "subpages": ["13u-002", "13u-003", "13u-004", "13u-005", "13u-006", "13u-007", "13u-008", "13u-009", "13u-010", "13u-011", "13u-012", "13u-013"], "next": "13u-002", "previous": "12u-016", "microtitle": "13-1 計算量・O記法・二分探索", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "半分に絞る回数を数える"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/13ページ。

今回の用語をまとめて復習：[計算量・O記法・二分探索](beginner-glossary.html#concept-13-algorithms)。

## なぜ使うか

データ量に応じて処理方法を選び、集計するための一歩です。このページでは、半分に絞る回数を数えることを練習します。

## 意味と小さな例

入力が増えると処理回数がどう増えるかを計算量で考えます。O記法はその増え方の上界を表す記法。並べた名簿を半分ずつ探す二分探索なら、8件は最大約3回の半分化で一件へ絞れます。

:::check 半分に絞る回数を数える
16件の候補を毎回半分へ絞ると、16→8の後、1件になるまでどう続きますか。
:::answer
16→8→4→2→1で四回の半分化です。候補を順番に一件ずつ調べる増え方と比べられます。実装の比較回数には終了判定等も入ります。
:::



## 今日の区切りと戻る場所

確認問題で「半分に絞る回数を数える」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](12u-016.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](13-reader.html)

<section class="resume-note" data-lesson="13-algorithms"><h2>次回の再開メモ</h2><label for="resume-13-algorithms">できたこと・止まった一文・次にすること</label><textarea id="resume-13-algorithms" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="12u-016.html">前の小ページ</a><a href="13u-002.html">次の小ページ</a></nav>
