{"title": "16 テンソル・固有値・低ランク", "part": "モデルを支える数学", "goal": "多次元配列の軸と平均する方向を確認する", "prereq": "15", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "next": "16u-002", "previous": "15u-019", "subpages": ["16u-002", "16u-003", "16u-004", "16u-005", "16u-006", "16u-007", "16u-008", "16u-009", "16u-010", "16u-012", "16u-014", "16u-016", "16u-018", "16u-020", "16u-021"], "microtitle": "16-1 テンソル・バッチ・shape", "microgoal": "shapeから要素数を求める"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/16ページ。

今回の用語をまとめて復習：[テンソル・バッチ・shape](beginner-glossary.html#concept-16-tensors)。

## なぜ使うか

多次元配列の軸と平均する方向を確認するための一歩です。このページでは、shapeから要素数を求めることを練習します。

## 意味と小さな例

数を複数の軸に沿って並べるテンソルの各軸の長さがshape。複数の例をまとめたものがバッチです。二例、各三位置、各四数なら形(2,3,4)で要素数24です。

:::check shapeから要素数を求める
バッチ3、位置4、各位置の数5ならshapeと総要素数を答えてください。
:::answer
shapeは(3,4,5)、要素数は3×4×5=60です。軸ごとの意味もこの順序で記録します。
:::



## 今日の区切りと戻る場所

確認問題で「shapeから要素数を求める」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](15u-019.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](16-reader.html)

<section class="resume-note" data-lesson="16-tensors"><h2>次回の再開メモ</h2><label for="resume-16-tensors">できたこと・止まった一文・次にすること</label><textarea id="resume-16-tensors" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="15u-019.html">前の小ページ</a><a href="16u-002.html">次の小ページ</a></nav>
