{"title": "42 分散学習と並列化", "part": "効率と現代のアーキテクチャ", "goal": "分ける対象と通信の意味を区別し、実効バッチを計算する", "prereq": "26・33・41", "subpages": ["42u-002", "42u-003", "42u-004", "42u-005", "42u-006", "42u-007", "42u-008", "42u-009", "42u-010", "42u-011", "42u-012", "42u-013", "42u-014"], "next": "42u-002", "previous": "41u-011", "microtitle": "42-1 Data Parallel・DDP・rank", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "同数データの勾配を平均する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/14ページ。

今回の用語をまとめて復習：[Data Parallel・DDP・rank](beginner-glossary.html#concept-42-distributed)。

## なぜ使うか

分ける対象と通信の意味を区別し、実効バッチを計算するための一歩です。このページでは、同数データの勾配を平均することを練習します。

## 意味と小さな例

各装置が同じモデルで別データを処理する方式がData Parallel、そのPyTorchの仕組みがDDP。参加する実行の番号がrankです。二装置の同数データの勾配2,6なら平均4で同じ更新を行います。

:::check 同数データの勾配を平均する
二つのrankが同じ数の例から勾配4と8を得ました。平均して更新に使う値は何ですか。
:::answer
6です。合計12と平均6を区別します。例数が異なる場合には、同じ単純平均でよいかを再確認します。
:::



## 今日の区切りと戻る場所

確認問題で「同数データの勾配を平均する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](41u-011.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](42-reader.html)

<section class="resume-note" data-lesson="42-distributed"><h2>次回の再開メモ</h2><label for="resume-42-distributed">できたこと・止まった一文・次にすること</label><textarea id="resume-42-distributed" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="41u-011.html">前の小ページ</a><a href="42u-002.html">次の小ページ</a></nav>
