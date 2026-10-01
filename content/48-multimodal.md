{"title": "48 多言語と画像・音声を扱う", "part": "現代のLLMと評価", "goal": "入力の表現と目的関数を説明し、言語別・モダリティ別に評価できる", "prereq": "23・29・32・36", "subpages": ["48u-002", "48u-003", "48u-004", "48u-005", "48u-006", "48u-007", "48u-008", "48u-009"], "next": "48u-002", "previous": "47u-007", "microtitle": "48-1 モダリティ・色チャネル・patch", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "画像の分割数と一片の数を求める"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/9ページ。

今回の用語をまとめて復習：[モダリティ・色チャネル・patch](beginner-glossary.html#concept-48-multimodal)。

## なぜ使うか

入力の表現と目的関数を説明し、言語別・モダリティ別に評価できるための一歩です。このページでは、画像の分割数と一片の数を求めることを練習します。

## 意味と小さな例

文章、画像、音声等の入力の種類がモダリティ。色を表す成分が色チャネル、画像の小片がpatchです。8×8画像を4×4に区切れば四片。色三成分なら各片は4×4×3=48数です。

:::check 画像の分割数と一片の数を求める
12×12画像を6×6のpatchへ分け、色3チャネルなら何片で一片は何個の数ですか。
:::answer
四片で、一片は6×6×3=108個です。片の個数と一片の幅を分けます。
:::



## 今日の区切りと戻る場所

確認問題で「画像の分割数と一片の数を求める」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](47u-007.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](48-reader.html)

<section class="resume-note" data-lesson="48-multimodal"><h2>次回の再開メモ</h2><label for="resume-48-multimodal">できたこと・止まった一文・次にすること</label><textarea id="resume-48-multimodal" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="47u-007.html">前の小ページ</a><a href="48u-002.html">次の小ページ</a></nav>
