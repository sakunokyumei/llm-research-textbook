{"title": "16 テンソル・固有値・低ランク", "part": "モデルを支える数学", "goal": "多次元配列の軸と平均する方向を確認する", "prereq": "15", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "next": "16u-002", "previous": "15u-020", "subpages": ["16u-002", "16u-003", "16u-004", "16u-005", "16u-006", "16u-007", "16u-008", "16u-009", "16u-010", "16u-011", "16u-012", "16u-013", "16u-014", "16u-015", "16u-016", "16u-017", "16u-018", "16u-019", "16u-020", "16u-021", "16u-022"], "microtitle": "16-1 テンソル・バッチ・shape"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/22ページ。今日の目標：テンソル・バッチ・shapeの小例を一つ追う。

今日の言葉：[テンソル](beginner-glossary.html#concept-16-tensors)・[バッチ](beginner-glossary.html#concept-16-tensors)・[shape](beginner-glossary.html#concept-16-tensors)。

## なぜ使うか

多次元配列の軸と平均する方向を確認するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

数を複数の軸に沿って並べるテンソルの各軸の長さがshape。複数の例をまとめたものがバッチです。二例、各三位置、各四数なら形(2,3,4)で要素数24です。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
数を複数の軸に沿って並べるテンソルの各軸の長さがshape。複数の例をまとめたものがバッチです。二例、各三位置、各四数なら形(2,3,4)で要素数24です。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](15-matrices.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](16-reader.html)

<section class="resume-note" data-lesson="16-tensors"><h2>次回の再開メモ</h2><label for="resume-16-tensors">できたこと・止まった一文・次にすること</label><textarea id="resume-16-tensors" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="15-matrices.html">前の小ページ</a><a href="16u-002.html">次の小ページ</a></nav>
