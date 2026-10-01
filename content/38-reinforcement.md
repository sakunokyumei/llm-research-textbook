{"title": "38 強化学習を、二つの選択肢から学ぶ", "part": "LLMを育てる・調整する", "goal": "方策・報酬・期待収益・方策勾配を区別する", "prereq": "18・20・23・26", "subpages": ["38u-002", "38u-003", "38u-004", "38u-005", "38u-006", "38u-007", "38u-008", "38u-009", "38u-010"], "next": "38u-002", "previous": "37u-008", "microtitle": "38-1 強化学習・state・action", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "状況と行動と報酬を分ける"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/10ページ。

今回の用語をまとめて復習：[強化学習・state・action](beginner-glossary.html#concept-38-reinforcement)。

## なぜ使うか

方策・報酬・期待収益・方策勾配を区別するための一歩です。このページでは、状況と行動と報酬を分けることを練習します。

## 意味と小さな例

状況stateで行動actionを選び、得た結果から改善するのが強化学習です。二つのボタンのどちらを押すか、押した後の得点で考えます。最初から各状況に正解の文章があるとは限りません。

:::check 状況と行動と報酬を分ける
ゲームで「残り一手」「右へ動く」「得点5」がありました。state、action、rewardへ対応させてください。
:::answer
残り一手等の状況がstate、右へ動くがaction、得点5がrewardです。行動前の状況と行動後の結果を分けます。
:::



## 今日の区切りと戻る場所

確認問題で「状況と行動と報酬を分ける」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](37u-008.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](38-reader.html)

<section class="resume-note" data-lesson="38-reinforcement"><h2>次回の再開メモ</h2><label for="resume-38-reinforcement">できたこと・止まった一文・次にすること</label><textarea id="resume-38-reinforcement" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="37u-008.html">前の小ページ</a><a href="38u-002.html">次の小ページ</a></nav>
