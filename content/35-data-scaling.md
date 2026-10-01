{"title": "35 データを作り、規模を見積もる", "part": "LLMを育てる・調整する", "goal": "データ来歴と計算予算を含めた事前学習計画を作る", "prereq": "13・22・29・33", "subpages": ["35u-002", "35u-003", "35u-004", "35u-005", "35u-006", "35u-007", "35u-008"], "next": "35u-002", "previous": "34u-010", "microtitle": "35-1 pipeline・品質フィルタ・packing", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/8ページ。今日の目標：pipeline・品質フィルタ・packingの小例を一つ追う。

今日の言葉：[pipeline](beginner-glossary.html#concept-35-data-scaling)・[品質フィルタ](beginner-glossary.html#concept-35-data-scaling)・[packing](beginner-glossary.html#concept-35-data-scaling)。

## なぜ使うか

データ来歴と計算予算を含めた事前学習計画を作るための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

段階をつなぐ手順がpipeline、不要な例を除く条件が品質フィルタ、短い列をまとめて枠を使うのがpackingです。長さ2と3を5枠へ入れても、別文書の正解を見せない境界を守ります。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
段階をつなぐ手順がpipeline、不要な例を除く条件が品質フィルタ、短い列をまとめて枠を使うのがpackingです。長さ2と3を5枠へ入れても、別文書の正解を見せない境界を守ります。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](34-generation.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](35-reader.html)

<section class="resume-note" data-lesson="35-data-scaling"><h2>次回の再開メモ</h2><label for="resume-35-data-scaling">できたこと・止まった一文・次にすること</label><textarea id="resume-35-data-scaling" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="34-generation.html">前の小ページ</a><a href="35u-002.html">次の小ページ</a></nav>
