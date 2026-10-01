{"title": "11 テストとデバッグで確かめる", "part": "Pythonと研究の道具", "goal": "最小例・期待値・例外から不具合を切り分ける", "prereq": "10", "subpages": ["11u-002", "11u-003", "11u-004", "11u-005", "11u-006", "11u-007", "11u-008", "11u-009", "11u-010"], "next": "11u-002", "previous": "10u-013", "microtitle": "11-1 テスト・仕様・assert", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/10ページ。今日の目標：テスト・仕様・assertの小例を一つ追う。

今日の言葉：[テスト](beginner-glossary.html#concept-11-debug)・[仕様](beginner-glossary.html#concept-11-debug)・[assert](beginner-glossary.html#concept-11-debug)。

## なぜ使うか

最小例・期待値・例外から不具合を切り分けるための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

仕様は期待する動作、テストはその動作を確かめる作業です。assert 2+3==5は成り立つことを確認します。負数も受け付ける仕様なら正数の確認だけでは足りません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
仕様は期待する動作、テストはその動作を確かめる作業です。assert 2+3==5は成り立つことを確認します。負数も受け付ける仕様なら正数の確認だけでは足りません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](10-data.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](11-reader.html)

<section class="resume-note" data-lesson="11-debug"><h2>次回の再開メモ</h2><label for="resume-11-debug">できたこと・止まった一文・次にすること</label><textarea id="resume-11-debug" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="10-data.html">前の小ページ</a><a href="11u-002.html">次の小ページ</a></nav>
