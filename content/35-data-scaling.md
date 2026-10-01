{"title": "35 データを作り、規模を見積もる", "part": "LLMを育てる・調整する", "goal": "データ来歴と計算予算を含めた事前学習計画を作る", "prereq": "13・22・29・33", "subpages": ["35u-002", "35u-003", "35u-004", "35u-005", "35u-006", "35u-007", "35u-008"], "next": "35u-002", "previous": "34u-010", "microtitle": "35-1 pipeline・品質フィルタ・packing", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "詰めた文書の境界を守る"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/8ページ。

今回の用語をまとめて復習：[pipeline・品質フィルタ・packing](beginner-glossary.html#concept-35-data-scaling)。

## なぜ使うか

データ来歴と計算予算を含めた事前学習計画を作るための一歩です。このページでは、詰めた文書の境界を守ることを練習します。

## 意味と小さな例

段階をつなぐ手順がpipeline、不要な例を除く条件が品質フィルタ、短い列をまとめて枠を使うのがpackingです。長さ2と3を5枠へ入れても、別文書の正解を見せない境界を守ります。

:::check 詰めた文書の境界を守る
二つの無関係な文書を一列へpackingしました。後の文書が前の文書を見てよいかを何で決めますか。
:::answer
課題の規約で決め、独立に扱うなら文書境界をまたがないmaskを使います。単に連結しただけでは独立性を保ちません。
:::



## 今日の区切りと戻る場所

確認問題で「詰めた文書の境界を守る」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](34u-010.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](35-reader.html)

<section class="resume-note" data-lesson="35-data-scaling"><h2>次回の再開メモ</h2><label for="resume-35-data-scaling">できたこと・止まった一文・次にすること</label><textarea id="resume-35-data-scaling" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="34u-010.html">前の小ページ</a><a href="35u-002.html">次の小ページ</a></nav>
