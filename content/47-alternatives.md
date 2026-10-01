{"title": "47 状態空間モデルと拡散言語モデル", "part": "効率と現代のアーキテクチャ", "goal": "情報の保持方法と生成の順序を分けて比較できる", "prereq": "15・20・31・43", "subpages": ["47u-002", "47u-003", "47u-004", "47u-005", "47u-006", "47u-007"], "next": "47u-002", "previous": "46u-009", "microtitle": "47-1 SSM・再帰的状態・scan", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "再帰状態を一段ずつ更新する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/7ページ。

今回の用語をまとめて復習：[SSM・再帰的状態・scan](beginner-glossary.html#concept-47-alternatives)。

## なぜ使うか

情報の保持方法と生成の順序を分けて比較できるための一歩です。このページでは、再帰状態を一段ずつ更新することを練習します。

## 意味と小さな例

小さな状態を更新して列を処理する模型がSSM。前の状態から次を作るのが再帰的状態の更新、それを順に進める操作がscanです。状態0へ入力1,2,3を足す模型なら1,3,6。全部の過去をそのまま保存する方式ではありません。

:::check 再帰状態を一段ずつ更新する
状態hをh←0.5h+xで更新します。初期h=0、入力が2、4の順なら各段の状態はいくつですか。
:::answer
一段目2、二段目0.5×2+4=5です。過去は状態を通じて次へ影響します。この模型だけで全てのSSMの性能は分かりません。
:::



## 今日の区切りと戻る場所

確認問題で「再帰状態を一段ずつ更新する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](46u-009.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](47-reader.html)

<section class="resume-note" data-lesson="47-alternatives"><h2>次回の再開メモ</h2><label for="resume-47-alternatives">できたこと・止まった一文・次にすること</label><textarea id="resume-47-alternatives" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="46u-009.html">前の小ページ</a><a href="47u-002.html">次の小ページ</a></nav>
