{"title": "11 テストとデバッグで確かめる", "part": "Pythonと研究の道具", "goal": "最小例・期待値・例外から不具合を切り分ける", "prereq": "10", "subpages": ["11u-002", "11u-003", "11u-004", "11u-005", "11u-006", "11u-007", "11u-008", "11u-009", "11u-010"], "next": "11u-002", "previous": "10u-013", "microtitle": "11-1 テスト・仕様・assert", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "仕様に合う境界のテストを追加する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/10ページ。

今回の用語をまとめて復習：[テスト・仕様・assert](beginner-glossary.html#concept-11-debug)。

## なぜ使うか

最小例・期待値・例外から不具合を切り分けるための一歩です。このページでは、仕様に合う境界のテストを追加することを練習します。

## 意味と小さな例

仕様は期待する動作、テストはその動作を確かめる作業です。assert 2+3==5は成り立つことを確認します。負数も受け付ける仕様なら正数の確認だけでは足りません。

:::check 仕様に合う境界のテストを追加する
負数も足せるadd関数を、add(2,3)==5だけで確認しました。追加する入力と期待値を一つ書いてください。
:::answer
例えばadd(−2,3)==1です。正数だけの成功では、負数の符号を誤る実装を発見できません。空や型の扱いは別に仕様を決めます。
:::



## 今日の区切りと戻る場所

確認問題で「仕様に合う境界のテストを追加する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](10u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](11-reader.html)

<section class="resume-note" data-lesson="11-debug"><h2>次回の再開メモ</h2><label for="resume-11-debug">できたこと・止まった一文・次にすること</label><textarea id="resume-11-debug" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="10u-013.html">前の小ページ</a><a href="11u-002.html">次の小ページ</a></nav>
