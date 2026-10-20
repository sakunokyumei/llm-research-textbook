{"title": "29 文章をトークンへ変える", "part": "言語モデルを作る", "goal": "文字・byte・BPEを区別し、データから語彙を学ぶ", "prereq": "10・13・23", "subpages": ["29u-002", "29u-003", "29u-004", "29u-005", "29u-006", "29u-007", "29u-008", "29u-009", "29u-010", "29u-011", "29u-012"], "next": "29u-002", "previous": "28u-013", "microtitle": "29-1 BPE・subword", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "決めた併合規則を適用する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/12ページ。

今回の用語をまとめて復習：[BPE・subword](beginner-glossary.html#concept-29-tokenization)。

## なぜ使うか

文字・byte・BPEを区別し、データから語彙を学ぶための一歩です。このページでは、決めた併合規則を適用することを練習します。

## 意味と小さな例

文章を分ける単位を作る方法の一つがBPE。小さい文字の組で頻出する隣接組をまとめます。単語全体より小さい単位がsubwordです。a b a bなら(a,b)をまとめてab abとできます。実装で頻度と同点の規約も記録します。

:::check 決めた併合規則を適用する
並びa b c a bで、隣接するa bをabへ併合するとどうなりますか。
:::answer
ab c abです。どの組を併合するかという規則を適用した結果で、必ず辞書の単語になるとは限りません。
:::



## 今日の区切りと戻る場所

確認問題で「決めた併合規則を適用する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](28u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](29-reader.html)

<section class="resume-note" data-lesson="29-tokenization"><h2>次回の再開メモ</h2><label for="resume-29-tokenization">できたこと・止まった一文・次にすること</label><textarea id="resume-29-tokenization" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="28u-013.html">前の小ページ</a><a href="29u-002.html">次の小ページ</a></nav>
