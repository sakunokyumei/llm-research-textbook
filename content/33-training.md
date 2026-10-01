{"title": "33 小さな言語モデルを学習・再開する", "part": "言語モデルを作る", "goal": "データ・損失・更新・保存・再開を一周する", "prereq": "12・26・32", "subpages": ["33u-002", "33u-003", "33u-004", "33u-005", "33u-006", "33u-007", "33u-008", "33u-009", "33u-010", "33u-011", "33u-012", "33u-013", "33u-014", "33u-015", "33u-016", "33u-017", "33u-018", "33u-019"], "next": "33u-002", "previous": "32u-016", "microtitle": "33-1 プロセス・config・metrics", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "設定と測定結果を別々に保存する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/19ページ。

今回の用語をまとめて復習：[プロセス・config・metrics](beginner-glossary.html#concept-33-training)。

## なぜ使うか

データ・損失・更新・保存・再開を一周するための一歩です。このページでは、設定と測定結果を別々に保存することを練習します。

## 意味と小さな例

実行中のプログラムがプロセス、実験設定がconfig、測った値がmetricsです。学習率0.1は設定、誤差0.2は結果。結果を見て設定を変えた場合は別の実験として記録します。

:::check 設定と測定結果を別々に保存する
steps=100とloss=0.4をconfigとmetricsへ分けてください。
:::answer
更新回数steps=100はconfig、測ったloss=0.4はmetricsです。損失を見て更新回数を変えたら、その試行も別の設定として残します。
:::



## 今日の区切りと戻る場所

確認問題で「設定と測定結果を別々に保存する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](32u-016.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](33-reader.html)

<section class="resume-note" data-lesson="33-training"><h2>次回の再開メモ</h2><label for="resume-33-training">できたこと・止まった一文・次にすること</label><textarea id="resume-33-training" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="32u-016.html">前の小ページ</a><a href="33u-002.html">次の小ページ</a></nav>
