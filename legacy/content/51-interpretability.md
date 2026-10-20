{"title": "51 モデルの内部を調べる", "part": "現代のLLMと評価", "goal": "観察と因果介入を区別し、解釈の仮説を検証する", "prereq": "16・18・27・31・50", "subpages": ["51u-002", "51u-003", "51u-004", "51u-005", "51u-006", "51u-007"], "next": "51u-002", "previous": "50u-010", "microtitle": "51-1 probe・activation patching・SAE", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "読める情報と因果を区別する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/7ページ。

今回の用語をまとめて復習：[probe・activation patching・SAE](beginner-glossary.html#concept-51-interpretability)。

## なぜ使うか

観察と因果介入を区別し、解釈の仮説を検証するための一歩です。このページでは、読める情報と因果を区別することを練習します。

## 意味と小さな例

内部から情報を読めるか調べるprobe、途中の値を入れ替える介入activation patching、疎な成分で再構成するSAEを分けます。途中の値を0へして答えが変わっても、どこを変えたか、対照は何かを記録しないと原因を判定できません。

:::check 読める情報と因果を区別する
probeで内部から正解ラベルを読めました。それでモデル自身がその情報を回答に使ったと証明できますか。
:::answer
証明できません。情報の存在と利用の因果は別です。介入と対照を設計し、介入が他の性質も壊していないか調べます。
:::



## 今日の区切りと戻る場所

確認問題で「読める情報と因果を区別する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](50u-010.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](51-reader.html)

<section class="resume-note" data-lesson="51-interpretability"><h2>次回の再開メモ</h2><label for="resume-51-interpretability">できたこと・止まった一文・次にすること</label><textarea id="resume-51-interpretability" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="50u-010.html">前の小ページ</a><a href="51u-002.html">次の小ページ</a></nav>
